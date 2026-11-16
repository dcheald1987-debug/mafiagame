"""Rebuild masked sprite materials from Cropped PNGs and ensure assets exist.
Runtime C++ applies these via SetSpriteMaterialPath — no façade Planes.
"""
import unreal
import os

SRC = unreal.Paths.project_content_dir() + "Art/Empire/Sprites/Source/Cropped"
DEST = "/Game/Art/Empire/Sprites"
TEX = DEST + "/Textures"
MAT = DEST + "/Materials"

# name without T_/M_Sprite_ prefix -> relative png
SHEETS = [
    ("Car_Packard", "Cars/S_Packard.png"),
    ("Car_Harlan", "Cars/S_HarlanSedan.png"),
    ("Car_ModelA", "Cars/S_ModelA.png"),
    ("Car_Taxi", "Cars/S_Taxi.png"),
    ("Car_Police", "Cars/S_PoliceCar.png"),
    ("Car_Delivery", "Cars/S_DeliveryTruck.png"),
    ("Char_Eddie", "Characters/S_Eddie.png"),
    ("Char_Nicky", "Characters/S_Nicky.png"),
    ("Char_Nora", "Characters/S_Nora.png"),
    ("Char_Quinn", "Characters/S_Quinn.png"),
    ("Char_Bridget", "Characters/S_Bridget.png"),
    ("Char_CivMan", "Characters/S_CivMan.png"),
    ("Char_CivWoman", "Characters/S_CivWoman.png"),
    ("Char_DockWorker", "Characters/S_DockWorker.png"),
    ("Char_HarlanCrew", "Characters/S_Harlan.png"),
    ("Prop_DockCrates", "Props/S_DockCrates.png"),
    ("Prop_CallBox", "Props/S_CallBox.png"),
    ("Prop_StreetLamp", "Props/S_StreetLamp.png"),
]


def ensure_dir(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def purge(content_rel_no_ext):
    root = unreal.Paths.project_content_dir()
    base = os.path.normpath(os.path.join(root, content_rel_no_ext.replace("/", os.sep)))
    for ext in (".uasset", ".uexp", ".ubulk"):
        p = base + ext
        if os.path.isfile(p):
            try:
                os.remove(p)
            except OSError:
                pass


def import_texture(name, rel):
    dest = "%s/%s" % (TEX, name)
    disk = os.path.normpath(os.path.join(SRC, rel.replace("/", os.sep)))
    if not os.path.isfile(disk):
        unreal.log_warning("Missing " + disk)
        return None
    if unreal.EditorAssetLibrary.does_asset_exist(dest):
        try:
            unreal.EditorAssetLibrary.delete_asset(dest)
        except Exception:
            pass
    purge("Art/Empire/Sprites/Textures/" + name)
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
            tex.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_UI)
            tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_DEFAULT)
            unreal.EditorAssetLibrary.save_asset(dest)
        except Exception:
            pass
    unreal.log("Tex " + name)
    return tex


def make_masked(name, texture):
    path = "%s/%s" % (MAT, name)
    mat = unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None
    if mat is not None:
        unreal.MaterialEditingLibrary.delete_all_material_expressions(mat)
    else:
        purge("Art/Empire/Sprites/Materials/" + name)
        mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, MAT, unreal.Material, unreal.MaterialFactoryNew()
        )
    if mat is None:
        return None
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
    mat.set_editor_property("two_sided", True)
    sample = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionTextureSample, -400, 0
    )
    sample.set_editor_property("texture", texture)
    unreal.MaterialEditingLibrary.connect_material_property(
        sample, "RGB", unreal.MaterialProperty.MP_BASE_COLOR
    )
    unreal.MaterialEditingLibrary.connect_material_property(
        sample, "RGB", unreal.MaterialProperty.MP_EMISSIVE_COLOR
    )
    unreal.MaterialEditingLibrary.connect_material_property(
        sample, "A", unreal.MaterialProperty.MP_OPACITY_MASK
    )
    unreal.MaterialEditingLibrary.layout_material_expressions(mat)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(path)
    unreal.log("Mat " + name)
    return mat


def main():
    ensure_dir(TEX)
    ensure_dir(MAT)
    n = 0
    for key, rel in SHEETS:
        tex = import_texture("T_" + key, rel)
        if not tex:
            continue
        make_masked("M_Sprite_" + key, tex)
        n += 1
    unreal.EditorAssetLibrary.save_directory(DEST)
    unreal.log("WireElevenLabsSprites OK mats=%d" % n)


main()
