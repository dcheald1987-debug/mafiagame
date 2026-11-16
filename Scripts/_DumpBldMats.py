import unreal
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level("/Game/Maps/Empire/Levee_Greybox")
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    lab = a.get_actor_label()
    if not (lab.startswith("Row_") or lab.startswith("Facade") or lab.startswith("BlockPad")):
        continue
    smc = getattr(a, "static_mesh_component", None)
    mat = None
    mesh = None
    if smc:
        mesh = smc.static_mesh.get_name() if smc.static_mesh else "None"
        try:
            m = smc.get_material(0)
            mat = m.get_name() if m else "None"
        except Exception:
            mat = "?"
    loc = a.get_actor_location()
    sc = a.get_actor_scale3d()
    rot = a.get_actor_rotation()
    print("A %s mesh=%s mat=%s xy=(%.0f,%.0f) scale=(%.3f,%.3f,%.3f) yaw=%.0f" % (
        lab, mesh, mat, loc.x, loc.y, sc.x, sc.y, sc.z, rot.yaw))
