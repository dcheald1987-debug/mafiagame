"""Create period skins, apply to Levee rows, ensure single sun. Headless art pass."""
import unreal

# --- Create skins (inline so one Cmd invocation) ---
import importlib.util
import os

ROOT = os.path.dirname(os.path.abspath(__file__))


def _run(path):
    spec = importlib.util.spec_from_file_location("levee_step", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)


unreal.log("ART PASS — CreateBuildingSkins")
_run(os.path.join(ROOT, "CreateBuildingSkins.py"))

unreal.log("ART PASS — ApplyBuildingSkins")
_run(os.path.join(ROOT, "ApplyBuildingSkins.py"))

# Dual-sun fix on current level (Apply already loaded Levee)
MAP_PATH = "/Game/Maps/Empire/Levee_Greybox"


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


def fix_single_sun():
    actor = find_by_label("Sun_Levee")
    if actor is None:
        actor = spawn(
            unreal.DirectionalLight,
            unreal.Vector(0.0, 0.0, 800.0),
            None,
            "Sun_Levee",
            unreal.Rotator(-42.0, -35.0, 0.0),
        )
    light = actor.get_component_by_class(unreal.DirectionalLightComponent)
    if light:
        light.set_intensity(6.0)
        light.set_light_color(unreal.LinearColor(1.0, 0.95, 0.85, 1.0))
        try:
            light.set_editor_property("atmosphere_sun_light", True)
            light.set_editor_property("cast_shadows", True)
            light.set_editor_property("forward_shading_priority", 1)
        except Exception as exc:
            unreal.log_warning("Sun props partial: %s" % exc)

    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    removed = 0
    for other in list(sub.get_all_level_actors()):
        if other is None or other == actor:
            continue
        if isinstance(other, unreal.DirectionalLight) and other.get_actor_label() != "Sun_Levee":
            unreal.log("Removing competing sun: " + other.get_actor_label())
            sub.destroy_actor(other)
            removed += 1
    return removed


unreal.log("ART PASS — fix single sun")
n = fix_single_sun()
level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not level_editor.save_current_level():
    raise RuntimeError("save failed after sun fix")
unreal.log("ART PASS OK — skins applied, removed %d extra suns" % n)
