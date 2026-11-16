"""Import keyed street crowd / car / prop PNGs; dress Levee with thin Cubes (no Planes)."""
import unreal
import os

MAP_PATH = "/Game/Maps/Empire/Levee_Greybox"
SRC = unreal.Paths.project_content_dir() + "Art/Empire/Sprites/Source/Cropped"
DEST = "/Game/Art/Empire/Sprites"
FLAG = "Dress_StreetAssets_v1"

IMPORTS = [
    ("T_Char_RivalThug", "Characters/S_RivalThug.png"),
    ("T_Char_Cop", "Characters/S_Cop.png"),
    ("T_Char_Bartender", "Characters/S_Bartender.png"),
    ("T_Char_CivWoman_B", "Characters/S_CivWoman_B.png"),
    ("T_Char_Newsboy", "Characters/S_Newsboy.png"),
    ("T_Car_ModelA", "Cars/S_ModelA.png"),
    ("T_Car_Police", "Cars/S_PoliceCar.png"),
    ("T_Car_Taxi", "Cars/S_Taxi.png"),
    ("T_Car_Delivery", "Cars/S_DeliveryTruck.png"),
    ("T_Prop_LampHead", "Props/S_LampHead.png"),
    ("T_Prop_LampHeadBroken", "Props/S_LampHead_Broken.png"),
    ("T_Prop_TrafficHead", "Props/S_TrafficHead.png"),
    ("T_Prop_TrafficHeadSide", "Props/S_TrafficHead_Side.png"),
    ("T_Prop_TrafficPole", "Props/S_TrafficPole.png"),
    ("T_Prop_PedSignal", "Props/S_PedSignal.png"),
]

# Thin cube placers: (label, mat_key, loc, scale, yaw)
# Characters face south (-Y) toward iso camera; cars along avenues
PLACERS = [
    ("SpriteChar_RivalThug", "M_Sprite_Char_RivalThug", unreal.Vector(900.0, 200.0, 90.0), unreal.Vector(0.12, 1.1, 1.8), 0.0),
    ("SpriteChar_Cop", "M_Sprite_Char_Cop", unreal.Vector(400.0, 220.0, 90.0), unreal.Vector(0.12, 1.0, 1.7), 0.0),
    ("SpriteChar_Bartender", "M_Sprite_Char_Bartender", unreal.Vector(-1600.0, -1500.0, 90.0), unreal.Vector(0.12, 1.0, 1.7), 90.0),
    ("SpriteChar_CivWoman_B", "M_Sprite_Char_CivWoman_B", unreal.Vector(-200.0, 400.0, 85.0), unreal.Vector(0.12, 0.95, 1.6), 0.0),
    ("SpriteChar_Newsboy", "M_Sprite_Char_Newsboy", unreal.Vector(100.0, -100.0, 70.0), unreal.Vector(0.1, 0.7, 1.2), 0.0),
    ("SpriteCar_ModelA", "M_Sprite_Car_ModelA", unreal.Vector(600.0, 80.0, 55.0), unreal.Vector(2.4, 0.12, 1.0), 90.0),
    ("SpriteCar_Police", "M_Sprite_Car_Police", unreal.Vector(-400.0, 80.0, 55.0), unreal.Vector(2.5, 0.12, 1.05), 90.0),
    ("SpriteCar_Taxi", "M_Sprite_Car_Taxi", unreal.Vector(80.0, 600.0, 55.0), unreal.Vector(0.12, 2.4, 1.0), 0.0),
    ("SpriteCar_Delivery", "M_Sprite_Car_Delivery", unreal.Vector(1800.0, -900.0, 60.0), unreal.Vector(2.8, 0.12, 1.2), 90.0),
]

# Traffic signals at major intersections — pole + head as thin cubes
TRAFFIC = [
    (0.0, 0.0, 45.0),
    (1200.0, 0.0, -45.0),
    (-1200.0, 0.0, 135.0),
    (0.0, 1200.0, -135.0),
    (0.0, -1200.0, 45.0),
    (1200.0, 1200.0, -45.0),
]


