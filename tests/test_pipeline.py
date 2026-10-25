import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from pipeline.setup_windows import configure_code, merge_desktop_config, server_entry, reject_package_addons
from pipeline.runtime import SERVER_ARGS, SERVER_ENV, parse_blender_report, tool_text
from pipeline.configure_gpu import select_devices


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'Claude' / 'config.json'
        self.entry = server_entry(r'C:\Users\Friend Name\.local\bin\uv.exe')

    def test_dry_run_creates_no_files(self):
        result = merge_desktop_config(self.path, self.entry)
        self.assertTrue(result['changed'])
        self.assertFalse(self.path.parent.exists())

    def test_merge_preserves_other_servers_and_settings_and_backs_up_bytes(self):
        self.path.parent.mkdir()
        original = b'{"theme":"dark","mcpServers":{"other":{"command":"keep"}}}\n'
        self.path.write_bytes(original)
        result = merge_desktop_config(self.path, self.entry, apply=True)
        saved = json.loads(self.path.read_text())
        self.assertEqual(saved['theme'], 'dark')
        self.assertEqual(saved['mcpServers']['other'], {'command': 'keep'})
        self.assertEqual(saved['mcpServers']['blender']['command'], r'C:\Users\Friend Name\.local\bin\uv.exe')
        self.assertEqual(Path(result['backup']).read_bytes(), original)

    def test_client_uses_frozen_project_environment_outside_current_directory(self):
        args = self.entry['args']
        self.assertEqual(args[:2], ['run', '--frozen'])
        project = Path(args[args.index('--project') + 1])
        self.assertTrue(project.is_absolute())
        self.assertTrue((project / 'uv.lock').is_file())
        self.assertEqual(args[-1], 'mcp-for-blender')

    def test_setup_and_mcp_launcher_use_the_same_python_installation(self):
        uv = shutil.which('uv')
        self.assertIsNotNone(uv, 'Run the tests under uv as documented')
        result = subprocess.run(
            [uv, *SERVER_ARGS[:-1], 'python', '-c', 'import sys; print(sys.base_prefix)'],
            cwd=self.temp.name, env={**os.environ, **SERVER_ENV},
            capture_output=True, text=True, check=True, timeout=90)
        self.assertEqual(Path(result.stdout.strip()).resolve(), Path(sys.base_prefix).resolve())

    def test_second_apply_is_idempotent(self):
        merge_desktop_config(self.path, self.entry, apply=True)
        before = self.path.read_bytes()
        result = merge_desktop_config(self.path, self.entry, apply=True)
        self.assertFalse(result['changed'])
        self.assertEqual(self.path.read_bytes(), before)
        self.assertNotIn('backup', result)

    def test_conflicting_server_is_not_replaced_without_explicit_flag(self):
        self.path.parent.mkdir()
        original = b'{"mcpServers":{"blender":{"command":"another-server"}}}'
        self.path.write_bytes(original)
        with self.assertRaisesRegex(ValueError, 'already exists'):
            merge_desktop_config(self.path, self.entry, apply=True)
        self.assertEqual(self.path.read_bytes(), original)

    def test_explicit_replacement_preserves_unrelated_fields(self):
        self.path.parent.mkdir()
        self.path.write_text('{"theme":"dark","mcpServers":{"blender":{"command":"old"}}}')
        merge_desktop_config(self.path, self.entry, apply=True, replace=True)
        self.assertEqual(json.loads(self.path.read_text())['theme'], 'dark')

    def test_invalid_json_or_non_object_servers_are_never_overwritten(self):
        self.path.parent.mkdir()
        for value in ['{broken', '{"mcpServers":[]}', '[]']:
            with self.subTest(value=value):
                self.path.write_text(value)
                with self.assertRaises(ValueError):
                    merge_desktop_config(self.path, self.entry, apply=True)
                self.assertEqual(self.path.read_text(), value)

    def test_failed_code_replacement_restores_original_config(self):
        self.path.parent.mkdir()
        original = b'{"theme":"dark","mcpServers":{"blender":{"command":"old"}}}'
        self.path.write_bytes(original)

        def cli(command, **kwargs):
            if 'remove' in command:
                self.path.write_text('{"theme":"dark","mcpServers":{}}')
                return
            raise RuntimeError('CLI add failed')

        with patch('pipeline.setup_windows.subprocess.run', side_effect=cli):
            with self.assertRaisesRegex(RuntimeError, 'CLI add failed'):
                configure_code('claude', self.path, self.entry, replace=True)
        self.assertEqual(self.path.read_bytes(), original)

    def test_failed_first_code_install_removes_partial_config(self):
        def cli(command, **kwargs):
            self.path.parent.mkdir()
            self.path.write_text('{"mcpServers":{}}')
            raise RuntimeError('CLI stopped after partial write')

        with patch('pipeline.setup_windows.subprocess.run', side_effect=cli):
            with self.assertRaisesRegex(RuntimeError, 'partial write'):
                configure_code('claude', self.path, self.entry)
        self.assertFalse(self.path.exists())

    def test_old_package_addon_is_reported_before_installing_a_second_copy(self):
        addons = Path(self.temp.name) / 'addons'
        package = addons / 'old_mcp' / '__init__.py'
        package.parent.mkdir(parents=True)
        package.write_text('bl_info = {"name": "Blender MCP"}\n')
        with self.assertRaisesRegex(RuntimeError, 'package add-on'):
            reject_package_addons(addons)
        self.assertEqual(list(addons.iterdir()), [package.parent])


