"""Sparse Fab street lights — SpotLight glued to each lamp head, aimed at the road."""
import unreal
import os

MAP_PATH = "/Game/Maps/Empire/Levee_Greybox"
LAMP_FBX = unreal.Paths.project_dir() + "Art/Fab/StreetLights/source/StreetLight.fbx"
TEX_DIR = unreal.Paths.project_dir() + "Art/Fab/StreetLights/textures"
DEST = "/Game/Art/Empire/FabStreetLights"
DEST_TEX = "/Game/Art/Empire/FabStreetLights/Textures"
FLAG = "Dress_FabStreetLights_v5"

LAMP_SPOTS = [
    (0.0, 0.0),
    (0.0, -800.0),
    (1600.0, 0.0),
    (1600.0, -800.0),
    (-1600.0, -800.0),
    (800.0, 0.0),
    (-800.0, -800.0),
    (0.0, 800.0),
]
ROAD_W = 220.0
TARGET_POLE_H = 260.0
INTENSITY = 28.0
ATTEN = 320.0
INNER_CONE = 35.0
OUTER_CONE = 70.0


def ensure_dir(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def find_by_label(label):
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if actor.get_actor_label() == label:
            return actor
    return None


def spawn(cls, location, scale=None, label=None, rotation=None):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    rot = rotation or unreal.Rotator(0.0, 0.0, 0.0)
    actor = sub.spawn_actor_from_class(cls, location, rot)
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


def import_textures():
    ensure_dir(DEST_TEX)
    tex_root = os.path.normpath(TEX_DIR)
    if not os.path.isdir(tex_root):
        return
    tasks = []
    for name in os.listdir(tex_root):
        if not name.lower().endswith((".png", ".jpg", ".jpeg", ".tga")):
            continue
        task = unreal.AssetImportTask()
        task.set_editor_property("filename", os.path.join(tex_root, name))
        task.set_editor_property("destination_path", DEST_TEX)
        task.set_editor_property("destination_name", os.path.splitext(name)[0])
        task.set_editor_property("replace_existing", True)
        task.set_editor_property("automated", True)
        task.set_editor_property("save", True)
        tasks.append(task)
    if tasks:
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)


def import_lamp_fbx():
    ensure_dir(DEST)
    import_textures()
    disk = os.path.normpath(LAMP_FBX)
    if not os.path.isfile(disk):
        src = os.path.normpath(unreal.Paths.project_dir() + "Art/Fab/StreetLights/source")
        if os.path.isdir(src):
            for name in os.listdir(src):
                if name.lower().endswith(".fbx"):
                    disk = os.path.join(src, name)
                    break
    if not os.path.isfile(disk):
        raise RuntimeError("Missing street light FBX under Art/Fab/StreetLights/source")

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", disk)
    task.set_editor_property("destination_path", DEST)
    task.set_editor_property("destination_name", "SM_StreetLight")
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)
    options = unreal.FbxImportUI()
    options.set_editor_property("automated_import_should_detect_type", False)
    options.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_STATIC_MESH)
    options.set_editor_property("original_import_type", unreal.FBXImportType.FBXIT_STATIC_MESH)
    options.set_editor_property("static_mesh_import_data", unreal.FbxStaticMeshImportData())
    sm = options.get_editor_property("static_mesh_import_data")
    try:
        sm.set_editor_property("combine_meshes", True)
        sm.set_editor_property("auto_generate_collision", False)
        sm.set_editor_property("import_uniform_scale", 1.0)
        sm.set_editor_property("convert_scene", True)
    except Exception:
        pass
    task.set_editor_property("options", options)
    task.set_editor_property("factory", unreal.FbxFactory())
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

    meshes = []
    for path in unreal.EditorAssetLibrary.list_assets(DEST, True, False):
        asset = unreal.load_asset(path)
        if isinstance(asset, unreal.StaticMesh):
            meshes.append(asset)
    if not meshes:
        raise RuntimeError("Street light import produced no meshes")
    return max(meshes, key=lambda m: m.get_bounds().box_extent.z)


def lamp_head_world(lamp_actor, mesh, scale_s):
    bounds = mesh.get_bounds()
    origin = bounds.origin
    extent = bounds.box_extent
    local = unreal.Vector(
        origin.x * scale_s,
        (origin.y + extent.y * 0.55) * scale_s,
        (origin.z + extent.z * 0.88) * scale_s,
    )
    base = lamp_actor.get_actor_location()
    return unreal.Vector(base.x + local.x, base.y + local.y, base.z + local.z)


