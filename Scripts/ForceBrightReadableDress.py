"""Rebuild ALL building/road materials as bright Unlit Emissive-only and reassign on Levee.

Unlit ignores Base Color — prior mats that only lit Base Color (or used tiny emissive
amps on dark AI textures ~RGB 65) read as black. Fix: emissive = texture * boost + lift.
"""
import unreal
import os

MAP_PATH = "/Game/Maps/Empire/Levee_Greybox"
TEX = "/Game/Art/Empire/Sprites/Textures"
MAT = "/Game/Art/Empire/Sprites/Materials"
FLAG = "Dress_BrightReadable_v1"

# texture asset name -> material name
BUILDING = [
    ("T_Bld_Garage", "M_Bright_Garage"),
    ("T_Bld_Cafe", "M_Bright_Cafe"),
    ("T_Bld_Dock", "M_Bright_Dock"),
    ("T_Bld_Bar", "M_Bright_Bar"),
    ("T_Bld_Board", "M_Bright_Board"),
    ("T_Bld_Freight", "M_Bright_Freight"),
    ("T_Bld_Rope", "M_Bright_Rope"),
    ("T_Facade_A", "M_Bright_Facade_A"),
    ("T_Facade_B", "M_Bright_Facade_B"),
    ("T_Facade_C", "M_Bright_Facade_C"),
    ("T_Facade_D", "M_Bright_Facade_D"),
]

ROADS = [
    ("T_Road_Asphalt", "M_Bright_Asphalt", 3.0, 4.0),
    ("T_Road_Lines", "M_Bright_RoadLines", 1.0, 6.0),
    ("T_Sidewalk", "M_Bright_Sidewalk", 4.0, 4.0),
    ("T_Dirt_Lot", "M_Bright_Dirt", 3.0, 3.0),
    ("T_Road_Cobble", "M_Bright_Cobble", 3.0, 3.0),
    ("T_Crosswalk", "M_Bright_Crosswalk", 1.0, 1.0),
]

BLOCKS = [
    ("Row_Garage", "M_Bright_Garage"),
    ("Row_Cafe", "M_Bright_Cafe"),
    ("Row_Dock", "M_Bright_Dock"),
    ("Row_MidC", "M_Bright_Facade_C"),
    ("Row_MidA", "M_Bright_Facade_A"),
    ("Row_MidB", "M_Bright_Facade_B"),
    ("Row_Bar", "M_Bright_Bar"),
    ("Row_Board", "M_Bright_Board"),
    ("Row_MidD", "M_Bright_Facade_D"),
    ("Row_MidE", "M_Bright_Facade_A"),
    ("Row_MidF", "M_Bright_Facade_B"),
    ("Row_MidG", "M_Bright_Facade_C"),
    ("Row_Rope", "M_Bright_Rope"),
    ("Row_Freight", "M_Bright_Freight"),
]


def find_by_label(label):
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if actor.get_actor_label() == label:
            return actor
    return None


def spawn(cls, location, scale=None, label=None):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actor = sub.spawn_actor_from_class(cls, location, unreal.Rotator(0, 0, 0))
    if scale is not None:
        actor.set_actor_scale3d(scale)
    if label is not None:
        actor.set_actor_label(label)
    return actor


def wipe_mat(mat_name):
    mat_path = "%s/%s" % (MAT, mat_name)
    if unreal.EditorAssetLibrary.does_asset_exist(mat_path):
        try:
            unreal.EditorAssetLibrary.delete_asset(mat_path)
        except Exception:
            pass
    root = unreal.Paths.project_content_dir()
    base = os.path.normpath(os.path.join(root, "Art/Empire/Sprites/Materials", mat_name))
    for ext in (".uasset", ".uexp", ".ubulk"):
        p = base + ext
        if os.path.isfile(p):
            try:
                os.remove(p)
            except OSError:
                pass
    return mat_path


