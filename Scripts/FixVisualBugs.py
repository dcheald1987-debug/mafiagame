"""Kill floating RoofCards; rebuild continuous roads/pads. Blackthorn meshes keep native 3D crowns."""
import unreal

MAP_PATH = "/Game/Maps/Empire/Levee_Greybox"
MAT = "/Game/Art/Empire/Sprites/Materials"
FLAG = "Dress_VisualBugs_v1"

ROAD_W = 480.0
Z_ROAD = -28.0
Z_X = -26.0
AVENUES = [2400.0, 1200.0, 0.0, -1200.0, -2400.0]
STREETS = [2400.0, 1200.0, 0.0, -1200.0, -2400.0]

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

    n_roof = destroy_prefix("RoofCard_")
    n_rim = destroy_prefix("RoofRim_")
    unreal.log("DESTROY RoofCard=%d RoofRim=%d" % (n_roof, n_rim))

    m_asphalt = unreal.load_asset("%s/M_Depth_Asphalt" % MAT) or unreal.load_asset(
        "%s/M_Custom_Asphalt" % MAT
    )
    m_lines = unreal.load_asset("%s/M_Depth_Lines" % MAT) or unreal.load_asset(
        "%s/M_Custom_RoadLines" % MAT
    ) or m_asphalt

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

    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        lab = a.get_actor_label()
        if lab.startswith("FabRoad_"):
            a.set_actor_hidden_in_game(True)
            smc = getattr(a, "static_mesh_component", None)
            if smc:
                smc.set_visibility(False)

    # Seat block pads under buildings — no white pit voids
    for label in PARCELS:
        bld = find_by_label(label)
        if not bld:
            continue
        bloc = bld.get_actor_location()
        pad_label = "BlockPad_%s" % label.replace("_Mass", "")
        ensure_cube(
            pad_label,
            unreal.Vector(bloc.x, bloc.y, -20.0),
            unreal.Vector(6.4, 6.4, 0.35),
            m_asphalt,
        )
        if bld.static_mesh_component:
            bld.static_mesh_component.set_cast_shadow(True)

    destroy_prefix(FLAG)
    spawn(unreal.Actor, unreal.Vector(0, 0, -993), label=FLAG)
    if not les.save_current_level():
        raise RuntimeError("save failed")
    unreal.log("VISUAL BUGS OK roofs_destroyed=%d pads=%d" % (n_roof, len(PARCELS)))


main()
