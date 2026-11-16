"""Make Levee readable: daylight + soft sky, tame lamps, denser period buildings."""
import unreal

MAP_PATH = "/Game/Maps/Empire/Levee_Greybox"
MAT = "/Game/Art/Empire/Materials"
FLAG = "Dress_Levee_Dense_v1"
LANDMARKS = ("Row_Garage", "Row_Cafe", "Row_Bar", "Row_Board")
DOCKISH = ("Row_Dock", "Row_Freight", "Row_Rope")
TALL_MIDS = ("Row_MidA", "Row_MidC", "Row_MidF", "Row_Board")


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


def spawn(cls, location, scale=None, label=None, rotation=None):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    rot = rotation or unreal.Rotator(0.0, 0.0, 0.0)
    actor = sub.spawn_actor_from_class(cls, location, rot)
    if scale is not None:
        actor.set_actor_scale3d(scale)
    if label is not None:
        actor.set_actor_label(label)
    return actor


def ensure_cube(label, location, scale, material, rotation=None, collision=True):
    actor = find_by_label(label)
    mesh = unreal.load_asset("/Engine/BasicShapes/Cube")
    if actor is None:
        actor = spawn(unreal.StaticMeshActor, location, scale, label, rotation)
        actor.static_mesh_component.set_static_mesh(mesh)
    else:
        actor.set_actor_location(location, False, True)
        actor.set_actor_scale3d(scale)
        if rotation is not None:
            actor.set_actor_rotation(rotation, False)
        if actor.static_mesh_component.static_mesh is None:
            actor.static_mesh_component.set_static_mesh(mesh)
    smc = actor.static_mesh_component
    if material is not None:
        smc.set_material(0, material)
    if collision:
        smc.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    else:
        smc.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    actor.set_actor_hidden_in_game(False)
    return actor


def destroy_prefix_parts(prefix, suffixes):
    """Remove stale labeled parts before rebuilding denser façades."""
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in list(sub.get_all_level_actors()):
        label = actor.get_actor_label()
        if not label.startswith(prefix + "_"):
            continue
        for suf in suffixes:
            if label == prefix + "_" + suf or label.startswith(prefix + "_" + suf):
                sub.destroy_actor(actor)
                break


def destroy_label(label):
    actor = find_by_label(label)
    if actor:
        unreal.get_editor_subsystem(unreal.EditorActorSubsystem).destroy_actor(actor)


def ensure_directional_light():
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
        light.set_intensity(5.5)
        light.set_light_color(unreal.LinearColor(1.0, 0.96, 0.88, 1.0))
        try:
            light.set_editor_property("atmosphere_sun_light", True)
            light.set_editor_property("cast_shadows", True)
            light.set_editor_property("dynamic_shadow_distance_movable_light", 20000.0)
            # Win forward-shading / translucent / fog sun slot
            light.set_editor_property("forward_shading_priority", 1)
        except Exception:
            pass

    # Kill competing directional lights (old Light Source, duplicates)
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for other in list(sub.get_all_level_actors()):
        if other is None or other == actor:
            continue
        if not isinstance(other, unreal.DirectionalLight):
            continue
        label = other.get_actor_label()
        if label == "Sun_Levee":
            continue
        unreal.log("Removing competing sun: " + label)
        sub.destroy_actor(other)
    return actor


def ensure_sky_light():
    actor = find_by_label("Sky_Levee")
    if actor is None:
        actor = spawn(unreal.SkyLight, unreal.Vector(0.0, 0.0, 600.0), None, "Sky_Levee")
    light = actor.get_component_by_class(unreal.SkyLightComponent)
    if light:
        light.set_intensity(2.2)
        light.set_light_color(unreal.LinearColor(0.82, 0.88, 1.0, 1.0))
        try:
            light.set_editor_property("real_time_capture", True)
            light.set_mobility(unreal.ComponentMobility.MOVABLE)
        except Exception:
            pass
    return actor


