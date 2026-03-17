import bpy
import math
from mathutils import Vector


def _clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    # Purge orphans (Blender 3.x/4.x)
    try:
        bpy.ops.outliner.orphans_purge(do_recursive=True)
    except Exception:
        pass


def _ensure_collection(name: str) -> bpy.types.Collection:
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col


def _new_material(name: str, rgba):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (rgba[0], rgba[1], rgba[2], 1.0)
        bsdf.inputs["Roughness"].default_value = 0.35
        # Blender versions differ: "Specular" (older) vs "Specular IOR Level" (newer).
        if "Specular" in bsdf.inputs:
            bsdf.inputs["Specular"].default_value = 0.5
        elif "Specular IOR Level" in bsdf.inputs:
            bsdf.inputs["Specular IOR Level"].default_value = 0.5
    return mat


def _add_uv_sphere(name: str, location, radius: float, material: bpy.types.Material, collection: bpy.types.Collection):
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=64,
        ring_count=32,
        radius=radius,
        location=location,
    )
    obj = bpy.context.active_object
    obj.name = name
    if obj.data.materials:
        obj.data.materials[0] = material
    else:
        obj.data.materials.append(material)

    # Move into target collection
    for c in obj.users_collection:
        c.objects.unlink(obj)
    collection.objects.link(obj)
    return obj


def _add_cylinder(name: str, p0: Vector, p1: Vector, radius: float, material: bpy.types.Material, collection: bpy.types.Collection):
    direction = p1 - p0
    length = direction.length
    if length == 0:
        raise ValueError("Cylinder endpoints are identical")

    midpoint = (p0 + p1) / 2
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=48,
        radius=radius,
        depth=length,
        location=midpoint,
    )
    obj = bpy.context.active_object
    obj.name = name
    if obj.data.materials:
        obj.data.materials[0] = material
    else:
        obj.data.materials.append(material)

    # Align cylinder Z axis to direction vector
    z_axis = Vector((0, 0, 1))
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = z_axis.rotation_difference(direction.normalized())
    obj.rotation_mode = "XYZ"

    for c in obj.users_collection:
        c.objects.unlink(obj)
    collection.objects.link(obj)
    return obj


def _add_text(name: str, text: str, location, size: float, collection: bpy.types.Collection):
    bpy.ops.object.text_add(location=location)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.body = text
    obj.data.size = size
    obj.data.align_x = "CENTER"
    obj.data.align_y = "CENTER"
    # Face camera-ish (Y axis) by default
    obj.rotation_euler = (math.radians(90), 0, 0)

    for c in obj.users_collection:
        c.objects.unlink(obj)
    collection.objects.link(obj)
    return obj


def _frame_camera_to_objects(camera_obj, objects):
    # Simple framing: place camera along -Y, look at centroid
    pts = [o.location for o in objects]
    center = Vector((0, 0, 0))
    for p in pts:
        center += Vector(p)
    center /= max(1, len(pts))

    max_dist = 0.0
    for p in pts:
        max_dist = max(max_dist, (Vector(p) - center).length)
    dist = max(4.0, max_dist * 5.0)

    camera_obj.location = (center.x, center.y - dist, center.z + dist * 0.15)
    direction = center - camera_obj.location
    rot_quat = direction.to_track_quat("-Z", "Y")
    camera_obj.rotation_euler = rot_quat.to_euler()

def _export_glb(path: str):
    bpy.ops.export_scene.gltf(
        filepath=path,
        export_format="GLB",
        export_apply=True,
    )


def _setup_basic_light_and_camera(collection: bpy.types.Collection, focus_objects):
    bpy.ops.object.light_add(type="AREA", location=(0, -3.5, 3.0))
    light = bpy.context.active_object
    light.data.energy = 800
    light.data.size = 2.5
    for c in light.users_collection:
        c.objects.unlink(light)
    collection.objects.link(light)

    bpy.ops.object.camera_add(location=(0, -6, 1.0))
    cam = bpy.context.active_object
    bpy.context.scene.camera = cam
    for c in cam.users_collection:
        c.objects.unlink(cam)
    collection.objects.link(cam)

    _frame_camera_to_objects(cam, focus_objects)
    return cam


