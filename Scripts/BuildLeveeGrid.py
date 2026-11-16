"""1930 Chicago Near South Side / Levee — playable street replica.

Orientation (Unreal XY):
  +X east  → Lake Michigan / Illinois Central
  -X west  → South Branch + rail yards
  +Y north → Roosevelt Rd / Loop edge
  -Y south → Cermak (22nd) / 26th

Street lattice matches the historic orthogonal Chicago grid around
State–Clark × Roosevelt–Cermak (the old Levee), with Michigan Ave
Auto Row on the lake side and classic mid-block alleys.
"""
import unreal

MAP_PATH = "/Game/Maps/Empire/Levee_Greybox"
MAT = "/Game/Art/Empire/Materials"
FLAG = "Dress_Chicago1930_v2"

# N–S avenues: (label, X center) — east → west — 1200uu canyons (was 800)
AVENUES = [
    ("Michigan_Ave", 2400.0),   # Auto Row
    ("Wabash_Ave", 1200.0),
    ("State_St", 0.0),          # commercial spine / L corridor
    ("Dearborn_St", -1200.0),
    ("Clark_St", -2400.0),      # Levee west edge
]

# E–W streets: (label, Y center) — north → south
STREETS = [
    ("Roosevelt_Rd", 2400.0),   # 12th
    ("16th_St", 1200.0),
    ("18th_St", 0.0),
    ("Cermak_Rd", -1200.0),     # 22nd — Levee heart
    ("26th_St", -2400.0),
]

ROAD_W = 300.0
ALLEY_W = 80.0
Z_ROAD = -40.0
Z_WALK = -35.0
Z_WATER = -55.0
Z_L = 280.0

# Building parcels: Row_* → ((avenue_i, street_j), footprint_xy, floors)
# Cell sits between AVENUES[i]..[i+1] and STREETS[j]..[j+1]
# avenue_i 0 = Michigan|Wabash, 1 = Wabash|State, 2 = State|Dearborn, 3 = Dearborn|Clark
PARCELS = {
    # Footprints leave clear street canyons (block ~900 deep after road)
    "Row_Garage":  ((0, 2), (560.0, 500.0), 3),
    "Row_Cafe":    ((1, 2), (560.0, 500.0), 3),
    "Row_Dock":    ((0, 3), (560.0, 500.0), 2),
    "Row_MidC":    ((1, 3), (560.0, 500.0), 4),
    "Row_MidA":    ((2, 1), (560.0, 500.0), 4),
    "Row_MidB":    ((2, 2), (560.0, 500.0), 3),
    "Row_Bar":     ((3, 3), (560.0, 500.0), 3),
    "Row_Board":   ((2, 0), (560.0, 500.0), 4),
    "Row_MidD":    ((3, 1), (560.0, 500.0), 3),
    "Row_MidE":    ((3, 2), (560.0, 500.0), 3),
    "Row_MidF":    ((1, 1), (560.0, 500.0), 4),
    "Row_MidG":    ((0, 1), (560.0, 500.0), 3),
    "Row_Rope":    ((3, 0), (560.0, 460.0), 2),
    "Row_Freight": ((2, 3), (560.0, 500.0), 2),
}

# Sites on curbs (Chicago names) — parcel mids on 1200 grid
SITES = [
    ("Site_S01", "Pell's Garage", unreal.Vector(1800.0, -200.0, 40.0)),
    ("Site_S02", "Corvo Cafe", unreal.Vector(600.0, -200.0, 40.0)),
    ("Site_S03", "Dock Warehouse A", unreal.Vector(1800.0, -1400.0, 40.0)),
    ("Site_S04", "Hawser Bar", unreal.Vector(-1800.0, -1400.0, 40.0)),
    ("Site_S05", "Call Box Corner", unreal.Vector(0.0, 0.0, 40.0)),
    ("Site_S06", "Levee Boarding", unreal.Vector(-600.0, 1800.0, 40.0)),
    ("Site_S07", "Rope Walk", unreal.Vector(-1800.0, 1800.0, 40.0)),
    ("Site_S08", "Freight Office", unreal.Vector(-600.0, -1400.0, 40.0)),
]


def parcel_origin(ai, sj):
    ax0, ax1 = AVENUES[ai][1], AVENUES[ai + 1][1]
    # avenues listed east→west so ax0 > ax1
    cx = (ax0 + ax1) * 0.5
    sy0, sy1 = STREETS[sj][1], STREETS[sj + 1][1]
    # streets listed north→south so sy0 > sy1
    cy = (sy0 + sy1) * 0.5
    return unreal.Vector(cx, cy, 0.0)


def mat(name):
    asset = unreal.load_asset("%s/%s" % (MAT, name))
    if asset is None:
        raise RuntimeError("Missing " + name)
    return asset


def find_by_label(label):
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if actor.get_actor_label() == label:
            return actor
    return None


def spawn(cls, location, scale=None, label=None, rotation=None):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    rot = rotation or unreal.Rotator(0.0, 0.0, 0.0)
    actor = sub.spawn_actor_from_class(cls, location, rot)
    if scale is not None:
        actor.set_actor_scale3d(scale)
    if label is not None:
        actor.set_actor_label(label)
    return actor


