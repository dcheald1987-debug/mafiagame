"""Kill giant ortho triangle bugs + restore solid readable buildings and roads.

Root cause: Engine Plane façade cards (FacadePlane_*) + competing directionals
draw huge wedges under isometric orthographic camera.
"""
import unreal

MAP_PATH = "/Game/Maps/Empire/Levee_Greybox"
MAT = "/Game/Art/Empire/Materials"

# Wide Chicago grid (BuildLeveeGrid v2)
BLOCKS = [
    ("Row_Garage", unreal.Vector(1800.0, -600.0, 0.0), (560.0, 500.0), 3, "M_Brick_Tan", "M_Brick_Dark", "M_Roof_Slate"),
    ("Row_Cafe", unreal.Vector(600.0, -600.0, 0.0), (560.0, 500.0), 3, "M_Brick_Red", "M_Brick_Dark", "M_Roof_Tar"),
    ("Row_Dock", unreal.Vector(1800.0, -1800.0, 0.0), (560.0, 500.0), 2, "M_Brick_Dark", "M_Brick_Tan", "M_Roof_Tar"),
    ("Row_MidC", unreal.Vector(600.0, -1800.0, 0.0), (560.0, 500.0), 4, "M_Brick_Dark", "M_Brick_Red", "M_Roof_Slate"),
    ("Row_MidA", unreal.Vector(-600.0, 600.0, 0.0), (560.0, 500.0), 4, "M_Brick_Tan", "M_Brick_Dark", "M_Roof_Tar"),
    ("Row_MidB", unreal.Vector(-600.0, -600.0, 0.0), (560.0, 500.0), 3, "M_Brick_Red", "M_Brick_Tan", "M_Roof_Slate"),
    ("Row_Bar", unreal.Vector(-1800.0, -1800.0, 0.0), (560.0, 500.0), 3, "M_Brick_Red", "M_Brick_Dark", "M_Roof_Tar"),
    ("Row_Board", unreal.Vector(-600.0, 1800.0, 0.0), (560.0, 500.0), 4, "M_Brick_Tan", "M_Brick_Dark", "M_Roof_Slate"),
    ("Row_MidD", unreal.Vector(-1800.0, 600.0, 0.0), (560.0, 500.0), 3, "M_Brick_Dark", "M_Brick_Tan", "M_Roof_Tar"),
    ("Row_MidE", unreal.Vector(-1800.0, -600.0, 0.0), (560.0, 500.0), 3, "M_Brick_Tan", "M_Brick_Red", "M_Roof_Slate"),
    ("Row_MidF", unreal.Vector(600.0, 600.0, 0.0), (560.0, 500.0), 4, "M_Brick_Dark", "M_Brick_Tan", "M_Roof_Tar"),
    ("Row_MidG", unreal.Vector(1800.0, 600.0, 0.0), (560.0, 500.0), 3, "M_Brick_Red", "M_Brick_Dark", "M_Roof_Slate"),
    ("Row_Rope", unreal.Vector(-1800.0, 1800.0, 0.0), (560.0, 460.0), 2, "M_Brick_Tan", "M_Brick_Dark", "M_Roof_Tar"),
    ("Row_Freight", unreal.Vector(-600.0, -1800.0, 0.0), (560.0, 500.0), 2, "M_Brick_Dark", "M_Brick_Tan", "M_Roof_Tar"),
]

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
FLOOR_H = 180.0


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


def destroy_matching(pred):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    n = 0
    for actor in list(sub.get_all_level_actors()):
        if pred(actor.get_actor_label(), actor):
            sub.destroy_actor(actor)
            n += 1
    return n


def ensure_cube(label, location, scale, material, collision=False):
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
    # Force cube only — never leave a Plane mesh on building actors
    if smc.static_mesh is None or "Plane" in smc.static_mesh.get_name():
        smc.set_static_mesh(mesh)
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
    smc.set_cast_shadow(False)
    actor.set_actor_hidden_in_game(False)
    actor.set_actor_enable_collision(collision)
    return actor


def build_building(prefix, origin, footprint, floors, brick, trim, roof, window):
    fx, fy = footprint
    total_h = max(1, floors) * FLOOR_H
    front_y = origin.y - fy * 0.52

    # Destroy leftover plane parts for this row
    destroy_matching(lambda lab, _a: lab.startswith(prefix + "_") and (
        "Facade" in lab or "Plane" in lab
    ))

    ensure_cube(
        prefix + "_Mass",
        unreal.Vector(origin.x, origin.y, total_h * 0.5),
        unreal.Vector(fx / 100.0, fy / 100.0, total_h / 100.0),
        brick,
        collision=True,
    )
    ensure_cube(
        prefix + "_Shopfront",
        unreal.Vector(origin.x, origin.y, 70.0),
        unreal.Vector(fx / 100.0 * 1.02, fy / 100.0 * 1.02, 1.35),
        trim,
        collision=False,
    )
    ensure_cube(
        prefix + "_Cornice",
        unreal.Vector(origin.x, origin.y, total_h + 20.0),
        unreal.Vector(fx / 100.0 * 1.06, fy / 100.0 * 1.06, 0.4),
        roof,
        collision=False,
    )
    # Window cubes on front face (NOT planes)
    panes = 4 if fx >= 500 else 3
    pane_w = (fx * 0.78) / panes
    start_x = origin.x - (pane_w * panes) * 0.5 + pane_w * 0.5
    for fl in range(floors):
        z = 110.0 + fl * FLOOR_H
        for p in range(panes):
            ensure_cube(
                "%s_Win_%d_%d" % (prefix, fl, p),
                unreal.Vector(start_x + p * pane_w, front_y, z),
                unreal.Vector(pane_w / 100.0 * 0.65, 0.14, 0.8),
                window,
                collision=False,
            )


