"""Create 1920s/30s building façade skins — procedural brick / stone / shopfront / windows."""
import unreal

MAT_PATH = "/Game/Art/Empire/Materials/Skins"


def ensure_dir(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def _delete_if_exists(asset_path):
    if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        unreal.EditorAssetLibrary.delete_asset(asset_path)
    # Force-clear package so unattended recreate works
    pkg = asset_path
    if unreal.EditorAssetLibrary.does_asset_exist(pkg):
        unreal.EditorAssetLibrary.delete_asset(pkg)


def create_flat(name, r, g, b, roughness=0.85, metallic=0.0, emissive=None):
    asset_path = "%s/%s" % (MAT_PATH, name)
    _delete_if_exists(asset_path)
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    mat = asset_tools.create_asset(name, MAT_PATH, unreal.Material, unreal.MaterialFactoryNew())
    if mat is None:
        raise RuntimeError("Failed " + name)

    color = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant3Vector, -400, 0
    )
    color.set_editor_property("constant", unreal.LinearColor(r, g, b, 1.0))
    unreal.MaterialEditingLibrary.connect_material_property(color, "", unreal.MaterialProperty.MP_BASE_COLOR)

    rough = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant, -400, 140
    )
    rough.set_editor_property("r", roughness)
    unreal.MaterialEditingLibrary.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)

    if metallic > 0.0:
        met = unreal.MaterialEditingLibrary.create_material_expression(
            mat, unreal.MaterialExpressionConstant, -400, 220
        )
        met.set_editor_property("r", metallic)
        unreal.MaterialEditingLibrary.connect_material_property(met, "", unreal.MaterialProperty.MP_METALLIC)

    if emissive is not None:
        em = unreal.MaterialEditingLibrary.create_material_expression(
            mat, unreal.MaterialExpressionConstant3Vector, -400, 300
        )
        em.set_editor_property(
            "constant", unreal.LinearColor(emissive[0], emissive[1], emissive[2], 1.0)
        )
        unreal.MaterialEditingLibrary.connect_material_property(em, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

    unreal.MaterialEditingLibrary.layout_material_expressions(mat)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(asset_path)
    unreal.log("Skin " + name)
    return mat


def create_brick_skin(name, brick_rgb, mortar_rgb, tile_u=8.0, tile_v=16.0, roughness=0.9):
    """Procedural running-bond brick from UV frac — readable at iso distance."""
    asset_path = "%s/%s" % (MAT_PATH, name)
    _delete_if_exists(asset_path)
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    mat = asset_tools.create_asset(name, MAT_PATH, unreal.Material, unreal.MaterialFactoryNew())
    if mat is None:
        raise RuntimeError("Failed " + name)

    # UVs
    texcoord = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionTextureCoordinate, -900, 0
    )
    # Scale UV
    mul = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionMultiply, -700, 0
    )
    scale = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant2Vector, -900, 120
    )
    # UE5.8: Constant2Vector exposes R/G, not a Vector2D "constant"
    scale.set_editor_property("r", float(tile_u))
    scale.set_editor_property("g", float(tile_v))
    unreal.MaterialEditingLibrary.connect_material_expressions(texcoord, "", mul, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(scale, "", mul, "B")

    # Frac for tile
    frac_n = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionFrac, -520, 0
    )
    unreal.MaterialEditingLibrary.connect_material_expressions(mul, "", frac_n, "")

    # Component mask R/G as U/V in cell
    mask = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionComponentMask, -360, 0
    )
    mask.set_editor_property("r", True)
    mask.set_editor_property("g", True)
    mask.set_editor_property("b", False)
    mask.set_editor_property("a", False)
    unreal.MaterialEditingLibrary.connect_material_expressions(frac_n, "", mask, "")

    # Cheap mortar: edges of cell (Abs of (uv-0.5) style via subtract + abs)
    # Use Append + custom via two channels: if U near 0/1 or V near 0/1 → mortar
    # Simpler: Power on distance-to-edge approximation using Abs(Frac*2-1)
    sub = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionSubtract, -200, 80
    )
    half = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant, -360, 160
    )
    half.set_editor_property("r", 0.5)
    # Frac already 0-1; Abs(2*frac-1) via multiply then subtract — use OneMinus Abs trick
    # mortar_mask = saturate( (edge) ) where edge = max( abs(u-0.5), abs(v-0.5) ) > 0.42
    abs_n = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionAbs, -40, 80
    )
    # (frac - 0.5)
    unreal.MaterialEditingLibrary.connect_material_expressions(frac_n, "", sub, "A")
    # Constant3 so subtract works on vector — use Constant3Vector 0.5
    half3 = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant3Vector, -360, 200
    )
    half3.set_editor_property("constant", unreal.LinearColor(0.5, 0.5, 0.5, 1.0))
    unreal.MaterialEditingLibrary.connect_material_expressions(half3, "", sub, "B")
    unreal.MaterialEditingLibrary.connect_material_expressions(sub, "", abs_n, "")

    # Multiply by 2
    mul2 = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionMultiply, 120, 80
    )
    two = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant, 0, 160
    )
    two.set_editor_property("r", 2.0)
    unreal.MaterialEditingLibrary.connect_material_expressions(abs_n, "", mul2, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(two, "", mul2, "B")

    # Component mask to get max-ish via Add of R+G then cheap threshold
    mask2 = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionComponentMask, 280, 80
    )
    mask2.set_editor_property("r", True)
    mask2.set_editor_property("g", True)
    mask2.set_editor_property("b", False)
    mask2.set_editor_property("a", False)
    unreal.MaterialEditingLibrary.connect_material_expressions(mul2, "", mask2, "")

    add_rg = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionAdd, 440, 80
    )
    # Split: use Append isn't needed — Add on float2 adds components? In UE Add on float2 returns float2.
    # Use Break then Max
    break_n = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionBreakMaterialAttributes, 280, 200
    )
    # BreakMaterialAttributes needs material attributes — wrong.
    # Use ComponentMask R and G separately
    mask_r = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionComponentMask, 280, 40
    )
    mask_r.set_editor_property("r", True)
    mask_r.set_editor_property("g", False)
    mask_r.set_editor_property("b", False)
    mask_r.set_editor_property("a", False)
    unreal.MaterialEditingLibrary.connect_material_expressions(mul2, "", mask_r, "")

    mask_g = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionComponentMask, 280, 120
    )
    mask_g.set_editor_property("r", False)
    mask_g.set_editor_property("g", True)
    mask_g.set_editor_property("b", False)
    mask_g.set_editor_property("a", False)
    unreal.MaterialEditingLibrary.connect_material_expressions(mul2, "", mask_g, "")

    max_n = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionMax, 460, 80
    )
    unreal.MaterialEditingLibrary.connect_material_expressions(mask_r, "", max_n, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(mask_g, "", max_n, "B")

    # Smooth step-ish: Power to push mortar to edges
    power = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionPower, 620, 80
    )
    exp = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant, 460, 160
    )
    exp.set_editor_property("r", 8.0)
    unreal.MaterialEditingLibrary.connect_material_expressions(max_n, "", power, "Base")
    unreal.MaterialEditingLibrary.connect_material_expressions(exp, "", power, "Exp")

    brick_c = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant3Vector, 620, -40
    )
    brick_c.set_editor_property(
        "constant", unreal.LinearColor(brick_rgb[0], brick_rgb[1], brick_rgb[2], 1.0)
    )
    mortar_c = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant3Vector, 620, 160
    )
    mortar_c.set_editor_property(
        "constant", unreal.LinearColor(mortar_rgb[0], mortar_rgb[1], mortar_rgb[2], 1.0)
    )

    lerp = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionLinearInterpolate, 820, 40
    )
    unreal.MaterialEditingLibrary.connect_material_expressions(brick_c, "", lerp, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(mortar_c, "", lerp, "B")
    unreal.MaterialEditingLibrary.connect_material_expressions(power, "", lerp, "Alpha")
    unreal.MaterialEditingLibrary.connect_material_property(lerp, "", unreal.MaterialProperty.MP_BASE_COLOR)

    rough = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant, 820, 200
    )
    rough.set_editor_property("r", roughness)
    unreal.MaterialEditingLibrary.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)

    unreal.MaterialEditingLibrary.layout_material_expressions(mat)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(asset_path)
    unreal.log("Brick skin " + name)
    return mat


