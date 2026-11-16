import unreal
level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
level_editor.load_level("/Game/Maps/Empire/Levee_Greybox")
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
killed=0
for a in list(sub.get_all_level_actors()):
    lab=a.get_actor_label()
    if lab.endswith("_Base") or lab.startswith("Label_") or lab.startswith("PP_") or "TextRender" in (a.get_class().get_name() if a.get_class() else ""):
        sub.destroy_actor(a); killed+=1
level_editor.save_current_level()
unreal.log("CLEAN BASE OK killed=%d" % killed)
