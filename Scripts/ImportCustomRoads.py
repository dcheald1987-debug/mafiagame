"""Import ElevenLabs road PNGs/JPGs and dress Levee avenues, walks, ground, crosswalks."""
import unreal
import os

MAP_PATH = "/Game/Maps/Empire/Levee_Greybox"
SRC = unreal.Paths.project_content_dir() + "Art/Empire/Sprites/Source/Cropped/Roads"
TEX = "/Game/Art/Empire/Sprites/Textures"
MAT = "/Game/Art/Empire/Sprites/Materials"
FLAG = "Dress_CustomRoads_v2"

IMPORTS = [
    ("T_Road_Asphalt", "S_Road_Asphalt.jpg"),
    ("T_Road_Asphalt_B", "S_Road_Asphalt_B.jpg"),
    ("T_Dirt_Lot", "S_Dirt_Lot.jpg"),
    ("T_Road_Cobble", "S_Road_Cobble.jpg"),
    ("T_Sidewalk", "S_Sidewalk.jpg"),
    ("T_Sidewalk_B", "S_Sidewalk_B.jpg"),
    ("T_Crosswalk", "S_Crosswalk.jpg"),
    ("T_Road_Lines", "S_Road_Lines.jpg"),
]


def ensure_dir(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


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


def import_texture(name, filename):
    dest = "%s/%s" % (TEX, name)
    disk = os.path.normpath(os.path.join(SRC, filename))
    if not os.path.isfile(disk):
        unreal.log_warning("Missing " + disk)
        return None
    if unreal.EditorAssetLibrary.does_asset_exist(dest):
        unreal.EditorAssetLibrary.delete_asset(dest)
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", disk)
    task.set_editor_property("destination_path", TEX)
    task.set_editor_property("destination_name", name)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)
    task.set_editor_property("factory", unreal.TextureFactory())
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    tex = unreal.load_asset(dest)
    if tex:
        try:
            tex.set_editor_property("srgb", True)
            tex.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_WORLD)
            unreal.EditorAssetLibrary.save_asset(dest)
        except Exception:
            pass
    unreal.log("Imported " + name)
    return tex


