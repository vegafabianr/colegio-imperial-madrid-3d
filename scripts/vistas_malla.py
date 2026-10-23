# Views of the reference mesh (18_malla_referencia) and, with the same cameras, of the model. Run by 18:
#   blender -b --factory-startup --python scripts/vistas_malla.py -- views.json
# A view is [camera xyz, target xyz] or [camera xyz, target xyz, width in m] for an orthographic view.
# views.json: {"glbs": [...], "matrix": 4x4 tile frame -> local, "floor_box": [xmin, xmax, ymin, ymax], "floor_z": local z,
#              "model": .glb of the model or null, "views": {name: [camera xyz, target xyz]}, "lens": mm,
#              "size": [w, h], "out": prefix of the images}
import sys, json
import bpy
from mathutils import Matrix, Vector

config = json.load(open(sys.argv[sys.argv.index("--") + 1], encoding="utf-8"))
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# Mesh tiles, from the tile frame to the local frame of the project:
M = Matrix(config["matrix"])
area = config.get("area")   # Optional [xmin, xmax, ymin, ymax]: tiles outside it are dropped (memory)
for path in config["glbs"]:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    for ob in set(bpy.data.objects) - before:
        if ob.parent is None:
            ob.matrix_world = M @ ob.matrix_world
        if area and ob.type == "MESH":
            c = [ob.matrix_world @ Vector(b) for b in ob.bound_box]
            if not (min(p.x for p in c) < area[1] and max(p.x for p in c) > area[0]
                    and min(p.y for p in c) < area[3] and max(p.y for p in c) > area[2]):
                bpy.data.objects.remove(ob)
    if area:
        bpy.data.orphans_purge(do_recursive=True)
mesh_objects = [ob for ob in bpy.data.objects if ob.parent is None]
print("Tiles imported:", len(config["glbs"]))

# Heights: the tiles are on the ellipsoid. The offset is read on a patch of flat ground of known height (5th
# percentile of the mesh vertices inside floor_box, so that walls and noise above it do not count):
xmin, xmax, ymin, ymax = config["floor_box"]
floor = []
for ob in bpy.data.objects:
    if ob.type == "MESH":
        mw = ob.matrix_world
        floor += [w.z for w in (mw @ v.co for v in ob.data.vertices) if xmin < w.x < xmax and ymin < w.y < ymax]
floor.sort()
offset = floor[len(floor) // 20] - config["floor_z"]
print("Vertical offset:", round(offset, 2), "m from", len(floor), "vertices")
for ob in mesh_objects:
    ob.location.z -= offset

for engine in ["BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"]:
    try:
        scene.render.engine = engine
        break
    except TypeError:
        pass
scene.view_settings.view_transform = "Standard"
scene.render.resolution_x, scene.render.resolution_y = config["size"]
scene.render.image_settings.file_format = "JPEG"
scene.render.image_settings.quality = 90
world = bpy.data.worlds.new("cielo")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.8, 0.8, 0.8, 1.0)
scene.world = world
camera_data = bpy.data.cameras.new("vista")
camera_data.lens = config["lens"]
camera_data.clip_end = 5000
camera = bpy.data.objects.new("vista", camera_data)
scene.collection.objects.link(camera)
scene.camera = camera

def shoot(suffix):
    for name, view in config["views"].items():
        position, target = view[:2]
        # A third value makes the view orthographic, with that width in meters (elevations to measure on):
        camera_data.type = "ORTHO" if len(view) > 2 else "PERSP"
        if len(view) > 2:
            camera_data.ortho_scale = view[2]
        camera.location = Vector(position)
        if position[0] == target[0] and position[1] == target[1]:
            camera.rotation_euler = (0.0, 0.0, 0.0)   # Straight down, north up (true orthophoto)
        else:
            camera.rotation_euler = (Vector(target) - Vector(position)).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = config["out"] + name + suffix + ".jpg"
        bpy.ops.render.render(write_still=True)
        print("Saved:", scene.render.filepath)

shoot("")

# The model, with the same cameras, under a sun (its materials are not unlit like the mesh):
if config.get("model"):
    for ob in mesh_objects:
        for child in [ob] + list(ob.children_recursive):
            child.hide_render = True
    bpy.ops.import_scene.gltf(filepath=config["model"])
    sun_data = bpy.data.lights.new("sol", type="SUN")
    sun_data.energy = 3.0
    sun = bpy.data.objects.new("sol", sun_data)
    scene.collection.objects.link(sun)
    sun.rotation_euler = (0.7, 0, -2.36)
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.6, 0.6, 0.6, 1.0)
    shoot("_modelo")