def ensure_sky_atmosphere():
    if find_by_label("Atmosphere_Levee") is None:
        spawn(unreal.SkyAtmosphere, unreal.Vector(0.0, 0.0, 0.0), None, "Atmosphere_Levee")


def ensure_post_process():
    actor = find_by_label("PP_LeveeReadable")
    if actor is None:
        actor = spawn(unreal.PostProcessVolume, unreal.Vector(0.0, 0.0, 200.0), unreal.Vector(200.0, 200.0, 50.0), "PP_LeveeReadable")
    try:
        actor.set_editor_property("unbound", True)
        settings = actor.get_editor_property("settings")
        # Lock exposure so ortho street stays readable
        settings.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
        settings.set_editor_property("auto_exposure_bias", 1.35)
        settings.set_editor_property("override_auto_exposure_method", True)
        settings.set_editor_property("override_auto_exposure_bias", True)
        settings.set_editor_property("bloom_intensity", 0.35)
        settings.set_editor_property("override_bloom_intensity", True)
        actor.set_editor_property("settings", settings)
    except Exception as exc:
        unreal.log_warning("PP setup partial: %s" % exc)
    return actor


def tame_street_lamps():
    """Keep Fab tungsten lights; only strip obsolete bare poles without Fab meshes."""
    # FabStreetLights owns FabLamp_/FabLight_ — do not destroy those.
    pass