def build_molecule_hcl(export_glb_path: str = None):
    _clear_scene()
    col = _ensure_collection("Mol_HCl")

    mat_h = _new_material("MAT_H", (0.95, 0.95, 0.95))
    mat_cl = _new_material("MAT_Cl", (0.25, 0.85, 0.25))
    mat_bond = _new_material("MAT_Bond", (0.2, 0.2, 0.2))

    h_pos = Vector((-0.6, 0.0, 0.0))
    cl_pos = Vector((0.45, 0.0, 0.0))
    h = _add_uv_sphere("H", h_pos, radius=0.22, material=mat_h, collection=col)
    cl = _add_uv_sphere("Cl", cl_pos, radius=0.34, material=mat_cl, collection=col)
    _add_cylinder("Bond_H_Cl", h_pos, cl_pos, radius=0.07, material=mat_bond, collection=col)
    _add_text("Label_HCl", "HCl", (0.0, 0.0, 0.85), size=0.45, collection=col)

    _setup_basic_light_and_camera(col, [h, cl])

    if export_glb_path:
        _export_glb(export_glb_path)


def build_molecule_hno3(export_glb_path: str = None):
    _clear_scene()
    col = _ensure_collection("Mol_HNO3")

    mat_h = _new_material("MAT_H", (0.95, 0.95, 0.95))
    mat_o = _new_material("MAT_O", (0.90, 0.20, 0.20))
    mat_n = _new_material("MAT_N", (0.15, 0.40, 0.95))
    mat_bond = _new_material("MAT_Bond", (0.2, 0.2, 0.2))

    n_pos = Vector((0.0, 0.0, 0.0))
    o1_pos = Vector((0.75, 0.05, 0.0))
    o2_pos = Vector((-0.45, 0.70, 0.05))
    o3_pos = Vector((-0.45, -0.70, -0.05))
    h_pos = Vector((1.20, 0.10, 0.0))

    n = _add_uv_sphere("N", n_pos, radius=0.26, material=mat_n, collection=col)
    o1 = _add_uv_sphere("O1", o1_pos, radius=0.24, material=mat_o, collection=col)
    o2 = _add_uv_sphere("O2", o2_pos, radius=0.24, material=mat_o, collection=col)
    o3 = _add_uv_sphere("O3", o3_pos, radius=0.24, material=mat_o, collection=col)
    h = _add_uv_sphere("H", h_pos, radius=0.18, material=mat_h, collection=col)

    _add_cylinder("Bond_N_O1", n_pos, o1_pos, radius=0.06, material=mat_bond, collection=col)
    _add_cylinder("Bond_N_O2", n_pos, o2_pos, radius=0.06, material=mat_bond, collection=col)
    _add_cylinder("Bond_N_O3", n_pos, o3_pos, radius=0.06, material=mat_bond, collection=col)
    _add_cylinder("Bond_O1_H", o1_pos, h_pos, radius=0.05, material=mat_bond, collection=col)

    _add_text("Label_HNO3", "HNO3", (0.0, 0.0, 1.10), size=0.45, collection=col)
    _setup_basic_light_and_camera(col, [n, o1, o2, o3, h])

    if export_glb_path:
        _export_glb(export_glb_path)


