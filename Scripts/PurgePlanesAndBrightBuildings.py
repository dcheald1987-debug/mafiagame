"""Destroy EVERY BasicShapes Plane actor (ortho triangle wedges) + force bright cube buildings."""
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
ROAD_W = 300.0
FLOOR_H = 180.0


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
    smc = actor.static_mesh_component
    smc.set_static_mesh(cube)  # always cube — never plane
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


def main():
    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level_editor.load_level(MAP_PATH):
        raise RuntimeError("load failed")

    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    killed = 0
    for actor in list(sub.get_all_level_actors()):
        lab = actor.get_actor_label()
        # Old façade cards / landmark billboards / sprite props
        if (
            lab.startswith("Facade")
            or lab.startswith("FacadePlane_")
            or lab.startswith("Sprite_")
            or lab.startswith("LM_")
            or lab.startswith("Billboard")
        ):
            sub.destroy_actor(actor)
            killed += 1
            continue
        smc = getattr(actor, "static_mesh_component", None)
        if smc is None:
            continue
        mesh = smc.static_mesh
        if mesh is None:
            continue
        name = mesh.get_name()
        # Any plane / sprite card / thin sheet = triangle risk in ortho
        if "Plane" in name or "plane" in name:
            sub.destroy_actor(actor)
            killed += 1
            unreal.log("Destroyed plane actor %s mesh=%s" % (lab, name))

    # Also kill sky/directional leftovers
    for actor in list(sub.get_all_level_actors()):
        if isinstance(actor, (unreal.SkyLight, unreal.DirectionalLight)):
            sub.destroy_actor(actor)
            killed += 1
        else:
            try:
                if actor.get_component_by_class(unreal.SkyAtmosphereComponent):
                    sub.destroy_actor(actor)
                    killed += 1
            except Exception:
                pass

    asphalt = mat("M_Asphalt")
    sidewalk = mat("M_Sidewalk")
    bricks = [mat("M_Brick_Tan"), mat("M_Brick_Red"), mat("M_Brick_Dark")]
    trim = mat("M_Brick_Dark")
    roof = mat("M_Roof_Slate")
    window = mat("M_Lamp_Iron")

    ensure_cube("Ground", unreal.Vector(0, 0, -50), unreal.Vector(90, 80, 1), sidewalk, True)

    span_y = abs(STREETS[0] - STREETS[-1]) + ROAD_W * 2
    span_x = abs(AVENUES[0] - AVENUES[-1]) + ROAD_W * 2
    for i, x in enumerate(AVENUES):
        ensure_cube("Avenue_%d" % i, unreal.Vector(x, 0, -36), unreal.Vector(ROAD_W / 100.0, span_y / 100.0, 0.5), asphalt, True)
        ensure_cube("WalkE_%d" % i, unreal.Vector(x + ROAD_W * 0.5 + 55, 0, -32), unreal.Vector(1.2, span_y / 100.0, 0.35), sidewalk, True)
        ensure_cube("WalkW_%d" % i, unreal.Vector(x - ROAD_W * 0.5 - 55, 0, -32), unreal.Vector(1.2, span_y / 100.0, 0.35), sidewalk, True)
    for j, y in enumerate(STREETS):
        ensure_cube("Street_%d" % j, unreal.Vector(0, y, -36), unreal.Vector(span_x / 100.0, ROAD_W / 100.0, 0.5), asphalt, True)
        ensure_cube("WalkN_%d" % j, unreal.Vector(0, y + ROAD_W * 0.5 + 55, -32), unreal.Vector(span_x / 100.0, 1.2, 0.35), sidewalk, True)
        ensure_cube("WalkS_%d" % j, unreal.Vector(0, y - ROAD_W * 0.5 - 55, -32), unreal.Vector(span_x / 100.0, 1.2, 0.35), sidewalk, True)

    # Wipe old Row_* parts then rebuild solid
    for actor in list(sub.get_all_level_actors()):
        lab = actor.get_actor_label()
        if lab.startswith("Row_"):
            sub.destroy_actor(actor)

    # Solid readable masses only — no thin shop/window slabs (read as wireframes in ortho).
    for i, (prefix, origin, footprint, floors) in enumerate(BLOCKS):
        fx, fy = footprint
        total_h = floors * FLOOR_H
        brick = bricks[i % len(bricks)]
        ensure_cube(
            prefix + "_Mass",
            unreal.Vector(origin.x, origin.y, total_h * 0.5),
            unreal.Vector(fx / 100.0, fy / 100.0, total_h / 100.0),
            brick,
            True,
        )
        # Dark base band so floors read
        ensure_cube(
            prefix + "_Base",
            unreal.Vector(origin.x, origin.y, 45.0),
            unreal.Vector(fx / 100.0 * 1.02, fy / 100.0 * 1.02, 0.9),
            trim,
            False,
        )
        ensure_cube(
            prefix + "_Roof",
            unreal.Vector(origin.x, origin.y, total_h + 22.0),
            unreal.Vector(fx / 100.0 * 1.08, fy / 100.0 * 1.08, 0.55),
            roof,
            False,
        )
        # Thick front cornice (cube, not plane) for street face
        ensure_cube(
            prefix + "_Cornice",
            unreal.Vector(origin.x, origin.y - fy * 0.48, total_h - 30.0),
            unreal.Vector(fx / 100.0 * 0.95, 0.35, 0.35),
            trim,
            False,
        )

    # Do NOT spawn a map directional — DayNight owns the only sun.
    # Two directionals = forward-shading giant wedges.

    # Kill stale navmesh debug volumes that draw huge polys
    for actor in list(sub.get_all_level_actors()):
        lab = actor.get_actor_label()
        cls = actor.get_class().get_name() if actor.get_class() else ""
        if "NavMesh" in lab or "NavMesh" in cls or "RecastNavMesh" in cls:
            sub.destroy_actor(actor)
            killed += 1

    if not level_editor.save_current_level():
        raise RuntimeError("save failed")
    unreal.log("PURGE PLANES OK — destroyed=%d buildings=%d" % (killed, len(BLOCKS)))


main()
