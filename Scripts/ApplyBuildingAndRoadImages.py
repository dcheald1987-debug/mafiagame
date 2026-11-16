"""Apply existing building façade images + Fab asphalt to Levee cubes. No Plane meshes."""
import unreal
import os

MAP_PATH = "/Game/Maps/Empire/Levee_Greybox"
TEX = "/Game/Art/Empire/Sprites/Textures"
MAT = "/Game/Art/Empire/Sprites/Materials"
SRC = unreal.Paths.project_content_dir() + "Art/Empire/Sprites/Source/Cropped"
FLOOR_H = 190.0
FLAG = "Dress_BuildingRoadImages_v1"

# Building textures already imported as T_*
BLOCKS = [
    ("Row_Garage", unreal.Vector(1800.0, -600.0, 0.0), (560.0, 500.0), 3, "T_Bld_Garage"),
    ("Row_Cafe", unreal.Vector(600.0, -600.0, 0.0), (560.0, 500.0), 3, "T_Bld_Cafe"),
    ("Row_Dock", unreal.Vector(1800.0, -1800.0, 0.0), (560.0, 500.0), 2, "T_Bld_Dock"),
    ("Row_MidC", unreal.Vector(600.0, -1800.0, 0.0), (560.0, 500.0), 4, "T_Facade_C"),
    ("Row_MidA", unreal.Vector(-600.0, 600.0, 0.0), (560.0, 500.0), 4, "T_Facade_A"),
    ("Row_MidB", unreal.Vector(-600.0, -600.0, 0.0), (560.0, 500.0), 3, "T_Facade_B"),
    ("Row_Bar", unreal.Vector(-1800.0, -1800.0, 0.0), (560.0, 500.0), 3, "T_Bld_Bar"),
    ("Row_Board", unreal.Vector(-600.0, 1800.0, 0.0), (560.0, 500.0), 4, "T_Bld_Board"),
    ("Row_MidD", unreal.Vector(-1800.0, 600.0, 0.0), (560.0, 500.0), 3, "T_Facade_D"),
    ("Row_MidE", unreal.Vector(-1800.0, -600.0, 0.0), (560.0, 500.0), 3, "T_Facade_A"),
    ("Row_MidF", unreal.Vector(600.0, 600.0, 0.0), (560.0, 500.0), 4, "T_Facade_B"),
    ("Row_MidG", unreal.Vector(1800.0, 600.0, 0.0), (560.0, 500.0), 3, "T_Facade_C"),
    ("Row_Rope", unreal.Vector(-1800.0, 1800.0, 0.0), (560.0, 460.0), 2, "T_Bld_Rope"),
    ("Row_Freight", unreal.Vector(-600.0, -1800.0, 0.0), (560.0, 500.0), 2, "T_Bld_Freight"),
]


def ensure_dir(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def find_by_label(label):
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if actor.get_actor_label() == label:
            return actor
    return None


def spawn(cls, location, rotation=None, scale=None, label=None):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    rot = rotation or unreal.Rotator(0.0, 0.0, 0.0)
    actor = sub.spawn_actor_from_class(cls, location, rot)
    if scale is not None:
        actor.set_actor_scale3d(scale)
    if label is not None:
        actor.set_actor_label(label)
    return actor


def load_tex(name):
    return unreal.load_asset("%s/%s" % (TEX, name))


def import_texture(name, rel):
    dest = "%s/%s" % (TEX, name)
    disk = os.path.normpath(os.path.join(SRC, rel.replace("/", os.sep)))
    if not os.path.isfile(disk):
        unreal.log_warning("Missing " + disk)
        return None
    if unreal.EditorAssetLibrary.does_asset_exist(dest):
        return unreal.load_asset(dest)
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", disk)
    task.set_editor_property("destination_path", TEX)
    task.set_editor_property("destination_name", name)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)
    task.set_editor_property("factory", unreal.TextureFactory())
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    return unreal.load_asset(dest)


def find_existing_mat(candidates):
    for path in candidates:
        if unreal.EditorAssetLibrary.does_asset_exist(path):
            m = unreal.load_asset(path)
            if m is not None:
                return m
    return None


