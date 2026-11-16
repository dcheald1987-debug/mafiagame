import unreal

# Creates Brickyard, Halden Row, and Ames Hill greybox maps with WeekDirector + sites + hoods.

OWNER_NEUTRAL, OWNER_PLAYER, OWNER_RIVAL, OWNER_CONTESTED = 0, 1, 2, 3
KIND_RACKET, KIND_BUSINESS, KIND_STREET, KIND_BLOCK = 0, 1, 2, 3
ROLE_BAGMAN, ROLE_ENFORCER, ROLE_RECRUITER = 0, 1, 2

DISTRICTS = {
    "Brickyard": {
        "path": "/Game/Maps/Empire/Brickyard_Greybox",
        "label": "THE BRICKYARD",
        "buildings": [
            ("Bld_Kiln", (-1600.0, -1000.0, 220.0), (10.0, 8.0, 4.4)),
            ("Bld_Union", (-400.0, -1100.0, 180.0), (7.0, 6.0, 3.6)),
            ("Bld_YardOffice", (800.0, -900.0, 160.0), (6.0, 5.0, 3.2)),
            ("Bld_Stack", (1600.0, 200.0, 280.0), (5.0, 5.0, 5.6)),
            ("Bld_Shed", (-200.0, 1200.0, 140.0), (12.0, 6.0, 2.8)),
            ("Bld_Gate", (1200.0, 1400.0, 160.0), (8.0, 4.0, 3.2)),
        ],
        "sites": [
            ("B01", "Kiln Row", KIND_RACKET, OWNER_CONTESTED, "KilnBlock", 70, 2, (-1600.0, -700.0, 40.0)),
            ("B02", "Union Hall", KIND_BUSINESS, OWNER_NEUTRAL, "KilnBlock", 45, 1, (-400.0, -800.0, 40.0)),
            ("B03", "Yard Office", KIND_BUSINESS, OWNER_RIVAL, "YardBlock", 55, 1, (800.0, -600.0, 40.0)),
            ("B04", "Clay Pit", KIND_BLOCK, OWNER_RIVAL, "YardBlock", 0, 0, (400.0, 200.0, 40.0)),
            ("B05", "Stack Gate", KIND_STREET, OWNER_NEUTRAL, "GateBlock", 0, 0, (1200.0, 900.0, 40.0)),
            ("B06", "Night Shed", KIND_RACKET, OWNER_CONTESTED, "GateBlock", 60, 2, (-200.0, 1500.0, 40.0)),
        ],
        "player_hoods": [
            ("H01", "Eddie Voss", ROLE_BAGMAN, (-1400.0, -400.0, 100.0)),
            ("H02", "Nicky Ferro", ROLE_ENFORCER, (-1100.0, -400.0, 100.0)),
            ("H03", "Nora Pell", ROLE_RECRUITER, (-900.0, -200.0, 100.0)),
        ],
        "rivals": [
            ("R10", "Brick Red", ROLE_ENFORCER, (1400.0, 600.0, 100.0)),
            ("R11", "Mags Clay", ROLE_BAGMAN, (1500.0, 800.0, 100.0)),
        ],
    },
    "HaldenRow": {
        "path": "/Game/Maps/Empire/HaldenRow_Greybox",
        "label": "HALDEN ROW",
        "buildings": [
            ("Bld_BrownstoneA", (-1500.0, -800.0, 200.0), (6.0, 8.0, 4.0)),
            ("Bld_BrownstoneB", (-600.0, -800.0, 200.0), (6.0, 8.0, 4.0)),
            ("Bld_Boarding", (400.0, -1000.0, 180.0), (9.0, 6.0, 3.6)),
            ("Bld_Pharmacy", (1400.0, 0.0, 160.0), (5.0, 5.0, 3.2)),
            ("Bld_Club", (200.0, 1200.0, 180.0), (8.0, 6.0, 3.6)),
            ("Bld_Tailor", (-1200.0, 1100.0, 150.0), (5.0, 5.0, 3.0)),
        ],
        "sites": [
            ("HR01", "Brownstone A", KIND_BUSINESS, OWNER_PLAYER, "RowBlock", 50, 0, (-1500.0, -500.0, 40.0)),
            ("HR02", "Brownstone B", KIND_BUSINESS, OWNER_CONTESTED, "RowBlock", 50, 1, (-600.0, -500.0, 40.0)),
            ("HR03", "Row Boarding", KIND_BUSINESS, OWNER_RIVAL, "BoardBlock", 40, 1, (400.0, -700.0, 40.0)),
            ("HR04", "Corner Pharmacy", KIND_BUSINESS, OWNER_NEUTRAL, "ShopBlock", 35, 0, (1400.0, 300.0, 40.0)),
            ("HR05", "Back Club", KIND_RACKET, OWNER_RIVAL, "ClubBlock", 75, 2, (200.0, 1500.0, 40.0)),
            ("HR06", "Tailor Alley", KIND_STREET, OWNER_NEUTRAL, "ClubBlock", 0, 0, (-1200.0, 1400.0, 40.0)),
        ],
        "player_hoods": [
            ("H01", "Eddie Voss", ROLE_BAGMAN, (-1300.0, -200.0, 100.0)),
            ("H02", "Nicky Ferro", ROLE_ENFORCER, (-1000.0, -200.0, 100.0)),
            ("H03", "Nora Pell", ROLE_RECRUITER, (-800.0, 0.0, 100.0)),
        ],
        "rivals": [
            ("R20", "Silk Dana", ROLE_ENFORCER, (600.0, 1000.0, 100.0)),
            ("R21", "Pockets", ROLE_BAGMAN, (800.0, 1200.0, 100.0)),
        ],
    },
    "AmesHill": {
        "path": "/Game/Maps/Empire/AmesHill_Greybox",
        "label": "AMES HILL",
        "buildings": [
            ("Bld_Mill", (-1400.0, -1200.0, 260.0), (12.0, 8.0, 5.2)),
            ("Bld_Overlook", (200.0, -1400.0, 200.0), (7.0, 5.0, 4.0)),
            ("Bld_Company", (1400.0, -400.0, 220.0), (9.0, 7.0, 4.4)),
            ("Bld_Gatehouse", (-400.0, 400.0, 160.0), (5.0, 5.0, 3.2)),
            ("Bld_Cottage", (800.0, 1200.0, 140.0), (6.0, 5.0, 2.8)),
            ("Bld_Pump", (-1600.0, 1000.0, 180.0), (4.0, 4.0, 3.6)),
        ],
        "sites": [
            ("A01", "Ames Mill", KIND_RACKET, OWNER_RIVAL, "MillBlock", 90, 2, (-1400.0, -900.0, 40.0)),
            ("A02", "Overlook Lodge", KIND_BUSINESS, OWNER_CONTESTED, "MillBlock", 60, 1, (200.0, -1100.0, 40.0)),
            ("A03", "Company Office", KIND_BUSINESS, OWNER_RIVAL, "CompanyBlock", 70, 2, (1400.0, -100.0, 40.0)),
            ("A04", "Gatehouse", KIND_STREET, OWNER_NEUTRAL, "GateBlock", 0, 0, (-400.0, 700.0, 40.0)),
            ("A05", "Hill Cottage", KIND_BUSINESS, OWNER_NEUTRAL, "GateBlock", 30, 0, (800.0, 1500.0, 40.0)),
            ("A06", "Pump House", KIND_BLOCK, OWNER_CONTESTED, "PumpBlock", 0, 0, (-1600.0, 1300.0, 40.0)),
        ],
        "player_hoods": [
            ("H01", "Eddie Voss", ROLE_BAGMAN, (-1000.0, -400.0, 100.0)),
            ("H02", "Nicky Ferro", ROLE_ENFORCER, (-700.0, -400.0, 100.0)),
            ("H03", "Nora Pell", ROLE_RECRUITER, (-500.0, -200.0, 100.0)),
        ],
        "rivals": [
            ("R30", "Clerk Orth", ROLE_ENFORCER, (1200.0, 200.0, 100.0)),
            ("R31", "Watch Maeve", ROLE_BAGMAN, (1000.0, 400.0, 100.0)),
        ],
    },
}


