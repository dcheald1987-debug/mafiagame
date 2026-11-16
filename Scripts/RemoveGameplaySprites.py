"""Strip flat image billboards — restore 3D Levee massing. Refs stay in Art/Refs only."""
import unreal

MAP_PATH = "/Game/Maps/Empire/Levee_Greybox"
FLAGS = ("Dress_GameplaySprites_v1", "Dress_GameplaySprites_v2")


def main():
    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level_editor.load_level(MAP_PATH):
        raise RuntimeError("load failed")

    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    removed = 0
    restored = 0
    for actor in list(sub.get_all_level_actors()):
        label = actor.get_actor_label()
        if label.startswith("Sprite_") or label in FLAGS:
            sub.destroy_actor(actor)
            removed += 1
            continue
        # Unhide period building cubes that sprite dress hid
        if label.startswith("Row_") and (
            "_Mass" in label
            or "_Shopfront" in label
            or "_Win_" in label
            or "_Cornice" in label
            or "_Roof" in label
            or "_Stoop" in label
            or label.count("_") == 1
        ):
            smc = getattr(actor, "static_mesh_component", None)
            if smc:
                smc.set_visibility(True, False)
                actor.set_actor_hidden_in_game(False)
                restored += 1

    if not level_editor.save_current_level():
        raise RuntimeError("save failed")
    unreal.log("REMOVED SPRITE BILLBOARDS removed=%d restored_meshes=%d" % (removed, restored))


main()