def ensure_unlit_tex_mat(mat_name, texture):
    """Load-or-create opaque unlit textured material. Never fails on exists."""
    mat_path = "%s/%s" % (MAT, mat_name)
    mat = find_existing_mat([mat_path])
    if mat is None:
        # Prefer already-working sprite mats from earlier dress
        return None
    # Rebind texture sample if possible
    try:
        exprs = unreal.MaterialEditingLibrary.get_material_expressions(mat)
        for e in exprs:
            if isinstance(e, unreal.MaterialExpressionTextureSample):
                e.set_editor_property("texture", texture)
                break
        unreal.MaterialEditingLibrary.recompile_material(mat)
        unreal.EditorAssetLibrary.save_asset(mat_path)
    except Exception as exc:
        unreal.log_warning("rebind %s: %s" % (mat_name, exc))
    return mat


def create_fresh_unlit(mat_name, texture):
    """Create only if missing — purge orphan package files first."""
    mat_path = "%s/%s" % (MAT, mat_name)
    if unreal.EditorAssetLibrary.does_asset_exist(mat_path):
        return unreal.load_asset(mat_path)

    # Orphan on disk
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
        return None
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    mat.set_editor_property("two_sided", False)
    sample = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionTextureSample, -400, 0
    )
    sample.set_editor_property("texture", texture)
    unreal.MaterialEditingLibrary.connect_material_property(
        sample, "RGB", unreal.MaterialProperty.MP_BASE_COLOR
    )
    mul = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionMultiply, -150, 100
    )
    amp = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant, -350, 180
    )
    amp.set_editor_property("r", 0.4)
    unreal.MaterialEditingLibrary.connect_material_expressions(sample, "RGB", mul, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(amp, "", mul, "B")
    unreal.MaterialEditingLibrary.connect_material_property(
        mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR
    )
    # Tile UVs for roads
    unreal.MaterialEditingLibrary.layout_material_expressions(mat)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(mat_path)
    return mat


def resolve_bld_mat(tex_key):
    """Map T_Bld_Garage -> best available material."""
    short = tex_key.replace("T_Bld_", "").replace("T_", "")
    candidates = [
        "%s/M_Bld_Bld_%s" % (MAT, short) if tex_key.startswith("T_Bld_") else None,
        "%s/M_Bld_%s" % (MAT, short),
        "%s/M_Sprite_%s" % (MAT, tex_key.replace("T_", "")),
        "%s/M_Sprite_Bld_%s" % (MAT, short),
        "%s/M_Sprite_Facade_%s" % (MAT, short.replace("Facade_", "")) if "Facade" in tex_key else None,
    ]
    paths = [c for c in candidates if c]
    mat = find_existing_mat(paths)
    if mat:
        return mat
    tex = load_tex(tex_key)
    if tex is None:
        return None
    return create_fresh_unlit("M_Apply_%s" % short, tex)


def ensure_facade_cube(label, location, scale, material):
    cube = unreal.load_asset("/Engine/BasicShapes/Cube")
    actor = find_by_label(label)
    if actor is None:
        actor = spawn(unreal.StaticMeshActor, location, None, scale, label)
    else:
        actor.set_actor_location(location, False, True)
        actor.set_actor_rotation(unreal.Rotator(0, 0, 0), False)
        actor.set_actor_scale3d(scale)
    smc = actor.static_mesh_component
    smc.set_static_mesh(cube)
    smc.set_material(0, material)
    smc.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    smc.set_cast_shadow(False)
    actor.set_actor_hidden_in_game(False)
    return actor


def set_actor_mat(label, material):
    actor = find_by_label(label)
    if not actor or not material:
        return False
    smc = getattr(actor, "static_mesh_component", None)
    if not smc:
        return False
    smc.set_material(0, material)
    smc.set_cast_shadow(False)
    return True


def main():
    ensure_dir(MAT)
    ensure_dir(TEX)

    # Street-row building image (extra)
    import_texture("T_Bld_StreetRow", "Buildings/S_StreetRow.png")

    # Fab pack ships materials (not raw textures) — use them directly on road cubes
    road_mat = unreal.load_asset("/Game/Art/Empire/FabRoads/asphalt")
    walk_mat = unreal.load_asset("/Game/Art/Empire/FabRoads/Dark_Concrete")
    lines_mat = unreal.load_asset("/Game/Art/Empire/FabRoads/street_lines")
    if road_mat is None:
        road_mat = unreal.load_asset("/Game/Art/Empire/Materials/M_Asphalt")
    if walk_mat is None:
        walk_mat = unreal.load_asset("/Game/Art/Empire/Materials/M_Sidewalk")
    unreal.log("Road mats asphalt=%s walk=%s lines=%s" % (road_mat is not None, walk_mat is not None, lines_mat is not None))

    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level_editor.load_level(MAP_PATH):
        raise RuntimeError("load failed")

    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in list(sub.get_all_level_actors()):
        lab = actor.get_actor_label()
        if lab.startswith("FacadePlane_") or lab.startswith("FacadeCube_"):
            sub.destroy_actor(actor)
            continue
        if lab in (FLAG, "Dress_BuildingImages_v1", "Dress_ElevenLabs_v4"):
            sub.destroy_actor(actor)
            continue
        smc = getattr(actor, "static_mesh_component", None)
        if smc and smc.static_mesh and "Plane" in smc.static_mesh.get_name():
            sub.destroy_actor(actor)

    roof = unreal.load_asset("/Game/Art/Empire/Materials/M_Roof_Slate")
    bld_ok = 0
    for prefix, origin, footprint, floors, tex_key in BLOCKS:
        mat = resolve_bld_mat(tex_key)
        if mat is None:
            unreal.log_warning("No building mat for " + tex_key)
            continue
        fx, fy = footprint
        total_h = floors * FLOOR_H
        ensure_facade_cube(
            "FacadeCube_%s_S" % prefix,
            unreal.Vector(origin.x, origin.y - fy * 0.5 - 14.0, total_h * 0.5),
            unreal.Vector(fx / 100.0 * 0.98, 0.22, total_h / 100.0),
            mat,
        )
        ensure_facade_cube(
            "FacadeCube_%s_W" % prefix,
            unreal.Vector(origin.x - fx * 0.5 - 14.0, origin.y, total_h * 0.5),
            unreal.Vector(0.22, fy / 100.0 * 0.98, total_h / 100.0),
            mat,
        )
        if set_actor_mat(prefix + "_Mass", mat):
            bld_ok += 1
        set_actor_mat(prefix + "_Roof", roof)

    # Roads + walks + ground
    road_n = 0
    walk_n = 0
    for actor in sub.get_all_level_actors():
        lab = actor.get_actor_label()
        smc = getattr(actor, "static_mesh_component", None)
        if smc is None:
            continue
        if lab.startswith("Avenue_") or lab.startswith("Street_"):
            smc.set_material(0, road_mat)
            smc.set_cast_shadow(False)
            road_n += 1
        elif lab.startswith("Walk") or lab == "Ground":
            smc.set_material(0, walk_mat)
            smc.set_cast_shadow(False)
            walk_n += 1

    # Center stripe cubes on main avenues (optional visual)
    stripe_n = 0
    if lines_mat is not None:
        for i, x in enumerate([2400.0, 1200.0, 0.0, -1200.0, -2400.0]):
            label = "RoadStripe_%d" % i
            ensure_facade_cube(
                label,
                unreal.Vector(x, 0.0, -20.0),
                unreal.Vector(0.35, 54.0, 0.12),
                lines_mat,
            )
            stripe_n += 1

    if find_by_label(FLAG) is None:
        spawn(unreal.Actor, unreal.Vector(0, 0, -600), label=FLAG)

    if not level_editor.save_current_level():
        raise RuntimeError("save failed")
    unreal.log(
        "BUILDING+ROAD IMAGES OK — buildings=%d roads=%d walks=%d stripes=%d"
        % (bld_ok, road_n, walk_n, stripe_n)
    )


main()