def spawn(cls, location, scale=None, label=None):
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actor = subsystem.spawn_actor_from_class(cls, location, unreal.Rotator())
    if scale is not None:
        actor.set_actor_scale3d(scale)
    if label is not None:
        actor.set_actor_label(label)
    return actor


def cube_actor(label, location, scale):
    mesh = unreal.load_asset("/Engine/BasicShapes/Cube")
    actor = spawn(unreal.StaticMeshActor, unreal.Vector(*location), unreal.Vector(*scale), label)
    actor.static_mesh_component.set_static_mesh(mesh)
    return actor


def site(site_id, name, kind, owner, block_id, payout, heat, location):
    actor = spawn(unreal.LESiteActor, unreal.Vector(*location), unreal.Vector(1.0, 1.0, 1.0), "Site_" + site_id)
    actor.configure(site_id, unreal.Text(name), kind, owner, block_id, payout, heat)
    return actor


def hood(hood_id, name, role, faction, location):
    actor = spawn(unreal.LEHoodAgent, unreal.Vector(*location), None, "Hood_" + hood_id)
    actor.configure(hood_id, unreal.Text(name), role, faction, 60)
    return actor


def ensure_label(text, location, label):
    actor = spawn(unreal.TextRenderActor, unreal.Vector(*location), None, label)
    tr = actor.get_component_by_class(unreal.TextRenderComponent)
    if tr is None:
        tr = actor.text_render
    tr.set_text(unreal.Text(text))
    tr.set_world_size(140.0)
    tr.set_text_render_color(unreal.Color(28, 24, 18, 255))


