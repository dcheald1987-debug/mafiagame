"""Dress YOUR OpenAI roofs on building tops + refresh road plates."""
import unreal
import os

MAP_PATH = "/Game/Maps/Empire/Levee_Greybox"
SRC_BLD = unreal.Paths.project_content_dir() + "Art/Empire/Sprites/Source/Cropped/Buildings"
SRC_ROAD = unreal.Paths.project_content_dir() + "Art/Empire/Sprites/Source/Cropped/Roads"
TEX = "/Game/Art/Empire/Sprites/Textures"
MAT = "/Game/Art/Empire/Sprites/Materials"
FLAG = "Dress_RoofsRoads_v1"

ROAD_W = 480.0
GRID = 1200.0
PAD = GRID - ROAD_W
FOOTPRINT = PAD * 0.78
FLOOR_H = 190.0
AVENUES = [2400.0, 1200.0, 0.0, -1200.0, -2400.0]
STREETS = [2400.0, 1200.0, 0.0, -1200.0, -2400.0]

# label, avenue_i, street_j, floors, roof jpg
ROOFS = [
    ("Row_Garage_Mass", 0, 2, 3, "S_Roof_Garage.jpg"),
    ("Row_Cafe_Mass", 1, 2, 3, "S_Roof_Cafe.jpg"),
    ("Row_Dock_Mass", 0, 3, 2, "S_Roof_Dock.jpg"),
    ("Row_MidC_Mass", 1, 3, 4, "S_Roof_Facade_C.jpg"),
    ("Row_MidA_Mass", 2, 1, 4, "S_Roof_Facade_A.jpg"),
    ("Row_MidB_Mass", 2, 2, 3, "S_Roof_Facade_B.jpg"),
    ("Row_Bar_Mass", 3, 3, 3, "S_Roof_Bar.jpg"),
    ("Row_Board_Mass", 2, 0, 4, "S_Roof_Board.jpg"),
    ("Row_MidD_Mass", 3, 1, 3, "S_Roof_Facade_D.jpg"),
    ("Row_MidE_Mass", 3, 2, 3, "S_Roof_Facade_E.jpg"),
    ("Row_MidF_Mass", 1, 1, 4, "S_Roof_Facade_F.jpg"),
    ("Row_MidG_Mass", 0, 1, 3, "S_Roof_Facade_G.jpg"),
    ("Row_Rope_Mass", 3, 0, 2, "S_Roof_Rope.jpg"),
    ("Row_Freight_Mass", 2, 3, 2, "S_Roof_Freight.jpg"),
]

ROAD_IMPORTS = [
    ("T_Road_Asphalt", "S_Road_Asphalt.jpg"),
    ("T_Road_Lines", "S_Road_Lines.jpg"),
    ("T_Road_Cobble", "S_Road_Cobble.jpg"),
]


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


def parcel_center(ai, sj):
    return (AVENUES[ai] + AVENUES[ai + 1]) * 0.5, (STREETS[sj] + STREETS[sj + 1]) * 0.5


def ensure_dir(p):
    if not unreal.EditorAssetLibrary.does_directory_exist(p):
        unreal.EditorAssetLibrary.make_directory(p)


def purge(rel):
    root = unreal.Paths.project_content_dir()
    base = os.path.normpath(os.path.join(root, rel.replace("/", os.sep)))
    for ext in (".uasset", ".uexp", ".ubulk"):
        path = base + ext
        if os.path.isfile(path):
            try:
                os.remove(path)
            except OSError:
                pass


def no_shadow(smc):
    try:
        smc.set_cast_shadow(False)
    except Exception:
        pass
    for prop in ("cast_shadow", "cast_inset_shadow", "cast_static_shadow", "cast_dynamic_shadow"):
        try:
            smc.set_editor_property(prop, False)
        except Exception:
            pass


