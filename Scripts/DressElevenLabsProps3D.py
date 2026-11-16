"""Import latest ElevenLabs car/char/prop studio plates and dress Levee with
FULL 3D stand-ins (Engine Cube/Cylinder/Sphere — never Plane stickers).

Cars keep Chaos SportsCar skeletal mesh + period paint (C++).
Props: dock crates, call boxes, street lamps as real 3D volumes with lit mats
sampled from the new textures.
"""
import unreal
import os

MAP_PATH = "/Game/Maps/Empire/Levee_Greybox"
SRC = unreal.Paths.project_content_dir() + "Art/Empire/Sprites/Source/Cropped"
DEST = "/Game/Art/Empire/Sprites"
TEX_DIR = DEST + "/Textures"
MAT_DIR = DEST + "/Materials"
FLAG = "Dress_ElevenLabsProps3D_v1"

IMPORTS = [
    ("T_Car_Packard", "Cars/S_Packard.jpg"),
    ("T_Car_Harlan", "Cars/S_HarlanSedan.jpg"),
    ("T_Car_ModelA", "Cars/S_ModelA.jpg"),
    ("T_Car_Taxi", "Cars/S_Taxi.jpg"),
    ("T_Car_Police", "Cars/S_PoliceCar.jpg"),
    ("T_Car_Delivery", "Cars/S_DeliveryTruck.jpg"),
    ("T_Char_Quinn", "Characters/S_Quinn.jpg"),
    ("T_Char_CivMan", "Characters/S_CivMan.jpg"),
    ("T_Char_CivWoman", "Characters/S_CivWoman.jpg"),
    ("T_Char_DockWorker", "Characters/S_DockWorker.jpg"),
    ("T_Prop_DockCrates", "Props/S_DockCrates.jpg"),
    ("T_Prop_CallBox", "Props/S_CallBox.jpg"),
    ("T_Prop_StreetLamp", "Props/S_StreetLamp.jpg"),
]

