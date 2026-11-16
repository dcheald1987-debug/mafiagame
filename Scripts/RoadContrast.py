import unreal
level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
level_editor.load_level("/Game/Maps/Empire/Levee_Greybox")
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
asphalt = unreal.load_asset("/Game/Art/Empire/Materials/M_Asphalt")
sidewalk = unreal.load_asset("/Game/Art/Empire/Materials/M_Sidewalk")
cube = unreal.load_asset("/Engine/BasicShapes/Cube")
for a in sub.get_all_level_actors():
    lab = a.get_actor_label()
    smc = getattr(a, "static_mesh_component", None)
    if smc is None:
        continue
    if lab == "Ground":
        a.set_actor_scale3d(unreal.Vector(180, 180, 1))
        smc.set_static_mesh(cube)
        smc.set_material(0, sidewalk)
        unreal.log("Ground scale=%s" % a.get_actor_scale3d())
    elif lab.startswith("Avenue_") or lab.startswith("Street_"):
        smc.set_material(0, asphalt)
        smc.set_cast_shadow(False)
    elif lab.startswith("Walk"):
        smc.set_material(0, sidewalk)
level_editor.save_current_level()
unreal.log("ROADS CONTRAST OK")
