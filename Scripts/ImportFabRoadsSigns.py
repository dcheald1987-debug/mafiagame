"""Import Fab Modular Roads + pedestrian crossing sign and dress Chicago Levee grid.

Sources:
  Art/Fab/ModularRoads/source/Raods.fbx
  Art/Fab/RoadSigns/source/sign_pedestrian_crossing.fbx + textures/
"""
import unreal
import os

MAP_PATH = "/Game/Maps/Empire/Levee_Greybox"
ROAD_FBX = unreal.Paths.project_dir() + "Art/Fab/ModularRoads/source/Raods.fbx"
SIGN_FBX = unreal.Paths.project_dir() + "Art/Fab/RoadSigns/source/sign_pedestrian_crossing.fbx"
SIGN_TEX = unreal.Paths.project_dir() + "Art/Fab/RoadSigns/textures/Textures"
DEST_ROAD = "/Game/Art/Empire/FabRoads"
DEST_SIGN = "/Game/Art/Empire/FabSigns"
FLAG = "Dress_FabRoadsSigns_v2"

# Same lattice as BuildLeveeGrid v2 (1200uu Chicago grid)
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
ROAD_W = 300.0
Z_ROAD = -36.0

# Pedestrian signs at major crossings (x, y, yaw)
SIGN_SPOTS = [
    (0.0, 0.0, 0.0),
    (1200.0, 0.0, 90.0),
    (2400.0, -1200.0, 0.0),
    (-2400.0, -1200.0, 90.0),
    (0.0, 1200.0, 0.0),
    (-1200.0, 2400.0, 90.0),
]


def ensure_dir(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


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


def import_fbx(disk, dest_path, dest_name, combine=False, scale=1.0):
    ensure_dir(dest_path)
    disk = os.path.normpath(disk)
    if not os.path.isfile(disk):
        raise RuntimeError("Missing FBX " + disk)
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", disk)
    task.set_editor_property("destination_path", dest_path)
    task.set_editor_property("destination_name", dest_name)
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
        sm.set_editor_property("combine_meshes", combine)
        sm.set_editor_property("auto_generate_collision", True)
        sm.set_editor_property("import_uniform_scale", scale)
        sm.set_editor_property("convert_scene", True)
    except Exception as exc:
        unreal.log_warning("fbx opts: %s" % exc)
    task.set_editor_property("options", options)
    task.set_editor_property("factory", unreal.FbxFactory())
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    unreal.log("Imported FBX " + dest_name)


def import_sign_textures():
    ensure_dir(DEST_SIGN + "/Textures")
    tex_dir = os.path.normpath(SIGN_TEX)
    if not os.path.isdir(tex_dir):
        unreal.log_warning("No sign textures at " + tex_dir)
        return
    tasks = []
    for name in os.listdir(tex_dir):
        low = name.lower()
        if not (low.endswith(".jpg") or low.endswith(".png") or low.endswith(".tga")):
            continue
        # Prefer base color maps for materials we may wire later
        disk = os.path.join(tex_dir, name)
        asset = os.path.splitext(name)[0].replace(".", "_")
        dest = "%s/Textures/%s" % (DEST_SIGN, asset)
        if unreal.EditorAssetLibrary.does_asset_exist(dest):
            continue
        task = unreal.AssetImportTask()
        task.set_editor_property("filename", disk)
        task.set_editor_property("destination_path", DEST_SIGN + "/Textures")
        task.set_editor_property("destination_name", asset)
        task.set_editor_property("replace_existing", True)
        task.set_editor_property("automated", True)
        task.set_editor_property("save", True)
        task.set_editor_property("factory", unreal.TextureFactory())
        tasks.append(task)
    if tasks:
        # Import in chunks to avoid huge batch stalls
        chunk = 12
        for i in range(0, len(tasks), chunk):
            unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks[i:i + chunk])
    unreal.log("SIGN TEX — imported up to %d" % len(tasks))


def list_static_meshes(folder):
    meshes = []
    try:
        assets = unreal.EditorAssetLibrary.list_assets(folder, True, False)
    except Exception:
        return meshes
    for path in assets:
        asset = unreal.load_asset(path)
        if isinstance(asset, unreal.StaticMesh):
            meshes.append(asset)
    return meshes


def mesh_extent_xy(mesh):
    bounds = mesh.get_bounds()
    box = bounds.box_extent
    return abs(box.x) * 2.0, abs(box.y) * 2.0, abs(box.z) * 2.0


def pick_straight_road(meshes):
    """Prefer elongated flat piece for tiling along avenues."""
    best = None
    best_score = -1.0
    for m in meshes:
        sx, sy, sz = mesh_extent_xy(m)
        flat = min(sx, sy, sz) + 1.0
        long_axis = max(sx, sy)
        score = long_axis / flat
        if score > best_score:
            best_score = score
            best = m
    return best


def pick_crossing_road(meshes, straight):
    for m in meshes:
        if m == straight:
            continue
        sx, sy, sz = mesh_extent_xy(m)
        # Prefer more square footprints for intersections
        ratio = max(sx, sy) / max(0.01, min(sx, sy))
        if ratio < 1.6:
            return m
    for m in meshes:
        if m != straight:
            return m
    return straight


def destroy_prefix(prefix):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in list(sub.get_all_level_actors()):
        if actor.get_actor_label().startswith(prefix):
            sub.destroy_actor(actor)


def ensure_mesh_actor(label, mesh, location, rotation, scale):
    actor = find_by_label(label)
    if actor is None:
        actor = spawn(unreal.StaticMeshActor, location, scale, label, rotation)
    else:
        actor.set_actor_location(location, False, True)
        actor.set_actor_rotation(rotation, False)
        actor.set_actor_scale3d(scale)
    smc = actor.static_mesh_component
    smc.set_static_mesh(mesh)
    smc.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    actor.set_actor_hidden_in_game(False)
    return actor


