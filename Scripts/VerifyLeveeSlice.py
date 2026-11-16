import unreal

MAP_PATH = "/Game/Maps/Empire/Levee_Greybox"

REQUIRED_SITES = {"S01", "S02", "S03", "S04", "S05", "S06", "S07", "S08"}
REQUIRED_HOODS = {"H01", "H02", "H03", "R01", "R02"}
REQUIRED_LABELS = {
    "WeekDirector",
    "PlayerStart_City",
    "Stub_Brickyard",
    "Roof_Garage",
    "Label_Riverfront",
    "Dress_Levee_v2",
    "Water_Dock",
    "Walk_NS_W",
    "Pad_GarageBlock",
    "Label_Barrow",
    "Sun_Levee",
}


def main():
    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level_editor.load_level(MAP_PATH):
        raise RuntimeError("Could not load " + MAP_PATH)

    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    labels = {a.get_actor_label() for a in actors}

    sites = set()
    hoods = set()
    for actor in actors:
        if isinstance(actor, unreal.LESiteActor):
            sites.add(str(actor.get_editor_property("site_id")))
        elif isinstance(actor, unreal.LEHoodAgent):
            hoods.add(str(actor.get_editor_property("hood_id")))

    missing_labels = sorted(REQUIRED_LABELS - labels)
    missing_sites = sorted(REQUIRED_SITES - sites)
    missing_hoods = sorted(REQUIRED_HOODS - hoods)

    if missing_labels or missing_sites or missing_hoods:
        unreal.log_error(
            "SLICE FAIL labels=%s sites=%s hoods=%s"
            % (missing_labels, missing_sites, missing_hoods)
        )
        raise RuntimeError("Levee slice verification failed")

    unreal.log(
        "SLICE OK sites=%d hoods=%d actors=%d dressed=yes"
        % (len(sites), len(hoods), len(actors))
    )


main()
