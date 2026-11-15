import unreal

MAP_PATH = "/Game/Maps/Missions/C01_ServiceEntrance"


def spawn(actor_class, location, scale=None, label=None):
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actor = subsystem.spawn_actor_from_class(actor_class, location, unreal.Rotator(0.0, 0.0, 0.0))
    if scale is not None:
        actor.set_actor_scale3d(scale)
    if label is not None:
        actor.set_actor_label(label)
    return actor


def zone(name, zone_id, location, scale):
    actor = spawn(unreal.LERouteZone, location, scale, name)
    actor.set_editor_property("zone_id", zone_id)
    return actor


def main():
    unreal.EditorAssetLibrary.make_directory("/Game/Maps/Missions")
    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if unreal.EditorAssetLibrary.does_asset_exist(MAP_PATH):
        if not level_editor.load_level(MAP_PATH):
            raise RuntimeError("Could not load " + MAP_PATH)
    elif not level_editor.new_level(MAP_PATH):
        raise RuntimeError("Could not create " + MAP_PATH)

    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    existing = {actor.get_actor_label() for actor in actor_subsystem.get_all_level_actors()}
    if "C01_Director" in existing:
        unreal.log("C01 blockout already populated.")
        return

    cube = unreal.load_asset("/Engine/BasicShapes/Cube")
    road = spawn(
        unreal.StaticMeshActor,
        unreal.Vector(4500.0, 0.0, -50.0),
        unreal.Vector(90.0, 10.0, 1.0),
        "Road_HillToGarage",
    )
    road.static_mesh_component.set_static_mesh(cube)

    avenue = spawn(
        unreal.StaticMeshActor,
        unreal.Vector(2000.0, 1800.0, -50.0),
        unreal.Vector(8.0, 28.0, 1.0),
        "Road_Avenue",
    )
    avenue.static_mesh_component.set_static_mesh(cube)

    spawn(unreal.LEServiceEntranceDirector, unreal.Vector(0.0, 0.0, 120.0), None, "C01_Director")
    spawn(unreal.DirectionalLight, unreal.Vector(0.0, 0.0, 800.0), None, "KeyLight")
    spawn(unreal.SkyLight, unreal.Vector(0.0, 0.0, 400.0), None, "Sky")

    # Distances are a greybox of the drive, not the final city.
    # Hill is the long run. Avenue is the wrong turn. Cut, then garage to the left.
    zone("Zone_AmesHill", "AmesHill", unreal.Vector(1800.0, 0.0, 150.0), unreal.Vector(36.0, 14.0, 8.0))
    zone("Zone_Avenue", "Avenue", unreal.Vector(2000.0, 1800.0, 150.0), unreal.Vector(10.0, 24.0, 8.0))
    zone("Zone_Cut", "Cut", unreal.Vector(7200.0, 0.0, 150.0), unreal.Vector(8.0, 14.0, 8.0))
    zone("Zone_MissedTurn", "MissedTurn", unreal.Vector(9200.0, 0.0, 150.0), unreal.Vector(6.0, 14.0, 8.0))
    zone("Zone_Garage", "Garage", unreal.Vector(7600.0, -1600.0, 150.0), unreal.Vector(8.0, 8.0, 8.0))

    if not level_editor.save_current_level():
        raise RuntimeError("Could not save " + MAP_PATH)
    unreal.log("Saved C01 blockout to " + MAP_PATH)


main()
