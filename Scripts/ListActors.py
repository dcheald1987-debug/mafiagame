import unreal
level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
level_editor.load_level("/Game/Maps/Empire/Levee_Greybox")
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
n = 0
for a in sub.get_all_level_actors():
    lab = a.get_actor_label()
    cls = a.get_class().get_name()
    smc = getattr(a, "static_mesh_component", None)
    mesh = smc.static_mesh.get_name() if smc and smc.static_mesh else "-"
    scale = a.get_actor_scale3d()
    unreal.log("ACTOR %s cls=%s mesh=%s scale=(%.2f,%.2f,%.2f)" % (lab, cls, mesh, abs(scale.x), abs(scale.y), abs(scale.z)))
    n += 1
unreal.log("ACTOR COUNT %d" % n)
