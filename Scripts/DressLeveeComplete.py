import unreal

MAP_PATH = "/Game/Maps/Empire/Levee_Greybox"
MAT = "/Game/Art/Empire/Materials"
DRESS_FLAG = "Dress_Levee_v2"


def mat(name):
    asset = unreal.load_asset("%s/%s" % (MAT, name))
    if asset is None:
        raise RuntimeError("Missing material " + name + " — run CreateEmpireMaterials.py first")
    return asset


def find_by_label(label):
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if actor.get_actor_label() == label:
            return actor
    return None


def spawn(cls, location, scale=None, label=None):
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actor = subsystem.spawn_actor_from_class(cls, location, unreal.Rotator())
    if scale is not None:
        actor.set_actor_scale3d(scale)
    if label is not None:
        actor.set_actor_label(label)
    return actor


def set_mesh_mat(actor, material):
    if actor is None:
        return
    smc = actor.static_mesh_component
    if smc is None:
        return
    smc.set_material(0, material)


def ensure_cube(label, location, scale, material):
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
    set_mesh_mat(actor, material)
    return actor


def ensure_label(label, text, location, size=130.0):
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
    tr.set_text_render_color(unreal.Color(28, 24, 18, 255))
    return actor


def main():
    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level_editor.load_level(MAP_PATH):
        raise RuntimeError("Could not load " + MAP_PATH)

    m_brick = mat("M_Brick_Red")
    m_brick_dark = mat("M_Brick_Dark")
    m_brick_tan = mat("M_Brick_Tan")
    m_roof = mat("M_Roof_Grey")
    m_roof_slate = mat("M_Roof_Slate")
    m_roof_tar = mat("M_Roof_Tar")
    m_asphalt = mat("M_Asphalt")
    m_sidewalk = mat("M_Sidewalk")
    m_water = mat("M_Water")
    m_lamp = mat("M_Lamp_Iron")
    m_stub = mat("M_Stub_Locked")
    m_ground = mat("M_Ground_Dirt")

    # Ground + streets
    set_mesh_mat(find_by_label("Ground"), m_ground)
    set_mesh_mat(find_by_label("Street_NS"), m_asphalt)
    set_mesh_mat(find_by_label("Street_EW"), m_asphalt)

    # Building bodies — alternating brick for iso block read
    buildings = [
        ("Bld_Garage", m_brick),
        ("Bld_Cafe", m_brick_tan),
        ("Bld_Dock", m_brick_dark),
        ("Bld_Bar", m_brick),
        ("Bld_Board", m_brick_tan),
        ("Bld_Freight", m_brick_dark),
        ("Bld_Rope", m_brick),
    ]
    for label, material in buildings:
        set_mesh_mat(find_by_label(label), material)

    # Roof caps (spawn if missing from v1 dress)
    roofs = [
        ("Roof_Garage", unreal.Vector(-1800.0, -1200.0, 420.0), unreal.Vector(8.2, 6.2, 0.6), m_roof),
        ("Roof_Cafe", unreal.Vector(-900.0, -1200.0, 380.0), unreal.Vector(6.2, 6.2, 0.6), m_roof_slate),
        ("Roof_Dock", unreal.Vector(600.0, -1600.0, 460.0), unreal.Vector(10.2, 7.2, 0.6), m_roof_tar),
        ("Roof_Bar", unreal.Vector(1400.0, 200.0, 380.0), unreal.Vector(7.2, 6.2, 0.6), m_roof),
        ("Roof_Board", unreal.Vector(-200.0, 900.0, 340.0), unreal.Vector(8.2, 5.2, 0.6), m_roof_slate),
        ("Roof_Freight", unreal.Vector(1800.0, 1400.0, 500.0), unreal.Vector(9.2, 8.2, 0.6), m_roof_tar),
        ("Roof_Rope", unreal.Vector(400.0, 1400.0, 300.0), unreal.Vector(12.2, 4.2, 0.5), m_roof),
    ]
    for label, loc, scale, material in roofs:
        ensure_cube(label, loc, scale, material)

    # Sidewalk ribbons along the cross
    ensure_cube("Walk_NS_W", unreal.Vector(-220.0, 0.0, -35.0), unreal.Vector(1.2, 70.0, 0.25), m_sidewalk)
    ensure_cube("Walk_NS_E", unreal.Vector(220.0, 0.0, -35.0), unreal.Vector(1.2, 70.0, 0.25), m_sidewalk)
    ensure_cube("Walk_EW_N", unreal.Vector(0.0, -220.0, -35.0), unreal.Vector(70.0, 1.2, 0.25), m_sidewalk)
    ensure_cube("Walk_EW_S", unreal.Vector(0.0, 220.0, -35.0), unreal.Vector(70.0, 1.2, 0.25), m_sidewalk)

    # Water sheet off the dock (wharf read)
    ensure_cube("Water_Dock", unreal.Vector(600.0, -2400.0, -80.0), unreal.Vector(28.0, 10.0, 0.4), m_water)

    # Block tint pads — soft ground plates under districts
    pads = [
        ("Pad_GarageBlock", unreal.Vector(-1350.0, -1050.0, -45.0), unreal.Vector(18.0, 12.0, 0.15), m_sidewalk),
        ("Pad_DockBlock", unreal.Vector(600.0, -1450.0, -45.0), unreal.Vector(14.0, 12.0, 0.15), m_sidewalk),
        ("Pad_BarBlock", unreal.Vector(1150.0, 350.0, -45.0), unreal.Vector(14.0, 12.0, 0.15), m_sidewalk),
        ("Pad_RopeBlock", unreal.Vector(100.0, 1450.0, -45.0), unreal.Vector(16.0, 12.0, 0.15), m_sidewalk),
        ("Pad_FreightBlock", unreal.Vector(1800.0, 1550.0, -45.0), unreal.Vector(14.0, 12.0, 0.15), m_sidewalk),
    ]
    for label, loc, scale, material in pads:
        ensure_cube(label, loc, scale, material)

    # Brickyard stub + lamps
    ensure_cube(
        "Stub_Brickyard",
        unreal.Vector(-2800.0, 2200.0, 200.0),
        unreal.Vector(10.0, 8.0, 4.0),
        m_stub,
    )
    for i, loc in enumerate(
        [
            unreal.Vector(-400.0, -400.0, 120.0),
            unreal.Vector(400.0, -400.0, 120.0),
            unreal.Vector(-400.0, 400.0, 120.0),
            unreal.Vector(400.0, 400.0, 120.0),
            unreal.Vector(-1600.0, -900.0, 120.0),
            unreal.Vector(1500.0, 600.0, 120.0),
        ]
    ):
        ensure_cube("Lamp_%d" % i, loc, unreal.Vector(0.35, 0.35, 3.2), m_lamp)

    # Block labels
    ensure_label("Label_Riverfront", "RIVERFRONT", unreal.Vector(-1200.0, -1600.0, 520.0))
    ensure_label("Label_Wharf", "WHARF", unreal.Vector(900.0, -1800.0, 560.0))
    ensure_label("Label_Boardwalk", "BOARDWALK", unreal.Vector(-100.0, 1100.0, 420.0))
    ensure_label("Label_Freight", "FREIGHT YARD", unreal.Vector(1800.0, 1700.0, 600.0))
    ensure_label("Label_BrickyardStub", "BRICKYARD (LOCKED)", unreal.Vector(-2800.0, 2200.0, 520.0), 110.0)
    ensure_label("Label_Barrow", "HAWSER ROW", unreal.Vector(1200.0, 200.0, 440.0), 110.0)

    # Idempotent flag
    if find_by_label(DRESS_FLAG) is None:
        flag = spawn(unreal.Actor, unreal.Vector(0.0, 0.0, 5000.0), None, DRESS_FLAG)
        flag.set_actor_hidden_in_game(True)

    if not level_editor.save_current_level():
        raise RuntimeError("save failed")
    unreal.EditorAssetLibrary.save_directory(MAT)
    unreal.log("Dress Levee v2 complete — brick blocks, roofs, water, sidewalks, materials")


main()