def ensure_mesh(label, mesh, location, scale):
    actor = find_by_label(label)
    if actor is None:
        actor = spawn(unreal.StaticMeshActor, location, scale, label)
    else:
        actor.set_actor_location(location, False, True)
        actor.set_actor_scale3d(scale)
    actor.static_mesh_component.set_static_mesh(mesh)
    actor.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    actor.set_actor_hidden_in_game(False)
    return actor


def ensure_head_spotlight(label, lamp_actor, mesh, scale_s):
    head = lamp_head_world(lamp_actor, mesh, scale_s)
    rot = unreal.Rotator(-90.0, 0.0, 0.0)
    actor = find_by_label(label)
    if actor is None:
        actor = spawn(unreal.SpotLight, head, label=label, rotation=rot)
    else:
        actor.set_actor_location(head, False, True)
        actor.set_actor_rotation(rot, False)
    try:
        actor.attach_to_actor(
            lamp_actor,
            "None",
            unreal.AttachmentRule.KEEP_WORLD,
            unreal.AttachmentRule.KEEP_WORLD,
            unreal.AttachmentRule.KEEP_WORLD,
            False,
        )
    except Exception:
        pass
    light = actor.get_component_by_class(unreal.SpotLightComponent)
    if light:
        light.set_intensity(INTENSITY)
        light.set_light_color(unreal.LinearColor(1.0, 0.84, 0.62, 1.0))
        light.set_attenuation_radius(ATTEN)
        try:
            light.set_editor_property("inner_cone_angle", INNER_CONE)
            light.set_editor_property("outer_cone_angle", OUTER_CONE)
            light.set_editor_property("use_temperature", True)
            light.set_editor_property("temperature", 2500.0)
            light.set_editor_property("cast_shadows", False)
            light.set_editor_property("specular_scale", 0.0)
            light.set_editor_property("indirect_lighting_intensity", 0.0)
            light.set_editor_property("volumetric_scattering_intensity", 0.0)
            light.set_mobility(unreal.ComponentMobility.MOVABLE)
            try:
                light.set_editor_property("intensity_units", unreal.LightUnits.CANDELAS)
            except Exception:
                pass
        except Exception:
            pass
    return actor


def brighten_world():
    sun = find_by_label("Sun_Levee")
    if sun:
        light = sun.get_component_by_class(unreal.DirectionalLightComponent)
        if light:
            light.set_intensity(3.2)
            light.set_light_color(unreal.LinearColor(0.88, 0.9, 0.96, 1.0))
    sky = find_by_label("Sky_Levee")
    if sky:
        light = sky.get_component_by_class(unreal.SkyLightComponent)
        if light:
            light.set_intensity(0.9)
    pp = find_by_label("PP_LeveeReadable")
    if pp:
        try:
            settings = pp.get_editor_property("settings")
            settings.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
            settings.set_editor_property("auto_exposure_bias", 0.4)
            settings.set_editor_property("override_auto_exposure_method", True)
            settings.set_editor_property("override_auto_exposure_bias", True)
            settings.set_editor_property("bloom_intensity", 0.0)
            settings.set_editor_property("override_bloom_intensity", True)
            pp.set_editor_property("settings", settings)
        except Exception:
            pass


def main():
    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level_editor.load_level(MAP_PATH):
        raise RuntimeError("load failed")

    mesh = import_lamp_fbx()
    height = max(1.0, abs(mesh.get_bounds().box_extent.z) * 2.0)
    scale_s = TARGET_POLE_H / height
    scale = unreal.Vector(scale_s, scale_s, scale_s)

    destroy_prefix("FabLamp_")
    destroy_prefix("FabLight_")
    destroy_prefix("StreetLamp_")
    destroy_prefix("Dress_FabStreetLights_")
    brighten_world()

    placed = 0
    for i, (x, y) in enumerate(LAMP_SPOTS):
        base = unreal.Vector(x + ROAD_W * 0.5, y + ROAD_W * 0.5, 0.0)
        lamp = ensure_mesh("FabLamp_%d" % i, mesh, base, scale)
        ensure_head_spotlight("FabLight_%d" % i, lamp, mesh, scale_s)
        placed += 1

    spawn(unreal.Actor, unreal.Vector(0.0, 0.0, -980.0), label=FLAG)
    if not level_editor.save_current_level():
        raise RuntimeError("save failed")
    unreal.EditorAssetLibrary.save_directory(DEST)
    unreal.log("FAB STREET LIGHTS OK — lamps=%d head-mounted" % placed)


main()
