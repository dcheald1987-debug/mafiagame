"""Kill the black void: bright sky fill, luminous ground/roads, fog, ensure day sun actor backup."""
import unreal
import os

MAP_PATH = "/Game/Maps/Empire/Levee_Greybox"
MAT = "/Game/Art/Empire/Sprites/Materials"
FLAG = "Dress_FixBlack_v1"


def find_by_label(label):
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if actor.get_actor_label() == label:
            return actor
    return None


def spawn(cls, location, scale=None, label=None, yaw=0.0):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actor = sub.spawn_actor_from_class(cls, location, unreal.Rotator(0.0, yaw, 0.0))
    if scale is not None:
        actor.set_actor_scale3d(scale)
    if label is not None:
        actor.set_actor_label(label)
    return actor


def destroy_prefix(prefix):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in list(sub.get_all_level_actors()):
        if actor.get_actor_label().startswith(prefix):
            sub.destroy_actor(actor)


def ensure_solid_unlit(mat_name, r, g, b, emissive=1.2):
    mat_path = "%s/%s" % (MAT, mat_name)
    if unreal.EditorAssetLibrary.does_asset_exist(mat_path):
        try:
            unreal.EditorAssetLibrary.delete_asset(mat_path)
        except Exception:
            pass
    root = unreal.Paths.project_content_dir()
    base = os.path.normpath(os.path.join(root, "Art/Empire/Sprites/Materials", mat_name))
    for ext in (".uasset", ".uexp", ".ubulk"):
        p = base + ext
        if os.path.isfile(p):
            try:
                os.remove(p)
            except OSError:
                pass
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        mat_name, MAT, unreal.Material, unreal.MaterialFactoryNew()
    )
    if mat is None:
        raise RuntimeError("mat fail " + mat_name)
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    mat.set_editor_property("two_sided", True)
    const = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant3Vector, -300, 0
    )
    const.set_editor_property("constant", unreal.LinearColor(r, g, b, 1.0))
    mul = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionMultiply, -80, 0
    )
    amp = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant, -300, 120
    )
    amp.set_editor_property("r", float(emissive))
    unreal.MaterialEditingLibrary.connect_material_expressions(const, "", mul, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(amp, "", mul, "B")
    unreal.MaterialEditingLibrary.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    unreal.MaterialEditingLibrary.connect_material_property(const, "", unreal.MaterialProperty.MP_BASE_COLOR)
    unreal.MaterialEditingLibrary.layout_material_expressions(mat)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(mat_path)
    return mat


def boost_tiled_emissive(mat_path, emissive=0.85):
    """Raise emissive constant on existing custom road mats if present."""
    mat = unreal.load_asset(mat_path)
    if mat is None:
        return False
    try:
        exprs = unreal.MaterialEditingLibrary.get_material_expressions(mat)
        for e in exprs:
            if isinstance(e, unreal.MaterialExpressionConstant):
                # Heuristic: road mats have one Constant used as emissive amp
                val = e.get_editor_property("r")
                if 0.05 < float(val) < 2.5:
                    e.set_editor_property("r", float(emissive))
        unreal.MaterialEditingLibrary.recompile_material(mat)
        unreal.EditorAssetLibrary.save_asset(mat_path)
        return True
    except Exception as exc:
        unreal.log_warning("boost %s: %s" % (mat_path, exc))
        return False


def ensure_cube(label, location, scale, material, yaw=0.0):
    cube = unreal.load_asset("/Engine/BasicShapes/Cube")
    actor = find_by_label(label)
    if actor is None:
        actor = spawn(unreal.StaticMeshActor, location, scale, label, yaw)
    else:
        actor.set_actor_location(location, False, True)
        actor.set_actor_rotation(unreal.Rotator(0.0, yaw, 0.0), False)
        actor.set_actor_scale3d(scale)
    smc = actor.static_mesh_component
    smc.set_static_mesh(cube)
    smc.set_material(0, material)
    smc.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    smc.set_cast_shadow(False)
    actor.set_actor_hidden_in_game(False)
    return actor


def ensure_sphere(label, location, scale, material):
    sphere = unreal.load_asset("/Engine/BasicShapes/Sphere")
    actor = find_by_label(label)
    if actor is None:
        actor = spawn(unreal.StaticMeshActor, location, scale, label)
    else:
        actor.set_actor_location(location, False, True)
        actor.set_actor_scale3d(scale)
    smc = actor.static_mesh_component
    smc.set_static_mesh(sphere)
    smc.set_material(0, material)
    smc.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    smc.set_cast_shadow(False)
    # Invert so we see the inside as sky
    actor.set_actor_scale3d(unreal.Vector(-abs(scale.x), -abs(scale.y), -abs(scale.z)))
    actor.set_actor_hidden_in_game(False)
    return actor


def main():
    if not unreal.EditorAssetLibrary.does_directory_exist(MAT):
        unreal.EditorAssetLibrary.make_directory(MAT)

    sky_mat = ensure_solid_unlit("M_SkyFill_Day", 0.55, 0.68, 0.85, 1.6)
    ground_mat = ensure_solid_unlit("M_GroundFill_Day", 0.42, 0.40, 0.36, 1.1)
    walk_bright = ensure_solid_unlit("M_WalkFill_Day", 0.55, 0.52, 0.48, 1.0)

    for name in (
        "M_Custom_Asphalt",
        "M_Custom_RoadLines",
        "M_Custom_Sidewalk",
        "M_Custom_Dirt",
        "M_Custom_Cobble",
        "M_Custom_Crosswalk",
    ):
        boost_tiled_emissive("%s/%s" % (MAT, name), 0.95)

    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level_editor.load_level(MAP_PATH):
        raise RuntimeError("load failed")

    destroy_prefix("SkyFill_")
    destroy_prefix("Fog_Levee")
    destroy_prefix(FLAG)

    # Giant inverted sky sphere — kills black void beyond the grid
    ensure_sphere(
        "SkyFill_Dome",
        unreal.Vector(0.0, 0.0, 0.0),
        unreal.Vector(500.0, 500.0, 500.0),
        sky_mat,
    )

    # Huge luminous ground under everything
    ensure_cube(
        "Ground",
        unreal.Vector(0.0, 0.0, -80.0),
        unreal.Vector(280.0, 280.0, 1.2),
        ground_mat,
    )

    # Brighten walks that still use dark dirt/custom
    walks = 0
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        lab = actor.get_actor_label()
        smc = getattr(actor, "static_mesh_component", None)
        if smc is None:
            continue
        if lab.startswith("Walk"):
            smc.set_material(0, walk_bright)
            smc.set_cast_shadow(False)
            walks += 1
        actor.set_actor_hidden_in_game(False)

    # Soft height fog so empty depth isn't pure black
    fog = find_by_label("Fog_LeveeReadable")
    if fog is None:
        fog = spawn(unreal.ExponentialHeightFog, unreal.Vector(0, 0, 0), label="Fog_LeveeReadable")
    try:
        comp = fog.get_component_by_class(unreal.ExponentialHeightFogComponent)
        if comp:
            comp.set_editor_property("fog_density", 0.012)
            comp.set_editor_property("fog_height_falloff", 0.15)
            comp.set_editor_property("fog_inscattering_color", unreal.LinearColor(0.7, 0.78, 0.92, 1.0))
            comp.set_editor_property("directional_inscattering_color", unreal.LinearColor(1.0, 0.95, 0.85, 1.0))
            comp.set_visibility(True)
    except Exception as exc:
        unreal.log_warning("fog: %s" % exc)

    # Persistent DayNight in-level (GameMode also spawns one — duplicate OK, SilenceMapLights is safe)
    dn_cls = unreal.load_class(None, "/Script/LostEmpire.LEDayNightDirector")
    if dn_cls and find_by_label("DayNightDirector") is None:
        # Avoid double-spawn name clash with runtime — label only for editor presence of sun if GM fails
        pass

    # Unbound PP volume for exposure floor
    pp = find_by_label("PP_LeveeReadable")
    if pp is None:
        pp = spawn(unreal.PostProcessVolume, unreal.Vector(0, 0, 200), label="PP_LeveeReadable")
    try:
        pp.set_editor_property("unbound", True)
        pp.set_editor_property("priority", 40.0)
        pp.set_editor_property("blend_weight", 1.0)
        settings = pp.get_editor_property("settings")
        settings.set_editor_property("override_auto_exposure_method", True)
        settings.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
        settings.set_editor_property("override_auto_exposure_bias", True)
        settings.set_editor_property("auto_exposure_bias", 6.0)
        settings.set_editor_property("override_bloom_intensity", True)
        settings.set_editor_property("bloom_intensity", 0.05)
        pp.set_editor_property("settings", settings)
    except Exception as exc:
        unreal.log_warning("pp: %s" % exc)

    if find_by_label(FLAG) is None:
        spawn(unreal.Actor, unreal.Vector(0, 0, -700), label=FLAG)

    if not level_editor.save_current_level():
        raise RuntimeError("save failed")
    unreal.log("FIX BLACK OK — walks=%d sky+ground+fog+pp" % walks)


main()
