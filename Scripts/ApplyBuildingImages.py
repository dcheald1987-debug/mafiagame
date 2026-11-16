"""Import cropped building PNGs and dress Row_* fronts as thin CUBES (never Planes)."""
import unreal
import os

MAP_PATH = "/Game/Maps/Empire/Levee_Greybox"
SRC = unreal.Paths.project_content_dir() + "Art/Empire/Sprites/Source/Cropped"
DEST = "/Game/Art/Empire/Sprites"
FLAG = "Dress_BuildingImages_v1"
FLOOR_H = 190.0

IMPORTS = [
    ("T_Bld_Garage", "Buildings/S_Garage.png"),
    ("T_Bld_Cafe", "Buildings/S_Cafe.png"),
    ("T_Bld_Dock", "Buildings/S_Dock.png"),
    ("T_Bld_Bar", "Buildings/S_Bar.png"),
    ("T_Bld_Board", "Buildings/S_Board.png"),
    ("T_Bld_Freight", "Buildings/S_Freight.png"),
    ("T_Bld_Rope", "Buildings/S_Rope.png"),
    ("T_Facade_A", "Buildings/S_Facade_A.png"),
    ("T_Facade_B", "Buildings/S_Facade_B.png"),
    ("T_Facade_C", "Buildings/S_Facade_C.png"),
    ("T_Facade_D", "Buildings/S_Facade_D.png"),
]

BLOCKS = [
    ("Row_Garage", unreal.Vector(1800.0, -600.0, 0.0), (560.0, 500.0), 3, "T_Bld_Garage"),
    ("Row_Cafe", unreal.Vector(600.0, -600.0, 0.0), (560.0, 500.0), 3, "T_Bld_Cafe"),
    ("Row_Dock", unreal.Vector(1800.0, -1800.0, 0.0), (560.0, 500.0), 2, "T_Bld_Dock"),
    ("Row_MidC", unreal.Vector(600.0, -1800.0, 0.0), (560.0, 500.0), 4, "T_Facade_C"),
    ("Row_MidA", unreal.Vector(-600.0, 600.0, 0.0), (560.0, 500.0), 4, "T_Facade_A"),
    ("Row_MidB", unreal.Vector(-600.0, -600.0, 0.0), (560.0, 500.0), 3, "T_Facade_B"),
    ("Row_Bar", unreal.Vector(-1800.0, -1800.0, 0.0), (560.0, 500.0), 3, "T_Bld_Bar"),
    ("Row_Board", unreal.Vector(-600.0, 1800.0, 0.0), (560.0, 500.0), 4, "T_Bld_Board"),
    ("Row_MidD", unreal.Vector(-1800.0, 600.0, 0.0), (560.0, 500.0), 3, "T_Facade_D"),
    ("Row_MidE", unreal.Vector(-1800.0, -600.0, 0.0), (560.0, 500.0), 3, "T_Facade_A"),
    ("Row_MidF", unreal.Vector(600.0, 600.0, 0.0), (560.0, 500.0), 4, "T_Facade_B"),
    ("Row_MidG", unreal.Vector(1800.0, 600.0, 0.0), (560.0, 500.0), 3, "T_Facade_C"),
    ("Row_Rope", unreal.Vector(-1800.0, 1800.0, 0.0), (560.0, 460.0), 2, "T_Bld_Rope"),
    ("Row_Freight", unreal.Vector(-600.0, -1800.0, 0.0), (560.0, 500.0), 2, "T_Bld_Freight"),
]


def ensure_dir(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def find_by_label(label):
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if actor.get_actor_label() == label:
            return actor
    return None


def spawn(cls, location, rotation=None, scale=None, label=None):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    rot = rotation or unreal.Rotator(0.0, 0.0, 0.0)
    actor = sub.spawn_actor_from_class(cls, location, rot)
    if scale is not None:
        actor.set_actor_scale3d(scale)
    if label is not None:
        actor.set_actor_label(label)
    return actor


def import_texture(name, rel):
    dest = "%s/Textures/%s" % (DEST, name)
    disk = os.path.normpath(os.path.join(SRC, rel.replace("/", os.sep)))
    if not os.path.isfile(disk):
        unreal.log_warning("Missing " + disk)
        return None
    if unreal.EditorAssetLibrary.does_asset_exist(dest):
        unreal.EditorAssetLibrary.delete_asset(dest)
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", disk)
    task.set_editor_property("destination_path", DEST + "/Textures")
    task.set_editor_property("destination_name", name)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)
    task.set_editor_property("factory", unreal.TextureFactory())
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    tex = unreal.load_asset(dest)
    if tex:
        try:
            tex.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_WORLD)
            tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_DEFAULT)
            tex.set_editor_property("srgb", True)
            unreal.EditorAssetLibrary.save_asset(dest)
        except Exception:
            pass
    unreal.log("Imported " + name)
    return tex


