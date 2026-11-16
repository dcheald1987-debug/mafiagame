"""Densify The Levee into a lifelike 1930 Near South Side / Motor Row / Levee slice.

Researched period landmarks (Near South CHRS + Motor Row district) with
streetwall massing, cornices, window bays, and specialty silhouettes
(church steeples, firehouse hose tower, White Castle turret, print plant).

Grid: Michigan→Clark × Roosevelt→26th (BuildLeveeGrid). Buildings sit in
parcels / curb setbacks — never on avenue centerlines.
"""
import unreal

MAP_PATH = "/Game/Maps/Empire/Levee_Greybox"
MAT = "/Game/Art/Empire/Materials"
FLAG = "Dress_ChicagoDense_v2"

# Road centers from BuildLeveeGrid
MICHIGAN = 1600.0
WABASH = 800.0
STATE = 0.0
DEARBORN = -800.0
CLARK = -1600.0
ROOSEVELT = 1600.0
ST16 = 800.0
ST18 = 0.0
CERMAK = -800.0
ST26 = -1600.0
ROAD_W = 220.0

# Parcel mid X between avenue pairs (east→west)
MID_MICH_WAB = (MICHIGAN + WABASH) * 0.5          # 1200
MID_WAB_STATE = (WABASH + STATE) * 0.5            # 400
MID_STATE_DEAR = (STATE + DEARBORN) * 0.5         # -400
MID_DEAR_CLARK = (DEARBORN + CLARK) * 0.5         # -1200
# East of Michigan toward lake / Calumet (Motor Row east frontage + Donnelley)
EAST_OF_MICH = MICHIGAN + ROAD_W * 0.5 + 320.0    # ~2030
WEST_OF_MICH = MICHIGAN - ROAD_W * 0.5 - 280.0    # ~1210 ≈ MID_MICH_WAB

FLOOR_H = 180.0


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


def destroy_prefix(prefix):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in list(sub.get_all_level_actors()):
        if actor.get_actor_label().startswith(prefix):
            sub.destroy_actor(actor)


def ensure_cube(label, location, scale, material, collision=True):
    actor = find_by_label(label)
    mesh = unreal.load_asset("/Engine/BasicShapes/Cube")
    if actor is None:
        actor = spawn(unreal.StaticMeshActor, location, scale, label)
        actor.static_mesh_component.set_static_mesh(mesh)
    else:
        actor.set_actor_location(location, False, True)
        actor.set_actor_scale3d(scale)
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


def ensure_label(label, text, location, size=80.0):
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
    tr.set_text_render_color(unreal.Color(36, 30, 24, 255))
    return actor


def build_streetwall(prefix, origin, footprint_xy, floors, brick, trim, roof, face_y=-1.0):
    """Chicago streetwall: mass + shop base + cornice + window bays + awning."""
    fx, fy = footprint_xy
    total_h = max(1, floors) * FLOOR_H
    front_y = origin.y + face_y * fy * 0.52

    ensure_cube(
        prefix + "_Mass",
        unreal.Vector(origin.x, origin.y, total_h * 0.5),
        unreal.Vector(fx / 100.0, fy / 100.0, total_h / 100.0),
        brick,
        collision=True,
    )
    # Storefront belt
    ensure_cube(
        prefix + "_Shop",
        unreal.Vector(origin.x, origin.y, 70.0),
        unreal.Vector(fx / 100.0 * 1.02, fy / 100.0 * 1.02, 1.4),
        trim,
        collision=False,
    )
    # Terra-cotta / limestone cornice
    ensure_cube(
        prefix + "_Cornice",
        unreal.Vector(origin.x, origin.y, total_h + 22.0),
        unreal.Vector(fx / 100.0 * 1.08, fy / 100.0 * 1.08, 0.42),
        roof,
        collision=False,
    )
    # Roof parapet strip
    ensure_cube(
        prefix + "_Parapet",
        unreal.Vector(origin.x, origin.y, total_h + 55.0),
        unreal.Vector(fx / 100.0 * 0.96, fy / 100.0 * 0.96, 0.55),
        brick,
        collision=False,
    )
    # Canvas awning over sidewalk
    ensure_cube(
        prefix + "_Awning",
        unreal.Vector(origin.x, front_y + face_y * 40.0, 130.0),
        unreal.Vector(fx / 100.0 * 0.88, 0.55, 0.12),
        mat("M_Brick_Red"),
        collision=False,
    )
    # Window bays
    panes = 5 if fx >= 550 else (4 if fx >= 400 else (3 if fx >= 280 else 2))
    pane_w = (fx * 0.82) / panes
    start_x = origin.x - (pane_w * panes) * 0.5 + pane_w * 0.5
    win = mat("M_Lamp_Iron")
    sill = mat("M_Sidewalk")
    for fl in range(floors):
        z = 110.0 + fl * FLOOR_H
        for p in range(panes):
            px = start_x + p * pane_w
            ensure_cube(
                "%s_Win_%d_%d" % (prefix, fl, p),
                unreal.Vector(px, front_y, z),
                unreal.Vector(pane_w / 100.0 * 0.62, 0.12, 0.85),
                win,
                collision=False,
            )
            ensure_cube(
                "%s_Sill_%d_%d" % (prefix, fl, p),
                unreal.Vector(px, front_y, z - 55.0),
                unreal.Vector(pane_w / 100.0 * 0.7, 0.16, 0.1),
                sill,
                collision=False,
            )