def build_molecule_h2so4(export_glb_path: str = None):
    _clear_scene()
    col = _ensure_collection("Mol_H2SO4")

    mat_h = _new_material("MAT_H", (0.95, 0.95, 0.95))
    mat_o = _new_material("MAT_O", (0.90, 0.20, 0.20))
    mat_s = _new_material("MAT_S", (0.95, 0.65, 0.15))
    mat_bond = _new_material("MAT_Bond", (0.2, 0.2, 0.2))

    s_pos = Vector((0.0, 0.0, 0.0))
    o1_pos = Vector((0.85, 0.15, 0.10))
    o2_pos = Vector((-0.35, 0.85, -0.10))
    o3_pos = Vector((-0.65, -0.55, 0.25))
    o4_pos = Vector((0.15, -0.75, -0.35))
    h1_pos = Vector((-0.62, 1.28, -0.18))
    h2_pos = Vector((1.25, 0.22, 0.15))

    s = _add_uv_sphere("S", s_pos, radius=0.28, material=mat_s, collection=col)
    o1 = _add_uv_sphere("O1", o1_pos, radius=0.24, material=mat_o, collection=col)
    o2 = _add_uv_sphere("O2", o2_pos, radius=0.24, material=mat_o, collection=col)
    o3 = _add_uv_sphere("O3", o3_pos, radius=0.24, material=mat_o, collection=col)
    o4 = _add_uv_sphere("O4", o4_pos, radius=0.24, material=mat_o, collection=col)
    h1 = _add_uv_sphere("H1", h1_pos, radius=0.18, material=mat_h, collection=col)
    h2 = _add_uv_sphere("H2", h2_pos, radius=0.18, material=mat_h, collection=col)

    _add_cylinder("Bond_S_O1", s_pos, o1_pos, radius=0.06, material=mat_bond, collection=col)
    _add_cylinder("Bond_S_O2", s_pos, o2_pos, radius=0.06, material=mat_bond, collection=col)
    _add_cylinder("Bond_S_O3", s_pos, o3_pos, radius=0.06, material=mat_bond, collection=col)
    _add_cylinder("Bond_S_O4", s_pos, o4_pos, radius=0.06, material=mat_bond, collection=col)
    _add_cylinder("Bond_O2_H1", o2_pos, h1_pos, radius=0.05, material=mat_bond, collection=col)
    _add_cylinder("Bond_O1_H2", o1_pos, h2_pos, radius=0.05, material=mat_bond, collection=col)

    _add_text("Label_H2SO4", "H2SO4", (0.0, 0.0, 1.20), size=0.45, collection=col)
    _setup_basic_light_and_camera(col, [s, o1, o2, o3, o4, h1, h2])

    if export_glb_path:
        _export_glb(export_glb_path)

