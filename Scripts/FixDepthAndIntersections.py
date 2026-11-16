"""Fix black intersection holes + restore 3D volume (Blackthorn masses, pads, thicker roofs)."""
import unreal
import os

MAP_PATH = "/Game/Maps/Empire/Levee_Greybox"
MESH_DIR = "/Game/Art/Empire/ExternalBuildings/Meshes"
SRC_BLD = unreal.Paths.project_content_dir() + "Art/Empire/Sprites/Source/Cropped/Buildings"
SRC_ROAD = unreal.Paths.project_content_dir() + "Art/Empire/Sprites/Source/Cropped/Roads"
TEX = "/Game/Art/Empire/Sprites/Textures"
MAT = "/Game/Art/Empire/Sprites/Materials"
FLAG = "Dress_DepthIntersect_v1"

ROAD_W = 480.0
GRID = 1200.0
PAD = GRID - ROAD_W
FOOTPRINT = PAD * 0.78
FLOOR_H = 190.0
Z_ROAD = -28.0
Z_X = -26.0
Z_PAD = -20.0

AVENUES = [2400.0, 1200.0, 0.0, -1200.0, -2400.0]
STREETS = [2400.0, 1200.0, 0.0, -1200.0, -2400.0]

# label, ai, sj, floors, wall_key, roof_jpg
PARCELS = [
    ("Row_Garage_Mass", 0, 2, 3, "Bld_Garage", "S_Roof_Garage.jpg"),
    ("Row_Cafe_Mass", 1, 2, 3, "Bld_Cafe", "S_Roof_Cafe.jpg"),
    ("Row_Dock_Mass", 0, 3, 2, "Bld_Dock", "S_Roof_Dock.jpg"),
    ("Row_MidC_Mass", 1, 3, 4, "Facade_C", "S_Roof_Facade_C.jpg"),
    ("Row_MidA_Mass", 2, 1, 4, "Facade_A", "S_Roof_Facade_A.jpg"),
    ("Row_MidB_Mass", 2, 2, 3, "Facade_B", "S_Roof_Facade_B.jpg"),
    ("Row_Bar_Mass", 3, 3, 3, "Bld_Bar", "S_Roof_Bar.jpg"),
    ("Row_Board_Mass", 2, 0, 4, "Bld_Board", "S_Roof_Board.jpg"),
    ("Row_MidD_Mass", 3, 1, 3, "Facade_D", "S_Roof_Facade_D.jpg"),
    ("Row_MidE_Mass", 3, 2, 3, "Facade_E", "S_Roof_Facade_E.jpg"),
    ("Row_MidF_Mass", 1, 1, 4, "Facade_F", "S_Roof_Facade_F.jpg"),
    ("Row_MidG_Mass", 0, 1, 3, "Facade_G", "S_Roof_Facade_G.jpg"),
    ("Row_Rope_Mass", 3, 0, 2, "Bld_Rope", "S_Roof_Rope.jpg"),
    ("Row_Freight_Mass", 2, 3, 2, "Bld_Freight", "S_Roof_Freight.jpg"),
]

WALL_PNG = {
    "Bld_Garage": "S_Garage.png",
    "Bld_Cafe": "S_Cafe.png",
    "Bld_Dock": "S_Dock.png",
    "Bld_Bar": "S_Bar.png",
    "Bld_Board": "S_Board.png",
    "Bld_Rope": "S_Rope.png",
    "Bld_Freight": "S_Freight.png",
    "Facade_A": "S_Facade_A.png",
    "Facade_B": "S_Facade_B.png",
    "Facade_C": "S_Facade_C.png",
    "Facade_D": "S_Facade_D.png",
    "Facade_E": "S_Facade_E.png",
    "Facade_F": "S_Facade_F.png",
    "Facade_G": "S_Facade_G.png",
}


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


