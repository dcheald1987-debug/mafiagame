"""Full-3D 1920s/30s Levee street densify — brick façades, sidewalks, warm lamps, StreetDirector."""
import unreal

MAP_PATH = "/Game/Maps/Empire/Levee_Greybox"
MAT = "/Game/Art/Empire/Materials"
FLAG = "Dress_Levee_Street_v1"


def mat(name):
    asset = unreal.load_asset("%s/%s" % (MAT, name))
    if asset is None:
        raise RuntimeError("Missing material " + name)
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
    smc = getattr(actor, "static_mesh_component", None)
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


def ensure_label(label, text, location, size=100.0):
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


def ensure_point_light(label, location, intensity=8000.0, temp=2800.0):
    actor = find_by_label(label)
    if actor is None:
        actor = spawn(unreal.PointLight, location, None, label)
    else:
        actor.set_actor_location(location, False, True)
    light = actor.get_component_by_class(unreal.PointLightComponent)
    if light:
        light.set_intensity(intensity)
        light.set_light_color(unreal.LinearColor(1.0, 0.72, 0.45, 1.0))
        try:
            light.set_editor_property("temperature", temp)
            light.set_editor_property("use_temperature", True)
        except Exception:
            pass
        light.set_attenuation_radius(1800.0)
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
    m_asphalt = mat("M_Asphalt")
    m_sidewalk = mat("M_Sidewalk")
    m_lamp = mat("M_Lamp_Iron")

    # Denser mid-block façades (period row houses / warehouses)
    densify = [
        ("Facade_A", unreal.Vector(-1400.0, -400.0, 180.0), unreal.Vector(4.0, 5.0, 3.6), m_brick),
        ("Facade_B", unreal.Vector(-600.0, -500.0, 160.0), unreal.Vector(3.5, 4.5, 3.2), m_brick_tan),
        ("Facade_C", unreal.Vector(200.0, -900.0, 200.0), unreal.Vector(5.0, 4.0, 4.0), m_brick_dark),
        ("Facade_D", unreal.Vector(900.0, -200.0, 170.0), unreal.Vector(4.0, 4.0, 3.4), m_brick),
        ("Facade_E", unreal.Vector(500.0, 600.0, 150.0), unreal.Vector(3.8, 5.0, 3.0), m_brick_tan),
        ("Facade_F", unreal.Vector(-1000.0, 700.0, 190.0), unreal.Vector(4.5, 4.0, 3.8), m_brick_dark),
        ("Facade_G", unreal.Vector(1600.0, 800.0, 210.0), unreal.Vector(5.0, 5.0, 4.2), m_brick),
        ("Facade_H", unreal.Vector(-200.0, -1500.0, 160.0), unreal.Vector(6.0, 3.5, 3.2), m_brick_tan),
        ("Cornice_A", unreal.Vector(-1400.0, -400.0, 380.0), unreal.Vector(4.2, 5.2, 0.35), m_roof),
        ("Cornice_B", unreal.Vector(-600.0, -500.0, 340.0), unreal.Vector(3.7, 4.7, 0.35), m_roof_slate),
        ("Cornice_C", unreal.Vector(200.0, -900.0, 420.0), unreal.Vector(5.2, 4.2, 0.35), m_roof),
        ("Cornice_G", unreal.Vector(1600.0, 800.0, 440.0), unreal.Vector(5.2, 5.2, 0.35), m_roof_slate),
    ]
    for label, loc, scale, material in densify:
        ensure_cube(label, loc, scale, material)

    # Extra sidewalk tongues
    ensure_cube("Walk_Alley_N", unreal.Vector(-800.0, 400.0, -35.0), unreal.Vector(12.0, 1.0, 0.25), m_sidewalk)
    ensure_cube("Walk_Alley_S", unreal.Vector(700.0, -600.0, -35.0), unreal.Vector(10.0, 1.0, 0.25), m_sidewalk)
    ensure_cube("Street_Alley", unreal.Vector(-800.0, 200.0, -40.0), unreal.Vector(1.5, 18.0, 0.2), m_asphalt)

    # Warm tungsten street mood (1920s/30s)
    lamps = [
        ("StreetLamp_0", unreal.Vector(-300.0, -300.0, 280.0)),
        ("StreetLamp_1", unreal.Vector(300.0, -300.0, 280.0)),
        ("StreetLamp_2", unreal.Vector(-300.0, 300.0, 280.0)),
        ("StreetLamp_3", unreal.Vector(300.0, 300.0, 280.0)),
        ("StreetLamp_4", unreal.Vector(-1500.0, -1000.0, 280.0)),
        ("StreetLamp_5", unreal.Vector(1400.0, 500.0, 280.0)),
        ("StreetLamp_6", unreal.Vector(600.0, -1400.0, 280.0)),
    ]
    for label, loc in lamps:
        ensure_cube(label + "_Pole", loc - unreal.Vector(0, 0, 100), unreal.Vector(0.3, 0.3, 3.5), m_lamp)
        ensure_point_light(label, loc, 9000.0, 2700.0)

    ensure_label("Label_Corner_Hawser", "HAWSER RD", unreal.Vector(200.0, 100.0, 360.0), 90.0)
    ensure_label("Label_Corner_Wharf", "WHARF ST", unreal.Vector(100.0, -400.0, 360.0), 90.0)

    # StreetDirector placeholder (runtime also spawns from GameMode)
    if find_by_label("StreetDirector") is None:
        cls = unreal.load_class(None, "/Script/LostEmpire.LEStreetDirector")
        if cls:
            d = spawn(cls, unreal.Vector(0.0, 0.0, 60.0), None, "StreetDirector")
            unreal.log("Spawned StreetDirector")
        else:
            unreal.log_warning("LEStreetDirector not loaded yet — GameMode will spawn at runtime")

    if find_by_label(FLAG) is None:
        flag = spawn(unreal.Actor, unreal.Vector(0.0, 0.0, 5100.0), None, FLAG)
        flag.set_actor_hidden_in_game(True)

    if not level_editor.save_current_level():
        raise RuntimeError("save failed")
    unreal.log("STREET DRESS OK — 1930s dense Levee")


main()
