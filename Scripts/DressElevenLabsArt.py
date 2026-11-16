"""Import new ElevenLabs single-view façades + characters; dress Levee.

Façades = flush planes on building fronts (3D mass stays for depth).
Characters = materials for runtime hood sprite planes.
"""
import unreal
import os

MAP_PATH = "/Game/Maps/Empire/Levee_Greybox"
SRC = unreal.Paths.project_content_dir() + "Art/Empire/Sprites/Source/Cropped"
DEST = "/Game/Art/Empire/Sprites"
FLAG = "Dress_ElevenLabs_v4"

# texture name -> relative under Cropped/
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
    ("T_Char_Eddie", "Characters/S_Eddie.png"),
    ("T_Char_Nicky", "Characters/S_Nicky.png"),
    ("T_Char_Nora", "Characters/S_Nora.png"),
    ("T_Char_HarlanCrew", "Characters/S_Harlan.png"),
    ("T_Char_Quinn", "Characters/S_Quinn.png"),
    ("T_Char_Bridget", "Characters/S_Bridget.png"),
]

# 1930 Chicago Near South parcels (BuildLeveeGrid / FixLeveeVisibility)
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
            tex.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_UI)
            tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_DEFAULT)
            unreal.EditorAssetLibrary.save_asset(dest)
        except Exception:
            pass
    unreal.log("Imported " + name)
    return tex


def _purge_package_files(content_rel_no_ext):
    """Remove orphan .uasset/.uexp when Asset Registry is stale (commandlet)."""
    root = unreal.Paths.project_content_dir()
    base = os.path.normpath(os.path.join(root, content_rel_no_ext.replace("/", os.sep)))
    for ext in (".uasset", ".uexp", ".ubulk"):
        path = base + ext
        if os.path.isfile(path):
            try:
                os.remove(path)
                unreal.log("Purged orphan " + path)
            except OSError as exc:
                unreal.log_warning("Could not purge %s: %s" % (path, exc))


def create_masked_mat(name, texture):
    mat_path = "%s/Materials/%s" % (DEST, name)
    mat = unreal.load_asset(mat_path) if unreal.EditorAssetLibrary.does_asset_exist(mat_path) else None
    if mat is not None:
        unreal.MaterialEditingLibrary.delete_all_material_expressions(mat)
    else:
        _purge_package_files("Art/Empire/Sprites/Materials/" + name)
        mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, DEST + "/Materials", unreal.Material, unreal.MaterialFactoryNew()
        )
    if mat is None:
        raise RuntimeError("mat fail " + name)
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
    mat.set_editor_property("two_sided", True)
    sample = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionTextureSample, -400, 0
    )
    sample.set_editor_property("texture", texture)
    unreal.MaterialEditingLibrary.connect_material_property(sample, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
    unreal.MaterialEditingLibrary.connect_material_property(sample, "RGB", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    unreal.MaterialEditingLibrary.connect_material_property(sample, "A", unreal.MaterialProperty.MP_OPACITY_MASK)
    unreal.MaterialEditingLibrary.layout_material_expressions(mat)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(mat_path)
    unreal.log("Material " + name)
    return mat


def ensure_facade_plane(label, origin, footprint_xy, floors, material):
    fx, fy = footprint_xy
    floor_h = 180.0
    total_h = floors * floor_h
    # Flush on south face (matches prior window/front_y convention)
    front_y = origin.y - fy * 0.52 - 8.0
    loc = unreal.Vector(origin.x, front_y, total_h * 0.5)
    # Plane: Pitch 90 stands up; scale X=width/100, Y=height/100
    rot = unreal.Rotator(90.0, 0.0, 0.0)
    scale = unreal.Vector(fx / 100.0, total_h / 100.0, 1.0)
    plane_mesh = unreal.load_asset("/Engine/BasicShapes/Plane")
    actor = find_by_label(label)
    if actor is None:
        actor = spawn(unreal.StaticMeshActor, loc, rot, scale, label)
        actor.static_mesh_component.set_static_mesh(plane_mesh)
    else:
        actor.set_actor_location(loc, False, True)
        actor.set_actor_rotation(rot, False)
        actor.set_actor_scale3d(scale)
        actor.static_mesh_component.set_static_mesh(plane_mesh)
    smc = actor.static_mesh_component
    smc.set_material(0, material)
    smc.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    smc.set_cast_shadow(False)
    actor.set_actor_hidden_in_game(False)
    return actor


def hide_front_extras(prefix):
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        label = actor.get_actor_label()
        if not label.startswith(prefix + "_"):
            continue
        if any(k in label for k in ("_Win_", "_Pilaster", "_Door", "_Awning", "_FireEsc", "_Shopfront", "_Stoop")):
            smc = getattr(actor, "static_mesh_component", None)
            if smc:
                smc.set_visibility(False, False)
                actor.set_actor_hidden_in_game(True)


def main():
    ensure_dir(DEST)
    ensure_dir(DEST + "/Textures")
    ensure_dir(DEST + "/Materials")

    mats = {}
    for name, rel in IMPORTS:
        tex = import_texture(name, rel)
        if tex is None:
            continue
        mat_name = name.replace("T_", "M_Sprite_")
        mats[name] = create_masked_mat(mat_name, tex)

    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level_editor.load_level(MAP_PATH):
        raise RuntimeError("load failed")

    # Clear prior façade dress / old sprite billboards
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in list(sub.get_all_level_actors()):
        lab = actor.get_actor_label()
        if lab.startswith("FacadePlane_") or lab.startswith("Sprite_") or lab in (
            "Dress_GameplaySprites_v1", "Dress_GameplaySprites_v2",
            "Dress_ElevenLabs_v1", "Dress_ElevenLabs_v2", "Dress_ElevenLabs_v3", FLAG,
        ):
            sub.destroy_actor(actor)

    # Façade Engine-Planes cause giant ortho wedges — do NOT spawn them.
    # Keep character sprite mats imported; buildings stay solid cubes from FixLevee*.
    placed = 0
    for prefix, origin, footprint, floors, tex_key in BLOCKS:
        # Explicitly remove any leftover plane for this row
        plane = find_by_label("FacadePlane_" + prefix)
        if plane:
            unreal.get_editor_subsystem(unreal.EditorActorSubsystem).destroy_actor(plane)
        placed += 1

    if find_by_label(FLAG) is None:
        spawn(unreal.Actor, unreal.Vector(0.0, 0.0, -600.0), label=FLAG)

    if not level_editor.save_current_level():
        raise RuntimeError("save failed")
    unreal.EditorAssetLibrary.save_directory(DEST)
    unreal.log("ELEVENLABS DRESS OK — planes_removed buildings=%d mats=%d (no façade planes)" % (placed, len(mats)))


main()