def build_gallery_preview():
    """
    Show multiple molecules in one Blender scene for viewing.
    (Exports are handled separately; this is just a viewport preview.)
    """
    _clear_scene()
    col = _ensure_collection("Molecule_Gallery")

    # Shared materials
    mat_h = _new_material("MAT_H", (0.95, 0.95, 0.95))
    mat_o = _new_material("MAT_O", (0.90, 0.20, 0.20))
    mat_n = _new_material("MAT_N", (0.15, 0.40, 0.95))
    mat_s = _new_material("MAT_S", (0.95, 0.65, 0.15))
    mat_cl = _new_material("MAT_Cl", (0.25, 0.85, 0.25))
    mat_bond = _new_material("MAT_Bond", (0.2, 0.2, 0.2))

    focus = []

    def add_hcl(offset: Vector):
        h_pos = offset + Vector((-0.6, 0.0, 0.0))
        cl_pos = offset + Vector((0.45, 0.0, 0.0))
        h = _add_uv_sphere("H", h_pos, radius=0.22, material=mat_h, collection=col)
        cl = _add_uv_sphere("Cl", cl_pos, radius=0.34, material=mat_cl, collection=col)
        _add_cylinder("Bond_H_Cl", h_pos, cl_pos, radius=0.07, material=mat_bond, collection=col)
        _add_text("Label_HCl", "HCl", (offset.x, offset.y, offset.z + 0.85), size=0.45, collection=col)
        focus.extend([h, cl])

    def add_hno3(offset: Vector):
        n_pos = offset + Vector((0.0, 0.0, 0.0))
        o1_pos = offset + Vector((0.75, 0.05, 0.0))
        o2_pos = offset + Vector((-0.45, 0.70, 0.05))
        o3_pos = offset + Vector((-0.45, -0.70, -0.05))
        h_pos = offset + Vector((1.20, 0.10, 0.0))

        n = _add_uv_sphere("N", n_pos, radius=0.26, material=mat_n, collection=col)
        o1 = _add_uv_sphere("O1", o1_pos, radius=0.24, material=mat_o, collection=col)
        o2 = _add_uv_sphere("O2", o2_pos, radius=0.24, material=mat_o, collection=col)
        o3 = _add_uv_sphere("O3", o3_pos, radius=0.24, material=mat_o, collection=col)
        h = _add_uv_sphere("H", h_pos, radius=0.18, material=mat_h, collection=col)

        _add_cylinder("Bond_N_O1", n_pos, o1_pos, radius=0.06, material=mat_bond, collection=col)
        _add_cylinder("Bond_N_O2", n_pos, o2_pos, radius=0.06, material=mat_bond, collection=col)
        _add_cylinder("Bond_N_O3", n_pos, o3_pos, radius=0.06, material=mat_bond, collection=col)
        _add_cylinder("Bond_O1_H", o1_pos, h_pos, radius=0.05, material=mat_bond, collection=col)

        _add_text("Label_HNO3", "HNO3", (offset.x, offset.y, offset.z + 1.10), size=0.45, collection=col)
        focus.extend([n, o1, o2, o3, h])

    def add_h2so4(offset: Vector):
        s_pos = offset + Vector((0.0, 0.0, 0.0))
        o1_pos = offset + Vector((0.85, 0.15, 0.10))
        o2_pos = offset + Vector((-0.35, 0.85, -0.10))
        o3_pos = offset + Vector((-0.65, -0.55, 0.25))
        o4_pos = offset + Vector((0.15, -0.75, -0.35))
        h1_pos = offset + Vector((-0.62, 1.28, -0.18))
        h2_pos = offset + Vector((1.25, 0.22, 0.15))

        s = _add_uv_sphere("S", s_pos, radius=0.28, material=mat_s, collection=col)
        o1 = _add_uv_sphere("O1", o1_pos, radius=0.24, material=mat_o, collection=col)
        o2 = _add_uv_sphere("O2", o2_pos, radius=0.24, material=mat_o, collection=col)
        o3 = _add_uv_sphere("O3", o3_pos, radius=0.24, material=mat_o, collection=col)
        o4 = _add_uv_sphere("O4", o4_pos, radius=0.24, material=mat_o, collection=col)
        h1 = _add_uv_sphere("H1", h1_pos, radius=0.18, material=mat_h, collection=col)
        h2 = _add_uv_sphere("H2", h2_pos, radius=0.18, material=mat_h, collection=col)

        _add_cylinder("Bond_S_O1", s_pos, o1_pos, radius=0.06, material=mat_bond, collection=col)
        _add_cylinder("Bond_S_O2", s_pos, o2_pos, radius=0.06, material=mat_bond, collection=col)
        _add_cylinder("Bond_S_O3", s_pos, o3_pos, radius=0.06, material=mat_bond, collection=col)
        _add_cylinder("Bond_S_O4", s_pos, o4_pos, radius=0.06, material=mat_bond, collection=col)
        _add_cylinder("Bond_O2_H1", o2_pos, h1_pos, radius=0.05, material=mat_bond, collection=col)
        _add_cylinder("Bond_O1_H2", o1_pos, h2_pos, radius=0.05, material=mat_bond, collection=col)

        _add_text("Label_H2SO4", "H2SO4", (offset.x, offset.y, offset.z + 1.20), size=0.45, collection=col)
        focus.extend([s, o1, o2, o3, o4, h1, h2])

    add_hcl(Vector((-3.0, 0.0, 0.0)))
    add_hno3(Vector((0.0, 0.0, 0.0)))
    add_h2so4(Vector((3.2, 0.0, 0.0)))

    _setup_basic_light_and_camera(col, focus)


