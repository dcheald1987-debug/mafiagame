"""Lay Fab modular roads (480uu) + snap buildings onto parcel centers (not random)."""
import unreal
import os
import runpy

MAP_PATH = "/Game/Maps/Empire/Levee_Greybox"
ROAD_FBX = unreal.Paths.project_dir() + "Art/Fab/ModularRoads/source/Raods.fbx"
DEST_ROAD = "/Game/Art/Empire/FabRoads"
FLAG = "Dress_FabRoadsParcels_v1"

ROAD_W = 480.0
Z_ROAD = -30.0

AVENUES = [
    ("Michigan_Ave", 2400.0),
    ("Wabash_Ave", 1200.0),
    ("State_St", 0.0),
    ("Dearborn_St", -1200.0),
    ("Clark_St", -2400.0),
]
STREETS = [
    ("Roosevelt_Rd", 2400.0),
    ("16th_St", 1200.0),
    ("18th_St", 0.0),
    ("Cermak_Rd", -1200.0),
    ("26th_St", -2400.0),
]

# Parcel centers between avenues/streets (same as building dress)
PARCELS = [
    ("Row_Garage_Mass", 1800.0, -600.0, 560.0, 500.0, 3),
    ("Row_Cafe_Mass", 600.0, -600.0, 560.0, 500.0, 3),
    ("Row_Dock_Mass", 1800.0, -1800.0, 560.0, 500.0, 2),
    ("Row_MidC_Mass", 600.0, -1800.0, 560.0, 500.0, 4),
    ("Row_MidA_Mass", -600.0, 600.0, 560.0, 500.0, 4),
    ("Row_MidB_Mass", -600.0, -600.0, 560.0, 500.0, 3),
    ("Row_Bar_Mass", -1800.0, -1800.0, 560.0, 500.0, 3),
    ("Row_Board_Mass", -600.0, 1800.0, 560.0, 500.0, 4),
    ("Row_MidD_Mass", -1800.0, 600.0, 560.0, 500.0, 3),
    ("Row_MidE_Mass", -1800.0, -600.0, 560.0, 500.0, 3),
    ("Row_MidF_Mass", 600.0, 600.0, 560.0, 500.0, 4),
    ("Row_MidG_Mass", 1800.0, 600.0, 560.0, 500.0, 3),
    ("Row_Rope_Mass", -1800.0, 1800.0, 560.0, 460.0, 2),
    ("Row_Freight_Mass", -600.0, -1800.0, 560.0, 500.0, 2),
]
FLOOR_H = 190.0


def find_by_label(label):
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if actor.get_actor_label() == label:
            return actor
    return None


def spawn(cls, location, scale=None, label=None, rotation=None):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    rot = rotation or unreal.Rotator(0, 0, 0)
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


def ensure_dir(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def mesh_extent(mesh):
    try:
        box = mesh.get_bounding_box()
        return (
            abs(box.max.x - box.min.x),
            abs(box.max.y - box.min.y),
            abs(box.max.z - box.min.z),
        )
    except Exception:
        return (400.0, 400.0, 50.0)


def list_static_meshes(path):
    out = []
    for p in unreal.EditorAssetLibrary.list_assets(path, True, False):
        a = unreal.load_asset(p)
        if isinstance(a, unreal.StaticMesh):
            out.append(a)
    return out


def import_road_fbx():
    ensure_dir(DEST_ROAD)
    disk = os.path.normpath(ROAD_FBX)
    if not os.path.isfile(disk):
        raise RuntimeError("Missing " + disk)
    # Skip reimport if meshes already present
    existing = list_static_meshes(DEST_ROAD)
    if existing:
        unreal.log("Fab roads already imported (%d)" % len(existing))
        return existing

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", disk)
    task.set_editor_property("destination_path", DEST_ROAD)
    task.set_editor_property("destination_name", "SM_ModularRoads")
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)
    options = unreal.FbxImportUI()
    options.set_editor_property("automated_import_should_detect_type", False)
    options.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_STATIC_MESH)
    options.set_editor_property("original_import_type", unreal.FBXImportType.FBXIT_STATIC_MESH)
    options.set_editor_property("static_mesh_import_data", unreal.FbxStaticMeshImportData())
    sm = options.get_editor_property("static_mesh_import_data")
    try:
        sm.set_editor_property("combine_meshes", False)
        sm.set_editor_property("import_uniform_scale", 100.0)
    except Exception:
        pass
    task.set_editor_property("options", options)
    task.set_editor_property("factory", unreal.FbxFactory())
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    return list_static_meshes(DEST_ROAD)


def pick_straight(meshes):
    # Prefer longer thin meshes
    best = None
    best_score = -1.0
    for m in meshes:
        sx, sy, sz = mesh_extent(m)
        long_axis = max(sx, sy)
        short_axis = min(sx, sy)
        score = long_axis / max(1.0, short_axis)
        if score > best_score:
            best_score = score
            best = m
    return best or meshes[0]


def pick_crossing(meshes, straight):
    for m in meshes:
        if m == straight:
            continue
        sx, sy, sz = mesh_extent(m)
        if abs(sx - sy) < max(sx, sy) * 0.35:
            return m
    return meshes[0]


