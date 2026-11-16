import unreal
le = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
le.load_level("/Game/Maps/Empire/Levee_Greybox")
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    lab = a.get_actor_label()
    if lab.startswith("Avenue_") or lab.startswith("Street_") or lab.startswith("Walk"):
        s = a.get_actor_scale3d()
        loc = a.get_actor_location()
        unreal.log("%s loc=(%.0f,%.0f,%.0f) scale=(%.2f,%.2f,%.2f)" % (lab, loc.x, loc.y, loc.z, abs(s.x), abs(s.y), abs(s.z)))
