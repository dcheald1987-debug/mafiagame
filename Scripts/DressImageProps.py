"""Replace cube props with upright image cards using YOUR ElevenLabs plates."""
import unreal

MAP_PATH = "/Game/Maps/Empire/Levee_Greybox"
FLAG = "Dress_ImageProps_v1"
PLANE = "/Engine/BasicShapes/Plane"

# label, mat, loc, scale (X=width, Y=height on upright plane), yaw
SPOTS = [
    ("ImgProp_Crates_A", "M_Sprite_Prop_DockCrates", unreal.Vector(2000.0, -2000.0, 90.0), unreal.Vector(2.2, 1.6, 1.0), 20.0),
    ("ImgProp_Crates_B", "M_Sprite_Prop_DockCrates", unreal.Vector(-400.0, -2000.0, 90.0), unreal.Vector(2.0, 1.5, 1.0), -30.0),
    ("ImgProp_CallBox_A", "M_Sprite_Prop_CallBox", unreal.Vector(280.0, 280.0, 70.0), unreal.Vector(0.55, 1.4, 1.0), 45.0),
    ("ImgProp_CallBox_B", "M_Sprite_Prop_CallBox", unreal.Vector(-2120.0, -920.0, 70.0), unreal.Vector(0.55, 1.4, 1.0), -45.0),
    ("ImgProp_Lamp_A", "M_Sprite_Prop_StreetLamp", unreal.Vector(240.0, -240.0, 160.0), unreal.Vector(0.45, 2.8, 1.0), 0.0),
    ("ImgProp_Lamp_B", "M_Sprite_Prop_StreetLamp", unreal.Vector(-240.0, 240.0, 160.0), unreal.Vector(0.45, 2.8, 1.0), 90.0),
    ("ImgProp_Lamp_C", "M_Sprite_Prop_StreetLamp", unreal.Vector(1440.0, -1440.0, 160.0), unreal.Vector(0.45, 2.8, 1.0), 45.0),
    ("ImgProp_Lamp_D", "M_Sprite_Prop_StreetLamp", unreal.Vector(-1440.0, 1440.0, 160.0), unreal.Vector(0.45, 2.8, 1.0), -45.0),
    ("ImgProp_Lamp_E", "M_Sprite_Prop_StreetLamp", unreal.Vector(2160.0, 0.0, 160.0), unreal.Vector(0.45, 2.8, 1.0), 0.0),
    ("ImgProp_Lamp_F", "M_Sprite_Prop_StreetLamp", unreal.Vector(-2160.0, 0.0, 160.0), unreal.Vector(0.45, 2.8, 1.0), 0.0),
]


def destroy_prefix(prefix):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in list(sub.get_all_level_actors()):
        if actor.get_actor_label().startswith(prefix):
            sub.destroy_actor(actor)


def main():
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(MAP_PATH)
    destroy_prefix("Prop_")
    destroy_prefix("ImgProp_")
    plane = unreal.load_asset(PLANE)
    n = 0
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for label, mat_name, loc, scale, yaw in SPOTS:
        mat = unreal.load_asset("/Game/Art/Empire/Sprites/Materials/%s" % mat_name)
        if not mat or not plane:
            unreal.log_warning("skip " + label)
            continue
        # Upright: Pitch 0, Roll 90 — same as character cards (avoids giant ortho wedges)
        actor = sub.spawn_actor_from_class(
            unreal.StaticMeshActor, loc, unreal.Rotator(0.0, yaw, 90.0)
        )
        actor.set_actor_label(label)
        actor.set_actor_scale3d(scale)
        smc = actor.static_mesh_component
        smc.set_static_mesh(plane)
        smc.set_material(0, mat)
        smc.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        smc.set_cast_shadow(False)
        n += 1
    # flag
    destroy_prefix(FLAG)
    flag = sub.spawn_actor_from_class(unreal.Actor, unreal.Vector(0.0, 0.0, -520.0))
    flag.set_actor_label(FLAG)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    unreal.log("DressImageProps: %d image cards" % n)


main()
