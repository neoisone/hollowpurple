"""Cycles setup for the requested device; never falls back to another backend."""

import json


def select_devices(devices, backend, name):
    targets = [d for d in devices if d.type == backend and name.casefold() in d.name.casefold()]
    if not targets:
        raise RuntimeError(f'{backend} device {name!r} not found: '
                           f'{[(d.name, d.type) for d in devices]}')
    for device in devices:
        device.use = device in targets
    return targets


def configure(bpy, backend='OPTIX', name='4090', samples=128):
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    prefs = bpy.context.preferences.addons['cycles'].preferences
    if backend == 'CPU':
        scene.cycles.device = 'CPU'
        devices = [{'name': 'CPU', 'type': 'CPU', 'enabled': True}]
    else:
        prefs.compute_device_type = backend
        prefs.get_devices()
        select_devices(prefs.devices, backend, name)
        scene.cycles.device = 'GPU'
        devices = [{'name': d.name, 'type': d.type, 'enabled': bool(d.use)} for d in prefs.devices]
    scene.cycles.samples = samples
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.02
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = 'OPENIMAGEDENOISE'
    report = {'engine': scene.render.engine, 'scene_device': scene.cycles.device,
              'backend': backend, 'devices': devices, 'samples': samples}
    print(json.dumps(report, indent=2))
    return report


if __name__ == '__main__':
    import bpy
    configure(bpy)
