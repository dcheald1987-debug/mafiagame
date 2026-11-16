import unreal
MAP = "/Game/Maps/Empire/Levee_Greybox"
le = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
le.load_level(MAP)
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
counts = {}
interesting = []
for a in sub.get_all_level_actors():
    lab = a.get_actor_label()
    cls = a.get_class().get_name()
    counts[cls] = counts.get(cls, 0) + 1
    if any(x in lab for x in ("Sun", "Sky", "Day", "Ground", "PP_", "Atmosphere", "Row_Garage", "Avenue_0", "Facade", "Sprite")):
        smc = getattr(a, "static_mesh_component", None)
        mat = None
        mesh = None
        scale = a.get_actor_scale3d()
        if smc:
            mesh = smc.static_mesh.get_name() if smc.static_mesh else None
            try:
                m0 = smc.get_material(0)
                mat = m0.get_name() if m0 else None
            except Exception:
                pass
        interesting.append("%s | %s | mesh=%s mat=%s scale=%s hidden=%s" % (lab, cls, mesh, mat, scale, a.is_hidden_ed()))
unreal.log("=== AUDIT INTERESTING ===")
for line in sorted(interesting):
    unreal.log(line)
unreal.log("=== CLASS COUNTS ===")
for k,v in sorted(counts.items(), key=lambda kv: -kv[1])[:25]:
    unreal.log("%s=%d" % (k,v))
# DayNight class search
for path in (
    "/Script/LostEmpire.LEDayNightDirector",
    "/Game/Blueprints/Empire/BP_DayNight",
):
    c = unreal.load_object(None, path) or unreal.load_class(None, path)
    unreal.log("class %s -> %s" % (path, c))
