"""Dress Levee toward Gangsters 2 plate: light warm roads, darker walks, curbs, HDRI sky."""
import unreal
import os
import math

MAP_PATH = "/Game/Maps/Empire/Levee_Greybox"
MAT = "/Game/Art/Empire/Sprites/Materials"
FLAG = "Dress_GangstersLook_v1"


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


def wipe_mat(name):
    path = "%s/%s" % (MAT, name)
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        try:
            unreal.EditorAssetLibrary.delete_asset(path)
        except Exception:
            pass
    root = unreal.Paths.project_content_dir()
    base = os.path.normpath(os.path.join(root, "Art/Empire/Sprites/Materials", name))
    for ext in (".uasset", ".uexp", ".ubulk"):
        p = base + ext
        if os.path.isfile(p):
            try:
                os.remove(p)
            except OSError:
                pass


def solid_unlit(name, r, g, b, emissive=2.2):
    wipe_mat(name)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MAT, unreal.Material, unreal.MaterialFactoryNew()
    )
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    c = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant3Vector, -300, 0
    )
    c.set_editor_property("constant", unreal.LinearColor(r, g, b, 1.0))
    mul = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionMultiply, -80, 0
    )
    amp = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant, -300, 100
    )
    amp.set_editor_property("r", float(emissive))
    unreal.MaterialEditingLibrary.connect_material_expressions(c, "", mul, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(amp, "", mul, "B")
    unreal.MaterialEditingLibrary.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset("%s/%s" % (MAT, name))
    return mat


def tex_emissive(name, tex, boost=3.5, lift=0.22, tile_u=4.0, tile_v=4.0):
    wipe_mat(name)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MAT, unreal.Material, unreal.MaterialFactoryNew()
    )
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    sample = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionTextureSample, -520, 0
    )
    sample.set_editor_property("texture", tex)
    uv = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionTextureCoordinate, -760, 0
    )
    mul_uv = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionMultiply, -640, 0
    )
    scale = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant2Vector, -760, 100
    )
    scale.set_editor_property("r", float(tile_u))
    scale.set_editor_property("g", float(tile_v))
    unreal.MaterialEditingLibrary.connect_material_expressions(uv, "", mul_uv, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(scale, "", mul_uv, "B")
    unreal.MaterialEditingLibrary.connect_material_expressions(mul_uv, "", sample, "Coordinates")
    mul = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionMultiply, -300, 0
    )
    amp = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant, -420, 120
    )
    amp.set_editor_property("r", float(boost))
    unreal.MaterialEditingLibrary.connect_material_expressions(sample, "RGB", mul, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(amp, "", mul, "B")
    add = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionAdd, -140, 0
    )
    lift_c = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant3Vector, -300, 140
    )
    # Warm beige lift — Gangsters asphalt reads light gray-beige
    lift_c.set_editor_property("constant", unreal.LinearColor(lift * 1.15, lift, lift * 0.85, 1.0))
    unreal.MaterialEditingLibrary.connect_material_expressions(mul, "", add, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(lift_c, "", add, "B")
    unreal.MaterialEditingLibrary.connect_material_property(add, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset("%s/%s" % (MAT, name))
    return mat


def set_mat(actor, material):
    if not actor or not material:
        return False
    smc = getattr(actor, "static_mesh_component", None)
    if not smc:
        return False
    smc.set_material(0, material)
    smc.set_cast_shadow(False)
    actor.set_actor_hidden_in_game(False)
    return True


def ensure_cube(label, loc, scale, material, yaw=0.0):
    cube = unreal.load_asset("/Engine/BasicShapes/Cube")
    actor = find_by_label(label)
    if actor is None:
        actor = spawn(unreal.StaticMeshActor, loc, scale, label, yaw)
    else:
        actor.set_actor_location(loc, False, True)
        actor.set_actor_rotation(unreal.Rotator(0, yaw, 0), False)
        actor.set_actor_scale3d(scale)
    smc = actor.static_mesh_component
    smc.set_static_mesh(cube)
    smc.set_material(0, material)
    smc.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    smc.set_cast_shadow(False)
    actor.set_actor_hidden_in_game(False)
    return actor


def destroy_prefix(prefix):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in list(sub.get_all_level_actors()):
        if actor.get_actor_label().startswith(prefix):
            sub.destroy_actor(actor)


def main():
    if not unreal.EditorAssetLibrary.does_directory_exist(MAT):
        unreal.EditorAssetLibrary.make_directory(MAT)

    asphalt_tex = unreal.load_asset("/Game/Art/Empire/Sprites/Textures/T_Road_Asphalt")
    walk_tex = unreal.load_asset("/Game/Art/Empire/Sprites/Textures/T_Sidewalk")
    cobble_tex = unreal.load_asset("/Game/Art/Empire/Sprites/Textures/T_Road_Cobble")

    # Light warm road (Gangsters plate) — heavy lift so it never reads black
    if asphalt_tex:
        road = tex_emissive("M_Gang_Asphalt", asphalt_tex, boost=6.5, lift=0.38, tile_u=5.0, tile_v=5.0)
    else:
        road = solid_unlit("M_Gang_Asphalt", 0.62, 0.58, 0.52, 2.4)

    if walk_tex:
        walk = tex_emissive("M_Gang_Walk", walk_tex, boost=4.5, lift=0.20, tile_u=4.0, tile_v=4.0)
    else:
        walk = solid_unlit("M_Gang_Walk", 0.48, 0.46, 0.44, 2.0)

    if cobble_tex:
        cobble = tex_emissive("M_Gang_Cobble", cobble_tex, boost=4.0, lift=0.18, tile_u=3.0, tile_v=3.0)
    else:
        cobble = walk

    curb = solid_unlit("M_Gang_Curb", 0.72, 0.70, 0.66, 2.2)
    ground = solid_unlit("M_Gang_Ground", 0.50, 0.48, 0.42, 2.0)
    roof = solid_unlit("M_Gang_Roof", 0.42, 0.40, 0.38, 1.9)

    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level_editor.load_level(MAP_PATH):
        raise RuntimeError("load failed")

    destroy_prefix("Curb_")
    destroy_prefix(FLAG)

    roads = walks = curbs = blds = 0
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in sub.get_all_level_actors():
        lab = actor.get_actor_label()
        if lab.startswith("Avenue_") or lab.startswith("Street_"):
            if set_mat(actor, road):
                roads += 1
        elif lab.startswith("Walk"):
            if set_mat(actor, walk):
                walks += 1
        elif lab == "Ground":
            set_mat(actor, ground)
        elif lab.startswith("Crosswalk_") or lab.startswith("RoadStripe_"):
            set_mat(actor, road)
        elif lab.startswith("CobblePatch_"):
            set_mat(actor, cobble)
        elif lab.endswith("_Roof"):
            if set_mat(actor, roof):
                blds += 1
        elif lab.endswith("_Mass") or lab.startswith("FacadeCube_"):
            # Keep existing bright façade textures; just ensure visible
            actor.set_actor_hidden_in_game(False)
            smc = getattr(actor, "static_mesh_component", None)
            if smc:
                smc.set_cast_shadow(False)
            blds += 1

    # Thin curb lips at main intersections (Gangsters edge read)
    for i, (x, y) in enumerate([
        (0.0, 0.0), (1200.0, 0.0), (-1200.0, 0.0), (0.0, 1200.0), (0.0, -1200.0),
        (1200.0, 1200.0), (-1200.0, -1200.0), (2400.0, 0.0), (-2400.0, 0.0),
    ]):
        ensure_cube("Curb_%d_N" % i, unreal.Vector(x, y + 155.0, -18.0), unreal.Vector(2.8, 0.12, 0.22), curb)
        ensure_cube("Curb_%d_E" % i, unreal.Vector(x + 155.0, y, -18.0), unreal.Vector(0.12, 2.8, 0.22), curb)
        curbs += 2

    # HDRI Backdrop if plugin class exists — soft day sky without black void
    hdri_cls = unreal.load_class(None, "/HDRIBackdrop/Blueprints/BP_HDRIBackdrop.BP_HDRIBackdrop_C")
    if hdri_cls is None:
        hdri_cls = unreal.EditorAssetLibrary.load_blueprint_class("/HDRIBackdrop/Blueprints/BP_HDRIBackdrop")
    if hdri_cls and find_by_label("HDRI_LeveeDay") is None:
        try:
            hdri = spawn(hdri_cls, unreal.Vector(0, 0, 0), label="HDRI_LeveeDay")
            unreal.log("Spawned HDRI backdrop")
        except Exception as exc:
            unreal.log_warning("HDRI spawn: %s" % exc)

    if find_by_label(FLAG) is None:
        spawn(unreal.Actor, unreal.Vector(0, 0, -740), label=FLAG)

    if not level_editor.save_current_level():
        raise RuntimeError("save failed")
    unreal.log("GANGSTERS LOOK OK — roads=%d walks=%d curbs=%d blds=%d" % (roads, walks, curbs, blds))


main()
