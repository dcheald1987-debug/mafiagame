# Lost Empire — art ref map (Levee)

Refs live under `Art/Refs/{Characters,Buildings,Cars,Kits,Props,Weapons,Video}`.

**In-game:** refs are **art direction only** (not world billboards). Real street = 3D massing + materials. Use Fab/meshes from these sheets. `ImportGameplaySprites.py` must not place sheets in the level — see `RemoveGameplaySprites.py`.

## Sites → building refs

| Site / row | Name | Ref |
|---|---|---|
| S01 / Row_Garage | Pell’s Garage | `Buildings/*bu-d989*` |
| S02 / Row_Cafe | Corvo Cafe | `Buildings/*bu-6a0c*` |
| S03 / Row_Dock | Dock № 3 warehouse | `Buildings/*bu-1635*` |
| S04 / Row_Bar | Hawser Bar | `Buildings/*bu-1e51*` |
| S05 / Row_Board | Rooms / boarding (olive) | `Buildings/*bu-4c02*` |
| Row_Freight | Warehouse 7 | `Buildings/*bu-0f18*` |
| Row_Rope | Pier No 6 | `Buildings/*bu-866e*` |
| Row_MidA–G | Street filler row | `Buildings/*fi-3945*` |
| Kit pieces | Modular storefront / brick / roof | `Kits/*mo-3e66*` |

## Cars

| In-game | Ref |
|---|---|
| Eddie’s Packard | Gloss black Packard 1936 (`Cars/*ve-f0b9*`) |
| Harlan Sedan | Dusty matte black 1937 (`Cars/*ve-7a01*`) |

## Characters (from prior drop)

| Role | Ref cue |
|---|---|
| Eddie Voss | Olive overcoat + brown fedora |
| Nicky Ferro | Pinstripe + black fedora (heavy) |
| Nora Pell | Burgundy fur-collar + cloche |
| Harlan crew | Trio sheet (lean / heavy / flat-cap) |
| Civilians | Dock worker, camel-coat man, tan-beret woman |

## Props / doors (`Props/*pr-*`)

| Piece | Use |
|---|---|
| Speakeasy peephole door | Hawser Bar / racket entry |
| 4-panel room door | Boarding / Call Box interiors |
| Saloon swinging doors | Hawser Bar interior |
| Art Deco frosted glass door | Corvo / office |
| Slide bolt, chain, push plates | Door interact / locked states |
| Coat rack | Interior dress |
| Warm lantern | Street / alley prop |
| Bar stool | Hawser Bar |
| Stacked crates | Dock / Freight / Pier dress |

## Weapons (`Weapons/*weapo-*`)

Street loop today only has Hit-and-run / Drive-by (no inventory). Use as **dossier icons + order VFX + skirmish**.

| Piece | Bind to |
|---|---|
| Thompson (drum) | Drive-by / Enforcer heavy |
| Pump shotgun | Enforcer Hit-and-run |
| Sawn-off | Rival street hit (close) |
| Lever rifle | Scout / rooftop rare |
| Baseball bat | Soft Hit / wound (no heat spike later) |
| Brass knuckles | Melee intimidate |
| Switchblade | Bagman hideout / quiet |
| 1911 | **Eddie** sidearm default |
| Service revolver | **Nora** / civilian cops later |
| Snub revolver | Pocket carry / bagman |
| Long revolver | Harlan crew |
| Luger | Rival specialty |
| C96 broomhandle | Rival boss / trophy |

**Slice lock (keep small):** Eddie = 1911 · Nicky = Thompson or pump · Nora = snub/revolver · Harlan = long revolver + sawn-off.

## Video turntables

Batch 1 (earlier):

| File | Use |
|---|---|
| `Video/orbit_three_quarter.mp4` | Static three-quarter — primary iso read |
| `Video/locked_side.mp4` | Locked-off side elevation |
| `Video/low_static.mp4` | Low static camera — street-level scale |

Batch 2 (2026-11-15 ~15:47 — credits ran out after these):

| File | Angle |
|---|---|
| `Video/batch2_side_154729.mp4` | Locked-off side |
| `Video/batch2_side_154748.mp4` | Locked-off side |
| `Video/batch2_front_154752.mp4` | Locked-off front |
| `Video/batch2_front_154753.mp4` | Locked-off front |
| `Video/batch2_front_154759.mp4` | Locked-off front |
| `Video/batch2_front_154814.mp4` | Locked-off front |

**Art lock status:** characters, landmark buildings, cars, weapons, props, + enough front/side video for silhouette. Remaining Seedance angles can wait for credits — do not block mesh / Fab / greybox swap.
