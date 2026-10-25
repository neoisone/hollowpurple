"""Pinned Windows setup. Defaults to inspection; --apply performs the setup."""

import argparse
import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from importlib.metadata import version
from pathlib import Path

from blender_mcp.addon_manager import find_existing_addon_installs, install_addon
from blender_mcp.setup_cli import (
    ConfigError, blender_is_running, blender_version, detect_clients,
    enable_addon_headless, find_blender_executables, read_json_config,
    safe_to_save_prefs,
)

from .runtime import SERVER_ARGS, server_environment, run_blender, script_path

ADDON_SHA256 = 'eb0facf69781a30e69792532087d8d41c6a14fcd323353250abe7988ee297fa5'


def server_entry(uv):
    return {'command': str(uv), 'args': list(SERVER_ARGS), 'env': server_environment()}


def reject_package_addons(addons):
    packages = [str(path) for path in find_existing_addon_installs([Path(addons)])
                if path.name == '__init__.py']
    if packages:
        raise RuntimeError('An existing MCP package add-on needs manual migration before '
                           'installing the pinned single-file add-on: ' + ', '.join(packages))


def merged_config(path, entry, replace=False):
    try:
        config, _ = read_json_config(path)
    except ConfigError as exc:
        raise ValueError(str(exc)) from exc
    servers = config.get('mcpServers', {})
    if not isinstance(servers, dict):
        raise ValueError('mcpServers must be a JSON object; config left unchanged')
    existing = servers.get('blender')
    if existing is not None and existing != entry and not replace:
        raise ValueError('A different blender server already exists; inspect it first '
                         'and pass --replace-existing only if you intend to replace it')
    merged = copy.deepcopy(config)
    merged.setdefault('mcpServers', {})['blender'] = entry
    return merged, existing != entry


def backup_file(path):
    if not path.exists():
        return None
    backup = path.with_name(f'{path.name}.{time.time_ns()}.bak')
    shutil.copy2(path, backup)
    return str(backup)


def merge_desktop_config(path, entry, apply=False, replace=False):
    path = Path(path)
    merged, changed = merged_config(path, entry, replace)
    result = {'path': str(path), 'changed': changed, 'applied': False}
    if not apply or not changed:
        return result
    path.parent.mkdir(parents=True, exist_ok=True)
    backup = backup_file(path)
    if backup:
        result['backup'] = backup
    staged = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8',
                                         dir=path.parent, delete=False) as handle:
            staged = Path(handle.name)
            handle.write(json.dumps(merged, indent=2) + '\n')
        os.replace(staged, path)
    finally:
        if staged is not None:
            staged.unlink(missing_ok=True)
    result['applied'] = True
    return result


def code_command(executable, entry):
    command = [str(executable), 'mcp', 'add', '--scope', 'user']
    for key, value in entry['env'].items():
        command += ['--env', f'{key}={value}']
    return command + ['--transport', 'stdio', 'blender', '--',
                      entry['command'], *entry['args']]