# (label, mesh_kind, location, scale, mat_tex, yaw)
# mesh_kind: cube | cylinder | sphere
PROP_SPOTS = [
    # Dock crates — 3D cubes along waterfront / alley
    ("Prop_Crates_DockA", "cube", unreal.Vector(2000.0, -2000.0, 40.0), unreal.Vector(1.6, 1.2, 1.1), "T_Prop_DockCrates", 15.0),
    ("Prop_Crates_DockB", "cube", unreal.Vector(2100.0, -1880.0, 40.0), unreal.Vector(1.4, 1.0, 0.9), "T_Prop_DockCrates", -20.0),
    ("Prop_Crates_Freight", "cube", unreal.Vector(-400.0, -2000.0, 40.0), unreal.Vector(1.5, 1.1, 1.0), "T_Prop_DockCrates", 40.0),
    ("Prop_Crates_Alley", "cube", unreal.Vector(-2000.0, 400.0, 40.0), unreal.Vector(1.2, 1.0, 0.85), "T_Prop_DockCrates", 5.0),
    # Police call boxes — tall cylinders on corners
    ("Prop_CallBox_State", "cylinder", unreal.Vector(280.0, 280.0, 55.0), unreal.Vector(0.35, 0.35, 1.1), "T_Prop_CallBox", 0.0),
    ("Prop_CallBox_Clark", "cylinder", unreal.Vector(-2120.0, -920.0, 55.0), unreal.Vector(0.35, 0.35, 1.1), "T_Prop_CallBox", 0.0),
    ("Prop_CallBox_Michigan", "cylinder", unreal.Vector(2120.0, 280.0, 55.0), unreal.Vector(0.35, 0.35, 1.1), "T_Prop_CallBox", 0.0),
    # Street lamps — pole (cylinder) + globe (sphere)
    ("Prop_Lamp_Pole_A", "cylinder", unreal.Vector(240.0, -240.0, 140.0), unreal.Vector(0.12, 0.12, 2.8), "T_Prop_StreetLamp", 0.0),
    ("Prop_Lamp_Head_A", "sphere", unreal.Vector(240.0, -240.0, 290.0), unreal.Vector(0.35, 0.35, 0.35), "T_Prop_StreetLamp", 0.0),
    ("Prop_Lamp_Pole_B", "cylinder", unreal.Vector(-240.0, 240.0, 140.0), unreal.Vector(0.12, 0.12, 2.8), "T_Prop_StreetLamp", 0.0),
    ("Prop_Lamp_Head_B", "sphere", unreal.Vector(-240.0, 240.0, 290.0), unreal.Vector(0.35, 0.35, 0.35), "T_Prop_StreetLamp", 0.0),
    ("Prop_Lamp_Pole_C", "cylinder", unreal.Vector(1440.0, -1440.0, 140.0), unreal.Vector(0.12, 0.12, 2.8), "T_Prop_StreetLamp", 0.0),
    ("Prop_Lamp_Head_C", "sphere", unreal.Vector(1440.0, -1440.0, 290.0), unreal.Vector(0.35, 0.35, 0.35), "T_Prop_StreetLamp", 0.0),
    ("Prop_Lamp_Pole_D", "cylinder", unreal.Vector(-1440.0, 1440.0, 140.0), unreal.Vector(0.12, 0.12, 2.8), "T_Prop_StreetLamp", 0.0),
    ("Prop_Lamp_Head_D", "sphere", unreal.Vector(-1440.0, 1440.0, 290.0), unreal.Vector(0.35, 0.35, 0.35), "T_Prop_StreetLamp", 0.0),
    ("Prop_Lamp_Pole_E", "cylinder", unreal.Vector(2160.0, 0.0, 140.0), unreal.Vector(0.12, 0.12, 2.8), "T_Prop_StreetLamp", 0.0),
    ("Prop_Lamp_Head_E", "sphere", unreal.Vector(2160.0, 0.0, 290.0), unreal.Vector(0.35, 0.35, 0.35), "T_Prop_StreetLamp", 0.0),
    ("Prop_Lamp_Pole_F", "cylinder", unreal.Vector(-2160.0, 0.0, 140.0), unreal.Vector(0.12, 0.12, 2.8), "T_Prop_StreetLamp", 0.0),
    ("Prop_Lamp_Head_F", "sphere", unreal.Vector(-2160.0, 0.0, 290.0), unreal.Vector(0.35, 0.35, 0.35), "T_Prop_StreetLamp", 0.0),
]


def ensure_dir(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def find_by_label(label):
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if actor.get_actor_label() == label:
            return actor
    return None


def destroy_prefix(prefix):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    n = 0
    for actor in list(sub.get_all_level_actors()):
        if actor.get_actor_label().startswith(prefix):
            sub.destroy_actor(actor)
            n += 1
    return n


def spawn(cls, location, scale=None, label=None, yaw=0.0):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actor = sub.spawn_actor_from_class(cls, location, unreal.Rotator(0.0, yaw, 0.0))
    if scale is not None:
        actor.set_actor_scale3d(scale)
    if label:
        actor.set_actor_label(label)
    return actor


def import_texture(name, rel):
    dest = "%s/%s" % (TEX_DIR, name)
    disk = os.path.normpath(os.path.join(SRC, rel.replace("/", os.sep)))
    if not os.path.isfile(disk):
        unreal.log_warning("Missing " + disk)
        return None
    if unreal.EditorAssetLibrary.does_asset_exist(dest):
        try:
            unreal.EditorAssetLibrary.delete_asset(dest)
        except Exception:
            pass
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", disk)
    task.set_editor_property("destination_path", TEX_DIR)
    task.set_editor_property("destination_name", name)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)
    task.set_editor_property("factory", unreal.TextureFactory())
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    tex = unreal.load_asset(dest)
    unreal.log("Imported " + name)
    return tex


def wipe_mat(name):
    path = "%s/%s" % (MAT_DIR, name)
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        try:
            unreal.EditorAssetLibrary.delete_asset(path)
        except Exception:
            pass
    root = unreal.Paths.project_content_dir()
    base = os.path.normpath(os.path.join(root, "Art/Empire/Sprites/Materials", name))
    for ext in (".uasset", ".uexp", ".ubulk"):
        p = base + ext
        if os.path.isfile(p):
            try:
                os.remove(p)
            except OSError:
                pass