def ensure_dir(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def find_by_label(label):
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if actor.get_actor_label() == label:
            return actor
    return None


def spawn(cls, location, scale=None, label=None, yaw=0.0):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actor = sub.spawn_actor_from_class(cls, location, unreal.Rotator(0.0, yaw, 0.0))
    if scale is not None:
        actor.set_actor_scale3d(scale)
    if label is not None:
        actor.set_actor_label(label)
    return actor


def destroy_prefix(prefix):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in list(sub.get_all_level_actors()):
        if actor.get_actor_label().startswith(prefix):
            sub.destroy_actor(actor)


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


def create_sprite_material(name, texture):
    mat_path = "%s/Materials/%s" % (DEST, name)
    if unreal.EditorAssetLibrary.does_asset_exist(mat_path):
        try:
            mat = unreal.EditorAssetLibrary.load_asset(mat_path)
            unreal.MaterialEditingLibrary.delete_all_material_expressions(mat)
        except Exception:
            unreal.EditorAssetLibrary.delete_asset(mat_path)
            mat = None
    else:
        mat = None
    if mat is None:
        if unreal.EditorAssetLibrary.does_asset_exist(mat_path):
            unreal.EditorAssetLibrary.delete_asset(mat_path)
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


def ensure_cube(label, location, scale, material, yaw=0.0):
    cube = unreal.load_asset("/Engine/BasicShapes/Cube")
    actor = find_by_label(label)
    if actor is None:
        actor = spawn(unreal.StaticMeshActor, location, scale, label, yaw)
    else:
        actor.set_actor_location(location, False, True)
        actor.set_actor_rotation(unreal.Rotator(0.0, yaw, 0.0), False)
        actor.set_actor_scale3d(scale)
    smc = actor.static_mesh_component
    smc.set_static_mesh(cube)
    smc.set_material(0, material)
    smc.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    smc.set_cast_shadow(False)
    actor.set_actor_hidden_in_game(False)
    return actor


def main():
    ensure_dir(DEST)
    ensure_dir(DEST + "/Textures")
    ensure_dir(DEST + "/Materials")

    mats = {}
    for tex_name, rel in IMPORTS:
        tex = import_texture(tex_name, rel)
        if tex is None:
            continue
        mat_name = tex_name.replace("T_", "M_Sprite_")
        mats[mat_name] = create_sprite_material(mat_name, tex)

    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level_editor.load_level(MAP_PATH):
        raise RuntimeError("load failed")

    destroy_prefix("SpriteChar_")
    destroy_prefix("SpriteCar_")
    destroy_prefix("TrafficPole_")
    destroy_prefix("TrafficHead_")
    destroy_prefix("PedSignal_")
    destroy_prefix(FLAG)

    placed = 0
    for label, mat_key, loc, scale, yaw in PLACERS:
        mat = mats.get(mat_key)
        if mat is None:
            unreal.log_warning("skip " + label)
            continue
        ensure_cube(label, loc, scale, mat, yaw)
        placed += 1

    pole_mat = mats.get("M_Sprite_Prop_TrafficPole")
    head_mat = mats.get("M_Sprite_Prop_TrafficHead")
    ped_mat = mats.get("M_Sprite_Prop_PedSignal")
    for i, (x, y, yaw) in enumerate(TRAFFIC):
        curb_x = x + 160.0
        curb_y = y + 160.0
        if pole_mat:
            ensure_cube(
                "TrafficPole_%d" % i,
                unreal.Vector(curb_x, curb_y, 140.0),
                unreal.Vector(0.15, 0.15, 2.8),
                pole_mat,
                yaw,
            )
            placed += 1
        if head_mat:
            # Head hangs toward intersection center
            hx = curb_x - 40.0
            hy = curb_y - 40.0
            ensure_cube(
                "TrafficHead_%d" % i,
                unreal.Vector(hx, hy, 260.0),
                unreal.Vector(0.55, 0.12, 1.1),
                head_mat,
                yaw + 45.0,
            )
            placed += 1
        if ped_mat and i < 4:
            ensure_cube(
                "PedSignal_%d" % i,
                unreal.Vector(curb_x + 30.0, curb_y - 20.0, 160.0),
                unreal.Vector(0.35, 0.1, 0.7),
                ped_mat,
                yaw,
            )
            placed += 1

    if find_by_label(FLAG) is None:
        spawn(unreal.Actor, unreal.Vector(0, 0, -650), label=FLAG)

    if not level_editor.save_current_level():
        raise RuntimeError("save failed")
    unreal.EditorAssetLibrary.save_directory(DEST)
    unreal.log("STREET ASSETS OK — placed=%d mats=%d" % (placed, len(mats)))


main()