def build_period_building(prefix, origin, footprint_xy, floors, brick_mat, trim_mat, roof_mat, window_mat):
    """Dense 1930s block: mass, shopfront, discrete windows, pilasters, cornice, roof + extras."""
    fx, fy = footprint_xy
    floor_h = 180.0
    total_h = floors * floor_h
    front_y = origin.y - fy * 0.52

    # Clear old single-strip windows / prior dense extras so rebuild stays clean
    destroy_prefix_parts(
        prefix,
        (
            "Win_",
            "Door",
            "Awning",
            "PilasterL",
            "PilasterR",
            "Chimney",
            "DockLedge",
            "FireEsc",
        ),
    )

    # Main mass (collision)
    ensure_cube(
        prefix + "_Mass",
        unreal.Vector(origin.x, origin.y, total_h * 0.5),
        unreal.Vector(fx / 100.0, fy / 100.0, total_h / 100.0),
        brick_mat,
        collision=True,
    )
    # Ground floor darker belt
    ensure_cube(
        prefix + "_Shopfront",
        unreal.Vector(origin.x, origin.y, 70.0),
        unreal.Vector(fx / 100.0 * 1.02, fy / 100.0 * 1.02, 1.4),
        trim_mat,
        collision=False,
    )

    # Discrete window panes per floor (2–4 by width)
    panes = 4 if fx >= 700.0 else (3 if fx >= 500.0 else 2)
    pane_w = (fx * 0.78) / panes
    span = pane_w * panes
    start_x = origin.x - span * 0.5 + pane_w * 0.5
    for i in range(floors):
        z = 110.0 + i * floor_h
        for p in range(panes):
            ensure_cube(
                "%s_Win_%d_%d" % (prefix, i, p),
                unreal.Vector(start_x + p * pane_w, front_y, z),
                unreal.Vector(pane_w / 100.0 * 0.72, 0.16, 0.85),
                window_mat,
                collision=False,
            )

    # Front-corner pilasters
    pilaster_h = total_h / 100.0 * 0.95
    ensure_cube(
        prefix + "_PilasterL",
        unreal.Vector(origin.x - fx * 0.48, front_y, total_h * 0.48),
        unreal.Vector(0.22, 0.2, pilaster_h),
        trim_mat,
        collision=False,
    )
    ensure_cube(
        prefix + "_PilasterR",
        unreal.Vector(origin.x + fx * 0.48, front_y, total_h * 0.48),
        unreal.Vector(0.22, 0.2, pilaster_h),
        trim_mat,
        collision=False,
    )

    # Landmark door + awning
    if prefix in LANDMARKS:
        ensure_cube(
            prefix + "_Door",
            unreal.Vector(origin.x, front_y - 10.0, 55.0),
            unreal.Vector(0.9, 0.22, 1.1),
            trim_mat,
            collision=False,
        )
        ensure_cube(
            prefix + "_Awning",
            unreal.Vector(origin.x, front_y - 40.0, 115.0),
            unreal.Vector(fx / 100.0 * 0.55, 0.7, 0.12),
            roof_mat,
            collision=False,
        )

    # Dock / freight loading ledge + chimney
    if prefix in DOCKISH:
        ensure_cube(
            prefix + "_DockLedge",
            unreal.Vector(origin.x, front_y - 35.0, 40.0),
            unreal.Vector(fx / 100.0 * 0.7, 0.9, 0.35),
            trim_mat,
            collision=False,
        )
        ensure_cube(
            prefix + "_Chimney",
            unreal.Vector(origin.x + fx * 0.28, origin.y + fy * 0.15, total_h + 90.0),
            unreal.Vector(0.55, 0.55, 1.1),
            brick_mat,
            collision=False,
        )

    # Fire escape on tall mid / boardwalk
    if prefix in TALL_MIDS or floors >= 4:
        for r in range(floors):
            z = 90.0 + r * floor_h
            ensure_cube(
                "%s_FireEsc_%d" % (prefix, r),
                unreal.Vector(origin.x + fx * 0.42, front_y - 25.0, z),
                unreal.Vector(0.55, 0.45, 0.12),
                trim_mat,
                collision=False,
            )
        ensure_cube(
            prefix + "_FireEscRail",
            unreal.Vector(origin.x + fx * 0.42, front_y - 25.0, total_h * 0.45),
            unreal.Vector(0.08, 0.08, total_h / 100.0 * 0.85),
            trim_mat,
            collision=False,
        )

    # Cornice
    ensure_cube(
        prefix + "_Cornice",
        unreal.Vector(origin.x, origin.y, total_h + 20.0),
        unreal.Vector(fx / 100.0 * 1.08, fy / 100.0 * 1.08, 0.35),
        trim_mat,
        collision=False,
    )
    # Flat tar roof
    ensure_cube(
        prefix + "_Roof",
        unreal.Vector(origin.x, origin.y, total_h + 45.0),
        unreal.Vector(fx / 100.0 * 0.95, fy / 100.0 * 0.95, 0.25),
        roof_mat,
        collision=False,
    )
    # Stoop
    ensure_cube(
        prefix + "_Stoop",
        unreal.Vector(origin.x, origin.y - fy * 0.55, 25.0),
        unreal.Vector(1.2, 0.8, 0.5),
        trim_mat,
        collision=False,
    )


