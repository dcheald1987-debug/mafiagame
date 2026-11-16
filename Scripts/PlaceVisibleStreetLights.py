"""Place visible Fab street-light poles + head PointLights on the wide Chicago grid."""
import unreal

MAP_PATH = "/Game/Maps/Empire/Levee_Greybox"
MESH_PATH = "/Game/Art/Empire/FabStreetLights/SM_StreetLight"
FLAG = "Dress_FabStreetLights_v6"

AVENUES = [2400.0, 1200.0, 0.0, -1200.0, -2400.0]
STREETS = [2400.0, 1200.0, 0.0, -1200.0, -2400.0]
ROAD_W = 300.0
TARGET_H = 380.0
INTENSITY = 700.0
ATTEN = 520.0


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


def head_world(base, mesh, scale_s):
    b = mesh.get_bounds()
    o, e = b.origin, b.box_extent
    return unreal.Vector(
        base.x + o.x * scale_s,
        base.y + (o.y + e.y * 0.7) * scale_s,
        base.z + (o.z + e.z * 0.9) * scale_s,
    )


def main():
    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level_editor.load_level(MAP_PATH):
        raise RuntimeError("load failed")

    mesh = unreal.load_asset(MESH_PATH)
    if mesh is None:
        raise RuntimeError("SM_StreetLight missing — import Fab pack first")

    destroy_prefix("FabLamp_")
    destroy_prefix("FabLight_")
    destroy_prefix("StreetLamp_")
    destroy_prefix("Dress_FabStreetLights")
    destroy_prefix("Dress_LeveeClean")

    height = max(1.0, abs(mesh.get_bounds().box_extent.z) * 2.0)
    scale_s = TARGET_H / height
    scale = unreal.Vector(scale_s, scale_s, scale_s)
    unreal.log("Street light scale=%.3f rawH=%.1f" % (scale_s, height))

    # One lamp NE curb per intersection + mid-block on State
    spots = []
    for x in AVENUES:
        for y in STREETS:
            spots.append((x + ROAD_W * 0.48, y + ROAD_W * 0.48))
    for y in (-600.0, 600.0):
        spots.append((ROAD_W * 0.48, y))

    placed = 0
    for i, (x, y) in enumerate(spots):
        base = unreal.Vector(x, y, 0.0)
        lamp = find_by_label("FabLamp_%d" % i)
        if lamp is None:
            lamp = spawn(unreal.StaticMeshActor, base, scale, "FabLamp_%d" % i)
        else:
            lamp.set_actor_location(base, False, True)
            lamp.set_actor_scale3d(scale)
        lamp.static_mesh_component.set_static_mesh(mesh)
        lamp.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        lamp.set_actor_hidden_in_game(False)

        head = head_world(base, mesh, scale_s)
        light = find_by_label("FabLight_%d" % i)
        if light is None:
            light = spawn(unreal.PointLight, head, label="FabLight_%d" % i)
        else:
            light.set_actor_location(head, False, True)
        try:
            light.attach_to_actor(
                lamp, "None",
                unreal.AttachmentRule.KEEP_WORLD,
                unreal.AttachmentRule.KEEP_WORLD,
                unreal.AttachmentRule.KEEP_WORLD,
                False,
            )
        except Exception:
            pass
        comp = light.get_component_by_class(unreal.PointLightComponent)
        if comp:
            comp.set_intensity(INTENSITY)
            comp.set_light_color(unreal.LinearColor(1.0, 0.82, 0.55, 1.0))
            comp.set_attenuation_radius(ATTEN)
            try:
                comp.set_editor_property("use_temperature", True)
                comp.set_editor_property("temperature", 2550.0)
                comp.set_editor_property("cast_shadows", False)
                comp.set_editor_property("source_radius", 20.0)
                comp.set_editor_property("specular_scale", 0.05)
                comp.set_editor_property("indirect_lighting_intensity", 0.0)
                comp.set_mobility(unreal.ComponentMobility.MOVABLE)
                try:
                    comp.set_editor_property("intensity_units", unreal.LightUnits.CANDELAS)
                except Exception:
                    pass
            except Exception:
                pass
        placed += 1

    # Readable night base until DayNight ticks
    moon = find_by_label("Moon_Levee")
    if moon is None:
        moon = spawn(
            unreal.DirectionalLight,
            unreal.Vector(0.0, 0.0, 600.0),
            label="Moon_Levee",
            rotation=unreal.Rotator(-38.0, 210.0, 0.0),
        )
    ml = moon.get_component_by_class(unreal.DirectionalLightComponent)
    if ml:
        ml.set_intensity(5.5)
        ml.set_light_color(unreal.LinearColor(0.7, 0.78, 0.95, 1.0))

    sky = find_by_label("Sky_Levee")
    if sky:
        sk = sky.get_component_by_class(unreal.SkyLightComponent)
        if sk:
            sk.set_intensity(2.2)

    pp = find_by_label("PP_LeveeReadable")
    if pp:
        try:
            settings = pp.get_editor_property("settings")
            settings.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
            settings.set_editor_property("auto_exposure_bias", 1.35)
            settings.set_editor_property("override_auto_exposure_method", True)
            settings.set_editor_property("override_auto_exposure_bias", True)
            settings.set_editor_property("bloom_intensity", 0.05)
            settings.set_editor_property("override_bloom_intensity", True)
            pp.set_editor_property("settings", settings)
        except Exception:
            pass

    spawn(unreal.Actor, unreal.Vector(0.0, 0.0, -980.0), label=FLAG)
    if not level_editor.save_current_level():
        raise RuntimeError("save failed")
    unreal.log("VISIBLE STREET LIGHTS OK — lamps=%d" % placed)


main()