def import_tex(name, disk_path):
    dest = "%s/%s" % (TEX, name)
    if not os.path.isfile(disk_path):
        unreal.log_warning("MISSING " + disk_path)
        return None
    if unreal.EditorAssetLibrary.does_asset_exist(dest):
        try:
            unreal.EditorAssetLibrary.delete_asset(dest)
        except Exception:
            pass
    purge("Art/Empire/Sprites/Textures/" + name)
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", disk_path)
    task.set_editor_property("destination_path", TEX)
    task.set_editor_property("destination_name", name)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)
    task.set_editor_property("factory", unreal.TextureFactory())
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    tex = unreal.load_asset(dest)
    if tex:
        try:
            tex.set_editor_property("srgb", True)
            tex.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_WORLD)
            unreal.EditorAssetLibrary.save_asset(dest)
        except Exception:
            pass
    unreal.log("TEX " + name)
    return tex


def make_lit_mat(name, tex, emissive=1.8):
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
    mat.set_editor_property("two_sided", True)
    sample = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionTextureSample, -400, 0
    )
    sample.set_editor_property("texture", tex)
    unreal.MaterialEditingLibrary.connect_material_property(
        sample, "RGB", unreal.MaterialProperty.MP_BASE_COLOR
    )
    mul = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionMultiply, -180, 140
    )
    amp = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant, -360, 180
    )
    amp.set_editor_property("r", float(emissive))
    unreal.MaterialEditingLibrary.connect_material_expressions(sample, "RGB", mul, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(amp, "", mul, "B")
    unreal.MaterialEditingLibrary.connect_material_property(
        mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR
    )
    rough = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant, -300, 280
    )
    rough.set_editor_property("r", 0.85)
    unreal.MaterialEditingLibrary.connect_material_property(
        rough, "", unreal.MaterialProperty.MP_ROUGHNESS
    )
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(path)
    return mat