def hide_cube_roads():
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        lab = actor.get_actor_label()
        if lab.startswith("Avenue_") or lab.startswith("Street_") or lab.startswith("Alley_"):
            # Keep Walk_* sidewalks; hide asphalt cubes under Fab tiles
            if not lab.startswith("Walk_"):
                actor.set_actor_hidden_in_game(True)
                smc = getattr(actor, "static_mesh_component", None)
                if smc:
                    smc.set_visibility(False, False)


def tile_line(mesh, label_prefix, axis, center_a, center_b, other, yaw, tile_i_start=0):
    """Tile mesh along axis ('x' or 'y') from center_a..center_b at fixed other coord."""
    sx, sy, sz = mesh_extent_xy(mesh)
    # After import, long axis may be X or Y — use larger horizontal extent as tile length
    tile_len = max(sx, sy)
    if tile_len < 50.0:
        tile_len = 400.0
    # Target road width ~ ROAD_W
    width = min(sx, sy)
    scale_w = (ROAD_W * 0.95) / max(1.0, width)
    scale = unreal.Vector(scale_w, scale_w, scale_w)
    # Effective step after scale
    step = tile_len * scale_w * 0.92
    if step < 80.0:
        step = 200.0
    a0, a1 = min(center_a, center_b), max(center_a, center_b)
    pos = a0
    i = tile_i_start
    rot = unreal.Rotator(0.0, yaw, 0.0)
    while pos <= a1 + 1.0:
        if axis == "y":
            loc = unreal.Vector(other, pos, Z_ROAD)
        else:
            loc = unreal.Vector(pos, other, Z_ROAD)
        ensure_mesh_actor("%s_%d" % (label_prefix, i), mesh, loc, rot, scale)
        pos += step
        i += 1
    return i


def place_signs(sign_mesh):
    destroy_prefix("FabSign_")
    # Photoreal sign — normalize height ~280uu
    sx, sy, sz = mesh_extent_xy(sign_mesh)
    height = max(sx, sy, sz)
    scale_s = 280.0 / max(1.0, height)
    scale = unreal.Vector(scale_s, scale_s, scale_s)
    for i, (x, y, yaw) in enumerate(SIGN_SPOTS):
        # Offset to curb corner
        loc = unreal.Vector(x + ROAD_W * 0.55, y + ROAD_W * 0.55, 0.0)
        ensure_mesh_actor(
            "FabSign_%d" % i,
            sign_mesh,
            loc,
            unreal.Rotator(0.0, yaw, 0.0),
            scale,
        )


def main():
    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level_editor.load_level(MAP_PATH):
        raise RuntimeError("load failed")

    ensure_dir(DEST_ROAD)
    ensure_dir(DEST_SIGN)

    import_fbx(ROAD_FBX, DEST_ROAD, "SM_ModularRoads", combine=False, scale=100.0)
    import_sign_textures()
    import_fbx(SIGN_FBX, DEST_SIGN, "SM_PedestrianCrossing", combine=True, scale=1.0)

    road_meshes = list_static_meshes(DEST_ROAD)
    sign_meshes = list_static_meshes(DEST_SIGN)
    if not road_meshes:
        raise RuntimeError("No road meshes imported")
    if not sign_meshes:
        raise RuntimeError("No sign meshes imported")

    for m in road_meshes:
        sx, sy, sz = mesh_extent_xy(m)
        unreal.log("ROAD MESH %s extent=(%.1f, %.1f, %.1f)" % (m.get_name(), sx, sy, sz))

    straight = pick_straight_road(road_meshes)
    crossing = pick_crossing_road(road_meshes, straight)
    sign = max(sign_meshes, key=lambda m: mesh_extent_xy(m)[2])
    unreal.log("Using straight=%s crossing=%s sign=%s" % (
        straight.get_name(), crossing.get_name(), sign.get_name()
    ))

    destroy_prefix("FabRoad_")
    hide_cube_roads()

    # NS avenues (tile along Y)
    y0, y1 = STREETS[-1][1], STREETS[0][1]
    idx = 0
    for name, x in AVENUES:
        idx = tile_line(straight, "FabRoad_NS_%s" % name, "y", y0, y1, x, 0.0, idx)

    # EW streets (tile along X) — yaw 90
    x0, x1 = AVENUES[-1][1], AVENUES[0][1]
    for name, y in STREETS:
        idx = tile_line(straight, "FabRoad_EW_%s" % name, "x", x0, x1, y, 90.0, idx)

    # Intersection pads
    for i, (_, x) in enumerate(AVENUES):
        for j, (_, y) in enumerate(STREETS):
            sx, sy, sz = mesh_extent_xy(crossing)
            scale_w = (ROAD_W * 1.15) / max(1.0, min(sx, sy))
            ensure_mesh_actor(
                "FabRoad_X_%d_%d" % (i, j),
                crossing,
                unreal.Vector(x, y, Z_ROAD + 2.0),
                unreal.Rotator(0.0, 0.0, 0.0),
                unreal.Vector(scale_w, scale_w, scale_w),
            )

    place_signs(sign)

    if find_by_label(FLAG) is None:
        spawn(unreal.Actor, unreal.Vector(0.0, 0.0, -900.0), label=FLAG)

    if not level_editor.save_current_level():
        raise RuntimeError("save failed")
    unreal.EditorAssetLibrary.save_directory(DEST_ROAD)
    unreal.EditorAssetLibrary.save_directory(DEST_SIGN)
    unreal.log(
        "FAB ROADS/SIGNS OK — roads=%d signs=%d spots=%d"
        % (len(road_meshes), len(sign_meshes), len(SIGN_SPOTS))
    )


main()
