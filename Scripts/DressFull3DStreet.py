"""Full-3D street pass: real building meshes, destroy stickers, place 3D cars on roads.

Characters stay C++ 3D silhouettes (no Plane sprites). Cars get readable lit body mats
and curb placement on avenues.
"""
import unreal
import os

MAP_PATH = "/Game/Maps/Empire/Levee_Greybox"
MESH_DIR = "/Game/Art/Empire/ExternalBuildings/Meshes"
TEX_DIR = "/Game/Art/Empire/ExternalBuildings/Textures"
MAT_DIR = "/Game/Art/Empire/ExternalBuildings/Materials"
SPRITE_MAT = "/Game/Art/Empire/Sprites/Materials"
FLAG = "Dress_Full3D_v1"

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
    if label is not None:
        actor.set_actor_label(label)
    return actor


def destroy_matching(pred):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    n = 0
    for actor in list(sub.get_all_level_actors()):
        if pred(actor.get_actor_label()):
            sub.destroy_actor(actor)
            n += 1
    return n


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


def wipe_mat(mat_dir, name):
    path = "%s/%s" % (mat_dir, name)
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        try:
            unreal.EditorAssetLibrary.delete_asset(path)
        except Exception:
            pass
    root = unreal.Paths.project_content_dir()
    # ExternalBuildings or Sprites
    for sub in (
        "Art/Empire/ExternalBuildings/Materials",
        "Art/Empire/Sprites/Materials",
    ):
        base = os.path.normpath(os.path.join(root, sub, name))
        for ext in (".uasset", ".uexp", ".ubulk"):
            p = base + ext
            if os.path.isfile(p):
                try:
                    os.remove(p)
                except OSError:
                    pass


def make_lit_building_mat(idx):
    name = "M_ExtBld_3D_%d" % idx
    wipe_mat(MAT_DIR, name)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MAT_DIR, unreal.Material, unreal.MaterialFactoryNew()
    )
    if not mat:
        return None
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)

    base = unreal.load_asset("%s/Building%d_Base_color" % (TEX_DIR, idx))
    sample = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionTextureSample, -450, 0
    )
    if base:
        sample.set_editor_property("texture", base)
    unreal.MaterialEditingLibrary.connect_material_property(sample, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)

    mul = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionMultiply, -150, 160
    )
    amp = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant, -300, 200
    )
    amp.set_editor_property("r", 0.45)
    unreal.MaterialEditingLibrary.connect_material_expressions(sample, "RGB", mul, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(amp, "", mul, "B")
    unreal.MaterialEditingLibrary.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

    nrm = unreal.load_asset("%s/Building%d_Normal_OpenGL" % (TEX_DIR, idx))
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

    rough = unreal.load_asset("%s/Building%d_Roughness" % (TEX_DIR, idx))
    if rough:
        rs = unreal.MaterialEditingLibrary.create_material_expression(
            mat, unreal.MaterialExpressionTextureSample, -450, 460
        )
        rs.set_editor_property("texture", rough)
        unreal.MaterialEditingLibrary.connect_material_property(rs, "R", unreal.MaterialProperty.MP_ROUGHNESS)

    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset("%s/%s" % (MAT_DIR, name))
    return mat


def make_solid_lit(name, r, g, b, emissive=0.35):
    wipe_mat(SPRITE_MAT, name)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, SPRITE_MAT, unreal.Material, unreal.MaterialFactoryNew()
    )
    if not mat:
        return None
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    c = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant3Vector, -300, 0
    )
    c.set_editor_property("constant", unreal.LinearColor(r, g, b, 1.0))
    unreal.MaterialEditingLibrary.connect_material_property(c, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mul = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionMultiply, -80, 120
    )
    amp = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant, -300, 140
    )
    amp.set_editor_property("r", float(emissive))
    unreal.MaterialEditingLibrary.connect_material_expressions(c, "", mul, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(amp, "", mul, "B")
    unreal.MaterialEditingLibrary.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    rough = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant, -300, 220
    )
    rough.set_editor_property("r", 0.45)
    unreal.MaterialEditingLibrary.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset("%s/%s" % (SPRITE_MAT, name))
    return mat


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
    smc.set_cast_shadow(True)
    actor.set_actor_hidden_in_game(False)
    return actor