class ResultTests(unittest.TestCase):
    def test_blender_report_ignores_log_lines_and_requires_success(self):
        report = parse_blender_report('Blender startup\nHOLLOWPURPLE_RESULT {"ok":true,"version":[5,2,2]}\nBlender quit\n')
        self.assertEqual(report['version'], [5, 2, 2])
        with self.assertRaisesRegex(RuntimeError, 'No result'):
            parse_blender_report('Blender crashed')
        with self.assertRaisesRegex(RuntimeError, 'OptiX missing'):
            parse_blender_report('HOLLOWPURPLE_RESULT {"ok":false,"error":"OptiX missing"}')

    def test_mcp_text_error_does_not_pass_as_success(self):
        for content in ['Error executing code: Not connected to Blender', 'Error checking addon status: refused', 'Rejected by safe mode - blocked']:
            result = SimpleNamespace(isError=False, content=[SimpleNamespace(type='text', text=content)])
            with self.subTest(content=content), self.assertRaises(RuntimeError):
                tool_text(result)
        result = SimpleNamespace(isError=True, content=[SimpleNamespace(type='text', text='failure')])
        with self.assertRaises(RuntimeError):
            tool_text(result)
        good = SimpleNamespace(isError=False, content=[SimpleNamespace(type='text', text='Code executed successfully: done')])
        self.assertEqual(tool_text(good), 'Code executed successfully: done')


class DeviceTests(unittest.TestCase):
    def test_selects_only_requested_optix_gpu_and_disables_cpu_and_cuda(self):
        devices = [SimpleNamespace(name=n, type=t, use=True) for n, t in [
            ('NVIDIA GeForce RTX 4090', 'OPTIX'),
            ('NVIDIA GeForce RTX 4090', 'CUDA'), ('CPU', 'CPU'),
            ('Other GPU', 'OPTIX')]]
        select_devices(devices, 'OPTIX', '4090')
        self.assertEqual([d.use for d in devices], [True, False, False, False])

    def test_missing_target_fails_without_silently_enabling_cpu(self):
        devices = [SimpleNamespace(name='CPU', type='CPU', use=False)]
        with self.assertRaisesRegex(RuntimeError, 'not found'):
            select_devices(devices, 'OPTIX', '4090')
        self.assertFalse(devices[0].use)


if __name__ == '__main__':
    unittest.main()
