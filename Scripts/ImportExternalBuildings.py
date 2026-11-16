"""Import Blackthorn City Buildings FBX + textures and dress Levee Row_*_Mass.

Sources live under Content/Art/Empire/ExternalBuildings/Blackthorn (from Downloads zip).
"""
import unreal
import os

MAP_PATH = "/Game/Maps/Empire/Levee_Greybox"
SRC_ROOT = unreal.Paths.project_content_dir() + "Art/Empire/ExternalBuildings/Blackthorn"
DEST_MESH = "/Game/Art/Empire/ExternalBuildings/Meshes"
DEST_TEX = "/Game/Art/Empire/ExternalBuildings/Textures"
DEST_MAT = "/Game/Art/Empire/ExternalBuildings/Materials"
FBX_DISK = os.path.normpath(os.path.join(SRC_ROOT, "source", "City Buildings.fbx"))
TEX_DISK = os.path.normpath(os.path.join(SRC_ROOT, "textures"))

ROW_MASS_LABELS = [
    "Row_Garage_Mass",
    "Row_Cafe_Mass",
    "Row_Dock_Mass",
    "Row_Bar_Mass",
    "Row_Board_Mass",
    "Row_Freight_Mass",
    "Row_Rope_Mass",
    "Row_MidA_Mass",
    "Row_MidB_Mass",
    "Row_MidC_Mass",
    "Row_MidD_Mass",
    "Row_MidE_Mass",
    "Row_MidF_Mass",
    "Row_MidG_Mass",
]


def ensure_dir(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def find_by_label(label):
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if actor.get_actor_label() == label:
            return actor
    return None


def import_textures():
    tex_map = {}
    if not os.path.isdir(TEX_DISK):
        unreal.log_warning("Missing textures " + TEX_DISK)
        return tex_map
    tasks = []
    for name in os.listdir(TEX_DISK):
        if not name.lower().endswith(".png"):
            continue
        disk = os.path.join(TEX_DISK, name)
        asset_name = os.path.splitext(name)[0]
        dest = "%s/%s" % (DEST_TEX, asset_name)
        if unreal.EditorAssetLibrary.does_asset_exist(dest):
            unreal.EditorAssetLibrary.delete_asset(dest)
        task = unreal.AssetImportTask()
        task.set_editor_property("filename", disk)
        task.set_editor_property("destination_path", DEST_TEX)
        task.set_editor_property("destination_name", asset_name)
        task.set_editor_property("replace_existing", True)
        task.set_editor_property("automated", True)
        task.set_editor_property("save", True)
        task.set_editor_property("factory", unreal.TextureFactory())
        tasks.append(task)
    if tasks:
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    for name in os.listdir(TEX_DISK):
        if not name.lower().endswith(".png"):
            continue
        asset_name = os.path.splitext(name)[0]
        tex = unreal.load_asset("%s/%s" % (DEST_TEX, asset_name))
        if tex:
            tex_map[asset_name] = tex
    unreal.log("EXTERNAL BLD — textures %d" % len(tex_map))
    return tex_map


def import_fbx():
    ensure_dir(DEST_MESH)
    if not os.path.isfile(FBX_DISK):
        raise RuntimeError("Missing FBX " + FBX_DISK)

    # Clear prior imports in dest
    try:
        assets = unreal.EditorAssetLibrary.list_assets(DEST_MESH, True, False)
        for a in assets:
            unreal.EditorAssetLibrary.delete_asset(a)
    except Exception:
        pass

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", FBX_DISK)
    task.set_editor_property("destination_path", DEST_MESH)
    task.set_editor_property("destination_name", "SM_CityBuildings")
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)

    options = unreal.FbxImportUI()
    options.set_editor_property("automated_import_should_detect_type", False)
    options.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_STATIC_MESH)
    options.set_editor_property("original_import_type", unreal.FBXImportType.FBXIT_STATIC_MESH)
    options.set_editor_property("static_mesh_import_data", unreal.FbxStaticMeshImportData())
    sm = options.get_editor_property("static_mesh_import_data")
    try:
        sm.set_editor_property("combine_meshes", False)
        sm.set_editor_property("auto_generate_collision", True)
        sm.set_editor_property("import_uniform_scale", 1.0)
        sm.set_editor_property("convert_scene", True)
        sm.set_editor_property("force_front_x_axis", False)
    except Exception as exc:
        unreal.log_warning("fbx options partial: %s" % exc)
    task.set_editor_property("options", options)

    factory = unreal.FbxFactory()
    task.set_editor_property("factory", factory)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

    meshes = []
    for path in unreal.EditorAssetLibrary.list_assets(DEST_MESH, True, False):
        asset = unreal.load_asset(path)
        if isinstance(asset, unreal.StaticMesh):
            meshes.append(asset)
    meshes.sort(key=lambda m: m.get_name())
    unreal.log("EXTERNAL BLD — meshes %d: %s" % (len(meshes), ", ".join(m.get_name() for m in meshes)))
    return meshes


