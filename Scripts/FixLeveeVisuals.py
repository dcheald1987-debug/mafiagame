"""Fix Levee from screenshot issues:
1) Snap Blackthorn buildings onto parcel sidewalks (not roads)
2) Dress each parcel with YOUR ElevenLabs façade image card (street-facing)
3) Delete static RoadCar3D editor cars (runtime LEStreetCar free-roams with your plates)
4) Rebuild façade sprite mats from Cropped PNGs
"""
import unreal
import os

MAP_PATH = "/Game/Maps/Empire/Levee_Greybox"
MESH_DIR = "/Game/Art/Empire/ExternalBuildings/Meshes"
SRC = unreal.Paths.project_content_dir() + "Art/Empire/Sprites/Source/Cropped"
DEST = "/Game/Art/Empire/Sprites"
TEX = DEST + "/Textures"
MAT = DEST + "/Materials"
FLAG = "Dress_FixLeveeVisuals_v1"
FLOOR_H = 190.0

# Parcel centers = sidewalk block centers between avenues/streets (1200 grid, 480 roads)
# x,y are block centers; footprint fits inside sidewalk square
PARCELS = [
    # label, x, y, fx, fy, floors, facade_key
    ("Row_Garage_Mass", 1800.0, -600.0, 560.0, 500.0, 3, "Bld_Garage"),
    ("Row_Cafe_Mass", 600.0, -600.0, 560.0, 500.0, 3, "Bld_Cafe"),
    ("Row_Dock_Mass", 1800.0, -1800.0, 560.0, 500.0, 2, "Bld_Dock"),
    ("Row_MidC_Mass", 600.0, -1800.0, 560.0, 500.0, 4, "Facade_C"),
    ("Row_MidA_Mass", -600.0, 600.0, 560.0, 500.0, 4, "Facade_A"),
    ("Row_MidB_Mass", -600.0, -600.0, 560.0, 500.0, 3, "Facade_B"),
    ("Row_Bar_Mass", -1800.0, -1800.0, 560.0, 500.0, 3, "Bld_Bar"),
    ("Row_Board_Mass", -600.0, 1800.0, 560.0, 500.0, 4, "Bld_Board"),
    ("Row_MidD_Mass", -1800.0, 600.0, 560.0, 500.0, 3, "Facade_D"),
    ("Row_MidE_Mass", -1800.0, -600.0, 560.0, 500.0, 3, "Facade_A"),
    ("Row_MidF_Mass", 600.0, 600.0, 560.0, 500.0, 4, "Facade_B"),
    ("Row_MidG_Mass", 1800.0, 600.0, 560.0, 500.0, 3, "Facade_C"),
    ("Row_Rope_Mass", -1800.0, 1800.0, 560.0, 460.0, 2, "Bld_Rope"),
    ("Row_Freight_Mass", -600.0, -1800.0, 560.0, 500.0, 2, "Bld_Freight"),
]

FACADE_PNG = {
    "Bld_Garage": "Buildings/S_Garage.png",
    "Bld_Cafe": "Buildings/S_Cafe.png",
    "Bld_Dock": "Buildings/S_Dock.png",
    "Bld_Bar": "Buildings/S_Bar.png",
    "Bld_Board": "Buildings/S_Board.png",
    "Bld_Freight": "Buildings/S_Freight.png",
    "Bld_Rope": "Buildings/S_Rope.png",
    "Facade_A": "Buildings/S_Facade_A.png",
    "Facade_B": "Buildings/S_Facade_B.png",
    "Facade_C": "Buildings/S_Facade_C.png",
    "Facade_D": "Buildings/S_Facade_D.png",
}


def ensure_dir(p):
    if not unreal.EditorAssetLibrary.does_directory_exist(p):
        unreal.EditorAssetLibrary.make_directory(p)


def find_by_label(label):
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if a.get_actor_label() == label:
            return a
    return None


def destroy_prefix(prefix):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    n = 0
    for a in list(sub.get_all_level_actors()):
        if a.get_actor_label().startswith(prefix):
            sub.destroy_actor(a)
            n += 1
    return n


def spawn(cls, loc, scale=None, label=None, rot=None):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    a = sub.spawn_actor_from_class(cls, loc, rot or unreal.Rotator(0, 0, 0))
    if scale is not None:
        a.set_actor_scale3d(scale)
    if label:
        a.set_actor_label(label)
    return a