def configure_code(executable, config, entry, replace=False):
    desired = {'type': 'stdio', **entry}
    _, changed = merged_config(config, desired, replace)
    if not changed:
        return {'changed': False, 'path': str(config)}
    backup = backup_file(config)
    current, _ = read_json_config(config)
    try:
        if 'blender' in current.get('mcpServers', {}):
            subprocess.run([executable, 'mcp', 'remove', '--scope', 'user', 'blender'],
                           check=True, timeout=60)
        subprocess.run(code_command(executable, entry), check=True, timeout=60)
    except (OSError, RuntimeError, subprocess.SubprocessError):
        if backup:
            shutil.copy2(backup, config)
        else:
            config.unlink(missing_ok=True)
        raise
    return {'changed': True, 'path': str(config), 'backup': backup}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client', choices=['desktop', 'code'], required=True)
    parser.add_argument('--blender', help='Actual absolute path to blender.exe')
    parser.add_argument('--uv', help='Override discovered uv.exe path')
    parser.add_argument('--config', type=Path, help='Desktop config path override')
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--replace-existing', action='store_true')
    parser.add_argument('--allow-version-mismatch', action='store_true')
    args = parser.parse_args(argv)
    if sys.platform != 'win32':
        parser.error('This setup command targets native Windows; use --help for instructions.')
    if version('mcp-for-blender') != '2.1.9':
        raise RuntimeError('Run with uv run --frozen to load the pinned package.')

    uv = args.uv or shutil.which('uv')
    if not uv or not Path(uv).is_file():
        raise RuntimeError('Install uv with winget, reopen PowerShell, and verify Get-Command uv.')
    entry = server_entry(str(Path(uv).resolve()))
    clients = detect_clients(platform='win32')
    client_key = 'claude-' + args.client
    client = next((item for item in clients if item.key == client_key), None)
    if args.client == 'desktop':
        config = args.config or (client.config_path if client else None)
        if config is None:
            raise RuntimeError('Open Claude Desktop once, then retry; or pass its actual --config path.')
        config_plan = merge_desktop_config(config, entry, replace=args.replace_existing)
    else:
        if client is None:
            raise RuntimeError('Install Claude Code, reopen PowerShell, sign in, then retry.')
        config = Path(os.environ.get('CLAUDE_CONFIG_DIR') or Path.home()) / '.claude.json'
        _, changed = merged_config(config, {'type': 'stdio', **entry}, args.replace_existing)
        config_plan = {'path': str(config), 'changed': changed}

    if args.blender:
        blender = Path(args.blender).resolve()
    else:
        candidates = find_blender_executables(platform='win32')
        blender = next((Path(item) for item in candidates
                        if blender_version(item) == (5, 2)), None)
        if blender is None and args.allow_version_mismatch and candidates:
            blender = Path(candidates[0])
    if blender is None or not blender.is_file():
        raise RuntimeError('Blender 5.2 not found; pass --blender with the actual executable path.')
    probe = run_blender(blender, script_path('blender_probe.py'))
    if probe['version'][:2] != [5, 2] and not args.allow_version_mismatch:
        raise RuntimeError('Expected Blender 5.2; use --allow-version-mismatch deliberately for another version.')
    addons = Path(probe['addons_dir'])
    reject_package_addons(addons)
    print(json.dumps({'mode': 'apply' if args.apply else 'dry-run',
                      'client': args.client, 'config': config_plan,
                      'server': entry, 'blender': probe}, indent=2))
    if not args.apply:
        print('No configuration or add-on files written. Rerun with --apply to install.')
        return
    if blender_is_running(platform='win32'):
        raise RuntimeError('Save and close all Blender windows, then rerun --apply. No process will be stopped.')

    result = install_addon(addons)
    if not result.success:
        raise RuntimeError(result.message)
    print(result.message)
    actual = hashlib.sha256((addons / 'blender_mcp.py').read_bytes()).hexdigest()
    if actual != ADDON_SHA256:
        raise RuntimeError('Installed add-on does not match the pinned release hash. Stop and inspect it.')

    if args.client == 'desktop':
        print(json.dumps(merge_desktop_config(config, entry, apply=True,
                                              replace=args.replace_existing), indent=2))
    else:
        print(json.dumps(configure_code(client.cli_path, config, entry,
                                        replace=args.replace_existing), indent=2))
    if safe_to_save_prefs(addons.parents[2], tuple(probe['version'][:2])):
        enabled, message = enable_addon_headless(str(blender), 'blender_mcp')
        print(message)
        if not enabled:
            raise RuntimeError('Add-on copied but could not be enabled. Enable MCP for Blender in Preferences.')
    else:
        print('Finish Blender settings migration first, then enable MCP for Blender in Preferences.')
    print('Setup files are ready. Open Blender and verify its MCP listener. '
          'Fully restart the chosen Claude client. Run pipeline.check_mcp next.')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f'SETUP FAILED: {exc}', file=sys.stderr)
        sys.exit(1)
