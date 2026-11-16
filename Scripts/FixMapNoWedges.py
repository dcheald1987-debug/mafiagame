"""Nuclear map fix: strip wedge-like leftovers, keep one bright cube city + roads."""
import unreal

MAP_PATH = "/Game/Maps/Empire/Levee_Greybox"
MAT = "/Game/Art/Empire/Materials"

BLOCKS = [
    ("Row_Garage", unreal.Vector(1800.0, -600.0, 0.0), (560.0, 500.0), 3),
    ("Row_Cafe", unreal.Vector(600.0, -600.0, 0.0), (560.0, 500.0), 3),
    ("Row_Dock", unreal.Vector(1800.0, -1800.0, 0.0), (560.0, 500.0), 2),
    ("Row_MidC", unreal.Vector(600.0, -1800.0, 0.0), (560.0, 500.0), 4),
    ("Row_MidA", unreal.Vector(-600.0, 600.0, 0.0), (560.0, 500.0), 4),
    ("Row_MidB", unreal.Vector(-600.0, -600.0, 0.0), (560.0, 500.0), 3),
    ("Row_Bar", unreal.Vector(-1800.0, -1800.0, 0.0), (560.0, 500.0), 3),
    ("Row_Board", unreal.Vector(-600.0, 1800.0, 0.0), (560.0, 500.0), 4),
    ("Row_MidD", unreal.Vector(-1800.0, 600.0, 0.0), (560.0, 500.0), 3),
    ("Row_MidE", unreal.Vector(-1800.0, -600.0, 0.0), (560.0, 500.0), 3),
    ("Row_MidF", unreal.Vector(600.0, 600.0, 0.0), (560.0, 500.0), 4),
    ("Row_MidG", unreal.Vector(1800.0, 600.0, 0.0), (560.0, 500.0), 3),
    ("Row_Rope", unreal.Vector(-1800.0, 1800.0, 0.0), (560.0, 460.0), 2),
    ("Row_Freight", unreal.Vector(-600.0, -1800.0, 0.0), (560.0, 500.0), 2),
]

AVENUES = [2400.0, 1200.0, 0.0, -1200.0, -2400.0]
STREETS = [2400.0, 1200.0, 0.0, -1200.0, -2400.0]
ROAD_W = 320.0
FLOOR_H = 190.0

KEEP_PREFIX = (
    "Ground",
    "Avenue_",
    "Street_",
    "WalkE_",
    "WalkW_",
    "WalkN_",
    "WalkS_",
    "Row_",
    "WeekDirector",
    "StreetDirector",
    "DayNight",
    "PlayerStart",
    "WorldSettings",
    "DefaultPhysicsVolume",
    "AbstractNavData",
    "GameplayDebugger",
    "Brush",
    "CameraActor",
)


def mat(name):
    a = unreal.load_asset("%s/%s" % (MAT, name))
    if a is None:
        raise RuntimeError("Missing " + name)
    return a


def find_by_label(label):
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if actor.get_actor_label() == label:
            return actor
    return None


def spawn(cls, location, scale=None, label=None):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actor = sub.spawn_actor_from_class(cls, location, unreal.Rotator(0.0, 0.0, 0.0))
    if scale is not None:
        actor.set_actor_scale3d(scale)
    if label is not None:
        actor.set_actor_label(label)
    return actor


def ensure_cube(label, location, scale, material, collision=False):
    cube = unreal.load_asset("/Engine/BasicShapes/Cube")
    actor = find_by_label(label)
    if actor is None:
        actor = spawn(unreal.StaticMeshActor, location, scale, label)
    else:
        actor.set_actor_location(location, False, True)
        actor.set_actor_scale3d(scale)
        actor.set_actor_rotation(unreal.Rotator(0.0, 0.0, 0.0), False)
    smc = actor.static_mesh_component
    smc.set_static_mesh(cube)
    if material:
        smc.set_material(0, material)
    if collision:
        smc.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
        try:
            smc.set_collision_profile_name("BlockAll")
        except Exception:
            pass
    else:
        smc.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    smc.set_cast_shadow(False)
    actor.set_actor_hidden_in_game(False)
    actor.set_actor_enable_collision(collision)
    return actor


def should_keep(lab, cls):
    if not lab:
        return False
    for p in KEEP_PREFIX:
        if lab == p or lab.startswith(p):
            # Only keep OUR numbered grid roads, not DenseChicago named avenues
            if lab.startswith("Avenue_") and not lab[7:].isdigit() and "_" in lab[7:]:
                return False
            if lab.startswith("Street_") and not lab[7:].isdigit() and "_" in lab[7:]:
                return False
            if lab.startswith("Walk_") and not (
                lab.startswith("WalkE_")
                or lab.startswith("WalkW_")
                or lab.startswith("WalkN_")
                or lab.startswith("WalkS_")
            ):
                return False
            return True
    if "NavMesh" in lab or "Recast" in cls or "Volume" in cls:
        return False
    if cls in ("WorldSettings", "DefaultPhysicsVolume", "Brush"):
        return True
    return False