def add_steeple(prefix, origin, base_h, brick, roof):
    """Gothic / Romanesque steeple for churches."""
    ensure_cube(
        prefix + "_Steeple",
        unreal.Vector(origin.x, origin.y - 40.0, base_h + 220.0),
        unreal.Vector(1.4, 1.4, 4.4),
        brick,
        collision=False,
    )
    ensure_cube(
        prefix + "_Spire",
        unreal.Vector(origin.x, origin.y - 40.0, base_h + 480.0),
        unreal.Vector(0.7, 0.7, 2.2),
        roof,
        collision=False,
    )


def add_hose_tower(prefix, origin, base_h, brick):
    """Firehouse hose-drying tower."""
    ensure_cube(
        prefix + "_HoseTower",
        unreal.Vector(origin.x + 120.0, origin.y + 80.0, base_h + 160.0),
        unreal.Vector(1.1, 1.1, 3.2),
        brick,
        collision=False,
    )


def add_turret(prefix, origin, roof):
    """White Castle porcelain turret."""
    ensure_cube(
        prefix + "_Turret",
        unreal.Vector(origin.x + 90.0, origin.y - 60.0, 220.0),
        unreal.Vector(1.0, 1.0, 1.6),
        roof,
        collision=False,
    )
    ensure_cube(
        prefix + "_Cupola",
        unreal.Vector(origin.x + 90.0, origin.y - 60.0, 320.0),
        unreal.Vector(0.55, 0.55, 0.7),
        mat("M_Brick_Dark"),
        collision=False,
    )


def add_colonnade(prefix, origin, fx, fy, z, sill):
    """Museum colonnade suggestion along lakefront face."""
    cols = 6
    span = fx * 0.75
    start = origin.x - span * 0.5
    step = span / max(1, cols - 1)
    for i in range(cols):
        ensure_cube(
            "%s_Col_%d" % (prefix, i),
            unreal.Vector(start + i * step, origin.y - fy * 0.48, z),
            unreal.Vector(0.45, 0.45, 2.8),
            sill,
            collision=False,
        )


