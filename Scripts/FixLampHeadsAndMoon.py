"""Re-seat SpotLights on lamp heads + ensure Moon_Levee exists for night roofs."""
import unreal

MAP_PATH = "/Game/Maps/Empire/Levee_Greybox"
MESH_PATH = "/Game/Art/Empire/FabStreetLights/SM_StreetLight"
INTENSITY_NIGHT = 32.0
ATTEN = 340.0


def find_by_label(label):
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if actor.get_actor_label() == label:
            return actor
    return None


def spawn(cls, location, label=None, rotation=None):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    rot = rotation or unreal.Rotator(0.0, 0.0, 0.0)
    actor = sub.spawn_actor_from_class(cls, location, rot)
    if label:
        actor.set_actor_label(label)
    return actor


def head_offset(mesh, scale_s):
    """Local offset to lamp head — top of bounds, along arm (+Y for this Fab mesh)."""
    b = mesh.get_bounds()
    o, e = b.origin, b.box_extent
    return unreal.Vector(
        o.x * scale_s,
        (o.y + e.y * 0.75) * scale_s,
        (o.z + e.z * 0.92) * scale_s,
    )


def main():
    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level_editor.load_level(MAP_PATH):
        raise RuntimeError("load failed")

    mesh = unreal.load_asset(MESH_PATH)
    if mesh is None:
        raise RuntimeError("missing SM_StreetLight")

    # Discover scale from first FabLamp
    scale_s = 1.0
    lamps = []
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        lab = actor.get_actor_label()
        if lab.startswith("FabLamp_"):
            lamps.append(actor)
            s = actor.get_actor_scale3d()
            scale_s = max(s.z, 0.01)

    off = head_offset(mesh, scale_s)
    unreal.log("Lamp head local offset=(%.1f, %.1f, %.1f) scale=%.3f lamps=%d" % (off.x, off.y, off.z, scale_s, len(lamps)))

    fixed = 0
    for lamp in lamps:
        idx = lamp.get_actor_label().replace("FabLamp_", "")
        light_label = "FabLight_%s" % idx
        base = lamp.get_actor_location()
        head = unreal.Vector(base.x + off.x, base.y + off.y, base.z + off.z)
        rot = unreal.Rotator(-90.0, 0.0, 0.0)

        light = find_by_label(light_label)
        if light is None:
            light = spawn(unreal.SpotLight, head, light_label, rot)
        else:
            light.set_actor_location(head, False, True)
            light.set_actor_rotation(rot, False)

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

        comp = light.get_component_by_class(unreal.SpotLightComponent)
        if comp:
            comp.set_intensity(INTENSITY_NIGHT)
            comp.set_light_color(unreal.LinearColor(1.0, 0.84, 0.62, 1.0))
            comp.set_attenuation_radius(ATTEN)
            try:
                comp.set_editor_property("inner_cone_angle", 32.0)
                comp.set_editor_property("outer_cone_angle", 68.0)
                comp.set_editor_property("use_temperature", True)
                comp.set_editor_property("temperature", 2500.0)
                comp.set_editor_property("cast_shadows", False)
                comp.set_editor_property("specular_scale", 0.0)
                comp.set_editor_property("indirect_lighting_intensity", 0.0)
                comp.set_mobility(unreal.ComponentMobility.MOVABLE)
            except Exception:
                pass
        fixed += 1

    # Moon directional for night roof fill
    moon = find_by_label("Moon_Levee")
    if moon is None:
        moon = spawn(unreal.DirectionalLight, unreal.Vector(0.0, 0.0, 500.0), "Moon_Levee", unreal.Rotator(-35.0, 220.0, 0.0))
    light = moon.get_component_by_class(unreal.DirectionalLightComponent)
    if light:
        light.set_intensity(2.2)
        light.set_light_color(unreal.LinearColor(0.62, 0.7, 0.92, 1.0))
        try:
            light.set_editor_property("cast_shadows", True)
        except Exception:
            pass

    sun = find_by_label("Sun_Levee")
    if sun:
        sl = sun.get_component_by_class(unreal.DirectionalLightComponent)
        if sl:
            sl.set_intensity(5.5)
            sl.set_light_color(unreal.LinearColor(1.0, 0.96, 0.88, 1.0))

    sky = find_by_label("Sky_Levee")
    if sky:
        sk = sky.get_component_by_class(unreal.SkyLightComponent)
        if sk:
            sk.set_intensity(1.4)
            sk.set_light_color(unreal.LinearColor(0.55, 0.62, 0.8, 1.0))

    pp = find_by_label("PP_LeveeReadable")
    if pp:
        try:
            settings = pp.get_editor_property("settings")
            settings.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
            settings.set_editor_property("auto_exposure_bias", 0.7)
            settings.set_editor_property("override_auto_exposure_method", True)
            settings.set_editor_property("override_auto_exposure_bias", True)
            settings.set_editor_property("bloom_intensity", 0.02)
            settings.set_editor_property("override_bloom_intensity", True)
            pp.set_editor_property("settings", settings)
        except Exception:
            pass

    if not level_editor.save_current_level():
        raise RuntimeError("save failed")
    unreal.log("LAMP HEADS + MOON OK — fixed=%d" % fixed)


main()
