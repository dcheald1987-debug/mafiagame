import unreal
level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
level_editor.load_level("/Game/Maps/Empire/Levee_Greybox")
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
# Prefer strongly contrasting road/ground mats
road = unreal.load_asset("/Game/Art/Empire/Materials/M_Roof_Tar")
if road is None:
    road = unreal.load_asset("/Game/Art/Empire/Materials/M_Asphalt")
walk = unreal.load_asset("/Game/Art/Empire/Materials/M_Sidewalk")
ground = unreal.load_asset("/Game/Art/Empire/Materials/M_Ground_Dirt")
if ground is None:
    ground = walk
cube = unreal.load_asset("/Engine/BasicShapes/Cube")
for a in list(sub.get_all_level_actors()):
    lab = a.get_actor_label()
    smc = getattr(a, "static_mesh_component", None)
    if smc is None:
        continue
    smc.set_static_mesh(cube)
    smc.set_cast_shadow(False)
    if lab == "Ground":
        a.set_actor_scale3d(unreal.Vector(200, 200, 1))
        smc.set_material(0, ground)
    elif lab.startswith("Avenue_") or lab.startswith("Street_"):
        # Thicker roads so they read above ground
        loc = a.get_actor_location()
        a.set_actor_location(unreal.Vector(loc.x, loc.y, -28.0), False, True)
        scale = a.get_actor_scale3d()
        a.set_actor_scale3d(unreal.Vector(scale.x, scale.y, 0.85))
        smc.set_material(0, road)
    elif lab.startswith("Walk"):
        loc = a.get_actor_location()
        a.set_actor_location(unreal.Vector(loc.x, loc.y, -24.0), False, True)
        smc.set_material(0, walk)
level_editor.save_current_level()
unreal.log("ROADS VISIBLE OK")
