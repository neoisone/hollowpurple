"""Use the official MCP SDK to verify the connection without an LLM call."""

import argparse
import asyncio
import json
import shutil
import socket
import sys
from datetime import timedelta

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from .runtime import PROTOCOL, SERVER_ARGS, server_environment, script_path, tool_text


async def check(uv, configure_gpu=False):
    with socket.create_connection(('127.0.0.1', 9876), timeout=3):
        pass
    parameters = StdioServerParameters(command=uv, args=SERVER_ARGS, env=server_environment())
    async with stdio_client(parameters) as streams:
        async with ClientSession(*streams, read_timeout_seconds=timedelta(seconds=60)) as session:
            await session.initialize()
            tools = {tool.name for tool in (await session.list_tools()).tools}
            required = {'get_addon_status', 'get_scene_info', 'execute_blender_code', 'look'}
            if not required <= tools:
                raise RuntimeError(f'Required tools missing: {sorted(required - tools)}')
            prompt = 'Verify my local Blender MCP setup and report its actual version and scene.'
            status_text = tool_text(await session.call_tool('get_addon_status', {'user_prompt': prompt}))
            # This pinned server can append guidance after the leading JSON payload.
            status, _ = json.JSONDecoder().raw_decode(status_text.lstrip())
            if (status.get('protocol_version') != PROTOCOL
                    or status.get('expected_protocol_version') != PROTOCOL
                    or not status.get('up_to_date')):
                raise RuntimeError(f'Add-on/server protocol does not match: {status_text}')
            scene = tool_text(await session.call_tool('get_scene_info', {'user_prompt': prompt}))
            code = "import bpy; print({'version':bpy.app.version_string,'file':bpy.data.filepath,'scene':bpy.context.scene.name})"
            if configure_gpu:
                code = script_path('configure_gpu.py').read_text(encoding='utf-8')
                # __name__ is not guaranteed to be __main__ inside the add-on's exec.
                code = code.split("if __name__ == '__main__':")[0] + '\nimport bpy\nconfigure(bpy)\n'
                prompt = 'Configure my live Blender scene to use the RTX 4090 through OptiX.'
            execution = tool_text(await session.call_tool('execute_blender_code', {'code': code, 'user_prompt': prompt}))
            return {'ok': True, 'addon': status, 'scene': scene, 'execution': execution,
                    'gpu_configured': configure_gpu}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--uv', default=shutil.which('uv'))
    parser.add_argument('--configure-gpu', action='store_true', help='Also configure the active live scene for OptiX/4090')
    args = parser.parse_args()
    if not args.uv:
        parser.error('uv not found; install uv and reopen the terminal.')
    try:
        report = asyncio.run(check(args.uv, args.configure_gpu))
    except (Exception, ExceptionGroup) as exc:
        print(f'MCP CHECK FAILED: {exc}', file=sys.stderr)
        sys.exit(1)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