def make_tiled_road_mat(name, tex, tile_u=6.0, tile_v=6.0, emissive=0.35):
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
    texcoord = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionTextureCoordinate, -700, 0
    )
    mul_uv = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionMultiply, -520, 0
    )
    scale = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant2Vector, -700, 120
    )
    scale.set_editor_property("r", float(tile_u))
    scale.set_editor_property("g", float(tile_v))
    unreal.MaterialEditingLibrary.connect_material_expressions(texcoord, "", mul_uv, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(scale, "", mul_uv, "B")
    sample = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionTextureSample, -300, 0
    )
    sample.set_editor_property("texture", tex)
    unreal.MaterialEditingLibrary.connect_material_expressions(mul_uv, "", sample, "Coordinates")
    unreal.MaterialEditingLibrary.connect_material_property(
        sample, "RGB", unreal.MaterialProperty.MP_BASE_COLOR
    )
    mul_e = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionMultiply, -80, 140
    )
    amp = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant, -280, 180
    )
    amp.set_editor_property("r", float(emissive))
    unreal.MaterialEditingLibrary.connect_material_expressions(sample, "RGB", mul_e, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(amp, "", mul_e, "B")
    unreal.MaterialEditingLibrary.connect_material_property(
        mul_e, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR
    )
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(path)
    return mat


def place_roof(label, cx, cy, floors, mat):
    total_h = floors * FLOOR_H
    # Flat slab just above the mass top
    loc = unreal.Vector(cx, cy, total_h + 6.0)
    # Thin in Z so top face shows the roof plate
    scale = unreal.Vector(FOOTPRINT / 100.0 * 1.02, FOOTPRINT / 100.0 * 1.02, 0.08)
    cube = unreal.load_asset("/Engine/BasicShapes/Cube")
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actor = find_by_label(label)
    if actor is None:
        actor = sub.spawn_actor_from_class(unreal.StaticMeshActor, loc, unreal.Rotator(0, 0, 0))
        actor.set_actor_label(label)
    actor.set_actor_location(loc, False, True)
    actor.set_actor_rotation(unreal.Rotator(0, 0, 0), False)
    actor.set_actor_scale3d(scale)
    smc = actor.static_mesh_component
    smc.set_static_mesh(cube)
    smc.set_material(0, mat)
    smc.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    no_shadow(smc)
    actor.set_actor_hidden_in_game(False)
    unreal.log("ROOF %s <- %s" % (label, mat.get_name()))


def main():
    ensure_dir(TEX)
    ensure_dir(MAT)
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not les.load_level(MAP_PATH):
        raise RuntimeError("load failed")

    destroy_prefix("RoofCard_")
    destroy_prefix("CobblePatch_")

    # --- Roofs ---
    roof_mats = {}
    for _lab, _ai, _sj, _fl, jpg in ROOFS:
        key = jpg.replace(".jpg", "")
        if key in roof_mats:
            continue
        disk = os.path.normpath(os.path.join(SRC_BLD, jpg))
        tex = import_tex("T_" + key, disk)
        if tex:
            roof_mats[key] = make_lit_mat("M_" + key, tex, 2.0)

    n_roofs = 0
    for label, ai, sj, floors, jpg in ROOFS:
        key = jpg.replace(".jpg", "")
        mat = roof_mats.get(key)
        if not mat:
            continue
        cx, cy = parcel_center(ai, sj)
        place_roof("RoofCard_" + label, cx, cy, floors, mat)
        n_roofs += 1

    # --- Roads ---
    road_tex = {}
    for name, filename in ROAD_IMPORTS:
        disk = os.path.normpath(os.path.join(SRC_ROAD, filename))
        t = import_tex(name, disk)
        if t:
            road_tex[name] = t

    asphalt = None
    lines = None
    cobble = None
    if "T_Road_Asphalt" in road_tex:
        asphalt = make_tiled_road_mat("M_Custom_Asphalt", road_tex["T_Road_Asphalt"], 6.0, 6.0, 0.4)
    if "T_Road_Lines" in road_tex:
        lines = make_tiled_road_mat("M_Custom_RoadLines", road_tex["T_Road_Lines"], 1.0, 8.0, 0.4)
    if "T_Road_Cobble" in road_tex:
        cobble = make_tiled_road_mat("M_Custom_Cobble", road_tex["T_Road_Cobble"], 4.0, 4.0, 0.35)

    n_roads = 0
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in sub.get_all_level_actors():
        lab = actor.get_actor_label()
        smc = getattr(actor, "static_mesh_component", None)
        if not smc:
            continue
        mat = None
        if lab.startswith("Avenue_") or lab.startswith("FabRoad_NS_") or lab.startswith("FabRoad_EW_"):
            tail = lab.split("_")[-1]
            idx = int(tail) if tail.isdigit() else hash(lab) % 2
            mat = lines if (idx % 2 == 0 and lines) else asphalt
        elif lab.startswith("Street_"):
            tail = lab.split("_")[-1]
            idx = int(tail) if tail.isdigit() else 0
            mat = lines if (idx % 2 == 1 and lines) else asphalt
        elif lab.startswith("FabRoad_X_"):
            mat = asphalt
        if mat:
            smc.set_material(0, mat)
            no_shadow(smc)
            n_roads += 1

    if cobble:
        for lab, loc in (
            ("CobblePatch_Dock", unreal.Vector(1800.0, -1800.0, -30.0)),
            ("CobblePatch_Rope", unreal.Vector(-1800.0, 1800.0, -30.0)),
        ):
            cube = unreal.load_asset("/Engine/BasicShapes/Cube")
            a = find_by_label(lab)
            if a is None:
                a = sub.spawn_actor_from_class(unreal.StaticMeshActor, loc, unreal.Rotator(0, 0, 0))
                a.set_actor_label(lab)
            a.set_actor_location(loc, False, True)
            a.set_actor_scale3d(unreal.Vector(8.0, 8.0, 0.2))
            smc = a.static_mesh_component
            smc.set_static_mesh(cube)
            smc.set_material(0, cobble)
            no_shadow(smc)

    destroy_prefix(FLAG)
    flag = sub.spawn_actor_from_class(unreal.Actor, unreal.Vector(0, 0, -970))
    flag.set_actor_label(FLAG)

    if not les.save_current_level():
        raise RuntimeError("save failed")
    unreal.EditorAssetLibrary.save_directory(MAT)
    unreal.EditorAssetLibrary.save_directory(TEX)
    unreal.log("ROOFS+ROADS OK — roofs=%d roads=%d" % (n_roofs, n_roads))


main()