def create_tiled_unlit(mat_name, texture, tile_u=4.0, tile_v=4.0, emissive=0.25):
    mat_path = "%s/%s" % (MAT, mat_name)
    # Always rebuild cleanly
    if unreal.EditorAssetLibrary.does_asset_exist(mat_path):
        unreal.EditorAssetLibrary.delete_asset(mat_path)
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
    mat.set_editor_property("two_sided", False)

    texcoord = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionTextureCoordinate, -700, 0
    )
    mul_uv = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionMultiply, -520, 0
    )
    scale = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant2Vector, -700, 120
    )
    scale.set_editor_property("r", float(tile_u))
    scale.set_editor_property("g", float(tile_v))
    unreal.MaterialEditingLibrary.connect_material_expressions(texcoord, "", mul_uv, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(scale, "", mul_uv, "B")

    sample = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionTextureSample, -300, 0
    )
    sample.set_editor_property("texture", texture)
    unreal.MaterialEditingLibrary.connect_material_expressions(mul_uv, "", sample, "Coordinates")
    unreal.MaterialEditingLibrary.connect_material_property(
        sample, "RGB", unreal.MaterialProperty.MP_BASE_COLOR
    )

    mul_e = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionMultiply, -80, 140
    )
    amp = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant, -300, 200
    )
    amp.set_editor_property("r", float(emissive))
    unreal.MaterialEditingLibrary.connect_material_expressions(sample, "RGB", mul_e, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(amp, "", mul_e, "B")
    unreal.MaterialEditingLibrary.connect_material_property(
        mul_e, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR
    )

    unreal.MaterialEditingLibrary.layout_material_expressions(mat)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(mat_path)
    unreal.log("Material " + mat_name)
    return mat


def set_mat(label, material):
    actor = find_by_label(label)
    if not actor or not material:
        return False
    smc = getattr(actor, "static_mesh_component", None)
    if not smc:
        return False
    smc.set_material(0, material)
    smc.set_cast_shadow(False)
    return True


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


def main():
    ensure_dir(TEX)
    ensure_dir(MAT)

    texs = {}
    for name, filename in IMPORTS:
        t = import_texture(name, filename)
        if t:
            texs[name] = t

    mats = {}
    if "T_Road_Asphalt" in texs:
        mats["asphalt"] = create_tiled_unlit("M_Custom_Asphalt", texs["T_Road_Asphalt"], 6.0, 6.0, 0.2)
    if "T_Road_Lines" in texs:
        mats["lines"] = create_tiled_unlit("M_Custom_RoadLines", texs["T_Road_Lines"], 1.0, 8.0, 0.22)
    if "T_Sidewalk" in texs:
        mats["walk"] = create_tiled_unlit("M_Custom_Sidewalk", texs["T_Sidewalk"], 5.0, 5.0, 0.28)
    if "T_Road_Cobble" in texs:
        mats["cobble"] = create_tiled_unlit("M_Custom_Cobble", texs["T_Road_Cobble"], 4.0, 4.0, 0.22)
    if "T_Dirt_Lot" in texs:
        mats["dirt"] = create_tiled_unlit("M_Custom_Dirt", texs["T_Dirt_Lot"], 4.0, 4.0, 0.2)
    if "T_Crosswalk" in texs:
        mats["xwalk"] = create_tiled_unlit("M_Custom_Crosswalk", texs["T_Crosswalk"], 1.0, 1.0, 0.25)

    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level_editor.load_level(MAP_PATH):
        raise RuntimeError("load failed")

    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in list(sub.get_all_level_actors()):
        lab = actor.get_actor_label()
        if lab.startswith("RoadStripe_") or lab.startswith("Crosswalk_") or lab == FLAG:
            sub.destroy_actor(actor)

    asphalt = mats.get("asphalt") or mats.get("lines")
    lines = mats.get("lines") or asphalt
    walk = mats.get("walk")
    cobble = mats.get("cobble") or asphalt
    dirt = mats.get("dirt") or walk
    xwalk = mats.get("xwalk")

    # Main grid roads use lined asphalt; alternate some to plain
    roads = 0
    walks = 0
    for actor in sub.get_all_level_actors():
        lab = actor.get_actor_label()
        smc = getattr(actor, "static_mesh_component", None)
        if smc is None:
            continue
        if lab.startswith("Avenue_") or lab.startswith("FabRoad_NS_") or lab.startswith("FabRoad_EW_"):
            # Main grid: alternate plain asphalt vs lined
            tail = lab.split("_")[-1]
            idx = int(tail) if tail.isdigit() else hash(lab) % 2
            smc.set_material(0, lines if (idx % 2 == 0 and lines) else asphalt)
            smc.set_cast_shadow(False)
            roads += 1
        elif lab.startswith("Street_"):
            idx = int(lab.split("_")[-1]) if lab.split("_")[-1].isdigit() else 0
            smc.set_material(0, lines if (idx % 2 == 1 and lines) else asphalt)
            smc.set_cast_shadow(False)
            roads += 1
        elif lab.startswith("FabRoad_X_"):
            smc.set_material(0, asphalt)
            smc.set_cast_shadow(False)
            roads += 1
        elif lab.startswith("Walk"):
            smc.set_material(0, walk or asphalt)
            smc.set_cast_shadow(False)
            walks += 1
        elif lab == "Ground":
            smc.set_material(0, dirt or walk or asphalt)
            smc.set_cast_shadow(False)

    # Wharf / freight feel — cobble patches near water-side blocks
    if cobble:
        ensure_cube(
            "CobblePatch_Dock",
            unreal.Vector(1800.0, -1800.0, -30.0),
            unreal.Vector(8.0, 8.0, 0.2),
            cobble,
        )
        ensure_cube(
            "CobblePatch_Rope",
            unreal.Vector(-1800.0, 1800.0, -30.0),
            unreal.Vector(7.0, 7.0, 0.2),
            cobble,
        )

    # Crosswalks at main intersections (center + mid)
    xwalk_n = 0
    if xwalk:
        spots = [
            (0.0, 0.0, 0.0),
            (1200.0, 0.0, 0.0),
            (-1200.0, 0.0, 0.0),
            (0.0, 1200.0, 90.0),
            (0.0, -1200.0, 90.0),
            (1200.0, 1200.0, 0.0),
            (-1200.0, -1200.0, 0.0),
            (1200.0, -1200.0, 90.0),
            (-1200.0, 1200.0, 90.0),
        ]
        for i, (x, y, yaw) in enumerate(spots):
            ensure_cube(
                "Crosswalk_%d" % i,
                unreal.Vector(x, y, -22.0),
                unreal.Vector(3.4, 3.4, 0.15),
                xwalk,
                yaw,
            )
            xwalk_n += 1

    if find_by_label(FLAG) is None:
        spawn(unreal.Actor, unreal.Vector(0, 0, -600), label=FLAG)

    if not level_editor.save_current_level():
        raise RuntimeError("save failed")
    unreal.EditorAssetLibrary.save_directory(TEX)
    unreal.EditorAssetLibrary.save_directory(MAT)
    unreal.log(
        "CUSTOM ROADS OK — roads=%d walks=%d crosswalks=%d mats=%d"
        % (roads, walks, xwalk_n, len(mats))
    )


main()
