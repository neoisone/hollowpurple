"""Read Blender's actual paths in a background process without saving preferences."""

import json
import bpy

print('HOLLOWPURPLE_RESULT ' + json.dumps({
    'ok': True,
    'version': list(bpy.app.version),
    'version_string': bpy.app.version_string,
    'executable': bpy.app.binary_path,
    'addons_dir': bpy.utils.user_resource('SCRIPTS', path='addons', create=False),
}))
