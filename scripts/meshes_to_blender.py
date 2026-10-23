# Build a Blender model from a JSON file of meshes (written by scripts/04_lod1.ipynb or 05_lod2.ipynb).
# Run from the project folder:
#   blender -b --factory-startup --python scripts/meshes_to_blender.py -- data/lod1_meshes.json blender/lod1.blend blender/lod1.glb

import sys
import json
import bpy
import bmesh

# Arguments after "--":
args = sys.argv[sys.argv.index("--") + 1:]
JSON_FILE = args[0]
BLEND_FILE = args[1]
GLB_FILE = args[2]

# Colors (RGBA) for each group of buildings:
COLORS = {
    "conjunto": (0.85, 0.72, 0.55, 1.0),
    "contexto": (0.75, 0.75, 0.75, 1.0),
    "piedra": (0.55, 0.55, 0.53, 1.0),
    "vidrio": (0.06, 0.07, 0.08, 1.0),
    "pizarra": (0.27, 0.29, 0.32, 1.0),
    "metal": (0.12, 0.12, 0.13, 1.0),
}

# Vertices closer than this (meters) are merged into one:
MERGE_DISTANCE = 0.001

# Start from an empty scene, and do not keep .blend1 backup copies when overwriting:
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version = 0

with open(JSON_FILE, encoding="utf-8") as f:
    data = json.load(f)

# One collection and one material per group:
collections = {}
materials = {}
for group in COLORS:
    collection = bpy.data.collections.new(group)
    bpy.context.scene.collection.children.link(collection)
    collections[group] = collection

    material = bpy.data.materials.new(group)
    material.diffuse_color = COLORS[group]
    material.use_nodes = True
    material.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = COLORS[group]
    materials[group] = material

# Photo materials: one per image file (parts with "image" and "uv", written by scripts/12_texturas.ipynb):
photo_materials = {}
def photo_material(path):
    if path not in photo_materials:
        material = bpy.data.materials.new("foto_" + path.replace("\\", "/").split("/")[-1])
        material.use_nodes = True
        nodes = material.node_tree.nodes
        texture = nodes.new("ShaderNodeTexImage")
        texture.image = bpy.data.images.load(path)
        material.node_tree.links.new(texture.outputs["Color"], nodes["Principled BSDF"].inputs["Base Color"])
        nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.9
        photo_materials[path] = material
    return photo_materials[path]

# Generated textures (parts with "texture" and "loop_uv", written by scripts/14_materiales.ipynb): one material
# per image file; the image repeats, because the texture coordinates are in tiles, not in 0-1:
texture_materials = {}
def texture_material(path):
    if path not in texture_materials:
        material = bpy.data.materials.new(path.replace("\\", "/").split("/")[-1].rsplit(".", 1)[0])
        material.use_nodes = True
        nodes = material.node_tree.nodes
        texture = nodes.new("ShaderNodeTexImage")
        texture.image = bpy.data.images.load(path)
        material.node_tree.links.new(texture.outputs["Color"], nodes["Principled BSDF"].inputs["Base Color"])
        nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.9
        texture_materials[path] = material
    return texture_materials[path]

# Plain colors (parts with "color" = (name, r, g, b) in 0-255 sRGB):
color_materials = {}
def color_material(color):
    name, r, g, b = color
    if name not in color_materials:
        # Blender colors are linear: convert from sRGB
        linear = [((c / 255 + 0.055) / 1.055) ** 2.4 if c / 255 > 0.04045 else c / 255 / 12.92 for c in (r, g, b)]
        material = bpy.data.materials.new(name)
        material.diffuse_color = (*linear, 1.0)
        material.use_nodes = True
        material.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*linear, 1.0)
        material.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.9
        color_materials[name] = material
    return color_materials[name]

# One object per building part:
for part in data["parts"]:
    mesh = bpy.data.meshes.new(part["name"])
    mesh.from_pydata(part["vertices"], [], part["faces"])

    # Texture coordinates: one (u, v) per vertex, copied to every corner of the faces that use it:
    if "uv" in part:
        uv_layer = mesh.uv_layers.new(name="foto")
        for loop in mesh.loops:
            uv_layer.data[loop.index].uv = part["uv"][loop.vertex_index]
    # Or one (u, v) per face corner, in the order of the faces:
    if "loop_uv" in part:
        uv_layer = mesh.uv_layers.new(name="textura")
        corners = [uv for face_uv in part["loop_uv"] for uv in face_uv]
        for loop in mesh.loops:
            uv_layer.data[loop.index].uv = corners[loop.index]

    # Merge repeated vertices, so that roof pieces and walls form one closed surface,
    # and make all face normals point outward:
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=MERGE_DISTANCE)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    if "texture" in part:
        mesh.materials.append(texture_material(part["texture"]))
    elif "color" in part:
        mesh.materials.append(color_material(part["color"]))
    elif "image" in part:
        mesh.materials.append(photo_material(part["image"]))
    else:
        mesh.materials.append(materials[part["group"]])

    obj = bpy.data.objects.new(part["name"], mesh)
    obj["parcel"] = part["parcel"]
    obj["height_m"] = part["height_m"]
    obj["height_method"] = part["height_method"]
    obj["lod"] = part["lod"]
    # Groups without a color of their own (e.g. "volumen" of 15_volumenes) get a collection when first seen:
    if part["group"] not in collections:
        collections[part["group"]] = bpy.data.collections.new(part["group"])
        bpy.context.scene.collection.children.link(collections[part["group"]])
    collections[part["group"]].objects.link(obj)

# Write the local origin in the scene, so it travels with the .blend:
bpy.context.scene["origin_epsg25830"] = data["origin"]

bpy.ops.wm.save_as_mainfile(filepath=BLEND_FILE)
bpy.ops.export_scene.gltf(filepath=GLB_FILE, export_format="GLB", export_extras=True)
print("Objects:", len(data["parts"]))