def ensure_cube(label, location, scale, material, collision=False):
    actor = find_by_label(label)
    mesh = unreal.load_asset("/Engine/BasicShapes/Cube")
    if actor is None:
        actor = spawn(unreal.StaticMeshActor, location, scale, label)
        actor.static_mesh_component.set_static_mesh(mesh)
    else:
        actor.set_actor_location(location, False, True)
        actor.set_actor_scale3d(scale)
        actor.set_actor_rotation(unreal.Rotator(0.0, 0.0, 0.0), False)
        if actor.static_mesh_component.static_mesh is None:
            actor.static_mesh_component.set_static_mesh(mesh)
    smc = actor.static_mesh_component
    if material is not None:
        smc.set_material(0, material)
    smc.set_collision_enabled(
        unreal.CollisionEnabled.QUERY_AND_PHYSICS if collision else unreal.CollisionEnabled.NO_COLLISION
    )
    actor.set_actor_hidden_in_game(False)
    return actor


def ensure_label(label, text, location, size=70.0):
    actor = find_by_label(label)
    if actor is None:
        actor = spawn(unreal.TextRenderActor, location, None, label)
    else:
        actor.set_actor_location(location, False, True)
    tr = actor.get_component_by_class(unreal.TextRenderComponent)
    if tr is None:
        tr = actor.text_render
    tr.set_text(unreal.Text(text))
    tr.set_world_size(size)
    tr.set_text_render_color(unreal.Color(32, 28, 22, 255))
    tr.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
    return actor


def destroy_matching(prefixes):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in list(sub.get_all_level_actors()):
        lab = actor.get_actor_label()
        if any(lab.startswith(p) for p in prefixes):
            sub.destroy_actor(actor)