def main():
    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level_editor.load_level(MAP_PATH):
        raise RuntimeError("load failed")

    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    killed = 0

    # 1) Destroy every directional / sky / atmosphere in the map
    for actor in list(sub.get_all_level_actors()):
        lab = actor.get_actor_label()
        cls = actor.get_class().get_name() if actor.get_class() else ""
        if isinstance(actor, (unreal.SkyLight, unreal.DirectionalLight)):
            sub.destroy_actor(actor)
            killed += 1
            continue
        try:
            if actor.get_component_by_class(unreal.SkyAtmosphereComponent):
                sub.destroy_actor(actor)
                killed += 1
                continue
        except Exception:
            pass
        if "NavMesh" in lab or "NavMesh" in cls or "RecastNavMesh" in cls:
            sub.destroy_actor(actor)
            killed += 1

    # 2) Destroy leftover DenseChicago / façades / lamps / lakes / EL that read as wedges
    for actor in list(sub.get_all_level_actors()):
        lab = actor.get_actor_label()
        cls = actor.get_class().get_name() if actor.get_class() else ""
        if should_keep(lab, cls):
            continue
        # Keep non-mesh gameplay actors (directors etc. already kept by prefix)
        smc = getattr(actor, "static_mesh_component", None)
        if smc is None and not isinstance(actor, unreal.StaticMeshActor):
            # still kill known bad labels
            bad = (
                lab.startswith("Facade")
                or lab.startswith("LM_")
                or lab.startswith("FabLamp")
                or lab.startswith("FabLight")
                or lab.startswith("Lamp_")
                or lab.startswith("Sprite_")
                or lab.startswith("Lake_")
                or lab.startswith("River_")
                or lab.startswith("Park_")
                or lab.startswith("Track_")
                or lab.startswith("El_")
                or lab.startswith("Moon_")
                or lab.startswith("Sun_")
                or lab.startswith("Fill")
            )
            if bad:
                sub.destroy_actor(actor)
                killed += 1
            continue

        # Kill all other static mesh actors (old named roads, landmarks, poles)
        sub.destroy_actor(actor)
        killed += 1

    # 3) Also kill any remaining Plane mesh
    for actor in list(sub.get_all_level_actors()):
        smc = getattr(actor, "static_mesh_component", None)
        if smc is None or smc.static_mesh is None:
            continue
        if "Plane" in smc.static_mesh.get_name():
            sub.destroy_actor(actor)
            killed += 1

    asphalt = mat("M_Asphalt")
    sidewalk = mat("M_Sidewalk")
    bricks = [mat("M_Brick_Tan"), mat("M_Brick_Red"), mat("M_Brick_Dark")]
    trim = mat("M_Brick_Dark")
    roof = mat("M_Roof_Slate")

    # Wipe and rebuild our grid only
    for actor in list(sub.get_all_level_actors()):
        lab = actor.get_actor_label()
        if (
            lab.startswith("Row_")
            or lab.startswith("Avenue_")
            or lab.startswith("Street_")
            or lab.startswith("WalkE_")
            or lab.startswith("WalkW_")
            or lab.startswith("WalkN_")
            or lab.startswith("WalkS_")
            or lab == "Ground"
        ):
            sub.destroy_actor(actor)

    # Huge ground so iso camera never sees black void wedges past the playable square
    ensure_cube("Ground", unreal.Vector(0, 0, -50), unreal.Vector(160, 160, 1), sidewalk, True)

    span_y = abs(STREETS[0] - STREETS[-1]) + ROAD_W * 2
    span_x = abs(AVENUES[0] - AVENUES[-1]) + ROAD_W * 2
    for i, x in enumerate(AVENUES):
        ensure_cube(
            "Avenue_%d" % i,
            unreal.Vector(x, 0, -36),
            unreal.Vector(ROAD_W / 100.0, span_y / 100.0, 0.55),
            asphalt,
            True,
        )
        ensure_cube(
            "WalkE_%d" % i,
            unreal.Vector(x + ROAD_W * 0.5 + 60, 0, -32),
            unreal.Vector(1.3, span_y / 100.0, 0.4),
            sidewalk,
            True,
        )
        ensure_cube(
            "WalkW_%d" % i,
            unreal.Vector(x - ROAD_W * 0.5 - 60, 0, -32),
            unreal.Vector(1.3, span_y / 100.0, 0.4),
            sidewalk,
            True,
        )
    for j, y in enumerate(STREETS):
        ensure_cube(
            "Street_%d" % j,
            unreal.Vector(0, y, -36),
            unreal.Vector(span_x / 100.0, ROAD_W / 100.0, 0.55),
            asphalt,
            True,
        )
        ensure_cube(
            "WalkN_%d" % j,
            unreal.Vector(0, y + ROAD_W * 0.5 + 60, -32),
            unreal.Vector(span_x / 100.0, 1.3, 0.4),
            sidewalk,
            True,
        )
        ensure_cube(
            "WalkS_%d" % j,
            unreal.Vector(0, y - ROAD_W * 0.5 - 60, -32),
            unreal.Vector(span_x / 100.0, 1.3, 0.4),
            sidewalk,
            True,
        )

    for i, (prefix, origin, footprint, floors) in enumerate(BLOCKS):
        fx, fy = footprint
        total_h = floors * FLOOR_H
        brick = bricks[i % len(bricks)]
        # One solid mass + roof only — no thin cornice/shop sheets
        ensure_cube(
            prefix + "_Mass",
            unreal.Vector(origin.x, origin.y, total_h * 0.5),
            unreal.Vector(fx / 100.0, fy / 100.0, total_h / 100.0),
            brick,
            True,
        )
        ensure_cube(
            prefix + "_Roof",
            unreal.Vector(origin.x, origin.y, total_h + 25.0),
            unreal.Vector(fx / 100.0 * 1.1, fy / 100.0 * 1.1, 0.6),
            roof,
            False,
        )

    if not level_editor.save_current_level():
        raise RuntimeError("save failed")
    unreal.log("NO WEDGES OK — destroyed=%d buildings=%d" % (killed, len(BLOCKS)))


main()
