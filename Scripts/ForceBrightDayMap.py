"""Force Levee map lights/materials into a readable daytime baseline."""
import unreal

MAP_PATH = "/Game/Maps/Empire/Levee_Greybox"


def main():
    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level_editor.load_level(MAP_PATH):
        raise RuntimeError("load failed")

    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    muted = 0
    for actor in list(sub.get_all_level_actors()):
        lab = actor.get_actor_label()
        # Mute old map sun/sky that fight DayNight (runtime also mutes)
        if lab in ("Sun_Levee", "Sky_Levee", "Moon_Levee", "Atmosphere_Levee"):
            for cls in (unreal.DirectionalLightComponent, unreal.SkyLightComponent, unreal.SkyAtmosphereComponent):
                comp = actor.get_component_by_class(cls)
                if comp:
                    try:
                        comp.set_visibility(False)
                        if hasattr(comp, "set_intensity"):
                            comp.set_intensity(0.0)
                    except Exception:
                        pass
            muted += 1

        # Brighten PP volume if present
        if lab == "PP_LeveeReadable":
            try:
                settings = actor.get_editor_property("settings")
                settings.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
                settings.set_editor_property("auto_exposure_bias", 3.5)
                settings.set_editor_property("override_auto_exposure_method", True)
                settings.set_editor_property("override_auto_exposure_bias", True)
                actor.set_editor_property("settings", settings)
                actor.set_editor_property("unbound", True)
            except Exception as exc:
                unreal.log_warning("PP: %s" % exc)

        # Unhide common level pieces
        if lab.startswith("Row_") or lab.startswith("Avenue_") or lab.startswith("Street_") or lab in ("Ground",):
            actor.set_actor_hidden_in_game(False)

    if not level_editor.save_current_level():
        raise RuntimeError("save failed")
    unreal.log("FORCE BRIGHT DAY MAP OK — muted=%d" % muted)


main()
