import unreal

MAP_PATH = "/Game/Maps/Missions/C01_ServiceEntrance"


def ensure_actor(label, actor_class, location, rotation=None, scale=None):
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in subsystem.get_all_level_actors():
        if actor.get_actor_label() == label:
            return actor
    rot = rotation or unreal.Rotator(0.0, 0.0, 0.0)
    actor = subsystem.spawn_actor_from_class(actor_class, location, rot)
    actor.set_actor_label(label)
    if scale is not None:
        actor.set_actor_scale3d(scale)
    return actor


def main():
    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level_editor.load_level(MAP_PATH):
        raise RuntimeError("Could not load " + MAP_PATH)

    cube = unreal.load_asset("/Engine/BasicShapes/Cube")
    garage_road = ensure_actor(
        "Road_GarageTurn",
        unreal.StaticMeshActor,
        unreal.Vector(7600.0, -800.0, -50.0),
        scale=unreal.Vector(8.0, 16.0, 1.0),
    )
    garage_road.static_mesh_component.set_static_mesh(cube)

    ensure_actor(
        "PlayerStart_Dock",
        unreal.PlayerStart,
        unreal.Vector(200.0, 0.0, 80.0),
        unreal.Rotator(0.0, 0.0, 0.0),
    )

    if not level_editor.save_current_level():
        raise RuntimeError("Could not save " + MAP_PATH)
    unreal.log("C01 driveable setup: PlayerStart at dock, garage stub road.")


main()