def main():
    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level_editor.load_level(MAP_PATH):
        raise RuntimeError("load failed")

    m_brick = mat("M_Brick_Red")
    m_brick_dark = mat("M_Brick_Dark")
    m_brick_tan = mat("M_Brick_Tan")
    m_roof = mat("M_Roof_Tar")
    m_roof_slate = mat("M_Roof_Slate")
    m_sidewalk = mat("M_Sidewalk")
    m_asphalt = mat("M_Asphalt")
    m_window = mat("M_Lamp_Iron")  # dark recessed windows

    # --- Lighting: readable daytime ---
    tame_street_lamps()
    ensure_directional_light()
    ensure_sky_light()
    ensure_sky_atmosphere()
    ensure_post_process()

    # Brighten ground / streets if present
    for label in ("Ground", "Street_NS", "Street_EW", "Street_Alley"):
        a = find_by_label(label)
        if a and a.static_mesh_component:
            if "Street" in label or "Alley" in label:
                a.static_mesh_component.set_material(0, m_asphalt)
            else:
                a.static_mesh_component.set_material(0, m_sidewalk)

    # --- 1930 Chicago Near South parcels (BuildLeveeGrid) ---
    # Wider 1200uu Chicago grid — smaller footprints so streets read as canyons
    blocks = [
        ("Row_Garage", unreal.Vector(1800.0, -600.0, 0.0), (560.0, 500.0), 3, m_brick, m_brick_dark, m_roof),
        ("Row_Cafe", unreal.Vector(600.0, -600.0, 0.0), (560.0, 500.0), 3, m_brick_tan, m_brick_dark, m_roof_slate),
        ("Row_Dock", unreal.Vector(1800.0, -1800.0, 0.0), (560.0, 500.0), 2, m_brick_dark, m_brick, m_roof),
        ("Row_MidC", unreal.Vector(600.0, -1800.0, 0.0), (560.0, 500.0), 4, m_brick_dark, m_brick_tan, m_roof),
        ("Row_MidA", unreal.Vector(-600.0, 600.0, 0.0), (560.0, 500.0), 4, m_brick, m_brick_dark, m_roof),
        ("Row_MidB", unreal.Vector(-600.0, -600.0, 0.0), (560.0, 500.0), 3, m_brick_tan, m_brick, m_roof_slate),
        ("Row_Bar", unreal.Vector(-1800.0, -1800.0, 0.0), (560.0, 500.0), 3, m_brick, m_brick_tan, m_roof_slate),
        ("Row_Board", unreal.Vector(-600.0, 1800.0, 0.0), (560.0, 500.0), 4, m_brick_tan, m_brick_dark, m_roof),
        ("Row_MidD", unreal.Vector(-1800.0, 600.0, 0.0), (560.0, 500.0), 3, m_brick, m_brick_dark, m_roof),
        ("Row_MidE", unreal.Vector(-1800.0, -600.0, 0.0), (560.0, 500.0), 3, m_brick_tan, m_brick, m_roof_slate),
        ("Row_MidF", unreal.Vector(600.0, 600.0, 0.0), (560.0, 500.0), 4, m_brick_dark, m_brick_tan, m_roof),
        ("Row_MidG", unreal.Vector(1800.0, 600.0, 0.0), (560.0, 500.0), 3, m_brick, m_brick_dark, m_roof_slate),
        ("Row_Rope", unreal.Vector(-1800.0, 1800.0, 0.0), (560.0, 460.0), 2, m_brick, m_brick_tan, m_roof_slate),
        ("Row_Freight", unreal.Vector(-600.0, -1800.0, 0.0), (560.0, 500.0), 2, m_brick_dark, m_brick, m_roof),
    ]
    for prefix, origin, footprint, floors, brick, trim, roof in blocks:
        build_period_building(prefix, origin, footprint, floors, brick, trim, roof, m_window)

    # Hide old flat Bld_* boxes so new rows read clean (keep if needed for collision — scale down/hide)
    for label in (
        "Bld_Garage", "Bld_Cafe", "Bld_Dock", "Bld_Bar", "Bld_Board", "Bld_Freight", "Bld_Rope",
        "Facade_A", "Facade_B", "Facade_C", "Facade_D", "Facade_E", "Facade_F", "Facade_G", "Facade_H",
        "Cornice_A", "Cornice_B", "Cornice_C", "Cornice_G",
    ):
        a = find_by_label(label)
        if a:
            a.set_actor_hidden_in_game(True)
            a.set_actor_enable_collision(False)

    # Remove prior dress flags
    for old in ("Dress_Levee_Daylight_v1", "Dress_GameplaySprites_v1", "Dress_GameplaySprites_v2"):
        destroy_label(old)
    if find_by_label(FLAG) is None:
        flag = spawn(unreal.Actor, unreal.Vector(0.0, 0.0, 5200.0), None, FLAG)
        flag.set_actor_hidden_in_game(True)

    if not level_editor.save_current_level():
        raise RuntimeError("save failed")
    unreal.log("LEVEE VISIBILITY OK — dense modular period buildings")


main()
