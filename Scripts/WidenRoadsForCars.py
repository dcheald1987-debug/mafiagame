"""Widen avenues/streets so period cars fit (two lanes + curb park).

Current road ≈ 320uu; car bodies ≈ 260–320uu long / 115–130uu wide.
Target road width 480uu (scale 4.8 on 100uu cube).
"""
import unreal

MAP_PATH = "/Game/Maps/Empire/Levee_Greybox"
FLAG = "Dress_WideRoads_v1"

# World units
ROAD_W = 480.0
WALK_W = 140.0  # sidewalk strip width
WALK_GAP = 70.0  # curb gap from road edge to walk center
AVENUES = [2400.0, 1200.0, 0.0, -1200.0, -2400.0]
STREETS = [2400.0, 1200.0, 0.0, -1200.0, -2400.0]


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


def set_xform(label, loc, scale):
    actor = find_by_label(label)
    if actor is None:
        return False
    actor.set_actor_location(loc, False, True)
    actor.set_actor_scale3d(scale)
    actor.set_actor_hidden_in_game(False)
    return True


def main():
    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level_editor.load_level(MAP_PATH):
        raise RuntimeError("load failed")

    span_y = abs(STREETS[0] - STREETS[-1]) + ROAD_W * 2.0
    span_x = abs(AVENUES[0] - AVENUES[-1]) + ROAD_W * 2.0
    road_s = ROAD_W / 100.0
    walk_s = WALK_W / 100.0
    half = ROAD_W * 0.5
    walk_off = half + WALK_GAP

    n = 0
    for i, x in enumerate(AVENUES):
        if set_xform(
            "Avenue_%d" % i,
            unreal.Vector(x, 0.0, -28.0),
            unreal.Vector(road_s, span_y / 100.0, 0.85),
        ):
            n += 1
        if set_xform(
            "WalkE_%d" % i,
            unreal.Vector(x + walk_off, 0.0, -24.0),
            unreal.Vector(walk_s, span_y / 100.0, 0.40),
        ):
            n += 1
        if set_xform(
            "WalkW_%d" % i,
            unreal.Vector(x - walk_off, 0.0, -24.0),
            unreal.Vector(walk_s, span_y / 100.0, 0.40),
        ):
            n += 1

    for j, y in enumerate(STREETS):
        if set_xform(
            "Street_%d" % j,
            unreal.Vector(0.0, y, -28.0),
            unreal.Vector(span_x / 100.0, road_s, 0.85),
        ):
            n += 1
        if set_xform(
            "WalkN_%d" % j,
            unreal.Vector(0.0, y + walk_off, -24.0),
            unreal.Vector(span_x / 100.0, walk_s, 0.40),
        ):
            n += 1
        if set_xform(
            "WalkS_%d" % j,
            unreal.Vector(0.0, y - walk_off, -24.0),
            unreal.Vector(span_x / 100.0, walk_s, 0.40),
        ):
            n += 1

    # Nudge curbs / crosswalks if present
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        lab = actor.get_actor_label()
        if lab.startswith("Curb_") or lab.startswith("Crosswalk_"):
            # Leave XY; slightly raise so they sit on thicker road
            loc = actor.get_actor_location()
            actor.set_actor_location(unreal.Vector(loc.x, loc.y, -16.0), False, True)

    if find_by_label(FLAG) is None:
        spawn(unreal.Actor, unreal.Vector(0, 0, -790), label=FLAG)

    if not level_editor.save_current_level():
        raise RuntimeError("save failed")
    unreal.log(
        "WIDE ROADS OK — pieces=%d road_w=%.0fuu (was ~320) walk_w=%.0f"
        % (n, ROAD_W, WALK_W)
    )


main()
