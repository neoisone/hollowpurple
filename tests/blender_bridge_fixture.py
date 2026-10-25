"""Temporary real add-on listener in a separate GUI Blender process."""

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

import bpy

parser = argparse.ArgumentParser()
parser.add_argument('--addon', type=Path, required=True)
parser.add_argument('--stop', type=Path, required=True)
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
if bpy.app.background:
    raise RuntimeError('The upstream bridge requires a GUI event loop; omit --background.')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.name = 'Hollowpurple isolated MCP test'
spec = importlib.util.spec_from_file_location('hollowpurple_fixture_addon', args.addon)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
module.register()
server = module.BlenderMCPServer(host='localhost', port=9876)
server.start()
if not server.running:
    raise RuntimeError('Test port unavailable; no existing process was stopped.')
bpy.types.blendermcp_server = server
deadline = time.monotonic() + 120


def finish():
    if time.monotonic() < deadline and not args.stop.exists():
        return 0.2
    server.stop()
    module.unregister()
    print('FIXTURE_STOPPED', flush=True)
    bpy.ops.wm.quit_blender()


bpy.app.timers.register(finish, first_interval=0.2)
print('FIXTURE_READY', flush=True)
