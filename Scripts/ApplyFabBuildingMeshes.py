"""Swap Levee Row_*_Mass cube bodies for City Sample / Fab building static meshes.

Run after Add to Project for City Sample Buildings:
  UnrealEditor-Cmd LostEmpire.uproject -run=pythonscript -script=Scripts/ApplyFabBuildingMeshes.py

Looks under common Fab / CitySample Content folders. Replaces each Row_*_Mass mesh,
hides decorative cube extras (windows/pilasters/etc), and scales the Fab mesh to the
previous mass footprint so the street still reads as blocks.
"""
import unreal
import math

MAP_PATH = "/Game/Maps/Empire/Levee_Greybox"

SEARCH_ROOTS = [
    "/Game/CitySample",
    "/Game/CitySampleBuildings",
    "/Game/Fab/CitySample",
    "/Game/Fab/CitySampleBuildings",
    "/Game/Fab",
    "/Game/AmericanCity",
    "/Game/American_City",
    "/Game/Megascans",
]

# Mass actors created by FixLeveeVisibility densify
ROW_MASS_LABELS = [
    "Row_Garage_Mass",
    "Row_Cafe_Mass",
    "Row_Dock_Mass",
    "Row_Bar_Mass",
    "Row_Board_Mass",
    "Row_Freight_Mass",
    "Row_Rope_Mass",
    "Row_MidA_Mass",
    "Row_MidB_Mass",
    "Row_MidC_Mass",
    "Row_MidD_Mass",
    "Row_MidE_Mass",
    "Row_MidF_Mass",
    "Row_MidG_Mass",
]

BUILDING_NAME_HINTS = (
    "bldg", "building", "bld_", "house", "tenement", "warehouse",
    "shop", "store", "facade", "block", "modular", "sm_b", "sm_building",
)


def _asset_registry():
    return unreal.AssetRegistryHelpers.get_asset_registry()


def _list_static_meshes(root):
    ar = _asset_registry()
    paths = []
    try:
        assets = ar.get_assets_by_path(root, recursive=True)
    except Exception:
        return paths
    for data in assets:
        try:
            cls = str(data.asset_class_path.asset_name) if hasattr(data, "asset_class_path") else str(data.asset_class)
        except Exception:
            cls = ""
        if "StaticMesh" not in cls:
            continue
        name = str(data.asset_name).lower()
        if any(k in name for k in ("decal", "particle", "icon", "ui_", "proxy", "lod0_collision", "hism")):
            continue
        paths.append(str(data.package_name) + "." + str(data.asset_name))
    return paths


def discover_meshes():
    found = []
    seen = set()
    for root in SEARCH_ROOTS:
        for path in _list_static_meshes(root):
            if path in seen:
                continue
            seen.add(path)
            found.append(path)
    # Prefer names that look like buildings
    preferred = [p for p in found if any(h in p.lower() for h in BUILDING_NAME_HINTS)]
    return preferred if preferred else found


def find_by_label(label):
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if actor.get_actor_label() == label:
            return actor
    return None


def hide_row_extras(prefix):
    """Hide cube façade extras once real mesh is on _Mass."""
    hidden = 0
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        label = actor.get_actor_label()
        if not label.startswith(prefix + "_"):
            continue
        if label.endswith("_Mass"):
            continue
        smc = getattr(actor, "static_mesh_component", None)
        if smc:
            smc.set_visibility(False, False)
            actor.set_actor_hidden_in_game(True)
            hidden += 1
    return hidden


def mesh_bounds_size(mesh):
    try:
        box = mesh.get_bounding_box()
        mn = box.min
        mx = box.max
        return unreal.Vector(abs(mx.x - mn.x), abs(mx.y - mn.y), abs(mx.z - mn.z))
    except Exception:
        return unreal.Vector(100.0, 100.0, 100.0)


def apply():
    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level_editor.load_level(MAP_PATH):
        raise RuntimeError("load failed " + MAP_PATH)

    # Ensure registry knows Fab content
    try:
        _asset_registry().scan_paths_synchronous(SEARCH_ROOTS, True)
    except Exception:
        pass

    meshes = discover_meshes()
    if not meshes:
        unreal.log_warning(
            "FAB MESHES — none found under %s. In Fab: Add City Sample Buildings "
            "to My Library, then Add to Project (LostEmpire), then re-run."
            % ", ".join(SEARCH_ROOTS)
        )
        return 0

    unreal.log("FAB MESHES — %d candidate building meshes" % len(meshes))
    swapped = 0
    for i, label in enumerate(ROW_MASS_LABELS):
        actor = find_by_label(label)
        if actor is None:
            unreal.log_warning("FAB MESHES — missing actor %s" % label)
            continue
        smc = actor.static_mesh_component
        if smc is None:
            continue

        # Current cube footprint in world units (BasicShapes Cube = 100uu)
        cur_scale = actor.get_actor_scale3d()
        target = unreal.Vector(abs(cur_scale.x) * 100.0, abs(cur_scale.y) * 100.0, abs(cur_scale.z) * 100.0)

        mesh_path = meshes[i % len(meshes)]
        mesh = unreal.load_asset(mesh_path)
        if mesh is None:
            unreal.log_warning("FAB MESHES — failed load %s" % mesh_path)
            continue

        smc.set_static_mesh(mesh)
        size = mesh_bounds_size(mesh)
        sx = target.x / max(size.x, 1.0)
        sy = target.y / max(size.y, 1.0)
        sz = target.z / max(size.z, 1.0)
        actor.set_actor_scale3d(unreal.Vector(sx, sy, sz))
        # Keep base on ground: lift so bottom sits near z=0
        loc = actor.get_actor_location()
        actor.set_actor_location(unreal.Vector(loc.x, loc.y, target.z * 0.5), False, True)

        prefix = label.rsplit("_Mass", 1)[0]
        hide_row_extras(prefix)
        swapped += 1
        unreal.log("FAB MESHES — %s -> %s" % (label, mesh_path))

    if not level_editor.save_current_level():
        raise RuntimeError("save failed")
    unreal.log("FAB MESHES — swapped %d / %d Row_*_Mass bodies" % (swapped, len(ROW_MASS_LABELS)))
    return swapped


if __name__ == "__main__":
    apply()
else:
    apply()
