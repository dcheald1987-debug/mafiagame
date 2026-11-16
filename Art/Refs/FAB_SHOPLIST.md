# Fab shopping list — Lost Empire (match Art/Refs)

Use **Fab** inside Unreal (Content Browser → Fab). Sign in with Epic.

## Priority (buildings)

| Pack | Why | Notes |
|---|---|---|
| [The American City: Modular 1920s Buildings](https://www.fab.com/listings/1131c43d-5b32-4bbf-93e9-a0dc31b6ac27) | Closest to Pell’s Garage / Corvo / tenements | Paid (~$10) — best period match |
| [City Sample Buildings](https://www.fab.com/listings/008fe959-5511-428e-93bd-f99b1179f6d5) | Free Epic modular city | Free — classic modules usable for mid-blocks |
| Quixel Modular Building Base Kit | Free brick/old downtown pieces | Free Megascans |

Search in Fab: `1920s modular building`, `brick tenement`, `speakeasy`, `warehouse`.

## Characters

Search: `1920s gangster`, `fedora character`, `period civilian`, `megascans people`  
Prefer MetaHuman-compatible or skeletal meshes with walk anims.

## Cars

Search: `1930s sedan`, `vintage car`, `packard`, `City Sample Vehicles` (free companion)

## Right now (editor)

1. Fab tab is open in LostEmpire — search `American City Modular 1920s`.
2. Edge has both listing pages open.
3. On each listing: **Add to My Library** → **Add to Project** → pick **LostEmpire**.
4. Prefer free first: **City Sample Buildings**, then paid **American City Modular 1920s**.

## After Add to Project

1. Content lands under `/Game/…` (often `CitySample`, `AmericanCity`, or `Fab/…`).
2. Run `Scripts/ApplyFabBuildingMeshes.py` in the editor (Execute Python Script) — swaps `Row_*` cubes for Fab static meshes.
3. Tell agent if characters/cars also landed — those get wired next (hood / street car placeholders).
