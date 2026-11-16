import unreal
MAP = "/Game/Maps/Empire/Levee_Greybox"
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(MAP)
walks = []
masses = []
roads = []
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    lab = a.get_actor_label()
    loc = a.get_actor_location()
    sc = a.get_actor_scale3d()
    if lab.startswith("Walk") or lab.startswith("Pad_") or lab.startswith("GridWalk"):
        walks.append((lab, loc.x, loc.y, loc.z, sc.x, sc.y, sc.z))
    if "Mass" in lab or lab.startswith("Row_"):
        masses.append((lab, loc.x, loc.y, loc.z, sc.x, sc.y, sc.z))
    if lab.startswith("FabRoad_") or lab.startswith("Avenue_") or lab.startswith("Street_"):
        roads.append((lab, loc.x, loc.y, loc.z))
print("=== WALKS %d ===" % len(walks))
for w in sorted(walks)[:40]:
    print("W %s xy=(%.0f,%.0f) z=%.0f scale=(%.2f,%.2f,%.2f)" % w)
print("=== MASSES/ROWS %d ===" % len(masses))
for m in sorted(masses):
    print("M %s xy=(%.0f,%.0f) z=%.0f scale=(%.2f,%.2f,%.2f)" % m)
print("=== ROADS sample %d ===" % len(roads))
for r in sorted(roads)[:15]:
    print("R %s xy=(%.0f,%.0f,%.0f)" % (r[0], r[1], r[2], r[3]))