def mesh_size(mesh):
    try:
        b = mesh.get_bounding_box()
        return unreal.Vector(abs(b.max.x - b.min.x), abs(b.max.y - b.min.y), abs(b.max.z - b.min.z))
    except Exception:
        return unreal.Vector(400, 400, 600)


def list_city_meshes():
    out = []
    for p in unreal.EditorAssetLibrary.list_assets(MESH_DIR, True, False):
        a = unreal.load_asset(p)
        if isinstance(a, unreal.StaticMesh) and "CityBuildings" in a.get_name():
            out.append(a)
    out.sort(key=lambda m: m.get_name())
    return out


def purge(rel):
    root = unreal.Paths.project_content_dir()
    base = os.path.normpath(os.path.join(root, rel.replace("/", os.sep)))
    for ext in (".uasset", ".uexp", ".ubulk"):
        p = base + ext
        if os.path.isfile(p):
            try:
                os.remove(p)
            except OSError:
                pass


def import_tex(name, rel):
    dest = "%s/%s" % (TEX, name)
    disk = os.path.normpath(os.path.join(SRC, rel.replace("/", os.sep)))
    if not os.path.isfile(disk):
        unreal.log_warning("missing " + disk)
        return None
    if unreal.EditorAssetLibrary.does_asset_exist(dest):
        try:
            unreal.EditorAssetLibrary.delete_asset(dest)
        except Exception:
            pass
    purge("Art/Empire/Sprites/Textures/" + name)
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", disk)
    task.set_editor_property("destination_path", TEX)
    task.set_editor_property("destination_name", name)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)
    task.set_editor_property("factory", unreal.TextureFactory())
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    return unreal.load_asset(dest)


