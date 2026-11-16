"""Buildings-only fix: center each Blackthorn mesh INSIDE its sidewalk pad.

Root cause of 'buildings on roads': actor XY was at parcel center, but mesh
pivots/bounds were off-center and scales overflowed the 720uu buildable gap
between 480uu roads on the 1200uu Chicago grid.
"""
import unreal

MAP_PATH = "/Game/Maps/Empire/Levee_Greybox"
MESH_DIR = "/Game/Art/Empire/ExternalBuildings/Meshes"
FLAG = "Dress_SnapBuildings_v1"

ROAD_W = 480.0
GRID = 1200.0
# Buildable interior between two road centerlines
PAD = GRID - ROAD_W  # 720
# Leave curb margin so mass never kisses asphalt
FOOTPRINT = PAD * 0.78  # ~560
FLOOR_H = 190.0

AVENUES = [2400.0, 1200.0, 0.0, -1200.0, -2400.0]  # east → west
STREETS = [2400.0, 1200.0, 0.0, -1200.0, -2400.0]  # north → south

# (label, avenue_i, street_j, floors) — cell between AVENUES[i]..[i+1], STREETS[j]..[j+1]
PARCELS = [
    ("Row_Garage_Mass", 0, 2, 3),
    ("Row_Cafe_Mass", 1, 2, 3),
    ("Row_Dock_Mass", 0, 3, 2),
    ("Row_MidC_Mass", 1, 3, 4),
    ("Row_MidA_Mass", 2, 1, 4),
    ("Row_MidB_Mass", 2, 2, 3),
    ("Row_Bar_Mass", 3, 3, 3),
    ("Row_Board_Mass", 2, 0, 4),
    ("Row_MidD_Mass", 3, 1, 3),
    ("Row_MidE_Mass", 3, 2, 3),
    ("Row_MidF_Mass", 1, 1, 4),
    ("Row_MidG_Mass", 0, 1, 3),
    ("Row_Rope_Mass", 3, 0, 2),
    ("Row_Freight_Mass", 2, 3, 2),
]


def parcel_center(ai, sj):
    cx = (AVENUES[ai] + AVENUES[ai + 1]) * 0.5
    cy = (STREETS[sj] + STREETS[sj + 1]) * 0.5
    return cx, cy


def find_by_label(label):
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if a.get_actor_label() == label:
            return a
    return None


def destroy_prefix(prefix):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in list(sub.get_all_level_actors()):
        if a.get_actor_label().startswith(prefix):
            sub.destroy_actor(a)


def spawn(cls, loc, scale=None, label=None):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    a = sub.spawn_actor_from_class(cls, loc, unreal.Rotator(0, 0, 0))
    if scale is not None:
        a.set_actor_scale3d(scale)
    if label:
        a.set_actor_label(label)
    return a


def list_city_meshes():
    out = []
    for p in unreal.EditorAssetLibrary.list_assets(MESH_DIR, True, False):
        a = unreal.load_asset(p)
        if isinstance(a, unreal.StaticMesh) and "CityBuildings" in a.get_name():
            out.append(a)
    out.sort(key=lambda m: m.get_name())
    return out


def mesh_box(mesh):
    b = mesh.get_bounding_box()
    return b.min, b.max


