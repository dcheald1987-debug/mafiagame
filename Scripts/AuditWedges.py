"""List likely wedge sources: planes, huge bounds, directional lights, thin sheets."""
import unreal

MAP_PATH = "/Game/Maps/Empire/Levee_Greybox"


def main():
    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level_editor.load_level(MAP_PATH):
        raise RuntimeError("load failed")

    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    planes = 0
    thin = 0
    huge = 0
    dirs = 0
    for actor in sub.get_all_level_actors():
        lab = actor.get_actor_label()
        cls = actor.get_class().get_name() if actor.get_class() else "?"
        if isinstance(actor, unreal.DirectionalLight) or "DirectionalLight" in cls:
            dirs += 1
            unreal.log("DIRLIGHT %s class=%s" % (lab, cls))
        try:
            dlc = actor.get_component_by_class(unreal.DirectionalLightComponent)
            if dlc:
                dirs += 1
                unreal.log("DIRCOMP %s intensity=%s vis=%s" % (lab, dlc.intensity, dlc.is_visible()))
        except Exception:
            pass

        smc = getattr(actor, "static_mesh_component", None)
        if smc is None:
            continue
        mesh = smc.static_mesh
        if mesh is None:
            continue
        mname = mesh.get_name()
        scale = actor.get_actor_scale3d()
        loc = actor.get_actor_location()
        sx, sy, sz = abs(scale.x), abs(scale.y), abs(scale.z)
        extents = sorted([sx, sy, sz])
        # thin sheet: one axis tiny, others large
        if extents[0] < 0.2 and extents[2] > 5.0:
            thin += 1
            unreal.log("THIN %s mesh=%s scale=(%.2f,%.2f,%.2f) loc=(%.0f,%.0f,%.0f)" % (
                lab, mname, sx, sy, sz, loc.x, loc.y, loc.z))
        if "Plane" in mname or "plane" in mname:
            planes += 1
            unreal.log("PLANE %s scale=(%.2f,%.2f,%.2f)" % (lab, sx, sy, sz))
        if max(sx, sy, sz) > 40.0:
            huge += 1
            unreal.log("HUGE %s mesh=%s scale=(%.2f,%.2f,%.2f)" % (lab, mname, sx, sy, sz))

    unreal.log("AUDIT OK planes=%d thin=%d huge=%d dirs=%d" % (planes, thin, huge, dirs))


main()