# ---------------------------------------------------------------------------
# LANDMARKS — researched Near South Side / Motor Row / Levee / lakefront
# Each: (label, origin, footprint_xy, floors, brick, trim, roof, extras)
# extras: None | "steeple" | "hose" | "turret" | "colonnade" | "plant"
# ---------------------------------------------------------------------------
LANDMARKS = [
    # Motor Row — Michigan Ave showrooms (1905–36 terra-cotta streetwall)
    # Ford Showroom era massing ~1444 S Michigan → near 14th/Roosevelt
    ("LM_FordShowroom", unreal.Vector(WEST_OF_MICH, (ROOSEVELT + ST16) * 0.5), (480.0, 360.0), 3,
     "M_Brick_Tan", "M_Brick_Dark", "M_Roof_Slate", None),
    # Wholesale Furniture Exposition — 1323 S Michigan (1904)
    ("LM_FurnitureExpo", unreal.Vector(WEST_OF_MICH, (ST16 + ST18) * 0.55 + 80.0), (500.0, 380.0), 5,
     "M_Brick_Tan", "M_Brick_Red", "M_Roof_Tar", None),
    # Engine Co. 104 — 1401 S Michigan (1905 firehouse)
    ("LM_Engine104", unreal.Vector(EAST_OF_MICH - 80.0, (ROOSEVELT + ST16) * 0.5 - 100.0), (360.0, 320.0), 2,
     "M_Brick_Red", "M_Brick_Dark", "M_Roof_Slate", "hose"),
    # Chess Records building site — 2120 S Michigan (1911 Motor Row showroom)
    ("LM_ChessShowroom", unreal.Vector(WEST_OF_MICH, (ST18 + CERMAK) * 0.5), (460.0, 360.0), 3,
     "M_Brick_Tan", "M_Brick_Dark", "M_Roof_Tar", None),
    # Second Presbyterian — 1936 S Michigan (1874 / 1900)
    ("LM_SecondPres", unreal.Vector(WEST_OF_MICH, (ST18 + CERMAK) * 0.5 - 200.0), (440.0, 480.0), 3,
     "M_Brick_Red", "M_Brick_Dark", "M_Roof_Slate", "steeple"),
    # Illinois Auto Club / Motor Row south end ~2400 S Michigan
    ("LM_AutoClub", unreal.Vector(WEST_OF_MICH, (CERMAK + ST26) * 0.5), (520.0, 400.0), 3,
     "M_Brick_Tan", "M_Sidewalk", "M_Roof_Slate", None),
    # More Motor Row streetwall east frontage
    ("LM_MotorRow_E1", unreal.Vector(EAST_OF_MICH, (ST16 + ST18) * 0.5), (480.0, 360.0), 4,
     "M_Brick_Tan", "M_Brick_Red", "M_Roof_Tar", None),
    ("LM_MotorRow_E2", unreal.Vector(EAST_OF_MICH, (CERMAK + ST26) * 0.5 + 100.0), (500.0, 380.0), 3,
     "M_Brick_Tan", "M_Brick_Dark", "M_Roof_Slate", None),

    # White Castle #16 — 43 E Cermak (1930 porcelain steel)
    ("LM_WhiteCastle", unreal.Vector(MID_WAB_STATE + 100.0, CERMAK + ROAD_W * 0.55 + 160.0), (260.0, 220.0), 1,
     "M_Sidewalk", "M_Brick_Dark", "M_Roof_Tar", "turret"),

    # R.R. Donnelley / Lakeside Press — 350 E Cermak (1912–25, Shaw)
    ("LM_Donnelley", unreal.Vector(EAST_OF_MICH + 200.0, CERMAK - 200.0), (900.0, 700.0), 6,
     "M_Brick_Dark", "M_Brick_Tan", "M_Roof_Tar", "plant"),
    # American Book Company — 320 E Cermak / Calumet (1912)
    ("LM_AmBookCo", unreal.Vector(EAST_OF_MICH + 100.0, CERMAK + 280.0), (560.0, 420.0), 5,
     "M_Brick_Dark", "M_Brick_Red", "M_Roof_Slate", None),

    # Prairie Avenue District
    # Glessner House — 1800 S Prairie (1886 Richardson)
    ("LM_Glessner", unreal.Vector(MID_MICH_WAB + 80.0, (ST16 + ST18) * 0.5 + 120.0), (360.0, 400.0), 3,
     "M_Brick_Dark", "M_Brick_Tan", "M_Roof_Slate", None),
    # Harriet F. Rees House — 2110 S Prairie (1888)
    ("LM_ReesHouse", unreal.Vector(MID_MICH_WAB + 40.0, (ST18 + CERMAK) * 0.5), (320.0, 360.0), 3,
     "M_Brick_Tan", "M_Brick_Dark", "M_Roof_Tar", None),
    # Clarke House — 1827 S Indiana (1836) — Indiana ≈ between Michigan & lake west fringe
    ("LM_ClarkeHouse", unreal.Vector(MID_MICH_WAB - 40.0, (ST16 + ST18) * 0.5 - 80.0), (300.0, 340.0), 2,
     "M_Brick_Tan", "M_Sidewalk", "M_Roof_Slate", None),
    # Wheeler-Kohn House — 2016 S Calumet
    ("LM_WheelerKohn", unreal.Vector(EAST_OF_MICH - 40.0, (ST18 + CERMAK) * 0.5 + 160.0), (340.0, 360.0), 3,
     "M_Brick_Red", "M_Brick_Tan", "M_Roof_Slate", None),

    # Quinn Chapel AME — 2401 S Wabash (1892)
    ("LM_QuinnChapel", unreal.Vector(MID_WAB_STATE + 60.0, (CERMAK + ST26) * 0.5), (400.0, 460.0), 3,
     "M_Brick_Red", "M_Brick_Dark", "M_Roof_Slate", "steeple"),

    # Levee dens — Clark / Dearborn between Roosevelt & Cermak (vice district era dens)
    ("LM_LeveeSaloon_A", unreal.Vector(MID_DEAR_CLARK, (ST16 + ST18) * 0.5), (420.0, 360.0), 3,
     "M_Brick_Red", "M_Brick_Dark", "M_Roof_Tar", None),
    ("LM_LeveeSaloon_B", unreal.Vector(MID_DEAR_CLARK, (ST18 + CERMAK) * 0.5), (420.0, 360.0), 4,
     "M_Brick_Dark", "M_Brick_Tan", "M_Roof_Slate", None),
    ("LM_LeveeBoard_A", unreal.Vector(MID_STATE_DEAR, (ST18 + CERMAK) * 0.5), (400.0, 360.0), 5,
     "M_Brick_Tan", "M_Brick_Dark", "M_Roof_Tar", None),
    ("LM_LeveeBoard_B", unreal.Vector(MID_STATE_DEAR, (ST16 + ST18) * 0.5), (400.0, 360.0), 4,
     "M_Brick_Red", "M_Brick_Tan", "M_Roof_Slate", None),
    ("LM_LeveeDive", unreal.Vector(MID_DEAR_CLARK - 40.0, (CERMAK + ST26) * 0.5), (380.0, 340.0), 3,
     "M_Brick_Dark", "M_Brick_Red", "M_Roof_Tar", None),

    # Printers Row / Dearborn Station edge (north toward Roosevelt)
    ("LM_PrintersA", unreal.Vector(MID_STATE_DEAR, (ROOSEVELT + ST16) * 0.5), (500.0, 420.0), 6,
     "M_Brick_Dark", "M_Brick_Red", "M_Roof_Tar", None),
    ("LM_PrintersB", unreal.Vector(MID_WAB_STATE, (ROOSEVELT + ST16) * 0.5), (500.0, 420.0), 5,
     "M_Brick_Red", "M_Brick_Dark", "M_Roof_Slate", None),
    ("LM_DearbornStation", unreal.Vector(MID_STATE_DEAR - 100.0, ROOSEVELT - ROAD_W * 0.5 - 200.0), (560.0, 380.0), 3,
     "M_Brick_Dark", "M_Sidewalk", "M_Roof_Slate", None),

    # State St commercial spine fillers
    ("LM_StateShop_A", unreal.Vector(MID_WAB_STATE - 40.0, (ST16 + ST18) * 0.5 + 60.0), (380.0, 340.0), 5,
     "M_Brick_Tan", "M_Brick_Dark", "M_Roof_Slate", None),
    ("LM_StateShop_B", unreal.Vector(MID_STATE_DEAR + 40.0, (CERMAK + ST26) * 0.5), (380.0, 340.0), 4,
     "M_Brick_Red", "M_Brick_Tan", "M_Roof_Tar", None),
    ("LM_WabashShop_A", unreal.Vector(MID_MICH_WAB - 60.0, (ROOSEVELT + ST16) * 0.5 + 40.0), (380.0, 340.0), 4,
     "M_Brick_Dark", "M_Brick_Tan", "M_Roof_Slate", None),
    ("LM_WabashShop_B", unreal.Vector(MID_WAB_STATE + 40.0, (ST18 + CERMAK) * 0.5 + 80.0), (360.0, 320.0), 3,
     "M_Brick_Tan", "M_Brick_Red", "M_Roof_Tar", None),
    ("LM_DearbornTen", unreal.Vector(MID_DEAR_CLARK + 60.0, (ROOSEVELT + ST16) * 0.5 - 40.0), (400.0, 380.0), 6,
     "M_Brick_Dark", "M_Brick_Red", "M_Roof_Tar", None),
    ("LM_ClarkWarehouse", unreal.Vector(MID_DEAR_CLARK - 80.0, (ROOSEVELT + ST16) * 0.5 + 80.0), (460.0, 400.0), 3,
     "M_Brick_Dark", "M_Lamp_Iron", "M_Roof_Tar", None),

    # Rail / river west
    ("LM_YardShed", unreal.Vector(CLARK - 500.0, ST18), (600.0, 500.0), 2,
     "M_Brick_Dark", "M_Lamp_Iron", "M_Roof_Tar", None),
    ("LM_RiverWharf", unreal.Vector(CLARK - 520.0, CERMAK), (580.0, 420.0), 2,
     "M_Brick_Dark", "M_Brick_Tan", "M_Roof_Tar", None),

    # Burnham Park lakefront — Field Museum (1921) + Soldier Field (1924)
    ("LM_FieldMuseum", unreal.Vector(EAST_OF_MICH + 700.0, ST16), (1100.0, 500.0), 3,
     "M_Sidewalk", "M_Brick_Tan", "M_Roof_Slate", "colonnade"),
    ("LM_SoldierField", unreal.Vector(EAST_OF_MICH + 700.0, CERMAK), (900.0, 600.0), 2,
     "M_Sidewalk", "M_Brick_Dark", "M_Roof_Tar", None),
    # Shedd Aquarium massing (1930) — further lake
    ("LM_Shedd", unreal.Vector(EAST_OF_MICH + 900.0, ST18 + 200.0), (520.0, 420.0), 2,
     "M_Sidewalk", "M_Brick_Tan", "M_Roof_Slate", None),
]