def build_hcl_with_ions(export_glb_path: str = None):
    _clear_scene()
    col = _ensure_collection("HCl_Ions")

    # Materials (conventional-ish colors)
    mat_h = _new_material("MAT_H", (0.95, 0.95, 0.95))
    mat_cl = _new_material("MAT_Cl", (0.25, 0.85, 0.25))
    mat_ion = _new_material("MAT_Ion", (0.20, 0.55, 1.00))
    mat_bond = _new_material("MAT_Bond", (0.2, 0.2, 0.2))

    # Layout: show original H—Cl and also separated H+ and Cl-
    # Molecule group
    h_pos = Vector((-1.4, 0.0, 0.0))
    cl_pos = Vector((-0.2, 0.0, 0.0))
    h = _add_uv_sphere("H", h_pos, radius=0.28, material=mat_h, collection=col)
    cl = _add_uv_sphere("Cl", cl_pos, radius=0.42, material=mat_cl, collection=col)
    _add_cylinder("Bond_H_Cl", h_pos, cl_pos, radius=0.07, material=mat_bond, collection=col)
    _add_text("Label_H", "H", (h_pos.x, h_pos.y, h_pos.z + 0.55), size=0.35, collection=col)
    _add_text("Label_Cl", "Cl", (cl_pos.x, cl_pos.y, cl_pos.z + 0.65), size=0.35, collection=col)

    # Ions group (separated)
    hp_pos = Vector((1.1, 0.0, 0.0))
    clm_pos = Vector((2.6, 0.0, 0.0))
    hp = _add_uv_sphere("H_plus", hp_pos, radius=0.22, material=mat_ion, collection=col)
    clm = _add_uv_sphere("Cl_minus", clm_pos, radius=0.44, material=mat_ion, collection=col)

    _add_text("Label_H_plus", "H+", (hp_pos.x, hp_pos.y, hp_pos.z + 0.55), size=0.32, collection=col)
    _add_text("Label_Cl_minus", "Cl-", (clm_pos.x, clm_pos.y, clm_pos.z + 0.70), size=0.32, collection=col)

    _setup_basic_light_and_camera(col, [h, cl, hp, clm])

    # Optional: export as GLB for Three.js
    if export_glb_path:
        _export_glb(export_glb_path)

def _keyframe_loc_scale(obj, frame: int, loc: Vector = None, scale: float = None):
    bpy.context.scene.frame_set(frame)
    if loc is not None:
        obj.location = loc
        obj.keyframe_insert(data_path="location", frame=frame)
    if scale is not None:
        obj.scale = (scale, scale, scale)
        obj.keyframe_insert(data_path="scale", frame=frame)