def create_emissive_tex_mat(mat_name, texture, tile_u=1.0, tile_v=1.0, boost=3.5, lift=0.12):
    """Unlit: Emissive = texture*boost + lift. Base Color unused."""
    wipe_mat(mat_name)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        mat_name, MAT, unreal.Material, unreal.MaterialFactoryNew()
    )
    if mat is None:
        raise RuntimeError("create fail " + mat_name)

    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    mat.set_editor_property("two_sided", False)

    sample = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionTextureSample, -500, 0
    )
    sample.set_editor_property("texture", texture)

    if abs(tile_u - 1.0) > 0.01 or abs(tile_v - 1.0) > 0.01:
        uv = unreal.MaterialEditingLibrary.create_material_expression(
            mat, unreal.MaterialExpressionTextureCoordinate, -750, 0
        )
        mul_uv = unreal.MaterialEditingLibrary.create_material_expression(
            mat, unreal.MaterialExpressionMultiply, -620, 0
        )
        scale = unreal.MaterialEditingLibrary.create_material_expression(
            mat, unreal.MaterialExpressionConstant2Vector, -750, 100
        )
        scale.set_editor_property("r", float(tile_u))
        scale.set_editor_property("g", float(tile_v))
        unreal.MaterialEditingLibrary.connect_material_expressions(uv, "", mul_uv, "A")
        unreal.MaterialEditingLibrary.connect_material_expressions(scale, "", mul_uv, "B")
        unreal.MaterialEditingLibrary.connect_material_expressions(mul_uv, "", sample, "Coordinates")

    mul = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionMultiply, -280, 0
    )
    amp = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant, -420, 120
    )
    amp.set_editor_property("r", float(boost))
    unreal.MaterialEditingLibrary.connect_material_expressions(sample, "RGB", mul, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(amp, "", mul, "B")

    add = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionAdd, -120, 0
    )
    lift_c = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant3Vector, -280, 140
    )
    lift_c.set_editor_property("constant", unreal.LinearColor(lift, lift, lift * 0.95, 1.0))
    unreal.MaterialEditingLibrary.connect_material_expressions(mul, "", add, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(lift_c, "", add, "B")

    # ONLY emissive — this is what Unlit actually draws
    unreal.MaterialEditingLibrary.connect_material_property(
        add, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR
    )

    unreal.MaterialEditingLibrary.layout_material_expressions(mat)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset("%s/%s" % (MAT, mat_name))
    unreal.log("Bright mat " + mat_name)
    return mat


def create_solid(mat_name, r, g, b, emissive=2.0):
    wipe_mat(mat_name)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        mat_name, MAT, unreal.Material, unreal.MaterialFactoryNew()
    )
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    c = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant3Vector, -300, 0
    )
    c.set_editor_property("constant", unreal.LinearColor(r, g, b, 1.0))
    mul = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionMultiply, -80, 0
    )
    amp = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant, -300, 100
    )
    amp.set_editor_property("r", float(emissive))
    unreal.MaterialEditingLibrary.connect_material_expressions(c, "", mul, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(amp, "", mul, "B")
    unreal.MaterialEditingLibrary.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset("%s/%s" % (MAT, mat_name))
    return mat


def set_mat(actor, material):
    if not actor or not material:
        return False
    smc = getattr(actor, "static_mesh_component", None)
    if not smc:
        return False
    smc.set_material(0, material)
    smc.set_cast_shadow(False)
    actor.set_actor_hidden_in_game(False)
    return True


def main():
    if not unreal.EditorAssetLibrary.does_directory_exist(MAT):
        unreal.EditorAssetLibrary.make_directory(MAT)

    mats = {}
    for tex_name, mat_name in BUILDING:
        tex = unreal.load_asset("%s/%s" % (TEX, tex_name))
        if tex is None:
            unreal.log_warning("missing tex " + tex_name)
            continue
        mats[mat_name] = create_emissive_tex_mat(mat_name, tex, 1.0, 1.0, boost=4.0, lift=0.15)

    for tex_name, mat_name, tu, tv in ROADS:
        tex = unreal.load_asset("%s/%s" % (TEX, tex_name))
        if tex is None:
            unreal.log_warning("missing tex " + tex_name)
            continue
        # Roads are charcoal (~65) — heavy boost
        mats[mat_name] = create_emissive_tex_mat(mat_name, tex, tu, tv, boost=5.0, lift=0.18)

    roof = create_solid("M_Bright_Roof", 0.45, 0.42, 0.40, 1.8)
    mats["M_Bright_Roof"] = roof

    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level_editor.load_level(MAP_PATH):
        raise RuntimeError("load failed")

    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    bld_n = road_n = walk_n = 0

    asphalt = mats.get("M_Bright_Asphalt") or mats.get("M_Bright_RoadLines")
    lines = mats.get("M_Bright_RoadLines") or asphalt
    walk = mats.get("M_Bright_Sidewalk") or asphalt
    dirt = mats.get("M_Bright_Dirt") or walk
    xwalk = mats.get("M_Bright_Crosswalk")

    for prefix, mat_key in BLOCKS:
        mat = mats.get(mat_key)
        if not mat:
            continue
        for suffix in ("_Mass",):
            if set_mat(find_by_label(prefix + suffix), mat):
                bld_n += 1
        if set_mat(find_by_label(prefix + "_Roof"), roof):
            bld_n += 1
        for face in ("_S", "_W"):
            if set_mat(find_by_label("FacadeCube_%s%s" % (prefix, face)), mat):
                bld_n += 1

    for actor in sub.get_all_level_actors():
        lab = actor.get_actor_label()
        if lab.startswith("Avenue_"):
            idx = int(lab.split("_")[-1]) if lab.split("_")[-1].isdigit() else 0
            if set_mat(actor, lines if idx % 2 == 0 else asphalt):
                road_n += 1
        elif lab.startswith("Street_"):
            idx = int(lab.split("_")[-1]) if lab.split("_")[-1].isdigit() else 0
            if set_mat(actor, lines if idx % 2 == 1 else asphalt):
                road_n += 1
        elif lab.startswith("Walk"):
            if set_mat(actor, walk):
                walk_n += 1
        elif lab == "Ground":
            set_mat(actor, dirt)
        elif lab.startswith("Crosswalk_") and xwalk:
            set_mat(actor, xwalk)
        elif lab.startswith("CobblePatch_") and mats.get("M_Bright_Cobble"):
            set_mat(actor, mats["M_Bright_Cobble"])
        elif lab.startswith("RoadStripe_") and lines:
            set_mat(actor, lines)

    # Keep sky fill if present
    sky = unreal.load_asset("%s/M_SkyFill_Day" % MAT)
    if sky and find_by_label("SkyFill_Dome"):
        set_mat(find_by_label("SkyFill_Dome"), sky)

    if find_by_label(FLAG) is None:
        spawn(unreal.Actor, unreal.Vector(0, 0, -720), label=FLAG)

    if not level_editor.save_current_level():
        raise RuntimeError("save failed")
    unreal.EditorAssetLibrary.save_directory(MAT)
    unreal.log(
        "BRIGHT READABLE OK — buildings=%d roads=%d walks=%d mats=%d"
        % (bld_n, road_n, walk_n, len(mats))
    )


main()