def main():
    ensure_dir(MAT_PATH)

    # --- Brick façades (flat period colours — procedural brick graphs fail SM5/SM6 cook) ---
    create_flat("M_Skin_BrickRed", 0.45, 0.18, 0.12, 0.92)
    create_flat("M_Skin_BrickSoot", 0.22, 0.14, 0.12, 0.94)
    create_flat("M_Skin_BrickTan", 0.52, 0.38, 0.26, 0.9)
    create_flat("M_Skin_BrickPainted", 0.62, 0.58, 0.50, 0.88)

    # --- Stone / tenement ---
    create_flat("M_Skin_Sandstone", 0.58, 0.48, 0.36, 0.78)
    create_flat("M_Skin_Limestone", 0.72, 0.68, 0.58, 0.7)
    create_flat("M_Skin_TenementCream", 0.68, 0.62, 0.50, 0.86)
    create_flat("M_Skin_TenementOlive", 0.38, 0.40, 0.30, 0.88)

    # --- Shopfront / trim / roof ---
    create_flat("M_Skin_CastIron", 0.08, 0.08, 0.09, 0.45, metallic=0.55)
    create_flat("M_Skin_WoodTrim", 0.28, 0.18, 0.10, 0.75)
    create_flat("M_Skin_CopperCornice", 0.35, 0.28, 0.16, 0.4, metallic=0.65)
    create_flat("M_Skin_RoofTin", 0.30, 0.32, 0.34, 0.35, metallic=0.7)
    create_flat("M_Skin_RoofTar", 0.10, 0.10, 0.11, 0.7)
    create_flat("M_Skin_AwningStripe", 0.55, 0.12, 0.10, 0.8)

    # --- Windows ---
    create_flat("M_Skin_WindowDark", 0.05, 0.07, 0.09, 0.15, metallic=0.2)
    create_flat("M_Skin_WindowWarm", 0.12, 0.08, 0.04, 0.2, emissive=(0.35, 0.22, 0.08))
    create_flat("M_Skin_WindowGreen", 0.08, 0.12, 0.08, 0.18, metallic=0.15)

    unreal.log("BUILDING SKINS OK under " + MAT_PATH)


main()