LABELS = [
    ("Label_MotorRow", "MOTOR ROW", unreal.Vector(MICHIGAN, ROOSEVELT + 220.0, 220.0), 80.0),
    ("Label_Levee", "THE LEVEE", unreal.Vector(MID_DEAR_CLARK, CERMAK + 200.0, 220.0), 90.0),
    ("Label_Lakeside", "LAKESIDE PRESS", unreal.Vector(EAST_OF_MICH + 200.0, CERMAK + 100.0, 280.0), 70.0),
    ("Label_Prairie", "PRAIRIE AVE", unreal.Vector(MID_MICH_WAB, ST16 + 200.0, 200.0), 70.0),
    ("Label_Printers", "PRINTERS ROW", unreal.Vector(MID_STATE_DEAR, ROOSEVELT - 100.0, 220.0), 70.0),
    ("Label_WhiteCastle", "WHITE CASTLE #16", unreal.Vector(MID_WAB_STATE + 100.0, CERMAK + 320.0, 180.0), 50.0),
]


def apply_extras(prefix, origin, footprint_xy, floors, brick, roof, extras):
    fx, fy = footprint_xy
    base_h = floors * FLOOR_H
    if extras == "steeple":
        add_steeple(prefix, origin, base_h, brick, roof)
    elif extras == "hose":
        add_hose_tower(prefix, origin, base_h, brick)
    elif extras == "turret":
        add_turret(prefix, origin, roof)
    elif extras == "colonnade":
        add_colonnade(prefix, origin, fx, fy, base_h * 0.55, mat("M_Sidewalk"))
    elif extras == "plant":
        # Donnelley plant: long loading bay + smokestack
        ensure_cube(
            prefix + "_Loading",
            unreal.Vector(origin.x - fx * 0.35, origin.y + fy * 0.35, 90.0),
            unreal.Vector(fx / 100.0 * 0.35, fy / 100.0 * 0.25, 1.8),
            mat("M_Lamp_Iron"),
            collision=False,
        )
        ensure_cube(
            prefix + "_Stack",
            unreal.Vector(origin.x + fx * 0.35, origin.y, base_h + 280.0),
            unreal.Vector(0.9, 0.9, 5.5),
            mat("M_Brick_Dark"),
            collision=False,
        )


def main():
    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level_editor.load_level(MAP_PATH):
        raise RuntimeError("load failed")

    # Clear prior dense dress (v1 + v2 parts) so we rebuild clean
    destroy_prefix("LM_")
    destroy_prefix("Label_MotorRow")
    destroy_prefix("Label_Levee")
    destroy_prefix("Label_Lakeside")
    destroy_prefix("Label_Prairie")
    destroy_prefix("Label_Printers")
    destroy_prefix("Label_WhiteCastle")
    destroy_prefix("Dress_ChicagoDense_")

    for prefix, origin, footprint, floors, bname, tname, rname, extras in LANDMARKS:
        brick = mat(bname)
        trim = mat(tname)
        roof = mat(rname)
        build_streetwall(prefix, origin, footprint, floors, brick, trim, roof)
        apply_extras(prefix, origin, footprint, floors, brick, roof, extras)

    for label, text, loc, size in LABELS:
        ensure_label(label, text, loc, size)

    spawn(unreal.Actor, unreal.Vector(0.0, 0.0, -950.0), label=FLAG)

    if not level_editor.save_current_level():
        raise RuntimeError("save failed")
    unreal.log("CHICAGO DENSE OK — landmarks=%d" % len(LANDMARKS))


main()