def main():
    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level_editor.load_level(MAP_PATH):
        raise RuntimeError("load failed")

    # 1) Kill triangle sources
    killed_planes = destroy_matching(
        lambda lab, a: lab.startswith("FacadePlane_")
        or lab.startswith("Sprite_")
        or "Plane" in lab
    )
    # Kill oversized / glitchy Fab lamps (mesh can include huge tris when scaled wrong)
    killed_lamps = destroy_matching(
        lambda lab, a: lab.startswith("FabLamp_") or lab.startswith("FabLight_")
    )
    # Kill leftover LM dense mass if any
    killed_lm = destroy_matching(lambda lab, a: lab.startswith("LM_"))
    # Kill map directionals / skylights / atmosphere (DayNight owns lighting)
    killed_lights = 0
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in list(sub.get_all_level_actors()):
        lab = actor.get_actor_label()
        if isinstance(actor, (unreal.SkyLight, unreal.DirectionalLight)) or lab in (
            "Sun_Levee", "Sky_Levee", "Moon_Levee", "Atmosphere_Levee", "PP_LeveeReadable",
        ):
            # Keep PP volume but fix it; destroy lights/atmosphere
            if lab == "PP_LeveeReadable":
                try:
                    settings = actor.get_editor_property("settings")
                    settings.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
                    settings.set_editor_property("auto_exposure_bias", 4.5)
                    settings.set_editor_property("override_auto_exposure_method", True)
                    settings.set_editor_property("override_auto_exposure_bias", True)
                    actor.set_editor_property("settings", settings)
                    actor.set_editor_property("unbound", True)
                except Exception:
                    pass
                continue
            if isinstance(actor, (unreal.SkyLight, unreal.DirectionalLight)) or lab in (
                "Sun_Levee", "Sky_Levee", "Moon_Levee", "Atmosphere_Levee",
            ):
                sub.destroy_actor(actor)
                killed_lights += 1

    brick = mat("M_Brick_Tan")
    trim = mat("M_Brick_Dark")
    roof = mat("M_Roof_Slate")
    window = mat("M_Lamp_Iron")
    asphalt = mat("M_Asphalt")
    sidewalk = mat("M_Sidewalk")

    # 2) Roads — bright, wide, solid cubes
    span_y = abs(STREETS[0][1] - STREETS[-1][1]) + ROAD_W * 2.0
    span_x = abs(AVENUES[0][1] - AVENUES[-1][1]) + ROAD_W * 2.0
    ensure_cube("Ground", unreal.Vector(0.0, 0.0, -50.0), unreal.Vector(90.0, 80.0, 1.0), sidewalk, True)
    for name, x in AVENUES:
        ensure_cube(
            "Avenue_%s" % name,
            unreal.Vector(x, 0.0, -36.0),
            unreal.Vector(ROAD_W / 100.0, span_y / 100.0, 0.45),
            asphalt,
            True,
        )
        half = ROAD_W * 0.5 + 55.0
        ensure_cube(
            "Walk_%s_E" % name,
            unreal.Vector(x + half, 0.0, -32.0),
            unreal.Vector(1.1, span_y / 100.0, 0.35),
            sidewalk,
            True,
        )
        ensure_cube(
            "Walk_%s_W" % name,
            unreal.Vector(x - half, 0.0, -32.0),
            unreal.Vector(1.1, span_y / 100.0, 0.35),
            sidewalk,
            True,
        )
    for name, y in STREETS:
        ensure_cube(
            "Street_%s" % name,
            unreal.Vector(0.0, y, -36.0),
            unreal.Vector(span_x / 100.0, ROAD_W / 100.0, 0.45),
            asphalt,
            True,
        )
        half = ROAD_W * 0.5 + 55.0
        ensure_cube(
            "Walk_%s_N" % name,
            unreal.Vector(0.0, y + half, -32.0),
            unreal.Vector(span_x / 100.0, 1.1, 0.35),
            sidewalk,
            True,
        )
        ensure_cube(
            "Walk_%s_S" % name,
            unreal.Vector(0.0, y - half, -32.0),
            unreal.Vector(span_x / 100.0, 1.1, 0.35),
            sidewalk,
            True,
        )

    # 3) Solid period buildings (cubes only)
    for prefix, origin, footprint, floors, b, t, r in BLOCKS:
        build_building(prefix, origin, footprint, floors, mat(b), mat(t), mat(r), window)

    # Drop dress flags so façades aren't reapplied blindly
    destroy_matching(
        lambda lab, _a: lab.startswith("Dress_ElevenLabs") or lab.startswith("Dress_ChicagoDense")
    )

    if not level_editor.save_current_level():
        raise RuntimeError("save failed")
    unreal.log(
        "NO TRIANGLES OK — planes=%d lamps=%d lm=%d lights=%d buildings=%d"
        % (killed_planes, killed_lamps, killed_lm, killed_lights, len(BLOCKS))
    )


main()
