"""Editor-side play smoke: load SP + RTS maps and assert boot-critical actors."""
import unreal

CHECKS = [
    (
        "/Game/Maps/Empire/Levee_Greybox",
        "SP",
        lambda labels, classes: "WeekDirector" in labels or any("LEWeekDirector" in c for c in classes),
    ),
    (
        "/Game/Maps/Empire/Levee_Skirmish",
        "RTS",
        lambda labels, classes: (
            any("LESkirmish" in c for c in classes)
            or "SkirmishDirector" in labels
        ),
    ),
]


def main():
    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    failures = []
    for path, name, ok_fn in CHECKS:
        # Prefer load over registry exists — commandlet registry can lag on fresh Content
        if not level_editor.load_level(path):
            failures.append("%s load fail" % name)
            continue
        actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
        labels = {a.get_actor_label() for a in actors}
        classes = [a.get_class().get_name() for a in actors]
        sites = sum(1 for c in classes if "LESiteActor" in c)
        if sites < 4 or not ok_fn(labels, classes):
            failures.append("%s weak sites=%d labels_has_sprites=%s" % (
                name, sites, "Dress_GameplaySprites_v1" in labels))
        else:
            unreal.log("PLAY SMOKE OK %s sites=%d actors=%d" % (name, sites, len(actors)))

    # Classes linked
    for path in (
        "/Script/LostEmpire.LEGameMode",
        "/Script/LostEmpire.LESkirmishGameMode",
        "/Script/LostEmpire.LEWeekDirector",
        "/Script/LostEmpire.LESkirmishDirector",
        "/Script/LostEmpire.LEStreetDirector",
        "/Script/LostEmpire.LEHoodlumCharacter",
        "/Script/LostEmpire.LEStreetCar",
    ):
        if unreal.load_class(None, path) is None:
            failures.append("class " + path)

    if failures:
        unreal.log_error("PLAY SMOKE FAIL " + "; ".join(failures))
        raise RuntimeError("Play smoke failed")
    unreal.log("PLAY SMOKE ALL OK")


main()