def build_district(key, data):
    map_path = data["path"]
    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    if unreal.EditorAssetLibrary.does_asset_exist(map_path):
        if not level_editor.load_level(map_path):
            raise RuntimeError("load failed " + map_path)
        existing = actor_subsystem.get_all_level_actors()
        if any(a.get_actor_label() == "WeekDirector" for a in existing):
            unreal.log(key + " already populated")
            return
        for actor in list(existing):
            label = actor.get_actor_label()
            if label not in ("WorldSettings", "Brush_0", "DefaultPhysicsVolume0", "AbstractNavData-Default"):
                try:
                    actor_subsystem.destroy_actor(actor)
                except Exception:
                    pass
    else:
        if not level_editor.new_level(map_path):
            raise RuntimeError("create failed " + map_path)

    cube_actor("Ground", (0.0, 0.0, -50.0), (70.0, 70.0, 1.0))
    cube_actor("Street_NS", (0.0, 0.0, -40.0), (5.0, 60.0, 0.4))
    cube_actor("Street_EW", (0.0, 0.0, -40.0), (60.0, 5.0, 0.4))

    for label, loc, scale in data["buildings"]:
        cube_actor(label, loc, scale)

    for sid, name, kind, owner, block, pay, heat, loc in data["sites"]:
        site(sid, name, kind, owner, block, pay, heat, loc)

    for hid, name, role, loc in data["player_hoods"]:
        hood(hid, name, role, OWNER_PLAYER, loc)
    for rid, name, role, loc in data["rivals"]:
        hood(rid, name, role, OWNER_RIVAL, loc)

    spawn(unreal.LEWeekDirector, unreal.Vector(0.0, 0.0, 400.0), None, "WeekDirector")
    spawn(unreal.PlayerStart, unreal.Vector(0.0, 0.0, 200.0), None, "PlayerStart_City")
    spawn(unreal.DirectionalLight, unreal.Vector(0.0, 0.0, 2000.0), None, "Sun")
    spawn(unreal.SkyLight, unreal.Vector(0.0, 0.0, 1500.0), None, "Sky")
    ensure_label(data["label"], (0.0, -2000.0, 500.0), "Label_District")

    if not level_editor.save_current_level():
        raise RuntimeError("save failed " + map_path)
    unreal.log("Saved " + map_path)


def main():
    unreal.EditorAssetLibrary.make_directory("/Game/Maps/Empire")
    for key, data in DISTRICTS.items():
        build_district(key, data)
    unreal.log("DISTRICTS OK — Brickyard, HaldenRow, AmesHill")


main()
