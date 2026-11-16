import unreal

SRC = "/Game/Maps/Empire/Levee_Greybox"
DST = "/Game/Maps/Empire/Levee_Skirmish"
GM_PATH = "/Script/LostEmpire.LESkirmishGameMode"


def main():
    if not unreal.EditorAssetLibrary.does_asset_exist(SRC):
        raise RuntimeError("Levee_Greybox missing")

    if unreal.EditorAssetLibrary.does_asset_exist(DST):
        unreal.EditorAssetLibrary.delete_asset(DST)

    if not unreal.EditorLevelLibrary.new_level_from_template(DST, SRC):
        raise RuntimeError("new_level_from_template failed")

    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    level_editor.load_level(DST)

    actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in list(actor_sub.get_all_level_actors()):
        cname = a.get_class().get_name()
        label = a.get_actor_label()
        if (
            "LEWeekDirector" in cname
            or label == "WeekDirector"
            or "LEHoodAgent" in cname
            or "LESkirmishDirector" in cname
        ):
            a.destroy_actor()

    gm_cls = unreal.load_class(None, GM_PATH)
    world = unreal.EditorLevelLibrary.get_editor_world()
    if world and gm_cls:
        ws = world.get_world_settings()
        ws.set_editor_property("default_game_mode", gm_cls)
        unreal.log("Levee_Skirmish GameMode -> LESkirmishGameMode")
    else:
        unreal.log_warning("Could not set GameMode override; use ?game=LESkirmishGameMode")

    director_cls = unreal.load_class(None, "/Script/LostEmpire.LESkirmishDirector")
    if director_cls:
        d = actor_sub.spawn_actor_from_class(director_cls, unreal.Vector(0.0, 0.0, 80.0))
        if d:
            d.set_actor_label("SkirmishDirector")

    level_editor.save_current_level()

    sites = sum(1 for a in actor_sub.get_all_level_actors() if "LESiteActor" in a.get_class().get_name())
    has_gm = gm_cls is not None
    unreal.log("SKIRMISH MAP OK sites=%d gm=%s" % (sites, has_gm))
    if sites < 4:
        raise RuntimeError("Skirmish map too thin")
    unreal.log("SKIRMISH CREATE OK")


main()
