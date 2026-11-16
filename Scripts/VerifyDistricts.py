import unreal

MAPS = {
    "Brickyard": "/Game/Maps/Empire/Brickyard_Greybox",
    "HaldenRow": "/Game/Maps/Empire/HaldenRow_Greybox",
    "AmesHill": "/Game/Maps/Empire/AmesHill_Greybox",
}


def main():
    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    failures = []
    for name, path in MAPS.items():
        if not unreal.EditorAssetLibrary.does_asset_exist(path):
            failures.append("%s missing asset" % name)
            continue
        if not level_editor.load_level(path):
            failures.append("%s load failed" % name)
            continue
        actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
        labels = {a.get_actor_label() for a in actors}
        sites = sum(1 for a in actors if isinstance(a, unreal.LESiteActor))
        hoods = sum(1 for a in actors if isinstance(a, unreal.LEHoodAgent))
        if "WeekDirector" not in labels:
            failures.append("%s no WeekDirector" % name)
        elif sites < 4 or hoods < 3:
            failures.append("%s weak content sites=%d hoods=%d" % (name, sites, hoods))
        else:
            unreal.log("DISTRICT OK %s sites=%d hoods=%d actors=%d" % (name, sites, hoods, len(actors)))

    if failures:
        unreal.log_error("DISTRICT FAIL " + "; ".join(failures))
        raise RuntimeError("District verification failed")
    unreal.log("DISTRICTS VERIFY OK")


main()
