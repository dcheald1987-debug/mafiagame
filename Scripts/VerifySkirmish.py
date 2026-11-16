import unreal

MAP = "/Game/Maps/Empire/Levee_Skirmish"


def main():
    if not unreal.EditorAssetLibrary.does_asset_exist(MAP):
        raise RuntimeError("Levee_Skirmish missing — run CreateSkirmishLevee.py")

    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level_editor.load_level(MAP):
        raise RuntimeError("Failed to load Levee_Skirmish")

    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    sites = sum(1 for a in actors if "LESiteActor" in a.get_class().get_name())
    week = sum(1 for a in actors if "LEWeekDirector" in a.get_class().get_name())
    labels = {a.get_actor_label() for a in actors}

    gm_ok = False
    world = unreal.EditorLevelLibrary.get_editor_world()
    if world:
        ws = world.get_world_settings()
        gm = ws.get_editor_property("default_game_mode")
        if gm and "LESkirmishGameMode" in str(gm):
            gm_ok = True

    if sites < 4:
        raise RuntimeError("Skirmish sites=%d" % sites)
    if week > 0:
        unreal.log_warning("WeekDirector still present — runtime disables it")
    if not gm_ok and "SkirmishDirector" not in labels:
        unreal.log_warning("No GM override and no SkirmishDirector actor — GameMode must spawn director")

    # Class availability
    for path in (
        "/Script/LostEmpire.LESkirmishGameMode",
        "/Script/LostEmpire.LESkirmishDirector",
        "/Script/LostEmpire.LESkirmishUnit",
        "/Script/LostEmpire.LESkirmishPlayerController",
        "/Script/LostEmpire.LESkirmishHUD",
    ):
        if unreal.load_class(None, path) is None:
            raise RuntimeError("Missing class %s" % path)

    unreal.log("SKIRMISH VERIFY OK sites=%d gm=%s" % (sites, gm_ok))


main()
