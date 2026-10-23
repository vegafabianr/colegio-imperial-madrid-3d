# Perspective view of a model, with a sun and a light grey sky. Run from the project folder:
#   blender -b blender/colegio_imperial_lod3.blend --python scripts/render_vista.py -- out.jpg cx cy cz tx ty tz lens_mm width_px height_px
# (cx, cy, cz) = camera, (tx, ty, tz) = point it looks at, in local coordinates (meters).

import sys
import math
import bpy
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
OUT_FILE = args[0]
camera_at = Vector([float(v) for v in args[1:4]])
target = Vector([float(v) for v in args[4:7]])
lens_mm = float(args[7])
width_px, height_px = int(args[8]), int(args[9])

scene = bpy.context.scene

# Camera looking at the target:
camera_data = bpy.data.cameras.new("vista")
camera_data.lens = lens_mm
camera_data.clip_end = 2000
camera = bpy.data.objects.new("vista", camera_data)
scene.collection.objects.link(camera)
camera.location = camera_at
camera.rotation_euler = (target - camera_at).to_track_quat("-Z", "Y").to_euler()
scene.camera = camera

# Sun from the south-west, 50 degrees high, with soft shadows:
sun_data = bpy.data.lights.new("sol", type="SUN")
sun_data.energy = 3.0
sun_data.angle = math.radians(3)
sun = bpy.data.objects.new("sol", sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(40), 0, math.radians(-135))

# Light grey sky, which also lights the shadows:
world = bpy.data.worlds.new("cielo")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.6, 0.6, 0.6, 1.0)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
scene.world = world

# EEVEE, with the colors as they are (no film look):
for engine in ["BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"]:
    try:
        scene.render.engine = engine
        break
    except TypeError:
        pass
scene.view_settings.view_transform = "Standard"
scene.render.resolution_x = width_px
scene.render.resolution_y = height_px
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "JPEG"
scene.render.image_settings.quality = 90
scene.render.filepath = OUT_FILE
bpy.ops.render.render(write_still=True)
print("Saved:", OUT_FILE)
