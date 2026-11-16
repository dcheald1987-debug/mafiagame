import unreal
import runpy
import os
root = unreal.Paths.project_dir()
runpy.run_path(os.path.join(root, "Scripts", "ImportCustomRoads.py"), run_name="__main__")
runpy.run_path(os.path.join(root, "Scripts", "ImportDressStreetAssets.py"), run_name="__main__")
unreal.log("BATCH_STREET_OK")
