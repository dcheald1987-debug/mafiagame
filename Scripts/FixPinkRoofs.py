"""Replace missing/magenta materials on Blackthorn building meshes with dark roof/wall mats."""
import unreal

MAP_PATH = "/Game/Maps/Empire/Levee_Greybox"
MAT = "/Game/Art/Empire/Sprites/Materials"
FLAG = "Dress_PinkRoof_v1"

PARCELS = [
    "Row_Garage_Mass",
    "Row_Cafe_Mass",
    "Row_Dock_Mass",
    "Row_MidC_Mass",
    "Row_MidA_Mass",
    "Row_MidB_Mass",
    "Row_Bar_Mass",
    "Row_Board_Mass",
    "Row_MidD_Mass",
    "Row_MidE_Mass",
    "Row_MidF_Mass",
    "Row_MidG_Mass",
    "Row_Rope_Mass",
    "Row_Freight_Mass",
]


def find_by_label(label):
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if a.get_actor_label() == label:
            return a
    return None


def destroy_prefix(prefix):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    n = 0
    for a in list(sub.get_all_level_actors()):
        if a.get_actor_label().startswith(prefix):
            sub.destroy_actor(a)
            n += 1
    return n


def main():
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not les.load_level(MAP_PATH):
        raise RuntimeError("load failed")

    m_wall = (
        unreal.load_asset("%s/M_Depth_Brick" % MAT)
        or unreal.load_asset("%s/M_Custom_Brick" % MAT)
        or unreal.load_asset("%s/M_Depth_Asphalt" % MAT)
        or unreal.load_asset("%s/M_Custom_Asphalt" % MAT)
    )
    m_roof = (
        unreal.load_asset("%s/M_S_Roof_Flat" % MAT)
        or unreal.load_asset("%s/M_Custom_RoofFlat" % MAT)
        or m_wall
    )
    if not m_wall:
        raise RuntimeError("no fallback mats")

    fixed = 0
    for label in PARCELS:
        a = find_by_label(label)
        if not a or not a.static_mesh_component:
            continue
        smc = a.static_mesh_component
        n = smc.get_num_materials()
        for i in range(n):
            mat = smc.get_material(i)
            name = mat.get_name().lower() if mat else ""
            # Missing slots / WorldGrid / default pinkish error mats
            if mat is None or "worldgrid" in name or "debug" in name or "default" in name:
                smc.set_material(i, m_roof if i == 0 else m_wall)
                fixed += 1
            else:
                # Force slot 0 toward roof-dark if named roof-like
                if i == 0 and ("roof" in name or "top" in name):
                    smc.set_material(i, m_roof)
                    fixed += 1
        # Ensure at least one solid mat
        if n == 0:
            smc.set_material(0, m_wall)
            fixed += 1
        unreal.log("MAT %s slots=%d" % (label, max(n, 1)))

    destroy_prefix(FLAG)
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    marker = sub.spawn_actor_from_class(unreal.Actor, unreal.Vector(0, 0, -994))
    marker.set_actor_label(FLAG)
    if not les.save_current_level():
        raise RuntimeError("save failed")
    unreal.log("PINK ROOF FIX OK fixed_slots=%d" % fixed)


main()
