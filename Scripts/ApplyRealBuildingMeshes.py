"""Replace sticker façade cubes with real 3D ExternalBuildings meshes.

Destroys FacadeCube_* / flat Roof cubes. Fits Building1-7 into each Row_*_Mass
footprint and rebuilds materials as lit + soft emissive so they stay readable.
"""
import unreal
import os

MAP_PATH = "/Game/Maps/Empire/Levee_Greybox"
MESH_DIR = "/Game/Art/Empire/ExternalBuildings/Meshes"
TEX_DIR = "/Game/Art/Empire/ExternalBuildings/Textures"
MAT_DIR = "/Game/Art/Empire/ExternalBuildings/Materials"
FLAG = "Dress_RealBuildings_v1"

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


def find_by_label(label):
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if actor.get_actor_label() == label:
            return actor
    return None


def spawn(cls, location, label=None):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actor = sub.spawn_actor_from_class(cls, location, unreal.Rotator(0, 0, 0))
    if label:
        actor.set_actor_label(label)
    return actor


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


def destroy_stickers():
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    n = 0
    for actor in list(sub.get_all_level_actors()):
        lab = actor.get_actor_label()
        if lab.startswith("FacadeCube_") or lab.startswith("FacadePlane_"):
            sub.destroy_actor(actor)
            n += 1
            continue
        # Flat roof slabs were part of the sticker kit — real meshes have roofs
        if lab.endswith("_Roof") and lab.startswith("Row_"):
            sub.destroy_actor(actor)
            n += 1
    return n


def rebuild_readable_mat(idx):
    """Lit + emissive fill from Base_color so 3D form reads under iso day light."""
    name = "M_ExtBld_Lit_%d" % idx
    mat_path = "%s/%s" % (MAT_DIR, name)
    if unreal.EditorAssetLibrary.does_asset_exist(mat_path):
        try:
            unreal.EditorAssetLibrary.delete_asset(mat_path)
        except Exception:
            pass
    root = unreal.Paths.project_content_dir()
    base_disk = os.path.normpath(os.path.join(root, "Art/Empire/ExternalBuildings/Materials", name))
    for ext in (".uasset", ".uexp", ".ubulk"):
        p = base_disk + ext
        if os.path.isfile(p):
            try:
                os.remove(p)
            except OSError:
                pass

    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MAT_DIR, unreal.Material, unreal.MaterialFactoryNew()
    )
    if mat is None:
        return None

    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)

    base = unreal.load_asset("%s/Building%d_Base_color" % (TEX_DIR, idx))
    if base is None:
        base = unreal.load_asset("%s/Building%d_Base_Color" % (TEX_DIR, idx))
    sample = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionTextureSample, -450, 0
    )
    if base:
        sample.set_editor_property("texture", base)
    unreal.MaterialEditingLibrary.connect_material_property(sample, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)

    # Soft emissive so façades never drop to black in ortho
    mul = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionMultiply, -150, 180
    )
    amp = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant, -300, 220
    )
    amp.set_editor_property("r", 0.55)
    unreal.MaterialEditingLibrary.connect_material_expressions(sample, "RGB", mul, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(amp, "", mul, "B")
    unreal.MaterialEditingLibrary.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

    nrm = unreal.load_asset("%s/Building%d_Normal_OpenGL" % (TEX_DIR, idx))
    if nrm:
        ns = unreal.MaterialEditingLibrary.create_material_expression(
            mat, unreal.MaterialExpressionTextureSample, -450, 280
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
            mat, unreal.MaterialExpressionTextureSample, -450, 480
        )
        rs.set_editor_property("texture", rough)
        unreal.MaterialEditingLibrary.connect_material_property(rs, "R", unreal.MaterialProperty.MP_ROUGHNESS)

    unreal.MaterialEditingLibrary.layout_material_expressions(mat)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(mat_path)
    return mat


def main():
    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level_editor.load_level(MAP_PATH):
        raise RuntimeError("load failed")

    killed = destroy_stickers()
    unreal.log("Removed sticker actors: %d" % killed)

    meshes = []
    for i in range(1, 8):
        m = unreal.load_asset("%s/Building%d" % (MESH_DIR, i))
        if m:
            meshes.append(m)
    if not meshes:
        # Fallback cubes from same pack
        for name in (
            "SM_CityBuildings_Cube",
            "SM_CityBuildings_Cube_001",
            "SM_CityBuildings_Cube_002",
            "SM_CityBuildings_Cube_003",
            "SM_CityBuildings_Cube_004",
            "SM_CityBuildings_Cube_005",
            "SM_CityBuildings_Cube_006",
        ):
            m = unreal.load_asset("%s/%s" % (MESH_DIR, name))
            if m:
                meshes.append(m)
    if not meshes:
        raise RuntimeError("No ExternalBuildings meshes found")

    mats = []
    for i in range(1, 8):
        mat = rebuild_readable_mat(i)
        if mat:
            mats.append(mat)

    swapped = 0
    for i, label in enumerate(ROW_MASS_LABELS):
        actor = find_by_label(label)
        if actor is None:
            unreal.log_warning("missing " + label)
            continue
        smc = actor.static_mesh_component
        if smc is None:
            continue

        # Capture current cube footprint before mesh swap
        cur_scale = actor.get_actor_scale3d()
        target = unreal.Vector(
            abs(cur_scale.x) * 100.0,
            abs(cur_scale.y) * 100.0,
            abs(cur_scale.z) * 100.0,
        )

        mesh = meshes[i % len(meshes)]
        smc.set_static_mesh(mesh)
        size = mesh_bounds_size(mesh)
        sx = target.x / max(size.x, 1.0)
        sy = target.y / max(size.y, 1.0)
        sxy = min(sx, sy) * 0.98
        sz = target.z / max(size.z, 1.0)
        actor.set_actor_scale3d(unreal.Vector(sxy, sxy, sz))

        # Sit on ground (mesh origin often center)
        loc = actor.get_actor_location()
        # Prefer XY from label origin; Z = half height
        actor.set_actor_location(unreal.Vector(loc.x, loc.y, target.z * 0.5), False, True)

        if mats:
            smc.set_material(0, mats[i % len(mats)])
        smc.set_cast_shadow(True)
        actor.set_actor_hidden_in_game(False)
        swapped += 1
        unreal.log("REAL BLD %s -> %s" % (label, mesh.get_name()))

    if find_by_label(FLAG) is None:
        spawn(unreal.Actor, unreal.Vector(0, 0, -760), label=FLAG)

    if not level_editor.save_current_level():
        raise RuntimeError("save failed")
    unreal.EditorAssetLibrary.save_directory("/Game/Art/Empire/ExternalBuildings")
    unreal.log("REAL BUILDINGS OK — swapped=%d stickers_removed=%d meshes=%d" % (swapped, killed, len(meshes)))


main()
