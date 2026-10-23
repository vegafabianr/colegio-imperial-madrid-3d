# Distances between the reference mesh (18_malla_referencia) and the model, both ways. Run by 19_control_malla:
#   blender -b --factory-startup --python scripts/malla_distancias.py -- config.json
# config.json: {"glbs", "matrix", "floor_box", "floor_z" (as in vistas_malla.py), "model": .glb of the model,
#               "area": [xmin, xmax, ymin, ymax] local, "spacing": m between samples, "out": .npz}
# Output: mesh samples (xyz, normal, distance to the model) and model samples (xyz, normal, distance to the mesh).
import sys, json, random
import bpy
import bmesh
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

config = json.load(open(sys.argv[sys.argv.index("--") + 1], encoding="utf-8"))
bpy.ops.wm.read_factory_settings(use_empty=True)
xmin, xmax, ymin, ymax = config["area"]

def import_glb(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    return list(set(bpy.data.objects) - before)

def triangles(objects, clip=True):
    """World triangles of the meshes, keeping those with a vertex inside the area."""
    out = []
    for ob in objects:
        if ob.type != "MESH":
            continue
        mw = ob.matrix_world
        mesh = ob.data
        co = [mw @ v.co for v in mesh.vertices]
        mesh.calc_loop_triangles()
        for tri in mesh.loop_triangles:
            p = [co[i] for i in tri.vertices]
            if not clip or any(xmin < q.x < xmax and ymin < q.y < ymax for q in p):
                out.append(p)
    return out

# Reference mesh, placed as in vistas_malla.py:
M = Matrix(config["matrix"])
# Memory (8 GB machine): only geometry is needed, so the textures of each tile are dropped at once, and tiles that
# do not reach the area are deleted.
tiles = []
for path in config["glbs"]:
    new = import_glb(path)
    for ob in new:
        if ob.parent is None:
            ob.matrix_world = M @ ob.matrix_world
    keep = []
    for ob in new:
        corners = [ob.matrix_world @ Vector(c) for c in ob.bound_box] if ob.type == "MESH" else []
        if corners and min(c.x for c in corners) < xmax and max(c.x for c in corners) > xmin                 and min(c.y for c in corners) < ymax and max(c.y for c in corners) > ymin:
            keep.append(ob)
        else:
            bpy.data.objects.remove(ob)
    for image in list(bpy.data.images):
        bpy.data.images.remove(image)
    bpy.data.orphans_purge(do_recursive=True)
    tiles += keep
print("Tiles kept:", len(tiles), "of", len(config["glbs"]))
bx0, bx1, by0, by1 = config["floor_box"]
floor = sorted(w.z for ob in tiles if ob.type == "MESH" for w in (ob.matrix_world @ v.co for v in ob.data.vertices)
               if bx0 < w.x < bx1 and by0 < w.y < by1)
offset = floor[len(floor) // 20] - config["floor_z"]
print("Vertical offset:", round(offset, 2))
for ob in tiles:
    if ob.parent is None:
        ob.location.z -= offset
bpy.context.view_layer.update()
mesh_tris = triangles(tiles)
model_tris = triangles(import_glb(config["model"]))
print("Triangles: mesh", len(mesh_tris), "| model", len(model_tris))

def bvh(tris):
    verts, faces = [], []
    for t in tris:
        faces.append((len(verts), len(verts) + 1, len(verts) + 2))
        verts += [tuple(v) for v in t]
    return BVHTree.FromPolygons(verts, faces, epsilon=0.0)

def samples(tris, spacing, seed):
    """Random points on the triangles, about one per spacing^2 of area, inside the area."""
    rng = random.Random(seed)
    out = []
    for a, b, c in tris:
        n = (b - a).cross(c - a)
        area = n.length / 2
        if area == 0:
            continue
        count = area / spacing ** 2
        k = int(count) + (1 if rng.random() < count - int(count) else 0)
        for _ in range(k):
            r1, r2 = rng.random(), rng.random()
            if r1 + r2 > 1:
                r1, r2 = 1 - r1, 1 - r2
            p = a + (b - a) * r1 + (c - a) * r2
            if xmin < p.x < xmax and ymin < p.y < ymax:
                out.append((p, n.normalized()))
    return out

def distances(points, tree, own_normal, cap=10.0):
    """Distance to the other surface and its sign along the normal of the mesh (outward on the photogrammetric mesh):
    > 0 when the sample lies outside the other surface. For mesh samples the normal is their own; for model samples,
    the normal of the nearest mesh face (the faces of the model are not always oriented)."""
    result = []
    for p, n in points:
        hit = tree.find_nearest(p, cap)
        if hit[0] is None:
            result.append((p.x, p.y, p.z, n.x, n.y, n.z, cap, 0.0))
            continue
        normal = n if own_normal else hit[1]
        result.append((p.x, p.y, p.z, n.x, n.y, n.z, hit[3], (p - hit[0]).dot(normal)))
    return np.array(result, dtype=np.float32)

spacing = config["spacing"]
mesh_side = distances(samples(mesh_tris, spacing, 1), bvh(model_tris), True)
model_side = distances(samples(model_tris, config.get("model_spacing", spacing), 2), bvh(mesh_tris), False)
np.savez_compressed(config["out"], mesh=mesh_side, model=model_side, offset=offset)
print("Saved:", config["out"], "| samples: mesh", len(mesh_side), "| model", len(model_side))