def spawn(cls, loc, scale=None, label=None, yaw=0.0):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    a = sub.spawn_actor_from_class(cls, loc, unreal.Rotator(0.0, yaw, 0.0))
    if scale is not None:
        a.set_actor_scale3d(scale)
    if label:
        a.set_actor_label(label)
    return a


def parcel_center(ai, sj):
    return (AVENUES[ai] + AVENUES[ai + 1]) * 0.5, (STREETS[sj] + STREETS[sj + 1]) * 0.5


def ensure_dir(p):
    if not unreal.EditorAssetLibrary.does_directory_exist(p):
        unreal.EditorAssetLibrary.make_directory(p)


def purge(rel):
    root = unreal.Paths.project_content_dir()
    base = os.path.normpath(os.path.join(root, rel.replace("/", os.sep)))
    for ext in (".uasset", ".uexp", ".ubulk"):
        path = base + ext
        if os.path.isfile(path):
            try:
                os.remove(path)
            except OSError:
                pass


def no_shadow(smc):
    try:
        smc.set_cast_shadow(False)
    except Exception:
        pass


def yes_shadow(smc):
    try:
        smc.set_cast_shadow(True)
    except Exception:
        pass


def import_tex(name, disk):
    dest = "%s/%s" % (TEX, name)
    if not os.path.isfile(disk):
        unreal.log_warning("MISSING " + disk)
        return None
    if unreal.EditorAssetLibrary.does_asset_exist(dest):
        try:
            unreal.EditorAssetLibrary.delete_asset(dest)
        except Exception:
            pass
    purge("Art/Empire/Sprites/Textures/" + name)
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", disk)
    task.set_editor_property("destination_path", TEX)
    task.set_editor_property("destination_name", name)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)
    task.set_editor_property("factory", unreal.TextureFactory())
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    tex = unreal.load_asset(dest)
    if tex:
        try:
            tex.set_editor_property("srgb", True)
            tex.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_WORLD)
            unreal.EditorAssetLibrary.save_asset(dest)
        except Exception:
            pass
    return tex


def make_lit(name, tex, emissive=1.6, tile_u=1.0, tile_v=1.0):
    path = "%s/%s" % (MAT, name)
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        try:
            unreal.EditorAssetLibrary.delete_asset(path)
        except Exception:
            pass
    purge("Art/Empire/Sprites/Materials/" + name)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MAT, unreal.Material, unreal.MaterialFactoryNew()
    )
    if not mat:
        return None
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    mat.set_editor_property("two_sided", False)

    sample = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionTextureSample, -350, 0
    )
    sample.set_editor_property("texture", tex)
    if tile_u != 1.0 or tile_v != 1.0:
        tc = unreal.MaterialEditingLibrary.create_material_expression(
            mat, unreal.MaterialExpressionTextureCoordinate, -700, 0
        )
        mul_uv = unreal.MaterialEditingLibrary.create_material_expression(
            mat, unreal.MaterialExpressionMultiply, -520, 0
        )
        sc = unreal.MaterialEditingLibrary.create_material_expression(
            mat, unreal.MaterialExpressionConstant2Vector, -700, 120
        )
        sc.set_editor_property("r", float(tile_u))
        sc.set_editor_property("g", float(tile_v))
        unreal.MaterialEditingLibrary.connect_material_expressions(tc, "", mul_uv, "A")
        unreal.MaterialEditingLibrary.connect_material_expressions(sc, "", mul_uv, "B")
        unreal.MaterialEditingLibrary.connect_material_expressions(mul_uv, "", sample, "Coordinates")

    unreal.MaterialEditingLibrary.connect_material_property(
        sample, "RGB", unreal.MaterialProperty.MP_BASE_COLOR
    )
    mul = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionMultiply, -150, 140
    )
    amp = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant, -320, 180
    )
    amp.set_editor_property("r", float(emissive))
    unreal.MaterialEditingLibrary.connect_material_expressions(sample, "RGB", mul, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(amp, "", mul, "B")
    unreal.MaterialEditingLibrary.connect_material_property(
        mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR
    )
    rough = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant, -300, 280
    )
    rough.set_editor_property("r", 0.75)
    unreal.MaterialEditingLibrary.connect_material_property(
        rough, "", unreal.MaterialProperty.MP_ROUGHNESS
    )
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(path)
    return mat


