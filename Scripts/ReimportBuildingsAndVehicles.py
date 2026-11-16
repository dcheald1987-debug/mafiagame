"""Reimport Blackthorn City Buildings FBX as real StaticMeshes, dress rows,
and place 3D vehicle meshes (Chaos SportsCar stand-in until Fab vintage packs land).
"""
import unreal
import os

MAP_PATH = "/Game/Maps/Empire/Levee_Greybox"
FBX_DISK = unreal.Paths.project_content_dir() + "Art/Empire/ExternalBuildings/Blackthorn/source/City Buildings.fbx"
TEX_DISK = unreal.Paths.project_content_dir() + "Art/Empire/ExternalBuildings/Blackthorn/textures"
DEST_MESH = "/Game/Art/Empire/ExternalBuildings/Meshes"
DEST_TEX = "/Game/Art/Empire/ExternalBuildings/Textures"
DEST_MAT = "/Game/Art/Empire/ExternalBuildings/Materials"
# Plugin skeletal mesh — full 3D until period Fab cars are added
VEHICLE_SKM = "/ChaosModularVehicleExamples/Models/SportsCar/SKM_SportsCar.SKM_SportsCar"
FLAG = "Dress_Reimport3D_v1"

ROW_MASS_LABELS = [
    "Row_Garage_Mass", "Row_Cafe_Mass", "Row_Dock_Mass", "Row_Bar_Mass",
    "Row_Board_Mass", "Row_Freight_Mass", "Row_Rope_Mass",
    "Row_MidA_Mass", "Row_MidB_Mass", "Row_MidC_Mass", "Row_MidD_Mass",
    "Row_MidE_Mass", "Row_MidF_Mass", "Row_MidG_Mass",
]


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
    if label:
        actor.set_actor_label(label)
    return actor


def destroy_prefix(prefix):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    n = 0
    for actor in list(sub.get_all_level_actors()):
        if actor.get_actor_label().startswith(prefix):
            sub.destroy_actor(actor)
            n += 1
    return n