def main():
    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level_editor.load_level(MAP_PATH):
        raise RuntimeError("load failed")

    m_asphalt = mat("M_Asphalt")
    m_sidewalk = mat("M_Sidewalk")
    m_water = mat("M_Water")
    m_dirt = mat("M_Ground_Dirt")
    m_iron = mat("M_Lamp_Iron")
    m_tar = mat("M_Roof_Tar")

    destroy_matching(
        (
            "Street_",
            "Avenue_",
            "Alley_",
            "Walk_",
            "Pad_",
            "GridRoad_",
            "GridWalk_",
            "GridAlley_",
            "Lake_",
            "River_",
            "Park_",
            "Track_",
            "El_",
            "Label_Ave_",
            "Label_St_",
            "Chi_",
        )
    )
    for old in (
        "Street_NS",
        "Street_EW",
        "Street_Alley",
        "Dress_Levee_Grid_v1",
        FLAG,
    ):
        a = find_by_label(old)
        if a:
            unreal.get_editor_subsystem(unreal.EditorActorSubsystem).destroy_actor(a)

    # Ground under the street lattice
    ensure_cube(
        "Ground",
        unreal.Vector(0.0, 0.0, -50.0),
        unreal.Vector(80.0, 72.0, 1.0),
        m_sidewalk,
        collision=True,
    )

    # --- Lake Michigan (east) + Burnham/Grant park strip ---
    ensure_cube(
        "Lake_Michigan",
        unreal.Vector(4200.0, 0.0, Z_WATER),
        unreal.Vector(22.0, 70.0, 0.8),
        m_water,
        collision=False,
    )
    ensure_cube(
        "Park_Burnham",
        unreal.Vector(3200.0, 0.0, -48.0),
        unreal.Vector(6.5, 64.0, 0.4),
        m_dirt,
        collision=True,
    )
    # Illinois Central lakeside tracks
    for i, y in enumerate((-1800.0, -600.0, 600.0, 1800.0)):
        ensure_cube(
            "Track_IC_%d" % i,
            unreal.Vector(2900.0, y, -38.0),
            unreal.Vector(1.2, 7.0, 0.15),
            m_tar,
        )

    # --- South Branch of the Chicago River (west) ---
    ensure_cube(
        "River_SouthBranch",
        unreal.Vector(-3600.0, 0.0, Z_WATER),
        unreal.Vector(10.0, 70.0, 0.8),
        m_water,
        collision=False,
    )
    # Rail yards west of Clark
    for i, y in enumerate((-1800.0, -600.0, 600.0, 1800.0)):
        ensure_cube(
            "Track_Yard_%d" % i,
            unreal.Vector(-3000.0, y, -38.0),
            unreal.Vector(4.5, 6.5, 0.2),
            m_tar,
        )

    # --- N–S avenues ---
    span_y = abs(STREETS[0][1] - STREETS[-1][1]) + ROAD_W * 2.0
    for i, (name, x) in enumerate(AVENUES):
        ensure_cube(
            "Avenue_%s" % name,
            unreal.Vector(x, 0.0, Z_ROAD),
            unreal.Vector(ROAD_W / 100.0, span_y / 100.0, 0.35),
            m_asphalt,
            collision=True,
        )
        half = ROAD_W * 0.5 + 45.0
        ensure_cube(
            "Walk_%s_E" % name,
            unreal.Vector(x + half, 0.0, Z_WALK),
            unreal.Vector(0.85, span_y / 100.0, 0.25),
            m_sidewalk,
        )
        ensure_cube(
            "Walk_%s_W" % name,
            unreal.Vector(x - half, 0.0, Z_WALK),
            unreal.Vector(0.85, span_y / 100.0, 0.25),
            m_sidewalk,
        )
        pretty = name.replace("_", " ").upper()
        ensure_label("Label_Ave_%s" % name, pretty, unreal.Vector(x, STREETS[0][1] + 180.0, 120.0), 55.0)

    # --- E–W streets ---
    span_x = abs(AVENUES[0][1] - AVENUES[-1][1]) + ROAD_W * 2.0
    for j, (name, y) in enumerate(STREETS):
        ensure_cube(
            "Street_%s" % name,
            unreal.Vector(0.0, y, Z_ROAD),
            unreal.Vector(span_x / 100.0, ROAD_W / 100.0, 0.35),
            m_asphalt,
            collision=True,
        )
        half = ROAD_W * 0.5 + 45.0
        ensure_cube(
            "Walk_%s_N" % name,
            unreal.Vector(0.0, y + half, Z_WALK),
            unreal.Vector(span_x / 100.0, 0.85, 0.25),
            m_sidewalk,
        )
        ensure_cube(
            "Walk_%s_S" % name,
            unreal.Vector(0.0, y - half, Z_WALK),
            unreal.Vector(span_x / 100.0, 0.85, 0.25),
            m_sidewalk,
        )
        pretty = name.replace("_", " ").upper()
        ensure_label("Label_St_%s" % name, pretty, unreal.Vector(AVENUES[0][1] + 200.0, y, 120.0), 55.0)

    # --- Classic Chicago mid-block N–S alleys between every avenue pair ---
    alley_i = 0
    for i in range(len(AVENUES) - 1):
        x = (AVENUES[i][1] + AVENUES[i + 1][1]) * 0.5
        for j in range(len(STREETS) - 1):
            y = (STREETS[j][1] + STREETS[j + 1][1]) * 0.5
            half = abs(STREETS[j][1] - STREETS[j + 1][1]) * 0.5 - ROAD_W * 0.45
            if half < 120.0:
                continue
            ensure_cube(
                "Alley_NS_%d" % alley_i,
                unreal.Vector(x, y, Z_ROAD),
                unreal.Vector(ALLEY_W / 100.0, (half * 2.0) / 100.0, 0.28),
                m_asphalt,
                collision=True,
            )
            alley_i += 1

    # --- South Side Elevated (State St corridor, ~1930 alignment) ---
    ensure_cube(
        "El_State_Deck",
        unreal.Vector(0.0, 0.0, Z_L),
        unreal.Vector(1.4, span_y / 100.0, 0.25),
        m_iron,
        collision=False,
    )
    for k, y in enumerate((-1200.0, -400.0, 400.0, 1200.0)):
        ensure_cube(
            "El_State_Col_%d" % k,
            unreal.Vector(0.0, y, Z_L * 0.5),
            unreal.Vector(0.35, 0.35, Z_L / 100.0),
            m_iron,
        )

    # Intersection lamps on inner grid
    lamp_i = 0
    for _, x in AVENUES[1:-1]:
        for _, y in STREETS[1:-1]:
            ensure_cube(
                "StreetLamp_%d_Pole" % lamp_i,
                unreal.Vector(x + ROAD_W * 0.55, y + ROAD_W * 0.55, 180.0),
                unreal.Vector(0.28, 0.28, 3.2),
                m_iron,
            )
            lamp_i += 1

    # Snap sites
    for label, _name, loc in SITES:
        actor = find_by_label(label)
        if actor:
            actor.set_actor_location(loc, False, True)

    # District title
    ensure_label(
        "Label_District",
        "THE LEVEE — CHICAGO 1930",
        unreal.Vector(0.0, 2100.0, 200.0),
        110.0,
    )

    # Drop prior grid flags so spacing rebuild is authoritative
    for old in ("Dress_Chicago1930_v1", "Dress_Chicago1930_v2"):
        a = find_by_label(old)
        if a:
            unreal.get_editor_subsystem(unreal.EditorActorSubsystem).destroy_actor(a)
    spawn(unreal.Actor, unreal.Vector(0.0, 0.0, -800.0), label=FLAG)

    for prefix, ((ai, sj), footprint, floors) in PARCELS.items():
        origin = parcel_origin(ai, sj)
        unreal.log(
            "CHI PARCEL %s -> (%.0f, %.0f) %sx%s f=%d"
            % (prefix, origin.x, origin.y, footprint[0], footprint[1], floors)
        )

    if not level_editor.save_current_level():
        raise RuntimeError("save failed")
    unreal.log(
        "CHICAGO 1930 OK — avenues=%d streets=%d alleys=%d parcels=%d"
        % (len(AVENUES), len(STREETS), alley_i, len(PARCELS))
    )


main()