def apply_buildings():
    killed = destroy_matching(
        lambda lab: lab.startswith("FacadeCube_")
        or lab.startswith("FacadePlane_")
        or lab.startswith("SpriteChar_")
        or lab.startswith("SpriteCar_")
        or (lab.startswith("Row_") and lab.endswith("_Roof"))
    )
    meshes = []
    # Prefer registry so we never confuse Materials with StaticMeshes
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    try:
        ar.scan_paths_synchronous([MESH_DIR], True)
    except Exception:
        pass
    for data in ar.get_assets_by_path(MESH_DIR, recursive=False):
        try:
            cls = str(data.asset_class_path.asset_name)
        except Exception:
            cls = str(getattr(data, "asset_class", ""))
        if "StaticMesh" not in cls:
            continue
        name = str(data.asset_name)
        if not (name.startswith("Building") or name.startswith("SM_CityBuildings")):
            continue
        path = "%s/%s.%s" % (MESH_DIR, name, name)
        m = unreal.load_asset(path)
        if isinstance(m, unreal.StaticMesh):
            meshes.append(m)
            unreal.log("Loaded mesh %s" % name)
    meshes.sort(key=lambda m: m.get_name())
    if not meshes:
        raise RuntimeError("No Building/SM_CityBuildings StaticMeshes in " + MESH_DIR)

    mats = [make_lit_building_mat(i) for i in range(1, 8)]
    mats = [m for m in mats if m]

    swapped = 0
    for i, label in enumerate(ROW_MASS_LABELS):
        actor = find_by_label(label)
        if not actor or not actor.static_mesh_component:
            continue
        smc = actor.static_mesh_component
        cur = actor.get_actor_scale3d()
        # Footprint from current cube (100uu) or existing mesh bounds
        if smc.static_mesh and isinstance(smc.static_mesh, unreal.StaticMesh):
            mesh_name = smc.static_mesh.get_name()
            if mesh_name.startswith("Building") or mesh_name.startswith("SM_City"):
                size = mesh_bounds_size(smc.static_mesh)
                target = unreal.Vector(abs(cur.x) * size.x, abs(cur.y) * size.y, abs(cur.z) * size.z)
            else:
                target = unreal.Vector(abs(cur.x) * 100.0, abs(cur.y) * 100.0, abs(cur.z) * 100.0)
        else:
            target = unreal.Vector(abs(cur.x) * 100.0, abs(cur.y) * 100.0, abs(cur.z) * 100.0)

        mesh = meshes[i % len(meshes)]
        if not isinstance(mesh, unreal.StaticMesh):
            unreal.log_warning("skip non-mesh at index %d" % i)
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
        unreal.log("3D BLD %s -> %s" % (label, mesh.get_name()))
    return swapped, killed


def place_road_cars(mats):
    """Editor-placed 3D blockout cars ON avenue curbs (runtime LEStreetCar also spawns)."""
    destroy_matching(lambda lab: lab.startswith("RoadCar3D_"))
    # Curb of main avenues — center of road lane-ish
    # On 480uu-wide avenues: park in the near curb lane (±140 from centerline)
    spots = [
        # (label, x, y, yaw, mat_key, sx, sy, sz) — sx along heading
        ("RoadCar3D_Packard", 140.0, -280.0, 90.0, "black", 2.8, 1.2, 0.7),
        ("RoadCar3D_Taxi", 140.0, 700.0, 0.0, "yellow", 2.6, 1.15, 0.65),
        ("RoadCar3D_Police", -140.0, 200.0, 90.0, "black", 2.7, 1.2, 0.7),
        ("RoadCar3D_ModelA", 1200.0, -140.0, 0.0, "black", 2.4, 1.1, 0.6),
        ("RoadCar3D_Delivery", 1800.0, -900.0, 90.0, "green", 3.2, 1.35, 1.05),
        ("RoadCar3D_Harlan", -2400.0, -1100.0, 90.0, "maroon", 2.8, 1.2, 0.7),
        ("RoadCar3D_Taxi2", -1200.0, 400.0, 0.0, "yellow", 2.6, 1.15, 0.65),
        ("RoadCar3D_Sedan", 2400.0, 200.0, 90.0, "navy", 2.7, 1.15, 0.68),
    ]
    n = 0
    for label, x, y, yaw, key, sx, sy, sz in spots:
        mat = mats.get(key)
        # Body
        ensure_cube(label, unreal.Vector(x, y, 40.0), unreal.Vector(sx, sy, sz), mat, yaw)
        # Cabin
        ensure_cube(
            label + "_Cabin",
            unreal.Vector(x, y, 70.0),
            unreal.Vector(sx * 0.55, sy * 0.9, sz * 0.7),
            mats.get("cabin") or mat,
            yaw,
        )
        n += 1
    return n


def main():
    if not unreal.EditorAssetLibrary.does_directory_exist(MAT_DIR):
        unreal.EditorAssetLibrary.make_directory(MAT_DIR)
    if not unreal.EditorAssetLibrary.does_directory_exist(SPRITE_MAT):
        unreal.EditorAssetLibrary.make_directory(SPRITE_MAT)

    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level_editor.load_level(MAP_PATH):
        raise RuntimeError("load failed")

    swapped, killed = apply_buildings()

    car_mats = {
        "black": make_solid_lit("M_Car3D_Black", 0.04, 0.04, 0.05, 0.25),
        "yellow": make_solid_lit("M_Car3D_Yellow", 0.85, 0.72, 0.12, 0.4),
        "green": make_solid_lit("M_Car3D_Green", 0.12, 0.28, 0.14, 0.3),
        "maroon": make_solid_lit("M_Car3D_Maroon", 0.28, 0.08, 0.1, 0.3),
        "navy": make_solid_lit("M_Car3D_Navy", 0.08, 0.12, 0.28, 0.3),
        "cabin": make_solid_lit("M_Car3D_Cabin", 0.15, 0.16, 0.18, 0.2),
    }
    cars = place_road_cars(car_mats)

    if find_by_label(FLAG) is None:
        spawn(unreal.Actor, unreal.Vector(0, 0, -780), label=FLAG)

    if not level_editor.save_current_level():
        raise RuntimeError("save failed")
    unreal.log(
        "FULL 3D STREET OK — buildings=%d stickers_removed=%d road_cars=%d"
        % (swapped, killed, cars)
    )


main()
