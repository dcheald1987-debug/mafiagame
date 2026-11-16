import unreal

MAP_PATH = "/Game/Maps/Empire/Levee_Greybox"


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


def main():
    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level_editor.load_level(MAP_PATH):
        raise RuntimeError("Could not load " + MAP_PATH)

    if find_by_label("Stub_Brickyard"):
        unreal.log("Levee dress already applied")
        return

    mesh = unreal.load_asset("/Engine/BasicShapes/Cube")

    # Taller roof caps for isometric read
    roofs = [
        ("Roof_Garage", unreal.Vector(-1800.0, -1200.0, 420.0), unreal.Vector(8.2, 6.2, 0.6)),
        ("Roof_Cafe", unreal.Vector(-900.0, -1200.0, 380.0), unreal.Vector(6.2, 6.2, 0.6)),
        ("Roof_Dock", unreal.Vector(600.0, -1600.0, 460.0), unreal.Vector(10.2, 7.2, 0.6)),
        ("Roof_Bar", unreal.Vector(1400.0, 200.0, 380.0), unreal.Vector(7.2, 6.2, 0.6)),
        ("Roof_Board", unreal.Vector(-200.0, 900.0, 340.0), unreal.Vector(8.2, 5.2, 0.6)),
        ("Roof_Freight", unreal.Vector(1800.0, 1400.0, 500.0), unreal.Vector(9.2, 8.2, 0.6)),
        ("Roof_Rope", unreal.Vector(400.0, 1400.0, 300.0), unreal.Vector(12.2, 4.2, 0.5)),
    ]
    for label, loc, scale in roofs:
        actor = spawn(unreal.StaticMeshActor, loc, scale, label)
        actor.static_mesh_component.set_static_mesh(mesh)

    # Brickyard stub — locked district marker off the Levee edge
    stub = spawn(
        unreal.StaticMeshActor,
        unreal.Vector(-2800.0, 2200.0, 200.0),
        unreal.Vector(10.0, 8.0, 4.0),
        "Stub_Brickyard",
    )
    stub.static_mesh_component.set_static_mesh(mesh)

    # Corner street lamps as vertical sticks
    for i, loc in enumerate(
        [
            unreal.Vector(-400.0, -400.0, 120.0),
            unreal.Vector(400.0, -400.0, 120.0),
            unreal.Vector(-400.0, 400.0, 120.0),
            unreal.Vector(400.0, 400.0, 120.0),
        ]
    ):
        lamp = spawn(unreal.StaticMeshActor, loc, unreal.Vector(0.4, 0.4, 3.0), "Lamp_%d" % i)
        lamp.static_mesh_component.set_static_mesh(mesh)

    # Block labels readable from iso
    blocks = [
        ("Label_Riverfront", "RIVERFRONT", unreal.Vector(-1200.0, -1600.0, 520.0)),
        ("Label_Wharf", "WHARF", unreal.Vector(900.0, -1800.0, 560.0)),
        ("Label_Boardwalk", "BOARDWALK", unreal.Vector(-100.0, 1100.0, 420.0)),
        ("Label_Freight", "FREIGHT YARD", unreal.Vector(1800.0, 1700.0, 600.0)),
        ("Label_BrickyardStub", "BRICKYARD (LOCKED)", unreal.Vector(-2800.0, 2200.0, 520.0)),
    ]
    for label, text, loc in blocks:
        actor = spawn(unreal.TextRenderActor, loc, None, label)
        tr = actor.get_component_by_class(unreal.TextRenderComponent)
        if tr is None:
            tr = actor.text_render
        tr.set_text(unreal.Text(text))
        tr.set_world_size(120.0)
        tr.set_text_render_color(unreal.Color(28, 24, 18, 255))

    if not level_editor.save_current_level():
        raise RuntimeError("save failed")
    unreal.log("Dressed Levee greybox with roofs, lamps, labels, Brickyard stub")


main()