def ensure_dir(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def mesh_bounds_size(mesh):
    try:
        box = mesh.get_bounding_box()
        return unreal.Vector(
            abs(box.max.x - box.min.x),
            abs(box.max.y - box.min.y),
            abs(box.max.z - box.min.z),
        )
    except Exception:
        return unreal.Vector(400.0, 400.0, 600.0)


def clear_stub_buildings():
    """Building1-7 were ~5KB stubs (not meshes). Delete before reimport."""
    n = 0
    for i in range(1, 8):
        path = "%s/Building%d" % (DEST_MESH, i)
        if unreal.EditorAssetLibrary.does_asset_exist(path):
            unreal.EditorAssetLibrary.delete_asset(path)
            n += 1
    return n


def import_textures():
    tex_map = {}
    disk = os.path.normpath(TEX_DISK)
    if not os.path.isdir(disk):
        unreal.log_warning("No textures at " + disk)
        return tex_map
    ensure_dir(DEST_TEX)
    tasks = []
    for name in os.listdir(disk):
        if not name.lower().endswith(".png"):
            continue
        asset_name = os.path.splitext(name)[0]
        dest = "%s/%s" % (DEST_TEX, asset_name)
        if unreal.EditorAssetLibrary.does_asset_exist(dest):
            # Keep existing textures
            tex = unreal.load_asset(dest)
            if tex:
                tex_map[asset_name] = tex
            continue
        task = unreal.AssetImportTask()
        task.set_editor_property("filename", os.path.join(disk, name))
        task.set_editor_property("destination_path", DEST_TEX)
        task.set_editor_property("destination_name", asset_name)
        task.set_editor_property("replace_existing", True)
        task.set_editor_property("automated", True)
        task.set_editor_property("save", True)
        task.set_editor_property("factory", unreal.TextureFactory())
        tasks.append(task)
    if tasks:
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    for name in os.listdir(disk):
        if not name.lower().endswith(".png"):
            continue
        asset_name = os.path.splitext(name)[0]
        tex = unreal.load_asset("%s/%s" % (DEST_TEX, asset_name))
        if tex:
            tex_map[asset_name] = tex
    unreal.log("Textures ready: %d" % len(tex_map))
    return tex_map


def import_fbx_buildings():
    ensure_dir(DEST_MESH)
    fbx = os.path.normpath(FBX_DISK)
    if not os.path.isfile(fbx):
        raise RuntimeError("Missing FBX " + fbx)

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", fbx)
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
    except Exception as exc:
        unreal.log_warning("fbx opts: %s" % exc)
    task.set_editor_property("options", options)
    task.set_editor_property("factory", unreal.FbxFactory())
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

    meshes = []
    for path in unreal.EditorAssetLibrary.list_assets(DEST_MESH, True, False):
        asset = unreal.load_asset(path)
        if isinstance(asset, unreal.StaticMesh):
            # Prefer non-tiny assets
            try:
                size = mesh_bounds_size(asset)
                vol = size.x * size.y * size.z
            except Exception:
                vol = 0
            if vol < 1.0:
                continue
            meshes.append(asset)
    meshes.sort(key=lambda m: m.get_name())
    unreal.log("FBX meshes: %d -> %s" % (len(meshes), ", ".join(m.get_name() for m in meshes)))
    return meshes


def make_mat(idx, tex_map):
    name = "M_ExtBld_PBR_%d" % idx
    mat_path = "%s/%s" % (DEST_MAT, name)
    if unreal.EditorAssetLibrary.does_asset_exist(mat_path):
        try:
            unreal.EditorAssetLibrary.delete_asset(mat_path)
        except Exception:
            pass
    ensure_dir(DEST_MAT)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, DEST_MAT, unreal.Material, unreal.MaterialFactoryNew()
    )
    if not mat:
        return None
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)

    def tex(suffix):
        return tex_map.get("Building%d_%s" % (idx, suffix))

    base = tex("Base_color") or tex("Base_Color")
    sample = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionTextureSample, -450, 0
    )
    if base:
        sample.set_editor_property("texture", base)
    unreal.MaterialEditingLibrary.connect_material_property(sample, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)

    mul = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionMultiply, -120, 160
    )
    amp = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant, -280, 200
    )
    amp.set_editor_property("r", 0.4)
    unreal.MaterialEditingLibrary.connect_material_expressions(sample, "RGB", mul, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(amp, "", mul, "B")
    unreal.MaterialEditingLibrary.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

    nrm = tex("Normal_OpenGL")
    if nrm:
        ns = unreal.MaterialEditingLibrary.create_material_expression(
            mat, unreal.MaterialExpressionTextureSample, -450, 260
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
            mat, unreal.MaterialExpressionTextureSample, -450, 460
        )
        rs.set_editor_property("texture", rough)
        unreal.MaterialEditingLibrary.connect_material_property(rs, "R", unreal.MaterialProperty.MP_ROUGHNESS)

    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(mat_path)
    return mat


def dress_buildings(meshes, mats):
    destroy_prefix("FacadeCube_")
    destroy_prefix("FacadePlane_")
    # Remove flat roofs
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in list(sub.get_all_level_actors()):
        lab = actor.get_actor_label()
        if lab.startswith("Row_") and lab.endswith("_Roof"):
            sub.destroy_actor(actor)

    swapped = 0
    for i, label in enumerate(ROW_MASS_LABELS):
        actor = find_by_label(label)
        if not actor or not actor.static_mesh_component:
            continue
        smc = actor.static_mesh_component
        cur = actor.get_actor_scale3d()
        if smc.static_mesh and isinstance(smc.static_mesh, unreal.StaticMesh):
            old = mesh_bounds_size(smc.static_mesh)
            # If still a unit cube (BasicShapes), use scale*100
            if old.x < 150 and old.y < 150 and "Cube" in smc.static_mesh.get_name() and "CityBuildings" not in smc.static_mesh.get_name():
                target = unreal.Vector(abs(cur.x) * 100.0, abs(cur.y) * 100.0, abs(cur.z) * 100.0)
            else:
                target = unreal.Vector(abs(cur.x) * old.x, abs(cur.y) * old.y, abs(cur.z) * old.z)
        else:
            target = unreal.Vector(abs(cur.x) * 100.0, abs(cur.y) * 100.0, abs(cur.z) * 100.0)

        mesh = meshes[i % len(meshes)]
        if not isinstance(mesh, unreal.StaticMesh):
            continue
        smc.set_static_mesh(mesh)
        size = mesh_bounds_size(mesh)
        sxy = min(target.x / max(size.x, 1.0), target.y / max(size.y, 1.0)) * 0.98
        sz = target.z / max(size.z, 1.0)
        actor.set_actor_scale3d(unreal.Vector(sxy, sxy, sz))
        loc = actor.get_actor_location()
        actor.set_actor_location(unreal.Vector(loc.x, loc.y, target.z * 0.5), False, True)
        if mats:
            smc.set_material(0, mats[i % len(mats)])
        smc.set_cast_shadow(True)
        actor.set_actor_hidden_in_game(False)
        swapped += 1
        unreal.log("BLD %s -> %s" % (label, mesh.get_name()))
    return swapped


def place_vehicles():
    """Place full-3D skeletal car meshes on widened curb lanes."""
    destroy_prefix("RoadCar3D_")
    skm = unreal.load_asset(VEHICLE_SKM)
    if skm is None:
        unreal.log_warning("Vehicle SKM missing: " + VEHICLE_SKM)
        return 0

    # Curb lane on 480uu roads
    spots = [
        ("RoadCar3D_Packard", 140.0, -280.0, 90.0, 0.55),
        ("RoadCar3D_Taxi", 140.0, 700.0, 0.0, 0.55),
        ("RoadCar3D_Police", -140.0, 200.0, 90.0, 0.55),
        ("RoadCar3D_ModelA", 1200.0, -140.0, 0.0, 0.5),
        ("RoadCar3D_Delivery", 1660.0, -900.0, 90.0, 0.65),
        ("RoadCar3D_Harlan", -2400.0, -1100.0, 90.0, 0.55),
        ("RoadCar3D_Taxi2", -1200.0, 400.0, 0.0, 0.55),
        ("RoadCar3D_Sedan", 2400.0, 200.0, 90.0, 0.55),
    ]
    n = 0
    for label, x, y, yaw, scale in spots:
        # SkeletalMeshActor
        actor = find_by_label(label)
        if actor is None:
            actor = spawn(unreal.SkeletalMeshActor, unreal.Vector(x, y, 0.0), label=label, yaw=yaw)
        else:
            actor.set_actor_location(unreal.Vector(x, y, 0.0), False, True)
            actor.set_actor_rotation(unreal.Rotator(0, yaw, 0), False)
        try:
            skc = actor.skeletal_mesh_component
            skc.set_skeletal_mesh_asset(skm)
            actor.set_actor_scale3d(unreal.Vector(scale, scale, scale))
            skc.set_cast_shadow(True)
            actor.set_actor_hidden_in_game(False)
            n += 1
            unreal.log("VEH %s" % label)
        except Exception as exc:
            unreal.log_warning("veh %s: %s" % (label, exc))
    return n


def main():
    stubs = clear_stub_buildings()
    unreal.log("Deleted stub Building assets: %d" % stubs)
    tex_map = import_textures()
    meshes = import_fbx_buildings()
    if not meshes:
        raise RuntimeError("FBX import produced no StaticMeshes")

    mats = []
    for i in range(1, 8):
        m = make_mat(i, tex_map)
        if m:
            mats.append(m)

    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level_editor.load_level(MAP_PATH):
        raise RuntimeError("load failed")

    blds = dress_buildings(meshes, mats)
    vehs = place_vehicles()

    if find_by_label(FLAG) is None:
        spawn(unreal.Actor, unreal.Vector(0, 0, -800), label=FLAG)

    if not level_editor.save_current_level():
        raise RuntimeError("save failed")
    unreal.EditorAssetLibrary.save_directory("/Game/Art/Empire/ExternalBuildings")
    unreal.log("REIMPORT 3D OK — buildings=%d vehicles=%d meshes=%d" % (blds, vehs, len(meshes)))


main()
