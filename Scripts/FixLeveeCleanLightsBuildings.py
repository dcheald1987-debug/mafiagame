"""Fix Levee: glitchy overlaps + sparse street lights that glow FROM the lamp head.

- Strip overlapping DenseChicago LM_* (z-fights Row_* + façades)
- Keep only lakefront / river landmarks outside Row parcels
- Few curb poles; SpotLight attached at the mesh lamp-head, aimed down at the road
"""
import unreal

MAP_PATH = "/Game/Maps/Empire/Levee_Greybox"
FLAG = "Dress_LeveeClean_v2"
MESH_PATH = "/Game/Art/Empire/FabStreetLights/SM_StreetLight"

KEEP_LM = (
    "LM_FieldMuseum",
    "LM_SoldierField",
    "LM_Shedd",
    "LM_Donnelley",
    "LM_AmBookCo",
    "LM_YardShed",
    "LM_RiverWharf",
)

# Sparse major crossings only
LAMP_SPOTS = [
    (0.0, 0.0),          # State & 18th
    (0.0, -800.0),       # State & Cermak
    (1600.0, 0.0),       # Michigan & 18th
    (1600.0, -800.0),    # Michigan & Cermak
    (-1600.0, -800.0),   # Clark & Cermak
    (800.0, 0.0),        # Wabash & 18th
    (-800.0, -800.0),    # Dearborn & Cermak
    (0.0, 800.0),        # State & 16th
]

ROAD_W = 220.0
TARGET_POLE_H = 260.0
# Soft pool under the head — not block-wide wash
INTENSITY = 28.0
ATTEN = 320.0
INNER_CONE = 35.0
OUTER_CONE = 70.0


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


def destroy_matching(predicate):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    n = 0
    for actor in list(sub.get_all_level_actors()):
        if predicate(actor.get_actor_label()):
            sub.destroy_actor(actor)
            n += 1
    return n


def keep_lm_label(lab):
    if not lab.startswith("LM_"):
        return False
    return any(lab.startswith(p) for p in KEEP_LM)


def mute_lamp_emissive():
    for path in (
        "/Game/Art/Empire/FabStreetLights/M_Street_Light_Emission",
        "/Game/Art/Empire/FabStreetLights/M_Street_Light_Pole",
    ):
        mat = unreal.load_asset(path)
        if mat is None:
            continue
        try:
            for name in ("EmissiveStrength", "Emissive Intensity", "EmissiveMultiplier"):
                try:
                    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
                        mat, name, 0.05
                    )
                except Exception:
                    pass
        except Exception as exc:
            unreal.log_warning("mute emissive %s: %s" % (path, exc))


def lamp_head_world(lamp_actor, mesh, scale_s):
    """World position of the glowing head (top of pole / end of arm)."""
    bounds = mesh.get_bounds()
    origin = bounds.origin
    extent = bounds.box_extent
    # Local head: near top of mesh; slight +Y for curved arm luminaires
    local = unreal.Vector(
        origin.x * scale_s,
        (origin.y + extent.y * 0.55) * scale_s,
        (origin.z + extent.z * 0.88) * scale_s,
    )
    base = lamp_actor.get_actor_location()
    return unreal.Vector(base.x + local.x, base.y + local.y, base.z + local.z)


def ensure_lamp_mesh(label, mesh, location, scale):
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
    """SpotLight at the lamp head, aimed straight down onto the curb."""
    head = lamp_head_world(lamp_actor, mesh, scale_s)
    # Pitch -90 = point down in Unreal
    rot = unreal.Rotator(-90.0, 0.0, 0.0)
    actor = find_by_label(label)
    if actor is None:
        actor = spawn(unreal.SpotLight, head, label=label, rotation=rot)
    else:
        actor.set_actor_location(head, False, True)
        actor.set_actor_rotation(rot, False)

    # Keep light glued to this pole
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
        try:
            actor.attach_to_actor(
                lamp_actor,
                "",
                unreal.AttachmentRule.KEEP_WORLD,
                unreal.AttachmentRule.KEEP_WORLD,
                unreal.AttachmentRule.KEEP_WORLD,
                False,
            )
        except Exception as exc:
            unreal.log_warning("attach light: %s" % exc)

    light = actor.get_component_by_class(unreal.SpotLightComponent)
    if light is None:
        light = actor.get_component_by_class(unreal.LocalLightComponent)
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
            light.set_editor_property("source_radius", 12.0)
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


def tame_world():
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
            light.set_light_color(unreal.LinearColor(0.58, 0.62, 0.75, 1.0))
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
        except Exception as exc:
            unreal.log_warning("PP: %s" % exc)


def main():
    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level_editor.load_level(MAP_PATH):
        raise RuntimeError("load failed")

    removed_lm = destroy_matching(
        lambda lab: lab.startswith("LM_") and not keep_lm_label(lab)
    )
    removed_lbl = destroy_matching(
        lambda lab: lab.startswith("Label_MotorRow")
        or lab.startswith("Label_Levee")
        or lab.startswith("Label_Lakeside")
        or lab.startswith("Label_Prairie")
        or lab.startswith("Label_Printers")
        or lab.startswith("Label_WhiteCastle")
        or lab.startswith("Dress_ChicagoDense")
    )
    removed_old = destroy_matching(
        lambda lab: lab.startswith("FabLamp_")
        or lab.startswith("FabLight_")
        or lab.startswith("StreetLamp_")
        or lab.startswith("Dress_FabStreetLights")
        or lab.startswith("Dress_LeveeClean")
    )

    mute_lamp_emissive()
    tame_world()

    mesh = unreal.load_asset(MESH_PATH)
    if mesh is None:
        raise RuntimeError("Missing SM_StreetLight")

    bounds = mesh.get_bounds().box_extent
    height = max(1.0, abs(bounds.z) * 2.0)
    scale_s = TARGET_POLE_H / height
    scale = unreal.Vector(scale_s, scale_s, scale_s)
    unreal.log(
        "Lamp head setup mesh=%s rawH=%.1f scale=%.3f"
        % (mesh.get_name(), height, scale_s)
    )

    placed = 0
    for i, (x, y) in enumerate(LAMP_SPOTS):
        base = unreal.Vector(x + ROAD_W * 0.5, y + ROAD_W * 0.5, 0.0)
        lamp = ensure_lamp_mesh("FabLamp_%d" % i, mesh, base, scale)
        ensure_head_spotlight("FabLight_%d" % i, lamp, mesh, scale_s)
        placed += 1

    spawn(unreal.Actor, unreal.Vector(0.0, 0.0, -990.0), label=FLAG)

    if not level_editor.save_current_level():
        raise RuntimeError("save failed")
    unreal.log(
        "LEVEE CLEAN OK — removed_lm=%d labels=%d old=%d lamps=%d (head-mounted spots)"
        % (removed_lm, removed_lbl, removed_old, placed)
    )


main()