def ensure_mesh_actor(label, mesh, loc, rot, scale):
    actor = find_by_label(label)
    if actor is None:
        actor = spawn(unreal.StaticMeshActor, loc, scale, label, rot)
    else:
        actor.set_actor_location(loc, False, True)
        actor.set_actor_rotation(rot, False)
        actor.set_actor_scale3d(scale)
    smc = actor.static_mesh_component
    smc.set_static_mesh(mesh)
    smc.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    smc.set_cast_shadow(False)
    actor.set_actor_hidden_in_game(False)
    return actor


def tile_line(mesh, prefix, axis, a0, a1, other, yaw, start_i):
    sx, sy, sz = mesh_extent(mesh)
    tile_len = max(sx, sy)
    if tile_len < 50:
        tile_len = 400.0
    width = min(sx, sy)
    scale_w = (ROAD_W * 0.95) / max(1.0, width)
    scale = unreal.Vector(scale_w, scale_w, scale_w)
    step = max(80.0, tile_len * scale_w * 0.92)
    lo, hi = min(a0, a1), max(a0, a1)
    pos = lo
    i = start_i
    rot = unreal.Rotator(0, yaw, 0)
    while pos <= hi + 1.0:
        loc = unreal.Vector(other, pos, Z_ROAD) if axis == "y" else unreal.Vector(pos, other, Z_ROAD)
        ensure_mesh_actor("%s_%d" % (prefix, i), mesh, loc, rot, scale)
        pos += step
        i += 1
    return i


def hide_cube_roads():
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        lab = actor.get_actor_label()
        if lab.startswith("Avenue_") or lab.startswith("Street_") or lab.startswith("RoadStripe_") or lab.startswith("Crosswalk_"):
            actor.set_actor_hidden_in_game(True)
            smc = getattr(actor, "static_mesh_component", None)
            if smc:
                smc.set_visibility(False, False)


def snap_parcels():
    n = 0
    for label, x, y, fx, fy, floors in PARCELS:
        actor = find_by_label(label)
        if not actor or not actor.static_mesh_component:
            continue
        smc = actor.static_mesh_component
        mesh = smc.static_mesh
        total_h = floors * FLOOR_H
        if mesh and isinstance(mesh, unreal.StaticMesh):
            try:
                box = mesh.get_bounding_box()
                sx = abs(box.max.x - box.min.x)
                sy = abs(box.max.y - box.min.y)
                sz = abs(box.max.z - box.min.z)
            except Exception:
                sx, sy, sz = 100.0, 100.0, 100.0
            sxy = min(fx / max(sx, 1.0), fy / max(sy, 1.0)) * 0.92
            szs = total_h / max(sz, 1.0)
            actor.set_actor_scale3d(unreal.Vector(sxy, sxy, szs))
        actor.set_actor_location(unreal.Vector(x, y, total_h * 0.5), False, True)
        actor.set_actor_rotation(unreal.Rotator(0, 0, 0), False)
        actor.set_actor_hidden_in_game(False)
        smc.set_cast_shadow(True)
        n += 1
        unreal.log("Parcel %s @ (%.0f,%.0f)" % (label, x, y))
    return n


def main():
    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level_editor.load_level(MAP_PATH):
        raise RuntimeError("load failed")

    meshes = import_road_fbx()
    if not meshes:
        raise RuntimeError("No Fab road meshes")

    straight = pick_straight(meshes)
    crossing = pick_crossing(meshes, straight)
    unreal.log("straight=%s crossing=%s" % (straight.get_name(), crossing.get_name()))

    destroy_prefix("FabRoad_")
    # Remove editor-placed static cars — runtime LEStreetCar free-roams
    destroy_prefix("RoadCar3D_")
    hide_cube_roads()

    y0, y1 = STREETS[-1][1], STREETS[0][1]
    x0, x1 = AVENUES[-1][1], AVENUES[0][1]
    idx = 0
    for name, x in AVENUES:
        idx = tile_line(straight, "FabRoad_NS_%s" % name, "y", y0, y1, x, 0.0, idx)
    for name, y in STREETS:
        idx = tile_line(straight, "FabRoad_EW_%s" % name, "x", x0, x1, y, 90.0, idx)

    for i, (_, x) in enumerate(AVENUES):
        for j, (_, y) in enumerate(STREETS):
            sx, sy, sz = mesh_extent(crossing)
            scale_w = (ROAD_W * 1.1) / max(1.0, min(sx, sy))
            ensure_mesh_actor(
                "FabRoad_X_%d_%d" % (i, j),
                crossing,
                unreal.Vector(x, y, Z_ROAD + 1.0),
                unreal.Rotator(0, 0, 0),
                unreal.Vector(scale_w, scale_w, scale_w),
            )

    parcels = snap_parcels()

    if find_by_label(FLAG) is None:
        spawn(unreal.Actor, unreal.Vector(0, 0, -820), label=FLAG)

    if not level_editor.save_current_level():
        raise RuntimeError("save failed")
    unreal.log("FAB ROADS+PARCELS OK — tiles~%d parcels=%d" % (idx, parcels))


main()