def make_lit_mat(name, texture, emissive=0.08):
    wipe_mat(name)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MAT_DIR, unreal.Material, unreal.MaterialFactoryNew()
    )
    if not mat:
        return None
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    sample = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionTextureSample, -450, 0
    )
    if texture:
        sample.texture = texture
    unreal.MaterialEditingLibrary.connect_material_property(
        sample, "RGB", unreal.MaterialProperty.MP_BASE_COLOR
    )
    # Mild emissive so iso day/night still reads the prop
    mul = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionMultiply, -200, 200
    )
    const = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant, -400, 260
    )
    const.set_editor_property("r", emissive)
    unreal.MaterialEditingLibrary.connect_material_expressions(sample, "RGB", mul, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(const, "", mul, "B")
    unreal.MaterialEditingLibrary.connect_material_property(
        mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR
    )
    rough = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant, -200, 360
    )
    rough.set_editor_property("r", 0.72)
    unreal.MaterialEditingLibrary.connect_material_property(
        rough, "", unreal.MaterialProperty.MP_ROUGHNESS
    )
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset("%s/%s" % (MAT_DIR, name))
    return mat


def mesh_for(kind):
    paths = {
        "cube": "/Engine/BasicShapes/Cube.Cube",
        "cylinder": "/Engine/BasicShapes/Cylinder.Cylinder",
        "sphere": "/Engine/BasicShapes/Sphere.Sphere",
    }
    return unreal.load_asset(paths[kind])


def dress_props(mats):
    destroy_prefix("Prop_")
    cube_cls = unreal.StaticMeshActor
    n = 0
    for label, kind, loc, scale, tex_key, yaw in PROP_SPOTS:
        mesh = mesh_for(kind)
        if not mesh:
            continue
        actor = spawn(cube_cls, loc, scale=scale, label=label, yaw=yaw)
        smc = actor.static_mesh_component
        smc.set_static_mesh(mesh)
        smc.set_mobility(unreal.ComponentMobility.STATIC)
        smc.set_cast_shadow(True)
        mat = mats.get(tex_key)
        if mat:
            smc.set_material(0, mat)
        # Lamp heads get a small point light
        if label.startswith("Prop_Lamp_Head_"):
            light = spawn(
                unreal.PointLight,
                unreal.Vector(loc.x, loc.y, loc.z + 10.0),
                label=label.replace("Head", "Light"),
            )
            try:
                light.point_light_component.set_editor_property("intensity", 1200.0)
                light.point_light_component.set_editor_property("attenuation_radius", 900.0)
                light.point_light_component.set_editor_property(
                    "light_color", unreal.Color(255, 210, 150, 255)
                )
            except Exception:
                pass
        n += 1
    return n


def set_flag():
    old = find_by_label(FLAG)
    if old:
        unreal.get_editor_subsystem(unreal.EditorActorSubsystem).destroy_actor(old)
    spawn(unreal.Actor, unreal.Vector(0.0, 0.0, -500.0), label=FLAG)


def main():
    unreal.EditorLevelLibrary.load_level(MAP_PATH)
    ensure_dir(TEX_DIR)
    ensure_dir(MAT_DIR)

    mats = {}
    for name, rel in IMPORTS:
        tex = import_texture(name, rel)
        if tex:
            mat = make_lit_mat("M_" + name, tex, emissive=0.06 if name.startswith("T_Prop") else 0.04)
            mats[name] = mat

    # Prop mats keyed by texture name used in PROP_SPOTS
    prop_mats = {
        "T_Prop_DockCrates": mats.get("T_Prop_DockCrates"),
        "T_Prop_CallBox": mats.get("T_Prop_CallBox"),
        "T_Prop_StreetLamp": mats.get("T_Prop_StreetLamp"),
    }
    n = dress_props(prop_mats)
    set_flag()
    unreal.EditorLevelLibrary.save_current_level()
    unreal.log("DressElevenLabsProps3D: placed %d prop meshes, imported %d textures" % (n, len(mats)))


main()
