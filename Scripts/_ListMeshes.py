import unreal
MESH_DIR = "/Game/Art/Empire/ExternalBuildings/Meshes"
for p in unreal.EditorAssetLibrary.list_assets(MESH_DIR, False, False):
    a = unreal.load_asset(p)
    unreal.log("ASSET %s type=%s" % (p, a.get_class().get_name() if a else None))