def create_facade_mat(name, texture):
    """Opaque unlit façade — never masked two-sided plane mats."""
    mat_path = "%s/Materials/%s" % (DEST, name)
    mat = None
    if unreal.EditorAssetLibrary.does_asset_exist(mat_path):
        mat = unreal.load_asset(mat_path)
        if mat is not None:
            unreal.MaterialEditingLibrary.delete_all_material_expressions(mat)
    if mat is None:
        try:
            unreal.EditorAssetLibrary.delete_asset(mat_path)
        except Exception:
            pass
        mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, DEST + "/Materials", unreal.Material, unreal.MaterialFactoryNew()
        )
    if mat is None:
        # Fallback: use prior double-prefixed name from first import
        alt = mat_path.replace("/M_Bld_", "/M_Bld_Bld_") if "_Facade_" not in name else None
        if alt and unreal.EditorAssetLibrary.does_asset_exist(alt):
            mat = unreal.load_asset(alt)
        if mat is None:
            raise RuntimeError("mat fail " + name)
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    mat.set_editor_property("two_sided", False)
    sample = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionTextureSample, -400, 0
    )
    sample.set_editor_property("texture", texture)
    unreal.MaterialEditingLibrary.connect_material_property(
        sample, "RGB", unreal.MaterialProperty.MP_BASE_COLOR
    )
    # Mild emissive so façades read in flat day light
    mul = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionMultiply, -150, 120
    )
    amp = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant, -350, 200
    )
    amp.set_editor_property("r", 0.35)
    unreal.MaterialEditingLibrary.connect_material_expressions(sample, "RGB", mul, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(amp, "", mul, "B")
    unreal.MaterialEditingLibrary.connect_material_property(
        mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR
    )
    unreal.MaterialEditingLibrary.layout_material_expressions(mat)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(mat_path)
    unreal.log("Material " + name)
    return mat


def ensure_facade_cube(label, location, scale, yaw_deg, material):
    """Thin CUBE façade — cubes do not produce ortho Plane wedges."""
    cube = unreal.load_asset("/Engine/BasicShapes/Cube")
    rot = unreal.Rotator(0.0, yaw_deg, 0.0)
    actor = find_by_label(label)
    if actor is None:
        actor = spawn(unreal.StaticMeshActor, location, rot, scale, label)
    else:
        actor.set_actor_location(location, False, True)
        actor.set_actor_rotation(rot, False)
        actor.set_actor_scale3d(scale)
    smc = actor.static_mesh_component
    smc.set_static_mesh(cube)  # never Plane
    smc.set_material(0, material)
    smc.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    smc.set_cast_shadow(False)
    actor.set_actor_hidden_in_game(False)
    actor.set_actor_enable_collision(False)
    return actor


def main():
    ensure_dir(DEST)
    ensure_dir(DEST + "/Textures")
    ensure_dir(DEST + "/Materials")

    mats = {}
    for name, rel in IMPORTS:
        tex = import_texture(name, rel)
        if tex is None:
            continue
        # T_Bld_Garage -> M_Bld_Garage ; T_Facade_A -> M_Bld_Facade_A
        mat_name = "M_Bld_" + name.replace("T_Bld_", "").replace("T_", "")
        mats[name] = create_facade_mat(mat_name, tex)

    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level_editor.load_level(MAP_PATH):
        raise RuntimeError("load failed")

    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    # Kill any leftover Plane façades / old dress flags
    for actor in list(sub.get_all_level_actors()):
        lab = actor.get_actor_label()
        if lab.startswith("FacadePlane_") or lab.startswith("FacadeCube_"):
            sub.destroy_actor(actor)
            continue
        if lab.startswith("Dress_ElevenLabs") or lab.startswith("Dress_GameplaySprites") or lab == FLAG:
            sub.destroy_actor(actor)
            continue
        smc = getattr(actor, "static_mesh_component", None)
        if smc and smc.static_mesh and "Plane" in smc.static_mesh.get_name():
            sub.destroy_actor(actor)

    roof = unreal.load_asset("/Game/Art/Empire/Materials/M_Roof_Slate")
    brick = unreal.load_asset("/Game/Art/Empire/Materials/M_Brick_Dark")
    placed = 0
    for prefix, origin, footprint, floors, tex_key in BLOCKS:
        mat = mats.get(tex_key)
        if mat is None:
            unreal.log_warning("No mat for " + tex_key)
            continue
        fx, fy = footprint
        total_h = floors * FLOOR_H
        # South face (toward -Y) — iso camera sees this
        ensure_facade_cube(
            "FacadeCube_%s_S" % prefix,
            unreal.Vector(origin.x, origin.y - fy * 0.5 - 14.0, total_h * 0.5),
            unreal.Vector(fx / 100.0 * 0.98, 0.22, total_h / 100.0),
            0.0,
            mat,
        )
        # West face (toward -X) — also visible under -45 yaw iso
        ensure_facade_cube(
            "FacadeCube_%s_W" % prefix,
            unreal.Vector(origin.x - fx * 0.5 - 14.0, origin.y, total_h * 0.5),
            unreal.Vector(0.22, fy / 100.0 * 0.98, total_h / 100.0),
            0.0,
            mat,
        )
        mass = find_by_label(prefix + "_Mass")
        if mass and mass.static_mesh_component:
            # Mass also gets the art so every angle shows the building image
            mass.static_mesh_component.set_material(0, mat)
            mass.static_mesh_component.set_cast_shadow(False)
        rf = find_by_label(prefix + "_Roof")
        if rf and rf.static_mesh_component and roof:
            rf.static_mesh_component.set_material(0, roof)
            rf.static_mesh_component.set_cast_shadow(False)
        placed += 1

    if find_by_label(FLAG) is None:
        spawn(unreal.Actor, unreal.Vector(0.0, 0.0, -600.0), label=FLAG)

    if not level_editor.save_current_level():
        raise RuntimeError("save failed")
    unreal.EditorAssetLibrary.save_directory(DEST)
    unreal.log("BUILDING IMAGES OK — façades=%d mats=%d (cube fronts, no planes)" % (placed, len(mats)))


main()
