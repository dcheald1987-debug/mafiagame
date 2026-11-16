import runpy, os, unreal
root = unreal.Paths.project_dir()
runpy.run_path(os.path.join(root, "Scripts", "WidenRoadsForCars.py"), run_name="__main__")
runpy.run_path(os.path.join(root, "Scripts", "DressFull3DStreet.py"), run_name="__main__")
unreal.log("BATCH_WIDE_3D_OK")