def list_city_meshes():
    out = []
    # Explicit loads — list_assets can miss these after cmdlet boot
    names = [
        "SM_CityBuildings_Cube",
        "SM_CityBuildings_Cube_001",
        "SM_CityBuildings_Cube_002",
        "SM_CityBuildings_Cube_003",
        "SM_CityBuildings_Cube_004",
        "SM_CityBuildings_Cube_005",
        "SM_CityBuildings_Cube_006",
        "Building1",
        "Building2",
        "Building3",
        "Building4",
        "Building5",
        "Building6",
        "Building7",
    ]
    for n in names:
        a = unreal.load_asset("%s/%s" % (MESH_DIR, n))
        if isinstance(a, unreal.StaticMesh):
            out.append(a)
    if not out:
        for p in unreal.EditorAssetLibrary.list_assets(MESH_DIR, True, False):
            a = unreal.load_asset(p)
            if isinstance(a, unreal.StaticMesh):
                out.append(a)
    # Last resort: Engine cube still gets roof rim + pads for depth
    if not out:
        c = unreal.load_asset("/Engine/BasicShapes/Cube")
        if c:
            out.append(c)
    unreal.log("city meshes=%d" % len(out))
    return out


def mesh_box(mesh):
    b = mesh.get_bounding_box()
    return b.min, b.max


def fit_blackthorn(actor, mesh, cx, cy, floors):
    """Real 3D Blackthorn mass — volume reads in iso."""
    smc = actor.static_mesh_component
    smc.set_static_mesh(mesh)
    mn, mx = mesh_box(mesh)
    sx = max(1.0, abs(mx.x - mn.x))
    sy = max(1.0, abs(mx.y - mn.y))
    sz = max(1.0, abs(mx.z - mn.z))
    total_h = floors * FLOOR_H
    sxy = min(FOOTPRINT / sx, FOOTPRINT / sy) * 0.92
    szs = total_h / sz
    # Pivot correction so bounds center sits on parcel
    cx_local = (mn.x + mx.x) * 0.5
    cy_local = (mn.y + mx.y) * 0.5
    cz_local = (mn.z + mx.z) * 0.5
    actor.set_actor_scale3d(unreal.Vector(sxy, sxy, szs))
    world = unreal.Vector(
        cx - cx_local * sxy,
        cy - cy_local * sxy,
        total_h * 0.5 - cz_local * szs,
    )
    actor.set_actor_location(world, False, True)
    actor.set_actor_rotation(unreal.Rotator(0, 0, 0), False)
    yes_shadow(smc)
    actor.set_actor_hidden_in_game(False)
    smc.set_visibility(True)


def ensure_cube(label, loc, scale, mat, yaw=0.0, shadows=False):
    cube = unreal.load_asset("/Engine/BasicShapes/Cube")
    actor = find_by_label(label)
    if actor is None:
        actor = spawn(unreal.StaticMeshActor, loc, scale, label, yaw)
    else:
        actor.set_actor_location(loc, False, True)
        actor.set_actor_rotation(unreal.Rotator(0, yaw, 0), False)
        actor.set_actor_scale3d(scale)
    smc = actor.static_mesh_component
    smc.set_static_mesh(cube)
    if mat:
        smc.set_material(0, mat)
    if shadows:
        yes_shadow(smc)
    else:
        no_shadow(smc)
    actor.set_actor_hidden_in_game(False)
    smc.set_visibility(True)
    return actor


