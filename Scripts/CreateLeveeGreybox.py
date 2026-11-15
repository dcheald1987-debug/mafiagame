import unreal

MAP_PATH = "/Game/Maps/Empire/Levee_Greybox"

# UENUM byte values from LEEmpireTypes.h
OWNER_NEUTRAL, OWNER_PLAYER, OWNER_RIVAL, OWNER_CONTESTED = 0, 1, 2, 3
KIND_RACKET, KIND_BUSINESS, KIND_STREET, KIND_BLOCK = 0, 1, 2, 3
ROLE_BAGMAN, ROLE_ENFORCER, ROLE_RECRUITER = 0, 1, 2


def spawn(cls, location, scale=None, label=None, rotation=None):
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    rot = rotation or unreal.Rotator(0.0, 0.0, 0.0)
    actor = subsystem.spawn_actor_from_class(cls, location, rot)
    if scale is not None:
        actor.set_actor_scale3d(scale)
    if label is not None:
        actor.set_actor_label(label)
    return actor


def cube_actor(label, location, scale):
    mesh = unreal.load_asset("/Engine/BasicShapes/Cube")
    actor = spawn(unreal.StaticMeshActor, location, scale, label)
    actor.static_mesh_component.set_static_mesh(mesh)
    return actor


def site(site_id, name, kind, owner, block_id, payout, heat, location):
    actor = spawn(unreal.LESiteActor, location, unreal.Vector(1.0, 1.0, 1.0), "Site_" + site_id)
    actor.configure(site_id, unreal.Text(name), kind, owner, block_id, payout, heat)
    return actor


def hood(hood_id, name, role, faction, location):
    actor = spawn(unreal.LEHoodAgent, location, None, "Hood_" + hood_id)
    actor.configure(hood_id, unreal.Text(name), role, faction, 60)
    return actor


def main():
    unreal.EditorAssetLibrary.make_directory("/Game/Maps/Empire")
    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if unreal.EditorAssetLibrary.does_asset_exist(MAP_PATH):
        if not level_editor.load_level(MAP_PATH):
            raise RuntimeError("load failed")
        existing = actor_subsystem.get_all_level_actors()
        if any(a.get_actor_label() == "WeekDirector" for a in existing):
            unreal.log("Levee greybox already populated")
            return
        # Incomplete prior run — clear and rebuild in place.
        for actor in list(existing):
            label = actor.get_actor_label()
            if label not in ("WorldSettings", "Brush_0", "DefaultPhysicsVolume0", "AbstractNavData-Default"):
                try:
                    actor_subsystem.destroy_actor(actor)
                except Exception:
                    pass
    else:
        if not level_editor.new_level(MAP_PATH):
            raise RuntimeError("create failed")

    cube_actor("Ground", unreal.Vector(0.0, 0.0, -50.0), unreal.Vector(80.0, 80.0, 1.0))

    buildings = [
        ("Bld_Garage", unreal.Vector(-1800.0, -1200.0, 200.0), unreal.Vector(8.0, 6.0, 4.0)),
        ("Bld_Cafe", unreal.Vector(-900.0, -1200.0, 180.0), unreal.Vector(6.0, 6.0, 3.6)),
        ("Bld_Dock", unreal.Vector(600.0, -1600.0, 220.0), unreal.Vector(10.0, 7.0, 4.4)),
        ("Bld_Bar", unreal.Vector(1400.0, 200.0, 180.0), unreal.Vector(7.0, 6.0, 3.6)),
        ("Bld_Board", unreal.Vector(-200.0, 900.0, 160.0), unreal.Vector(8.0, 5.0, 3.2)),
        ("Bld_Freight", unreal.Vector(1800.0, 1400.0, 240.0), unreal.Vector(9.0, 8.0, 4.8)),
        ("Bld_Rope", unreal.Vector(400.0, 1400.0, 140.0), unreal.Vector(12.0, 4.0, 2.8)),
    ]
    for label, loc, scale in buildings:
        cube_actor(label, loc, scale)

    cube_actor("Street_NS", unreal.Vector(0.0, 0.0, -40.0), unreal.Vector(6.0, 70.0, 0.4))
    cube_actor("Street_EW", unreal.Vector(0.0, 0.0, -40.0), unreal.Vector(70.0, 6.0, 0.4))

    site("S01", "Pell's Garage", KIND_RACKET, OWNER_PLAYER, "GarageBlock", 40, 0, unreal.Vector(-1800.0, -900.0, 40.0))
    site("S02", "Corvo Cafe", KIND_BUSINESS, OWNER_PLAYER, "GarageBlock", 55, 0, unreal.Vector(-900.0, -900.0, 40.0))
    site("S03", "Dock Warehouse A", KIND_RACKET, OWNER_CONTESTED, "DockBlock", 80, 2, unreal.Vector(600.0, -1300.0, 40.0))
    site("S04", "Hawser Bar", KIND_BUSINESS, OWNER_RIVAL, "BarBlock", 50, 1, unreal.Vector(1400.0, 500.0, 40.0))
    site("S05", "Call Box Corner", KIND_STREET, OWNER_NEUTRAL, "BarBlock", 0, 0, unreal.Vector(900.0, 500.0, 40.0))
    site("S06", "Levee Boarding", KIND_BUSINESS, OWNER_CONTESTED, "RopeBlock", 35, 1, unreal.Vector(-200.0, 1200.0, 40.0))
    site("S07", "Rope Walk", KIND_BLOCK, OWNER_RIVAL, "RopeBlock", 0, 0, unreal.Vector(400.0, 1700.0, 40.0))
    site("S08", "Freight Office", KIND_RACKET, OWNER_RIVAL, "FreightBlock", 70, 2, unreal.Vector(1800.0, 1700.0, 40.0))

    hood("H01", "Eddie Voss", ROLE_BAGMAN, OWNER_PLAYER, unreal.Vector(-1500.0, -600.0, 100.0))
    hood("H02", "Nicky Ferro", ROLE_ENFORCER, OWNER_PLAYER, unreal.Vector(-1200.0, -600.0, 100.0))
    hood("H03", "Nora Pell", ROLE_RECRUITER, OWNER_PLAYER, unreal.Vector(-1000.0, -400.0, 100.0))
    hood("R01", "Quinn", ROLE_ENFORCER, OWNER_RIVAL, unreal.Vector(1500.0, 800.0, 100.0))
    hood("R02", "Bridget", ROLE_BAGMAN, OWNER_RIVAL, unreal.Vector(1600.0, 1000.0, 100.0))

    spawn(unreal.LEWeekDirector, unreal.Vector(0.0, 0.0, 400.0), None, "WeekDirector")
    spawn(unreal.PlayerStart, unreal.Vector(0.0, 0.0, 200.0), None, "PlayerStart_City")
    spawn(unreal.DirectionalLight, unreal.Vector(0.0, 0.0, 2000.0), None, "Sun")
    spawn(unreal.SkyLight, unreal.Vector(0.0, 0.0, 1500.0), None, "Sky")

    # Optional nav bounds — skip if class missing in this build
    try:
        spawn(unreal.NavMeshBoundsVolume, unreal.Vector(0.0, 0.0, 0.0), unreal.Vector(50.0, 50.0, 20.0), "NavBounds")
    except Exception as exc:
        unreal.log_warning("NavMeshBoundsVolume skipped: " + str(exc))

    if not level_editor.save_current_level():
        raise RuntimeError("save failed")
    unreal.log("Saved isometric Levee greybox to " + MAP_PATH)


main()
