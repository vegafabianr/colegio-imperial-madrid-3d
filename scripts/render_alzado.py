# Orthographic elevation of a facade, with the same framing as a rectified photo (scripts/09_rectificar.ipynb).
# Run from the project folder (scripts/11_validacion_fachadas.ipynb does it):
#   blender -b blender/lod3.blend --python scripts/render_alzado.py -- out.png cx cy cz nx ny width_m height_m width_px height_px
# (cx, cy, cz) = center of the window in local coordinates; (nx, ny) = unit normal of the facade toward the street.

import os
import sys
import bpy
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
OUT = os.path.abspath(args[0])   # Blender does not resolve plain relative paths from the current folder
cx, cy, cz, nx, ny, width_m, height_m = [float(v) for v in args[1:8]]
width_px, height_px = int(args[8]), int(args[9])

scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.color_type = "MATERIAL"
scene.display.shading.light = "FLAT"
scene.display.shading.show_object_outline = True
scene.render.resolution_x = width_px
scene.render.resolution_y = height_px
scene.world = bpy.data.worlds.new("fondo")

# Camera 60 m out of the facade, looking at it, with orthographic projection (no perspective):
camera_data = bpy.data.cameras.new("alzado")
camera_data.type = "ORTHO"
camera_data.ortho_scale = max(width_m, height_m)   # Blender applies it to the larger side of the image
camera_data.clip_end = 500
camera = bpy.data.objects.new("alzado", camera_data)
scene.collection.objects.link(camera)
target = Vector((cx, cy, cz))
camera.location = target + Vector((nx, ny, 0)) * 60
camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
scene.camera = camera

scene.render.filepath = OUT
bpy.ops.render.render(write_still=True)