def main():
    ensure_dir(TEX)
    ensure_dir(MAT)
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not les.load_level(MAP_PATH):
        raise RuntimeError("load failed")

    cube = unreal.load_asset("/Engine/BasicShapes/Cube")
    meshes = list_city_meshes()
    if not meshes:
        raise RuntimeError("No Blackthorn CityBuildings meshes")

    # Textures
    asphalt_tex = import_tex(
        "T_Road_Asphalt", os.path.normpath(os.path.join(SRC_ROAD, "S_Road_Asphalt.jpg"))
    )
    lines_tex = import_tex(
        "T_Road_Lines", os.path.normpath(os.path.join(SRC_ROAD, "S_Road_Lines.jpg"))
    )
    cobble_tex = import_tex(
        "T_Road_Cobble", os.path.normpath(os.path.join(SRC_ROAD, "S_Road_Cobble.jpg"))
    )
    walk_disk = os.path.normpath(os.path.join(SRC_ROAD, "S_Sidewalk.jpg"))
    walk_tex = import_tex("T_Sidewalk", walk_disk) if os.path.isfile(walk_disk) else cobble_tex

    m_asphalt = make_lit("M_Depth_Asphalt", asphalt_tex, 0.55, 8.0, 8.0) if asphalt_tex else None
    m_lines = make_lit("M_Depth_Lines", lines_tex, 0.55, 1.5, 10.0) if lines_tex else m_asphalt
    m_cobble = make_lit("M_Depth_Cobble", cobble_tex, 0.5, 5.0, 5.0) if cobble_tex else m_asphalt
    m_walk = make_lit("M_Depth_Walk", walk_tex, 0.65, 6.0, 6.0) if walk_tex else m_cobble
    m_pad = m_walk or m_cobble or m_asphalt

    # --- Continuous cube roads (cover gaps) + intersection plugs ---
    destroy_prefix("RoadFill_X_")
    destroy_prefix("BlockPad_")
    # Unhide / rebuild Avenue_ Street_
    span_y = abs(STREETS[0] - STREETS[-1]) + ROAD_W * 2.0
    span_x = abs(AVENUES[0] - AVENUES[-1]) + ROAD_W * 2.0
    road_s = ROAD_W / 100.0

    for i, x in enumerate(AVENUES):
        mat = m_lines if (i % 2 == 0) else m_asphalt
        ensure_cube(
            "Avenue_%d" % i,
            unreal.Vector(x, 0.0, Z_ROAD),
            unreal.Vector(road_s, span_y / 100.0, 0.9),
            mat,
            shadows=False,
        )
    for j, y in enumerate(STREETS):
        mat = m_lines if (j % 2 == 1) else m_asphalt
        ensure_cube(
            "Street_%d" % j,
            unreal.Vector(0.0, y, Z_ROAD),
            unreal.Vector(span_x / 100.0, road_s, 0.9),
            mat,
            shadows=False,
        )

    # Fat intersection plugs so crossings never show black void
    n_x = 0
    for i, x in enumerate(AVENUES):
        for j, y in enumerate(STREETS):
            ensure_cube(
                "RoadFill_X_%d_%d" % (i, j),
                unreal.Vector(x, y, Z_X),
                unreal.Vector(road_s * 1.15, road_s * 1.15, 0.95),
                m_asphalt,
                shadows=False,
            )
            n_x += 1

    # Hide sparse Fab tiles that leave holes (keep cube grid as source of truth)
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        lab = a.get_actor_label()
        if lab.startswith("FabRoad_"):
            a.set_actor_hidden_in_game(True)
            smc = getattr(a, "static_mesh_component", None)
            if smc:
                smc.set_visibility(False)

    # Ground fill — not black void
    ground = find_by_label("Ground")
    if ground and ground.static_mesh_component and m_asphalt:
        ground.static_mesh_component.set_material(0, m_asphalt)
        no_shadow(ground.static_mesh_component)
        ground.set_actor_hidden_in_game(False)

    # --- Buildings: Blackthorn 3D + your wall mats + thick roofs + sidewalk pads ---
    wall_mats = {}
    for key, png in WALL_PNG.items():
        disk = os.path.normpath(os.path.join(SRC_BLD, png))
        # Prefer PNG; fall back jpg
        if not os.path.isfile(disk):
            disk = disk.replace(".png", ".jpg")
        tex = import_tex("T_User_" + key, disk)
        if tex:
            wall_mats[key] = make_lit("M_User_" + key, tex, 1.8)

    roof_mats = {}
    n_bld = 0
    n_roof = 0
    destroy_prefix("RoofCard_")
    destroy_prefix("RoofRim_")

    for i, (label, ai, sj, floors, wkey, roof_jpg) in enumerate(PARCELS):
        cx, cy = parcel_center(ai, sj)
        total_h = floors * FLOOR_H
        mesh = meshes[i % len(meshes)]

        actor = find_by_label(label)
        if actor is None:
            actor = spawn(unreal.StaticMeshActor, unreal.Vector(cx, cy, total_h * 0.5), label=label)
        fit_blackthorn(actor, mesh, cx, cy, floors)
        wmat = wall_mats.get(wkey)
        if wmat:
            try:
                nslots = actor.static_mesh_component.get_num_materials()
            except Exception:
                nslots = 1
            for s in range(max(1, nslots)):
                actor.static_mesh_component.set_material(s, wmat)
        n_bld += 1

        # Sidewalk pad under building (kills black parcel pits)
        ensure_cube(
            "BlockPad_%s" % label.replace("_Mass", ""),
            unreal.Vector(cx, cy, Z_PAD),
            unreal.Vector((PAD * 0.92) / 100.0, (PAD * 0.92) / 100.0, 0.35),
            m_pad,
            shadows=False,
        )

        # Thick roof slab + short parapet rim for depth
        rkey = roof_jpg.replace(".jpg", "")
        if rkey not in roof_mats:
            disk = os.path.normpath(os.path.join(SRC_BLD, roof_jpg))
            rtex = import_tex("T_" + rkey, disk)
            if rtex:
                roof_mats[rkey] = make_lit("M_" + rkey, rtex, 2.0)
        rmat = roof_mats.get(rkey)
        if rmat:
            # Main roof deck (thicker so iso sees volume)
            ensure_cube(
                "RoofCard_" + label,
                unreal.Vector(cx, cy, total_h + 18.0),
                unreal.Vector(FOOTPRINT / 100.0 * 1.02, FOOTPRINT / 100.0 * 1.02, 0.35),
                rmat,
                shadows=True,
            )
            # Parapet rim — thin walls so roof isn't a flat stamp
            rim_h = 0.55
            rim_t = 0.12
            half = FOOTPRINT * 0.51
            for suffix, loc, sc in (
                ("N", unreal.Vector(cx, cy + half, total_h + 40.0), unreal.Vector(FOOTPRINT / 100.0, rim_t, rim_h)),
                ("S", unreal.Vector(cx, cy - half, total_h + 40.0), unreal.Vector(FOOTPRINT / 100.0, rim_t, rim_h)),
                ("E", unreal.Vector(cx + half, cy, total_h + 40.0), unreal.Vector(rim_t, FOOTPRINT / 100.0, rim_h)),
                ("W", unreal.Vector(cx - half, cy, total_h + 40.0), unreal.Vector(rim_t, FOOTPRINT / 100.0, rim_h)),
            ):
                ensure_cube("RoofRim_%s_%s" % (label, suffix), loc, sc, rmat, shadows=True)
            n_roof += 1

    destroy_prefix(FLAG)
    spawn(unreal.Actor, unreal.Vector(0, 0, -980), label=FLAG)

    if not les.save_current_level():
        raise RuntimeError("save failed")
    unreal.EditorAssetLibrary.save_directory(MAT)
    unreal.EditorAssetLibrary.save_directory(TEX)
    unreal.log(
        "DEPTH+INTERSECT OK — bld=%d roofs=%d xfills=%d asphalt=%s"
        % (n_bld, n_roof, n_x, bool(m_asphalt))
    )


main()
