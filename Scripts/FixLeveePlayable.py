"""Make Levee playable: kill black skylight, rebuild roads, block buildings."""
import unreal

MAP_PATH = "/Game/Maps/Empire/Levee_Greybox"
MAT = "/Game/Art/Empire/Materials"

AVENUES = [
    ("Michigan_Ave", 2400.0),
    ("Wabash_Ave", 1200.0),
    ("State_St", 0.0),
    ("Dearborn_St", -1200.0),
    ("Clark_St", -2400.0),
]
STREETS = [
    ("Roosevelt_Rd", 2400.0),
    ("16th_St", 1200.0),
    ("18th_St", 0.0),
    ("Cermak_Rd", -1200.0),
    ("26th_St", -2400.0),
]
ROAD_W = 300.0
Z_ROAD = -36.0
Z_WALK = -32.0


def mat(name):
    asset = unreal.load_asset("%s/%s" % (MAT, name))
    if asset is None:
        raise RuntimeError("Missing " + name)
    return asset


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


def ensure_cube(label, location, scale, material, collision=True):
    actor = find_by_label(label)
    mesh = unreal.load_asset("/Engine/BasicShapes/Cube")
    if actor is None:
        actor = spawn(unreal.StaticMeshActor, location, scale, label)
        actor.static_mesh_component.set_static_mesh(mesh)
    else:
        actor.set_actor_location(location, False, True)
        actor.set_actor_scale3d(scale)
        if actor.static_mesh_component.static_mesh is None:
            actor.static_mesh_component.set_static_mesh(mesh)
    smc = actor.static_mesh_component
    if material is not None:
        smc.set_material(0, material)
    if collision:
        smc.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
        try:
            smc.set_collision_profile_name("BlockAll")
        except Exception:
            pass
    else:
        smc.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    actor.set_actor_hidden_in_game(False)
    actor.set_actor_enable_collision(collision)
    return actor


def main():
    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level_editor.load_level(MAP_PATH):
        raise RuntimeError("load failed")

    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    killed_sky = 0
    for actor in list(sub.get_all_level_actors()):
        # Destroy realtime skylights / atmosphere that paint the world black
        if isinstance(actor, unreal.SkyLight):
            light = actor.get_component_by_class(unreal.SkyLightComponent)
            if light:
                try:
                    light.set_editor_property("real_time_capture", False)
                except Exception:
                    pass
                light.set_visibility(False)
                light.set_intensity(0.0)
            sub.destroy_actor(actor)
            killed_sky += 1
            continue
        lab = actor.get_actor_label()
        if lab in ("Sky_Levee", "Atmosphere_Levee"):
            sub.destroy_actor(actor)
            killed_sky += 1

    m_asphalt = mat("M_Asphalt")
    m_sidewalk = mat("M_Sidewalk")

    # Ground plane
    ensure_cube(
        "Ground",
        unreal.Vector(0.0, 0.0, -50.0),
        unreal.Vector(90.0, 80.0, 1.0),
        m_sidewalk,
        collision=True,
    )

    # Full avenue / street lattice — bright, wide, blocking
    span_y = abs(STREETS[0][1] - STREETS[-1][1]) + ROAD_W * 2.0
    span_x = abs(AVENUES[0][1] - AVENUES[-1][1]) + ROAD_W * 2.0
    roads = 0
    for name, x in AVENUES:
        ensure_cube(
            "Avenue_%s" % name,
            unreal.Vector(x, 0.0, Z_ROAD),
            unreal.Vector(ROAD_W / 100.0, span_y / 100.0, 0.4),
            m_asphalt,
            collision=True,
        )
        half = ROAD_W * 0.5 + 50.0
        ensure_cube(
            "Walk_%s_E" % name,
            unreal.Vector(x + half, 0.0, Z_WALK),
            unreal.Vector(1.0, span_y / 100.0, 0.3),
            m_sidewalk,
            collision=True,
        )
        ensure_cube(
            "Walk_%s_W" % name,
            unreal.Vector(x - half, 0.0, Z_WALK),
            unreal.Vector(1.0, span_y / 100.0, 0.3),
            m_sidewalk,
            collision=True,
        )
        roads += 1
    for name, y in STREETS:
        ensure_cube(
            "Street_%s" % name,
            unreal.Vector(0.0, y, Z_ROAD),
            unreal.Vector(span_x / 100.0, ROAD_W / 100.0, 0.4),
            m_asphalt,
            collision=True,
        )
        half = ROAD_W * 0.5 + 50.0
        ensure_cube(
            "Walk_%s_N" % name,
            unreal.Vector(0.0, y + half, Z_WALK),
            unreal.Vector(span_x / 100.0, 1.0, 0.3),
            m_sidewalk,
            collision=True,
        )
        ensure_cube(
            "Walk_%s_S" % name,
            unreal.Vector(0.0, y - half, Z_WALK),
            unreal.Vector(span_x / 100.0, 1.0, 0.3),
            m_sidewalk,
            collision=True,
        )
        roads += 1

    # Building masses must block pawns
    blocked = 0
    for actor in list(sub.get_all_level_actors()):
        lab = actor.get_actor_label()
        if not (lab.endswith("_Mass") and lab.startswith("Row_")):
            continue
        smc = actor.static_mesh_component
        if smc is None:
            continue
        smc.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
        try:
            smc.set_collision_profile_name("BlockAll")
        except Exception:
            pass
        actor.set_actor_enable_collision(True)
        actor.set_actor_hidden_in_game(False)
        blocked += 1

    # Bright sun baked into map as backup (DayNight owns runtime lights)
    sun = find_by_label("Sun_Levee")
    if sun:
        light = sun.get_component_by_class(unreal.DirectionalLightComponent)
        if light:
            try:
                light.set_editor_property("atmosphere_sun_light", False)
                light.set_editor_property("real_time_capture", False)
            except Exception:
                pass
            light.set_cast_shadows(False)
            light.set_intensity(20.0)

    if not level_editor.save_current_level():
        raise RuntimeError("save failed")
    unreal.log(
        "LEVEE PLAYABLE OK — killed_sky=%d roads=%d blocked_mass=%d"
        % (killed_sky, roads, blocked)
    )


main()
