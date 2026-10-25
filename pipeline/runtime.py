"""Shared process and result handling; no Blender or client settings are changed."""

import json
import os
import subprocess
from pathlib import Path

PROTOCOL = 13
PYTHON = '3.11'
SERVER_ARGS = ['run', '--frozen', '--project', str(Path(__file__).resolve().parents[1]),
               '--python', PYTHON, 'mcp-for-blender']
MARKER = 'HOLLOWPURPLE_RESULT '


def server_environment():
    env = {
        'UV_PYTHON_PREFERENCE': 'only-managed',
        'BLENDER_HOST': 'localhost',
        'BLENDER_PORT': '9876',
        'DISABLE_TELEMETRY': '1',
    }
    if location := os.environ.get('UV_PYTHON_INSTALL_DIR'):
        env['UV_PYTHON_INSTALL_DIR'] = str(Path(location).expanduser().resolve())
    return env


def parse_blender_report(stdout):
    for line in reversed(stdout.splitlines()):
        if line.startswith(MARKER):
            report = json.loads(line[len(MARKER):])
            if not report.get('ok'):
                raise RuntimeError(report.get('error', 'Blender operation failed'))
            return report
    raise RuntimeError('No result from Blender. Last output:\n' + stdout[-3000:])


def run_blender(executable, script, args=(), timeout=180):
    result = subprocess.run(
        [str(executable), '--background', '--python-exit-code', '1',
         '--python', str(script), '--', *map(str, args)],
        capture_output=True, text=True, errors='replace', timeout=timeout,
        env={**os.environ, 'BLENDERMCP_NO_UPDATE_CHECK': '1'},
    )
    if result.returncode:
        raise RuntimeError(f'Blender exited {result.returncode}:\n'
                           + (result.stdout + result.stderr)[-4000:])
    return parse_blender_report(result.stdout)


def tool_text(result):
    text = '\n'.join(item.text for item in result.content if item.type == 'text')
    if result.isError or text.lstrip().startswith((
        'Error ', 'Error:', 'Rejected by safe mode', 'Could not determine',
    )):
        raise RuntimeError(text or 'MCP tool returned an error')
    if not text:
        raise RuntimeError('MCP tool returned no text')
    return text


def script_path(name):
    return Path(__file__).resolve().parent / name