def build_hcl_dissociation_animation(export_glb_path: str = None):
    """
    One GLB with a single animation:
    - Start: bonded H—Cl visible, ions hidden
    - End: bonded hidden, ions visible and separated

    Note: glTF doesn't support animating visibility reliably, so we animate SCALE to ~0.
    """
    _clear_scene()
    col = _ensure_collection("HCl_Dissociation_Anim")

    # Timeline
    scene = bpy.context.scene
    scene.render.fps = 30
    start_f = 1
    end_f = 60  # 2 seconds @ 30fps
    scene.frame_start = start_f
    scene.frame_end = end_f

    # Materials
    mat_h = _new_material("MAT_H", (0.95, 0.95, 0.95))
    mat_cl = _new_material("MAT_Cl", (0.25, 0.85, 0.25))
    mat_ion = _new_material("MAT_Ion", (0.20, 0.55, 1.00))
    mat_bond = _new_material("MAT_Bond", (0.2, 0.2, 0.2))

    # Bonded molecule (center)
    h0 = Vector((-0.35, 0.0, 0.0))
    cl0 = Vector((0.35, 0.0, 0.0))
    h = _add_uv_sphere("H_bonded", h0, radius=0.22, material=mat_h, collection=col)
    cl = _add_uv_sphere("Cl_bonded", cl0, radius=0.34, material=mat_cl, collection=col)
    bond = _add_cylinder("Bond_H_Cl", h0, cl0, radius=0.07, material=mat_bond, collection=col)

    # Ions (start near center but hidden)
    hp_start = Vector((-0.15, 0.0, 0.0))
    clm_start = Vector((0.15, 0.0, 0.0))
    hp_end = Vector((-1.15, 0.0, 0.0))
    clm_end = Vector((1.15, 0.0, 0.0))
    hp = _add_uv_sphere("H_plus", hp_start, radius=0.20, material=mat_ion, collection=col)
    clm = _add_uv_sphere("Cl_minus", clm_start, radius=0.36, material=mat_ion, collection=col)

    # Optional labels (website strips Label_* anyway)
    _add_text("Label_H_plus", "H+", (hp_end.x, hp_end.y, hp_end.z + 0.55), size=0.32, collection=col)
    _add_text("Label_Cl_minus", "Cl-", (clm_end.x, clm_end.y, clm_end.z + 0.65), size=0.32, collection=col)

    # Lighting/camera for preview
    _setup_basic_light_and_camera(col, [h, cl, hp, clm])

    # Keyframes
    eps = 0.001
    # Start: bonded visible, ions hidden at center
    _keyframe_loc_scale(h, start_f, loc=h0, scale=1.0)
    _keyframe_loc_scale(cl, start_f, loc=cl0, scale=1.0)
    _keyframe_loc_scale(bond, start_f, scale=1.0)
    _keyframe_loc_scale(hp, start_f, loc=hp_start, scale=eps)
    _keyframe_loc_scale(clm, start_f, loc=clm_start, scale=eps)

    # End: bonded hidden, ions visible separated
    _keyframe_loc_scale(h, end_f, loc=h0, scale=eps)
    _keyframe_loc_scale(cl, end_f, loc=cl0, scale=eps)
    _keyframe_loc_scale(bond, end_f, scale=eps)
    _keyframe_loc_scale(hp, end_f, loc=hp_end, scale=1.0)
    _keyframe_loc_scale(clm, end_f, loc=clm_end, scale=1.0)

    # Make animation interpolation smooth (best-effort, API differs between versions)
    for obj in [h, cl, bond, hp, clm]:
        action = getattr(getattr(obj, "animation_data", None), "action", None)
        fcurves = getattr(action, "fcurves", None)
        if not fcurves:
            continue
        for fc in fcurves:
            for kp in getattr(fc, "keyframe_points", []):
                kp.interpolation = "BEZIER"

    if export_glb_path:
        _export_glb(export_glb_path)


