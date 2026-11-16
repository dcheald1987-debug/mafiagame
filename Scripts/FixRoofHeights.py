"""Final visual polish: seat roofs at ~90% crown, restore continuous roads, kill rims."""
import unreal
import os

MAP_PATH = "/Game/Maps/Empire/Levee_Greybox"
SRC_ROAD = unreal.Paths.project_content_dir() + "Art/Empire/Sprites/Source/Cropped/Roads"
TEX = "/Game/Art/Empire/Sprites/Textures"
MAT = "/Game/Art/Empire/Sprites/Materials"
FLAG = "Dress_RoofHeights_v3"

FLOOR_H = 190.0
ROAD_W = 480.0
Z_ROAD = -28.0
Z_X = -26.0
AVENUES = [2400.0, 1200.0, 0.0, -1200.0, -2400.0]
STREETS = [2400.0, 1200.0, 0.0, -1200.0, -2400.0]

PARCELS = [
    ("Row_Garage_Mass", 3),
    ("Row_Cafe_Mass", 3),
    ("Row_Dock_Mass", 2),
    ("Row_MidC_Mass", 4),
    ("Row_MidA_Mass", 4),
    ("Row_MidB_Mass", 3),
    ("Row_Bar_Mass", 3),
    ("Row_Board_Mass", 4),
    ("Row_MidD_Mass", 3),
    ("Row_MidE_Mass", 3),
    ("Row_MidF_Mass", 4),
    ("Row_MidG_Mass", 3),
    ("Row_Rope_Mass", 2),
    ("Row_Freight_Mass", 2),
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


def spawn(cls, loc, scale=None, label=None):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    a = sub.spawn_actor_from_class(cls, loc, unreal.Rotator(0, 0, 0))
    if scale is not None:
        a.set_actor_scale3d(scale)
    if label:
        a.set_actor_label(label)
    return a


def ensure_cube(label, loc, scale, mat):
    cube = unreal.load_asset("/Engine/BasicShapes/Cube")
    a = find_by_label(label)
    if a is None:
        a = spawn(unreal.StaticMeshActor, loc, scale, label)
    else:
        a.set_actor_location(loc, False, True)
        a.set_actor_scale3d(scale)
    smc = a.static_mesh_component
    smc.set_static_mesh(cube)
    if mat:
        smc.set_material(0, mat)
    smc.set_cast_shadow(False)
    a.set_actor_hidden_in_game(False)
    smc.set_visibility(True)
    return a


def main():
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not les.load_level(MAP_PATH):
        raise RuntimeError("load failed")

    destroy_prefix("RoofRim_")

    m_asphalt = unreal.load_asset("%s/M_Depth_Asphalt" % MAT) or unreal.load_asset(
        "%s/M_Custom_Asphalt" % MAT
    )
    m_lines = unreal.load_asset("%s/M_Depth_Lines" % MAT) or unreal.load_asset(
        "%s/M_Custom_RoadLines" % MAT
    ) or m_asphalt

    # Continuous roads again
    span_y = abs(STREETS[0] - STREETS[-1]) + ROAD_W * 2.0
    span_x = abs(AVENUES[0] - AVENUES[-1]) + ROAD_W * 2.0
    road_s = ROAD_W / 100.0
    for i, x in enumerate(AVENUES):
        ensure_cube(
            "Avenue_%d" % i,
            unreal.Vector(x, 0.0, Z_ROAD),
            unreal.Vector(road_s, span_y / 100.0, 0.9),
            m_lines if i % 2 == 0 else m_asphalt,
        )
    for j, y in enumerate(STREETS):
        ensure_cube(
            "Street_%d" % j,
            unreal.Vector(0.0, y, Z_ROAD),
            unreal.Vector(span_x / 100.0, road_s, 0.9),
            m_lines if j % 2 == 1 else m_asphalt,
        )
    for i, x in enumerate(AVENUES):
        for j, y in enumerate(STREETS):
            ensure_cube(
                "RoadFill_X_%d_%d" % (i, j),
                unreal.Vector(x, y, Z_X),
                unreal.Vector(road_s * 1.2, road_s * 1.2, 0.95),
                m_asphalt,
            )

    # Hide broken Fab tile remnants
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if a.get_actor_label().startswith("FabRoad_"):
            a.set_actor_hidden_in_game(True)
            smc = getattr(a, "static_mesh_component", None)
            if smc:
                smc.set_visibility(False)

    n = 0
    for label, floors in PARCELS:
        bld = find_by_label(label)
        roof = find_by_label("RoofCard_" + label)
        if not bld or not roof:
            continue
        bloc = bld.get_actor_location()
        total_h = floors * FLOOR_H
        # Visual crown for Blackthorn stretch ≈ 90% of intended height
        top_z = bloc.z + total_h * 0.90
        roof.set_actor_location(unreal.Vector(bloc.x, bloc.y, top_z + 5.0), False, True)
        # Keep roof slightly smaller than mass so walls peek as cornice depth
        rs = roof.get_actor_scale3d()
        rw = max(3.8, min(6.2, abs(rs.x) * 0.96))
        rd = max(3.8, min(6.2, abs(rs.y) * 0.96))
        roof.set_actor_scale3d(unreal.Vector(rw, rd, 0.14))
        smc = roof.static_mesh_component
        if smc:
            smc.set_cast_shadow(True)
        # Building casts volume shadow
        if bld.static_mesh_component:
            bld.static_mesh_component.set_cast_shadow(True)
        n += 1
        unreal.log("SEAT %s z=%.0f" % (label, top_z + 5.0))

        pad = find_by_label("BlockPad_%s" % label.replace("_Mass", ""))
        if pad:
            pad.set_actor_location(unreal.Vector(bloc.x, bloc.y, -22.0), False, True)

    destroy_prefix(FLAG)
    spawn(unreal.Actor, unreal.Vector(0, 0, -992), label=FLAG)
    if not les.save_current_level():
        raise RuntimeError("save failed")
    unreal.log("VISUAL POLISH OK roofs=%d roads=rebuilt" % n)


main()
