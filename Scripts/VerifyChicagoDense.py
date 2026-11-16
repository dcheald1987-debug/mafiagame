"""Count dense landmarks + Fab street lamps on Levee."""
import unreal

MAP_PATH = "/Game/Maps/Empire/Levee_Greybox"


def main():
    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level_editor.load_level(MAP_PATH):
        raise RuntimeError("load failed")
    lm = 0
    lamps = 0
    lights = 0
    flags = []
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        lab = actor.get_actor_label()
        if lab.startswith("LM_") and lab.endswith("_Mass"):
            lm += 1
        if lab.startswith("FabLamp_"):
            lamps += 1
        if lab.startswith("FabLight_"):
            lights += 1
        if lab.startswith("Dress_ChicagoDense") or lab.startswith("Dress_FabStreetLights"):
            flags.append(lab)
    mesh = unreal.load_asset("/Game/Art/Empire/FabStreetLights/SM_StreetLight")
    unreal.log(
        "VERIFY CHICAGO — landmarks=%d lamps=%d lights=%d mesh=%s flags=%s"
        % (lm, lamps, lights, mesh is not None, flags)
    )


main()