def build_acid_row_with_hcl_anim(export_glb_path: str = None):
    """
    One scene, three acids arranged vertically (HNO3, HCl, H2SO4).
    Only HCl has the dissociation animation; the other two stay static.
    """
    _clear_scene()
    col = _ensure_collection("Acid_Row_HClAnim")

    scene = bpy.context.scene
    scene.render.fps = 30
    start_f = 1
    end_f = 60
    scene.frame_start = start_f
    scene.frame_end = end_f

    # Shared materials
    mat_h = _new_material("MAT_H", (0.95, 0.95, 0.95))
    mat_o = _new_material("MAT_O", (0.90, 0.20, 0.20))
    mat_n = _new_material("MAT_N", (0.15, 0.40, 0.95))
    mat_s = _new_material("MAT_S", (0.95, 0.65, 0.15))
    mat_cl = _new_material("MAT_Cl", (0.25, 0.85, 0.25))
    mat_bond = _new_material("MAT_Bond", (0.2, 0.2, 0.2))

    focus = []

    # Offsets along Y (top to bottom): HNO3, HCl, H2SO4
    off_hno3 = Vector((0.0, 2.6, 0.0))
    off_hcl = Vector((0.0, 0.0, 0.0))
    off_h2so4 = Vector((0.0, -2.6, 0.0))

    # --- Static HNO3 (top) ---
    n_pos = off_hno3 + Vector((0.0, 0.0, 0.0))
    o1_pos = off_hno3 + Vector((0.75, 0.05, 0.0))
    o2_pos = off_hno3 + Vector((-0.45, 0.70, 0.05))
    o3_pos = off_hno3 + Vector((-0.45, -0.70, -0.05))
    h_pos = off_hno3 + Vector((1.20, 0.10, 0.0))

    n = _add_uv_sphere("N_top", n_pos, radius=0.26, material=mat_n, collection=col)
    o1 = _add_uv_sphere("O1_top", o1_pos, radius=0.24, material=mat_o, collection=col)
    o2 = _add_uv_sphere("O2_top", o2_pos, radius=0.24, material=mat_o, collection=col)
    o3 = _add_uv_sphere("O3_top", o3_pos, radius=0.24, material=mat_o, collection=col)
    h = _add_uv_sphere("H_top", h_pos, radius=0.18, material=mat_h, collection=col)

    _add_cylinder("Bond_N_O1_top", n_pos, o1_pos, radius=0.06, material=mat_bond, collection=col)
    _add_cylinder("Bond_N_O2_top", n_pos, o2_pos, radius=0.06, material=mat_bond, collection=col)
    _add_cylinder("Bond_N_O3_top", n_pos, o3_pos, radius=0.06, material=mat_bond, collection=col)
    _add_cylinder("Bond_O1_H_top", o1_pos, h_pos, radius=0.05, material=mat_bond, collection=col)
    _add_text("Label_HNO3_row", "HNO3", (off_hno3.x, off_hno3.y, off_hno3.z + 1.1), size=0.45, collection=col)
    focus.extend([n, o1, o2, o3, h])

    # --- Animated HCl (middle) ---
    h0 = off_hcl + Vector((-0.35, 0.0, 0.0))
    cl0 = off_hcl + Vector((0.35, 0.0, 0.0))
    h_bonded = _add_uv_sphere("H_bonded_mid", h0, radius=0.22, material=mat_h, collection=col)
    cl_bonded = _add_uv_sphere("Cl_bonded_mid", cl0, radius=0.34, material=mat_cl, collection=col)
    bond = _add_cylinder("Bond_H_Cl_mid", h0, cl0, radius=0.07, material=mat_bond, collection=col)

    hp_start = off_hcl + Vector((-0.15, 0.0, 0.0))
    clm_start = off_hcl + Vector((0.15, 0.0, 0.0))
    hp_end = off_hcl + Vector((-1.15, 0.0, 0.0))
    clm_end = off_hcl + Vector((1.15, 0.0, 0.0))
    hp = _add_uv_sphere("H_plus_mid", hp_start, radius=0.20, material=mat_o, collection=col)
    clm = _add_uv_sphere("Cl_minus_mid", clm_start, radius=0.36, material=mat_cl, collection=col)

    _add_text("Label_HCl_row", "HCl", (off_hcl.x, off_hcl.y, off_hcl.z + 0.85), size=0.45, collection=col)
    _add_text("Label_H_plus_row", "H+", (hp_end.x, hp_end.y, hp_end.z + 0.55), size=0.32, collection=col)
    _add_text("Label_Cl_minus_row", "Cl-", (clm_end.x, clm_end.y, clm_end.z + 0.65), size=0.32, collection=col)
    focus.extend([h_bonded, cl_bonded, hp, clm])

    eps = 0.001
    _keyframe_loc_scale(h_bonded, start_f, loc=h0, scale=1.0)
    _keyframe_loc_scale(cl_bonded, start_f, loc=cl0, scale=1.0)
    _keyframe_loc_scale(bond, start_f, scale=1.0)
    _keyframe_loc_scale(hp, start_f, loc=hp_start, scale=eps)
    _keyframe_loc_scale(clm, start_f, loc=clm_start, scale=eps)

    _keyframe_loc_scale(h_bonded, end_f, loc=h0, scale=eps)
    _keyframe_loc_scale(cl_bonded, end_f, loc=cl0, scale=eps)
    _keyframe_loc_scale(bond, end_f, scale=eps)
    _keyframe_loc_scale(hp, end_f, loc=hp_end, scale=1.0)
    _keyframe_loc_scale(clm, end_f, loc=clm_end, scale=1.0)

    for obj in [h_bonded, cl_bonded, bond, hp, clm]:
        action = getattr(getattr(obj, "animation_data", None), "action", None)
        fcurves = getattr(action, "fcurves", None)
        if not fcurves:
            continue
        for fc in fcurves:
            for kp in getattr(fc, "keyframe_points", []):
                kp.interpolation = "BEZIER"

    # --- Static H2SO4 (bottom) ---
    s_pos = off_h2so4 + Vector((0.0, 0.0, 0.0))
    o1_pos = off_h2so4 + Vector((0.85, 0.15, 0.10))
    o2_pos = off_h2so4 + Vector((-0.35, 0.85, -0.10))
    o3_pos = off_h2so4 + Vector((-0.65, -0.55, 0.25))
    o4_pos = off_h2so4 + Vector((0.15, -0.75, -0.35))
    h1_pos = off_h2so4 + Vector((-0.62, 1.28, -0.18))
    h2_pos = off_h2so4 + Vector((1.25, 0.22, 0.15))

    s = _add_uv_sphere("S_bot", s_pos, radius=0.28, material=mat_s, collection=col)
    o1b = _add_uv_sphere("O1_bot", o1_pos, radius=0.24, material=mat_o, collection=col)
    o2b = _add_uv_sphere("O2_bot", o2_pos, radius=0.24, material=mat_o, collection=col)
    o3b = _add_uv_sphere("O3_bot", o3_pos, radius=0.24, material=mat_o, collection=col)
    o4b = _add_uv_sphere("O4_bot", o4_pos, radius=0.24, material=mat_o, collection=col)
    h1b = _add_uv_sphere("H1_bot", h1_pos, radius=0.18, material=mat_h, collection=col)
    h2b = _add_uv_sphere("H2_bot", h2_pos, radius=0.18, material=mat_h, collection=col)

    _add_cylinder("Bond_S_O1_bot", s_pos, o1_pos, radius=0.06, material=mat_bond, collection=col)
    _add_cylinder("Bond_S_O2_bot", s_pos, o2_pos, radius=0.06, material=mat_bond, collection=col)
    _add_cylinder("Bond_S_O3_bot", s_pos, o3_pos, radius=0.06, material=mat_bond, collection=col)
    _add_cylinder("Bond_S_O4_bot", s_pos, o4_pos, radius=0.06, material=mat_bond, collection=col)
    _add_cylinder("Bond_O2_H1_bot", o2_pos, h1_pos, radius=0.05, material=mat_bond, collection=col)
    _add_cylinder("Bond_O1_H2_bot", o1_pos, h2_pos, radius=0.05, material=mat_bond, collection=col)
    _add_text("Label_H2SO4_row", "H2SO4", (off_h2so4.x, off_h2so4.y, off_h2so4.z + 1.2), size=0.45, collection=col)
    focus.extend([s, o1b, o2b, o3b, o4b, h1b, h2b])

    _setup_basic_light_and_camera(col, focus)

    if export_glb_path:
        _export_glb(export_glb_path)


# ---- Run ----
# Exports for the website (Three.js)
# - Molecules
build_molecule_hcl(export_glb_path=r"D:\code\DoHoa\threejs\models\HCl.glb")
build_molecule_hno3(export_glb_path=r"D:\code\DoHoa\threejs\models\HNO3.glb")
build_molecule_h2so4(export_glb_path=r"D:\code\DoHoa\threejs\models\H2SO4.glb")
#
# - Extra teaching model (HCl + ions)
build_hcl_with_ions(export_glb_path=r"D:\code\DoHoa\threejs\models\HCl_ions.glb")

# Viewport preview: show 3 molecules in Blender (no animation)
build_gallery_preview()