def make_building_material(building_index, tex_map):
    """Building1..7 textured material."""
    ensure_dir(DEST_MAT)
    name = "M_ExtBld_%d" % building_index
    mat_path = "%s/%s" % (DEST_MAT, name)
    if unreal.EditorAssetLibrary.does_asset_exist(mat_path):
        mat = unreal.EditorAssetLibrary.load_asset(mat_path)
        try:
            unreal.MaterialEditingLibrary.delete_all_material_expressions(mat)
        except Exception:
            unreal.EditorAssetLibrary.delete_asset(mat_path)
            mat = None
    else:
        mat = None
    if mat is None:
        mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, DEST_MAT, unreal.Material, unreal.MaterialFactoryNew()
        )
    if mat is None:
        return None

    def tex(suffix):
        key = "Building%d_%s" % (building_index, suffix)
        return tex_map.get(key)

    base = tex("Base_color") or tex("Base_Color")
    sample = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionTextureSample, -400, 0
    )
    if base:
        sample.set_editor_property("texture", base)
    unreal.MaterialEditingLibrary.connect_material_property(sample, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)

    nrm = tex("Normal_OpenGL")
    if nrm:
        ns = unreal.MaterialEditingLibrary.create_material_expression(
            mat, unreal.MaterialExpressionTextureSample, -400, 200
        )
        ns.set_editor_property("texture", nrm)
        try:
            ns.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
        except Exception:
            pass
        unreal.MaterialEditingLibrary.connect_material_property(ns, "RGB", unreal.MaterialProperty.MP_NORMAL)

    rough = tex("Roughness")
    if rough:
        rs = unreal.MaterialEditingLibrary.create_material_expression(
            mat, unreal.MaterialExpressionTextureSample, -400, 400
        )
        rs.set_editor_property("texture", rough)
        unreal.MaterialEditingLibrary.connect_material_property(rs, "R", unreal.MaterialProperty.MP_ROUGHNESS)

    metal = tex("Metallic")
    if metal:
        ms = unreal.MaterialEditingLibrary.create_material_expression(
            mat, unreal.MaterialExpressionTextureSample, -400, 600
        )
        ms.set_editor_property("texture", metal)
        unreal.MaterialEditingLibrary.connect_material_property(ms, "R", unreal.MaterialProperty.MP_METALLIC)

    emis = tex("Emissive")
    if emis:
        es = unreal.MaterialEditingLibrary.create_material_expression(
            mat, unreal.MaterialExpressionTextureSample, -400, 800
        )
        es.set_editor_property("texture", emis)
        unreal.MaterialEditingLibrary.connect_material_property(es, "RGB", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

    unreal.MaterialEditingLibrary.layout_material_expressions(mat)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(mat_path)
    return mat


def mesh_bounds_size(mesh):
    try:
        box = mesh.get_bounding_box()
        return unreal.Vector(abs(box.max.x - box.min.x), abs(box.max.y - box.min.y), abs(box.max.z - box.min.z))
    except Exception:
        return unreal.Vector(400.0, 400.0, 600.0)


def hide_row_extras(prefix):
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        label = actor.get_actor_label()
        if not label.startswith(prefix + "_"):
            continue
        if label.endswith("_Mass"):
            continue
        smc = getattr(actor, "static_mesh_component", None)
        if smc:
            smc.set_visibility(False, False)
            actor.set_actor_hidden_in_game(True)


def dress_rows(meshes, mats):
    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level_editor.load_level(MAP_PATH):
        raise RuntimeError("load failed")

    if not meshes:
        raise RuntimeError("no meshes")

    swapped = 0
    for i, label in enumerate(ROW_MASS_LABELS):
        actor = find_by_label(label)
        if actor is None:
            unreal.log_warning("missing " + label)
            continue
        smc = actor.static_mesh_component
        if smc is None:
            continue

        cur_scale = actor.get_actor_scale3d()
        target = unreal.Vector(abs(cur_scale.x) * 100.0, abs(cur_scale.y) * 100.0, abs(cur_scale.z) * 100.0)

        mesh = meshes[i % len(meshes)]
        smc.set_static_mesh(mesh)
        size = mesh_bounds_size(mesh)
        # Uniform XY scale to footprint; keep height proportional-ish
        sx = target.x / max(size.x, 1.0)
        sy = target.y / max(size.y, 1.0)
        sxy = min(sx, sy)
        sz = target.z / max(size.z, 1.0)
        actor.set_actor_scale3d(unreal.Vector(sxy, sxy, sz))
        loc = actor.get_actor_location()
        actor.set_actor_location(unreal.Vector(loc.x, loc.y, target.z * 0.5), False, True)

        mat = mats[i % len(mats)] if mats else None
        if mat:
            smc.set_material(0, mat)

        prefix = label.rsplit("_Mass", 1)[0]
        hide_row_extras(prefix)
        swapped += 1
        unreal.log("EXTERNAL BLD — %s -> %s" % (label, mesh.get_name()))

    if not level_editor.save_current_level():
        raise RuntimeError("save failed")
    unreal.log("EXTERNAL BLD OK — swapped %d buildings" % swapped)
    return swapped


def main():
    ensure_dir(DEST_MESH)
    ensure_dir(DEST_TEX)
    ensure_dir(DEST_MAT)
    tex_map = import_textures()
    meshes = import_fbx()
    mats = []
    for i in range(1, 8):
        m = make_building_material(i, tex_map)
        if m:
            mats.append(m)
    # If FBX produced fewer/more meshes than 7, still dress with cycling
    dress_rows(meshes, mats)
    unreal.EditorAssetLibrary.save_directory("/Game/Art/Empire/ExternalBuildings")


main()