def fit_building(actor, mesh, cx, cy, floors):
    """Scale to fit FOOTPRINT xy and floors*FLOOR_H; pivot so bounds center = parcel."""
    smc = actor.static_mesh_component
    smc.set_static_mesh(mesh)
    mn, mx = mesh_box(mesh)
    sx = abs(mx.x - mn.x)
    sy = abs(mx.y - mn.y)
    sz = abs(mx.z - mn.z)
    if sx < 1.0:
        sx = 100.0
    if sy < 1.0:
        sy = 100.0
    if sz < 1.0:
        sz = 100.0

    local_cx = (mn.x + mx.x) * 0.5
    local_cy = (mn.y + mx.y) * 0.5
    # Sit building bottom on z=0
    local_bottom = mn.z

    sxy = min(FOOTPRINT / sx, FOOTPRINT / sy)
    target_h = floors * FLOOR_H
    szs = target_h / sz

    # Actor loc so scaled mesh CENTER lands on (cx, cy) and bottom on ground
    ax = cx - sxy * local_cx
    ay = cy - sxy * local_cy
    az = 0.0 - szs * local_bottom

    actor.set_actor_scale3d(unreal.Vector(sxy, sxy, szs))
    actor.set_actor_location(unreal.Vector(ax, ay, az), False, True)
    actor.set_actor_rotation(unreal.Rotator(0, 0, 0), False)
    smc.set_cast_shadow(True)
    actor.set_actor_hidden_in_game(False)

    # Verify world center of bounds
    world_cx = ax + sxy * local_cx
    world_cy = ay + sxy * local_cy
    world_w = sxy * sx
    world_d = sxy * sy
    unreal.log(
        "SNAP %s mesh=%s actor=(%.0f,%.0f,%.0f) center=(%.0f,%.0f) size=%.0fx%.0f scale=%.4f"
        % (actor.get_actor_label(), mesh.get_name(), ax, ay, az, world_cx, world_cy, world_w, world_d, sxy)
    )
    return abs(world_cx - cx) < 2.0 and abs(world_cy - cy) < 2.0


def ensure_pad(label, cx, cy):
    """Visible light pad = exact buildable square (debug + ground read)."""
    cube = unreal.load_asset("/Engine/BasicShapes/Cube")
    mat = unreal.load_asset("/Game/Art/Empire/Sprites/Materials/M_WalkFill_Day")
    if mat is None:
        mat = unreal.load_asset("/Game/Art/Empire/Materials/M_Sidewalk")
    # Cube is 100uu; scale so XY = PAD
    s = PAD / 100.0
    loc = unreal.Vector(cx, cy, -20.0)
    actor = find_by_label(label)
    if actor is None:
        actor = spawn(unreal.StaticMeshActor, loc, unreal.Vector(s, s, 0.15), label)
    else:
        actor.set_actor_location(loc, False, True)
        actor.set_actor_scale3d(unreal.Vector(s, s, 0.15))
    smc = actor.static_mesh_component
    smc.set_static_mesh(cube)
    if mat:
        smc.set_material(0, mat)
    smc.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    smc.set_cast_shadow(False)
    actor.set_actor_hidden_in_game(False)


def main():
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not les.load_level(MAP_PATH):
        raise RuntimeError("load failed")

    # Remove façade cards / stray roofs so only true masses remain for this pass
    destroy_prefix("FacadeCard_")
    destroy_prefix("BlockPad_")
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in list(sub.get_all_level_actors()):
        lab = a.get_actor_label()
        if lab.startswith("Row_") and lab.endswith("_Roof"):
            sub.destroy_actor(a)

    meshes = list_city_meshes()
    if not meshes:
        raise RuntimeError("No SM_CityBuildings_* meshes")

    ok = 0
    for i, (label, ai, sj, floors) in enumerate(PARCELS):
        cx, cy = parcel_center(ai, sj)
        ensure_pad("BlockPad_%s" % label.replace("_Mass", ""), cx, cy)

        actor = find_by_label(label)
        if actor is None:
            actor = spawn(
                unreal.StaticMeshActor,
                unreal.Vector(cx, cy, 0.0),
                label=label,
            )
        mesh = meshes[i % len(meshes)]
        if fit_building(actor, mesh, cx, cy, floors):
            ok += 1

    # Kill any Row_*_Mass not in our list (strays)
    keep = set(p[0] for p in PARCELS)
    for a in list(sub.get_all_level_actors()):
        lab = a.get_actor_label()
        if lab.startswith("Row_") and lab.endswith("_Mass") and lab not in keep:
            sub.destroy_actor(a)
            unreal.log("Destroyed stray " + lab)

    destroy_prefix(FLAG)
    spawn(unreal.Actor, unreal.Vector(0, 0, -910), label=FLAG)

    if not les.save_current_level():
        raise RuntimeError("save failed")
    unreal.log(
        "SNAP BUILDINGS OK — %d/%d centered in %.0fuu pads (road=%g grid=%g)"
        % (ok, len(PARCELS), FOOTPRINT, ROAD_W, GRID)
    )


main()
