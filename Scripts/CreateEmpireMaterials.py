import unreal

MAT_PATH = "/Game/Art/Empire/Materials"


def ensure_dir(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def create_color_material(name, r, g, b, roughness=0.85):
    asset_path = "%s/%s" % (MAT_PATH, name)
    if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        return unreal.load_asset(asset_path)

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.MaterialFactoryNew()
    mat = asset_tools.create_asset(name, MAT_PATH, unreal.Material, factory)
    if mat is None:
        raise RuntimeError("Failed to create material " + name)

    color_expr = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant3Vector, -380, 0
    )
    color_expr.set_editor_property("constant", unreal.LinearColor(r, g, b, 1.0))
    unreal.MaterialEditingLibrary.connect_material_property(
        color_expr, "", unreal.MaterialProperty.MP_BASE_COLOR
    )

    rough = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant, -380, 160
    )
    rough.set_editor_property("r", roughness)
    unreal.MaterialEditingLibrary.connect_material_property(
        rough, "", unreal.MaterialProperty.MP_ROUGHNESS
    )

    unreal.MaterialEditingLibrary.layout_material_expressions(mat)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(asset_path)
    unreal.log("Created " + asset_path)
    return mat


def main():
    ensure_dir(MAT_PATH)
    # Brick reds / roof greys / wet asphalt — readable from iso altitude
    create_color_material("M_Brick_Red", 0.42, 0.18, 0.12, 0.9)
    create_color_material("M_Brick_Dark", 0.28, 0.14, 0.10, 0.92)
    create_color_material("M_Brick_Tan", 0.48, 0.36, 0.26, 0.88)
    create_color_material("M_Roof_Grey", 0.38, 0.38, 0.40, 0.75)
    create_color_material("M_Roof_Slate", 0.22, 0.26, 0.30, 0.7)
    create_color_material("M_Roof_Tar", 0.12, 0.12, 0.13, 0.65)
    create_color_material("M_Asphalt", 0.16, 0.16, 0.17, 0.8)
    create_color_material("M_Sidewalk", 0.45, 0.43, 0.40, 0.95)
    create_color_material("M_Water", 0.18, 0.28, 0.34, 0.25)
    create_color_material("M_Lamp_Iron", 0.08, 0.08, 0.09, 0.55)
    create_color_material("M_Stub_Locked", 0.35, 0.32, 0.28, 0.9)
    create_color_material("M_Ground_Dirt", 0.32, 0.28, 0.22, 0.95)
    unreal.log("Empire materials ready under " + MAT_PATH)


main()
