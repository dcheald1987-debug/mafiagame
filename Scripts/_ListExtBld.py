import unreal
root = "/Game/Art/Empire/ExternalBuildings"
ar = unreal.AssetRegistryHelpers.get_asset_registry()
for a in ar.get_assets_by_path(root, recursive=True):
    try:
        cls = str(a.asset_class_path.asset_name)
    except Exception:
        cls = "?"
    if "StaticMesh" in cls or "Material" in cls:
        unreal.log("%s | %s" % (cls, a.package_name))
