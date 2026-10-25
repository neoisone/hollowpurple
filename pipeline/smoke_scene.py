"""Create and render a fresh test scene only in a separate background Blender."""

import argparse
import json
import sys
import time
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from configure_gpu import configure


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--backend', choices=['OPTIX', 'METAL', 'CPU'], default='OPTIX')
    parser.add_argument('--device-name', default='4090')
    parser.add_argument('--samples', type=int, default=64)
    parser.add_argument('--size', type=int, default=512)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    if not bpy.app.background:
        raise RuntimeError('Run this script in a separate background Blender process.')
    if args.samples < 1 or args.size < 64:
        raise ValueError('Samples must be positive and size at least 64.')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise RuntimeError('Output directory is not empty. Choose a new directory; nothing was overwritten.')

    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.name = 'MCP connection and render test'
    device = configure(bpy, args.backend, args.device_name, args.samples)
    scene.render.resolution_x = scene.render.resolution_y = args.size
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = str(output / 'smoke.png')
    scene.view_settings.view_transform = 'AgX'
    world = bpy.data.worlds.new('Neutral studio')
    world.use_nodes = True
    background = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
    background.inputs['Color'].default_value = (0.65, 0.7, 0.8, 1)
    background.inputs['Strength'].default_value = 0.35
    scene.world = world

    def material(name, color):
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        node = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        node.inputs['Base Color'].default_value = color
        return mat, node

    bpy.ops.mesh.primitive_plane_add(size=200)
    ground, node = material('Neutral ground', (0.12, 0.14, 0.17, 1))
    node.inputs['Roughness'].default_value = 0.35
    bpy.context.object.data.materials.append(ground)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=0.52, location=(-0.85, 0, 1.1))
    orb, node = material('Red emissive test', (0.35, 0.008, 0.015, 1))
    node.inputs['Emission Color'].default_value = (1, 0.01, 0.018, 1)
    node.inputs['Emission Strength'].default_value = 1.8
    bpy.context.object.data.materials.append(orb)
    for polygon in bpy.context.object.data.polygons:
        polygon.use_smooth = True
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=0.7, location=(0.8, 0, 0.72))
    glass = bpy.data.materials.new('Clear glass test')
    glass.use_nodes = True
    nodes = glass.node_tree.nodes
    nodes.clear()
    shader = nodes.new('ShaderNodeBsdfGlass')
    shader.inputs['Roughness'].default_value = 0.025
    shader.inputs['IOR'].default_value = 1.45
    sink = nodes.new('ShaderNodeOutputMaterial')
    glass.node_tree.links.new(shader.outputs[0], sink.inputs['Surface'])
    bpy.context.object.data.materials.append(glass)
    bpy.ops.object.light_add(type='AREA', location=(0, -3, 5))
    bpy.context.object.data.energy = 650
    bpy.context.object.data.shape = 'DISK'
    bpy.context.object.data.size = 4
    bpy.ops.object.camera_add(location=(3.8, -6.2, 3.1))
    camera = bpy.context.object
    camera.rotation_euler = (Vector((0, 0, 0.8)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera.data.lens = 55
    scene.camera = camera
    bpy.ops.wm.save_as_mainfile(filepath=str(output / 'mcp_smoke.blend'))
    started = time.monotonic()
    bpy.ops.render.render(write_still=True)
    report = {'ok': True, 'blender': bpy.app.version_string,
              'device': device, 'resolution': [args.size, args.size],
              'render_seconds': time.monotonic() - started,
              'image': str(output / 'smoke.png'), 'blend': str(output / 'mcp_smoke.blend')}
    (output / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('HOLLOWPURPLE_RESULT ' + json.dumps(report))


if __name__ == '__main__':
    main()
