"""Import cropped PNG sprites into Content as textures/materials ONLY.

Do NOT place billboards in the level — flat concept sprites read poorly on The Levee.
World dress stays 3D massing (FixLeveeVisibility / ApplyBuildingSkins) until real meshes land.
"""
import unreal
import os

SRC_ROOT = unreal.Paths.project_content_dir() + "Art/Empire/Sprites/Source/Cropped"
DEST = "/Game/Art/Empire/Sprites"

IMPORTS = [
    ("T_Bld_Garage", "Buildings/S_Garage.png"),
    ("T_Bld_Cafe", "Buildings/S_Cafe.png"),
    ("T_Bld_Dock", "Buildings/S_Dock.png"),
    ("T_Bld_Bar", "Buildings/S_Bar.png"),
    ("T_Bld_Board", "Buildings/S_Board.png"),
    ("T_Bld_Freight", "Buildings/S_Freight.png"),
    ("T_Bld_Rope", "Buildings/S_Rope.png"),
    ("T_Bld_StreetRow", "Buildings/S_StreetRow.png"),
    ("T_Car_Packard", "Cars/S_Packard.png"),
    ("T_Car_Harlan", "Cars/S_HarlanSedan.png"),
    ("T_Char_Eddie", "Characters/S_Eddie.png"),
    ("T_Char_Nicky", "Characters/S_Nicky.png"),
    ("T_Char_Nora", "Characters/S_Nora.png"),
    ("T_Char_HarlanCrew", "Characters/S_Harlan.png"),
    ("T_Char_Quinn", "Characters/S_Quinn.png"),
    ("T_Char_Bridget", "Characters/S_Bridget.png"),
    ("T_Char_DockWorker", "Characters/S_DockWorker.png"),
    ("T_Char_CivMan", "Characters/S_CivMan.png"),
    ("T_Char_CivWoman", "Characters/S_CivWoman.png"),
]


def ensure_dir(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def import_texture(name, rel_file):
    dest_path = "%s/Textures/%s" % (DEST, name)
    disk = os.path.normpath(os.path.join(SRC_ROOT, rel_file.replace("/", os.sep)))
    if not os.path.isfile(disk):
        unreal.log_warning("Missing source " + disk)
        return None

    if unreal.EditorAssetLibrary.does_asset_exist(dest_path):
        unreal.EditorAssetLibrary.delete_asset(dest_path)

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", disk)
    task.set_editor_property("destination_path", DEST + "/Textures")
    task.set_editor_property("destination_name", name)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)
    task.set_editor_property("factory", unreal.TextureFactory())
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    tex = unreal.load_asset(dest_path)
    if tex:
        try:
            tex.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_UI)
            tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_DEFAULT)
            unreal.EditorAssetLibrary.save_asset(dest_path)
        except Exception:
            pass
    unreal.log("Imported " + name)
    return tex


def create_sprite_material(name, texture):
    mat_path = "%s/Materials/%s" % (DEST, name)
    mat = unreal.EditorAssetLibrary.load_asset(mat_path) if unreal.EditorAssetLibrary.does_asset_exist(mat_path) else None
    if mat is not None:
        try:
            unreal.MaterialEditingLibrary.delete_all_material_expressions(mat)
        except Exception:
            unreal.EditorAssetLibrary.delete_asset(mat_path)
            mat = None
    if mat is None:
        if unreal.EditorAssetLibrary.does_asset_exist(mat_path):
            unreal.EditorAssetLibrary.delete_asset(mat_path)
        mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, DEST + "/Materials", unreal.Material, unreal.MaterialFactoryNew()
        )
    if mat is None:
        raise RuntimeError("mat fail " + name)

    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
    mat.set_editor_property("two_sided", True)

    sample = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionTextureSample, -400, 0
    )
    sample.set_editor_property("texture", texture)
    unreal.MaterialEditingLibrary.connect_material_property(sample, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
    unreal.MaterialEditingLibrary.connect_material_property(sample, "RGB", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    unreal.MaterialEditingLibrary.connect_material_property(sample, "A", unreal.MaterialProperty.MP_OPACITY_MASK)
    unreal.MaterialEditingLibrary.layout_material_expressions(mat)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(mat_path)
    unreal.log("Material " + name)
    return mat


def main():
    ensure_dir(DEST)
    ensure_dir(DEST + "/Textures")
    ensure_dir(DEST + "/Materials")
    count = 0
    for name, rel in IMPORTS:
        tex = import_texture(name, rel)
        if tex is None:
            continue
        create_sprite_material(name.replace("T_", "M_Sprite_"), tex)
        count += 1
    unreal.EditorAssetLibrary.save_directory(DEST)
    unreal.log("SPRITE IMPORT OK — %d mats (content only, no level billboards)" % count)


main()
