"""Apply period building skins to Levee row massing (including dense façade extras)."""
import unreal

MAP_PATH = "/Game/Maps/Empire/Levee_Greybox"
SKIN = "/Game/Art/Empire/Materials/Skins"


def skin(name):
    asset = unreal.load_asset("%s/%s" % (SKIN, name))
    if asset is None:
        raise RuntimeError("Missing skin " + name)
    return asset


def find_by_label(label):
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if actor.get_actor_label() == label:
            return actor
    return None


def set_mat(label, material):
    actor = find_by_label(label)
    if actor is None:
        return False
    smc = getattr(actor, "static_mesh_component", None)
    if smc is None:
        return False
    smc.set_material(0, material)
    return True


def set_mat_prefix(prefix, material):
    """Skin every actor whose label starts with prefix (e.g. Row_Garage_Win_)."""
    n = 0
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        label = actor.get_actor_label()
        if label.startswith(prefix):
            smc = getattr(actor, "static_mesh_component", None)
            if smc:
                smc.set_material(0, material)
                n += 1
    return n


def apply_row(prefix, mass, shop, win, cornice, roof, stoop=None, trim=None):
    trim = trim or shop
    set_mat(prefix + "_Mass", mass)
    set_mat(prefix + "_Shopfront", shop)
    set_mat_prefix(prefix + "_Win_", win)
    set_mat(prefix + "_Cornice", cornice)
    set_mat(prefix + "_Roof", roof)
    set_mat(prefix + "_Stoop", stoop or shop)
    set_mat(prefix + "_PilasterL", trim)
    set_mat(prefix + "_PilasterR", trim)
    set_mat(prefix + "_Door", trim)
    set_mat(prefix + "_Awning", roof)
    set_mat(prefix + "_Chimney", mass)
    set_mat(prefix + "_DockLedge", trim)
    set_mat_prefix(prefix + "_FireEsc", trim)


def main():
    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level_editor.load_level(MAP_PATH):
        raise RuntimeError("load failed")

    brick_red = skin("M_Skin_BrickRed")
    brick_soot = skin("M_Skin_BrickSoot")
    brick_tan = skin("M_Skin_BrickTan")
    brick_paint = skin("M_Skin_BrickPainted")
    sandstone = skin("M_Skin_Sandstone")
    cream = skin("M_Skin_TenementCream")
    olive = skin("M_Skin_TenementOlive")
    cast = skin("M_Skin_CastIron")
    wood = skin("M_Skin_WoodTrim")
    copper = skin("M_Skin_CopperCornice")
    tin = skin("M_Skin_RoofTin")
    tar = skin("M_Skin_RoofTar")
    win_dark = skin("M_Skin_WindowDark")
    win_warm = skin("M_Skin_WindowWarm")
    win_green = skin("M_Skin_WindowGreen")

    apply_row("Row_Garage", brick_red, cast, win_dark, copper, tar, wood, cast)
    apply_row("Row_Cafe", cream, wood, win_warm, copper, tin, wood, wood)
    apply_row("Row_Dock", brick_soot, cast, win_dark, cast, tar, cast, cast)
    apply_row("Row_Bar", brick_tan, wood, win_warm, copper, tin, wood, wood)
    apply_row("Row_Board", brick_paint, wood, win_green, copper, tin, wood, wood)
    apply_row("Row_Freight", brick_soot, cast, win_dark, cast, tar, cast, cast)
    apply_row("Row_Rope", brick_red, wood, win_dark, copper, tar, wood, wood)

    apply_row("Row_MidA", brick_red, cast, win_warm, copper, tin, cast, cast)
    apply_row("Row_MidB", sandstone, wood, win_dark, copper, tin, wood, wood)
    apply_row("Row_MidC", brick_tan, cast, win_warm, copper, tar, cast, cast)
    apply_row("Row_MidD", olive, wood, win_green, copper, tin, wood, wood)
    apply_row("Row_MidE", cream, wood, win_warm, copper, tin, wood, wood)
    apply_row("Row_MidF", brick_soot, cast, win_dark, cast, tar, cast, cast)
    apply_row("Row_MidG", brick_red, wood, win_warm, copper, tin, wood, wood)

    if not level_editor.save_current_level():
        raise RuntimeError("save failed")
    unreal.EditorAssetLibrary.save_directory(SKIN)
    unreal.log("BUILDING SKINS APPLIED")


main()
