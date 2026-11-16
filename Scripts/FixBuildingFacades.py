"""v7 — YOUR plates on every building cube. Kill ALL mesh shadows in the level."""
import unreal
import os

MAP_PATH = "/Game/Maps/Empire/Levee_Greybox"
SRC = unreal.Paths.project_content_dir() + "Art/Empire/Sprites/Source/Cropped"
TEX = "/Game/Art/Empire/Sprites/Textures"
MAT = "/Game/Art/Empire/Sprites/Materials"
FLAG = "Dress_FixFacades_v7"

ROAD_W = 480.0
GRID = 1200.0
PAD = GRID - ROAD_W
FOOTPRINT = PAD * 0.78
FLOOR_H = 190.0
AVENUES = [2400.0, 1200.0, 0.0, -1200.0, -2400.0]
STREETS = [2400.0, 1200.0, 0.0, -1200.0, -2400.0]

PARCELS = [
    ("Row_Garage_Mass", 0, 2, 3, "Bld_Garage", "Buildings/S_Garage.png"),
    ("Row_Cafe_Mass", 1, 2, 3, "Bld_Cafe", "Buildings/S_Cafe.png"),
    ("Row_Dock_Mass", 0, 3, 2, "Bld_Dock", "Buildings/S_Dock.png"),
    ("Row_MidC_Mass", 1, 3, 4, "Facade_C", "Buildings/S_Facade_C.png"),
    ("Row_MidA_Mass", 2, 1, 4, "Facade_A", "Buildings/S_Facade_A.png"),
    ("Row_MidB_Mass", 2, 2, 3, "Facade_B", "Buildings/S_Facade_B.png"),
    ("Row_Bar_Mass", 3, 3, 3, "Bld_Bar", "Buildings/S_Bar.png"),
    ("Row_Board_Mass", 2, 0, 4, "Bld_Board", "Buildings/S_Board.png"),
    ("Row_MidD_Mass", 3, 1, 3, "Facade_D", "Buildings/S_Facade_D.png"),
    ("Row_MidE_Mass", 3, 2, 3, "Facade_E", "Buildings/S_Facade_E.png"),
    ("Row_MidF_Mass", 1, 1, 4, "Facade_F", "Buildings/S_Facade_F.png"),
    ("Row_MidG_Mass", 0, 1, 3, "Facade_G", "Buildings/S_Facade_G.png"),
    ("Row_Rope_Mass", 3, 0, 2, "Bld_Rope", "Buildings/S_Rope.png"),
    ("Row_Freight_Mass", 2, 3, 2, "Bld_Freight", "Buildings/S_Freight.png"),
]

KILL = ("FrontCard_", "SideCard_", "FacadeCard_", "FacadeCube_", "FacadePlane_")


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
    if not smc:
        return
    try:
        smc.set_cast_shadow(False)
    except Exception:
        pass
    for prop in (
        "cast_shadow",
        "cast_inset_shadow",
        "cast_static_shadow",
        "cast_dynamic_shadow",
        "cast_contact_shadow",
        "cast_hidden_shadow",
        "cast_shadow_as_two_sided",
    ):
        try:
            smc.set_editor_property(prop, False)
        except Exception:
            pass


def import_tex(name, rel):
    dest = "%s/%s" % (TEX, name)
    disk = os.path.normpath(os.path.join(SRC, rel.replace("/", os.sep)))
    if not os.path.isfile(disk):
        unreal.log_warning("MISSING " + disk)
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
    tex = unreal.load_asset(dest)
    if tex:
        try:
            tex.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_WORLD)
            tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_DEFAULT)
            tex.set_editor_property("srgb", True)
            unreal.EditorAssetLibrary.save_asset(dest)
        except Exception:
            pass
    return tex


def make_photo_mat(name, tex):
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
    # Lit + strong emissive fill so YOUR photo reads on every face (no black sides)
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    mat.set_editor_property("two_sided", True)

    sample = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionTextureSample, -450, 0
    )
    sample.set_editor_property("texture", tex)
    try:
        sample.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
    except Exception:
        pass
    unreal.MaterialEditingLibrary.connect_material_property(
        sample, "RGB", unreal.MaterialProperty.MP_BASE_COLOR
    )
    mul = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionMultiply, -200, 160
    )
    amp = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant, -380, 200
    )
    amp.set_editor_property("r", 2.5)
    unreal.MaterialEditingLibrary.connect_material_expressions(sample, "RGB", mul, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(amp, "", mul, "B")
    unreal.MaterialEditingLibrary.connect_material_property(
        mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR
    )
    rough = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant, -300, 320
    )
    rough.set_editor_property("r", 0.9)
    unreal.MaterialEditingLibrary.connect_material_property(
        rough, "", unreal.MaterialProperty.MP_ROUGHNESS
    )

    unreal.MaterialEditingLibrary.layout_material_expressions(mat)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(path)
    return mat


def kill_every_mesh_shadow():
    n = 0
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        try:
            comps = a.get_components_by_class(unreal.PrimitiveComponent)
        except Exception:
            comps = None
        if not comps:
            smc = getattr(a, "static_mesh_component", None)
            if smc:
                no_shadow(smc)
                n += 1
            continue
        for c in comps:
            no_shadow(c)
            n += 1
        # lights
        try:
            lights = a.get_components_by_class(unreal.LightComponent)
        except Exception:
            lights = None
        for c in lights or []:
            try:
                c.set_editor_property("cast_shadows", False)
            except Exception:
                pass
            try:
                c.set_editor_property("dynamic_shadow_distance_movable_light", 0.0)
            except Exception:
                pass
    unreal.log("shadows killed on ~%d comps" % n)


def dress_actor(label, ai, sj, floors, mat):
    cube = unreal.load_asset("/Engine/BasicShapes/Cube")
    cx, cy = parcel_center(ai, sj)
    total_h = floors * FLOOR_H
    loc = unreal.Vector(cx, cy, total_h * 0.5)
    scale = unreal.Vector(FOOTPRINT / 100.0, FOOTPRINT / 100.0, total_h / 100.0)
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
    no_shadow(smc)
    actor.set_actor_hidden_in_game(False)
    smc.set_visibility(True)
    unreal.log("DRESS %s <- %s" % (label, mat.get_name()))


def main():
    ensure_dir(TEX)
    ensure_dir(MAT)
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not les.load_level(MAP_PATH):
        raise RuntimeError("load failed")

    for p in KILL:
        destroy_prefix(p)

    mats = {}
    for _lab, _ai, _sj, _fl, key, rel in PARCELS:
        if key in mats:
            continue
        tex = import_tex("T_User_" + key, rel)
        if tex:
            mats[key] = make_photo_mat("M_User_" + key, tex)

    for label, ai, sj, floors, key, _rel in PARCELS:
        mat = mats.get(key)
        if mat:
            dress_actor(label, ai, sj, floors, mat)

    kill_every_mesh_shadow()

    destroy_prefix(FLAG)
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    flag = sub.spawn_actor_from_class(unreal.Actor, unreal.Vector(0, 0, -960))
    flag.set_actor_label(FLAG)

    if not les.save_current_level():
        raise RuntimeError("save failed")
    unreal.EditorAssetLibrary.save_directory(MAT)
    unreal.EditorAssetLibrary.save_directory(TEX)
    unreal.log("FIX FACADES v7 OK mats=%d — YOUR images, no mesh shadows" % len(mats))


main()
