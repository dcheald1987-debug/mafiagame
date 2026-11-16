"""Destroy TextRender street labels + huge PP volume that wreck the map read."""
import unreal

MAP_PATH = "/Game/Maps/Empire/Levee_Greybox"


def main():
    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level_editor.load_level(MAP_PATH):
        raise RuntimeError("load failed")

    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    killed = 0
    for actor in list(sub.get_all_level_actors()):
        lab = actor.get_actor_label()
        cls = actor.get_class().get_name() if actor.get_class() else ""
        kill = False
        if lab.startswith("Label_"):
            kill = True
        if lab.startswith("PP_") or isinstance(actor, unreal.PostProcessVolume):
            kill = True
        if lab.startswith("Dress_"):
            kill = True
        if "TextRender" in cls:
            kill = True
        if kill:
            sub.destroy_actor(actor)
            killed += 1
            unreal.log("Killed %s" % lab)

    if not level_editor.save_current_level():
        raise RuntimeError("save failed")
    unreal.log("KILL LABELS OK — destroyed=%d" % killed)


main()
