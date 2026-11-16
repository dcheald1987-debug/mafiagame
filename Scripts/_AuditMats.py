import unreal

def mat_info(path):
    m = unreal.load_asset(path)
    if not m:
        unreal.log("MISSING " + path)
        return
    try:
        shading = m.get_editor_property("shading_model")
        blend = m.get_editor_property("blend_mode")
    except Exception as e:
        shading, blend = str(e), "?"
    exprs = []
    try:
        for e in unreal.MaterialEditingLibrary.get_material_expressions(m):
            n = e.get_class().get_name()
            extra = ""
            if isinstance(e, unreal.MaterialExpressionTextureSample):
                t = e.get_editor_property("texture")
                extra = " tex=%s" % (t.get_name() if t else "NONE")
            elif isinstance(e, unreal.MaterialExpressionConstant):
                extra = " r=%s" % e.get_editor_property("r")
            elif isinstance(e, unreal.MaterialExpressionConstant3Vector):
                c = e.get_editor_property("constant")
                extra = " c=%s" % c
            exprs.append(n + extra)
    except Exception as ex:
        exprs = [str(ex)]
    unreal.log("MAT %s shade=%s blend=%s exprs=%s" % (path, shading, blend, exprs))

for p in (
    "/Game/Art/Empire/Sprites/Materials/M_Bld_Bld_Garage",
    "/Game/Art/Empire/Sprites/Materials/M_Bld_Facade_A",
    "/Game/Art/Empire/Sprites/Materials/M_Custom_Asphalt",
    "/Game/Art/Empire/Sprites/Materials/M_Custom_RoadLines",
    "/Game/Art/Empire/Sprites/Materials/M_Custom_Dirt",
    "/Game/Art/Empire/Sprites/Materials/M_GroundFill_Day",
    "/Game/Art/Empire/Sprites/Materials/M_SkyFill_Day",
    "/Game/Art/Empire/Materials/M_Roof_Slate",
    "/Game/Art/Empire/FabRoads/asphalt",
):
    mat_info(p)

# textures
for t in (
    "/Game/Art/Empire/Sprites/Textures/T_Bld_Garage",
    "/Game/Art/Empire/Sprites/Textures/T_Facade_A",
    "/Game/Art/Empire/Sprites/Textures/T_Road_Asphalt",
    "/Game/Art/Empire/Sprites/Textures/T_Road_Lines",
    "/Game/Art/Empire/Sprites/Textures/T_Sidewalk",
):
    a = unreal.load_asset(t)
    unreal.log("TEX %s -> %s" % (t, a.get_name() if a else "NONE"))

# sample actor mats on map
le = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
le.load_level("/Game/Maps/Empire/Levee_Greybox")
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for want in ("Ground", "Avenue_0", "Row_Garage_Mass", "FacadeCube_Row_Garage_S", "Walk_0", "SkyFill_Dome"):
    for a in sub.get_all_level_actors():
        if a.get_actor_label() == want:
            smc = getattr(a, "static_mesh_component", None)
            m = smc.get_material(0) if smc else None
            unreal.log("ACTOR %s mat=%s hidden=%s" % (want, m.get_name() if m else None, a.actor_is_being_destroyed()))