def make_masked(name, tex):
    path = "%s/%s" % (MAT, name)
    mat = unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None
    if mat:
        unreal.MaterialEditingLibrary.delete_all_material_expressions(mat)
    else:
        purge("Art/Empire/Sprites/Materials/" + name)
        mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, MAT, unreal.Material, unreal.MaterialFactoryNew()
        )
    if not mat:
        return None
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
    mat.set_editor_property("two_sided", True)
    sample = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionTextureSample, -400, 0
    )
    sample.set_editor_property("texture", tex)
    unreal.MaterialEditingLibrary.connect_material_property(sample, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
    unreal.MaterialEditingLibrary.connect_material_property(sample, "RGB", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    unreal.MaterialEditingLibrary.connect_material_property(sample, "A", unreal.MaterialProperty.MP_OPACITY_MASK)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(path)
    return mat


def make_lit_facade(name, tex):
    """Opaque lit mat for wrapping onto 3D building mesh."""
    path = "%s/%s" % (MAT, name)
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        try:
            unreal.EditorAssetLibrary.delete_asset(path)
        except Exception:
            pass
    purge("Art/Empire/Sprites/Materials/" + name)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MAT, unreal.Material, unreal.MaterialFactoryNew()
    )
    if not mat:
        return None
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    sample = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionTextureSample, -400, 0
    )
    sample.set_editor_property("texture", tex)
    unreal.MaterialEditingLibrary.connect_material_property(sample, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
    mul = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionMultiply, -200, 180
    )
    c = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant, -380, 220
    )
    c.set_editor_property("r", 0.25)
    unreal.MaterialEditingLibrary.connect_material_expressions(sample, "RGB", mul, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(c, "", mul, "B")
    unreal.MaterialEditingLibrary.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(path)
    return mat


def ensure_building(label, x, y, fx, fy, floors, mesh, lit_mat):
    total_h = floors * FLOOR_H
    actor = find_by_label(label)
    if actor is None:
        actor = spawn(unreal.StaticMeshActor, unreal.Vector(x, y, total_h * 0.5), label=label)
    smc = actor.static_mesh_component
    smc.set_static_mesh(mesh)
    size = mesh_size(mesh)
    sxy = min(fx / max(size.x, 1.0), fy / max(size.y, 1.0)) * 0.90
    sz = total_h / max(size.z, 1.0)
    actor.set_actor_scale3d(unreal.Vector(sxy, sxy, sz))
    actor.set_actor_location(unreal.Vector(x, y, total_h * 0.5), False, True)
    actor.set_actor_rotation(unreal.Rotator(0, 0, 0), False)
    if lit_mat:
        smc.set_material(0, lit_mat)
    smc.set_cast_shadow(True)
    actor.set_actor_hidden_in_game(False)
    return actor


def place_facade_card(label, x, y, fx, fy, floors, mat):
    """Street-facing image card on the south curb of the parcel — YOUR building plate."""
    total_h = floors * FLOOR_H
    # South face of parcel (negative Y) — iso-readable
    front_y = y - fy * 0.52 - 20.0
    loc = unreal.Vector(x, front_y, total_h * 0.55)
    # Screen-ish upright card: yaw -45 matches iso; thin depth
    # Use cube: scale X=width, Y=thin, Z=height — rotated yaw -45
    width = fx / 100.0 * 0.95
    height = total_h / 100.0 * 0.95
    actor = find_by_label(label)
    cube = unreal.load_asset("/Engine/BasicShapes/Cube")
    if actor is None:
        actor = spawn(
            unreal.StaticMeshActor,
            loc,
            scale=unreal.Vector(width, 0.06, height),
            label=label,
            rot=unreal.Rotator(0, -45.0, 0),
        )
    else:
        actor.set_actor_location(loc, False, True)
        actor.set_actor_rotation(unreal.Rotator(0, -45.0, 0), False)
        actor.set_actor_scale3d(unreal.Vector(width, 0.06, height))
    smc = actor.static_mesh_component
    smc.set_static_mesh(cube)
    if mat:
        smc.set_material(0, mat)
    smc.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    smc.set_cast_shadow(False)
    actor.set_actor_hidden_in_game(False)
    return actor


def main():
    ensure_dir(TEX)
    ensure_dir(MAT)
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not les.load_level(MAP_PATH):
        raise RuntimeError("load failed")

    # Kill static editor cars + old props/cards that confuse the shot
    n_cars = destroy_prefix("RoadCar3D_")
    destroy_prefix("ImgProp_")
    destroy_prefix("Prop_")
    destroy_prefix("FacadeCard_")
    destroy_prefix("FacadePlane_")
    destroy_prefix("FacadeCube_")

    # Rebuild façade mats from YOUR PNGs
    sprite_mats = {}
    lit_mats = {}
    for key, rel in FACADE_PNG.items():
        tex = import_tex("T_" + key, rel)
        if not tex:
            continue
        sprite_mats[key] = make_masked("M_Sprite_" + key, tex)
        lit_mats[key] = make_lit_facade("M_Lit_" + key, tex)

    meshes = list_city_meshes()
    if not meshes:
        # fallback any ExternalBuildings static mesh
        for p in unreal.EditorAssetLibrary.list_assets(MESH_DIR, True, False):
            a = unreal.load_asset(p)
            if isinstance(a, unreal.StaticMesh):
                meshes.append(a)
    if not meshes:
        raise RuntimeError("No building meshes in " + MESH_DIR)

    placed = 0
    cards = 0
    for i, (label, x, y, fx, fy, floors, fkey) in enumerate(PARCELS):
        mesh = meshes[i % len(meshes)]
        lit = lit_mats.get(fkey)
        ensure_building(label, x, y, fx, fy, floors, mesh, lit)
        placed += 1
        smat = sprite_mats.get(fkey)
        if smat:
            place_facade_card("FacadeCard_" + label, x, y, fx, fy, floors, smat)
            cards += 1
        unreal.log("PARCEL %s @ (%.0f,%.0f) mesh=%s" % (label, x, y, mesh.get_name()))

    # Remove any stray StaticMeshActor buildings not on our parcel list
    keep = set(p[0] for p in PARCELS) | set("FacadeCard_" + p[0] for p in PARCELS)
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in list(sub.get_all_level_actors()):
        lab = a.get_actor_label()
        if lab.startswith("Row_") and lab.endswith("_Mass") and lab not in keep:
            sub.destroy_actor(a)
        if lab.startswith("Row_") and lab.endswith("_Roof"):
            sub.destroy_actor(a)

    destroy_prefix(FLAG)
    spawn(unreal.Actor, unreal.Vector(0, 0, -900), label=FLAG)

    if not les.save_current_level():
        raise RuntimeError("save failed")
    unreal.EditorAssetLibrary.save_directory(DEST)
    unreal.log(
        "FIX LEVEe OK — parcels=%d facade_cards=%d killed_static_cars=%d meshes=%d"
        % (placed, cards, n_cars, len(meshes))
    )


main()
