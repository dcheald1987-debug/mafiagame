import unreal

def main():
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    les.load_level("/Game/Maps/Empire/Levee_Greybox")
    n = 0
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        lab = a.get_actor_label()
        # kill any remaining cards
        if lab.startswith(("FrontCard_","SideCard_","FacadeCard_","FacadeCube_","FacadePlane_")):
            unreal.get_editor_subsystem(unreal.EditorActorSubsystem).destroy_actor(a)
            n += 1
            continue
        for cls_name in ("DirectionalLightComponent", "LightComponent"):
            try:
                cls = getattr(unreal, cls_name)
                comps = a.get_components_by_class(cls)
            except Exception:
                comps = None
            if not comps:
                continue
            for c in comps:
                for prop in ("cast_shadows", "cast_shadow", "dynamic_shadow_distance_movable_light"):
                    try:
                        if prop.startswith("dynamic"):
                            c.set_editor_property(prop, 0.0)
                        else:
                            c.set_editor_property(prop, False)
                        n += 1
                    except Exception:
                        pass
        if lab.endswith("_Mass") and lab.startswith("Row_"):
            smc = a.static_mesh_component
            if smc:
                smc.set_cast_shadow(False)
                mat = smc.get_material(0)
                unreal.log("CHECK %s mat=%s cast=%s" % (lab, mat.get_name() if mat else None, smc.get_editor_property("cast_shadow") if hasattr(smc,"get_editor_property") else "?"))
    # also try actor class DirectionalLight
    for a in list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()):
        try:
            if isinstance(a, unreal.DirectionalLight):
                a.set_cast_shadows(False)
                n += 1
                unreal.log("DIRLIGHT " + a.get_actor_label())
        except Exception:
            pass
    les.save_current_level()
    unreal.log("SHADOW SWEEP OK n=%d" % n)

main()
