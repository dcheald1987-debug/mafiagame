# Lost Empire — Multiplayer RTS (roadmap lock)

Same Saint Lorne maps (Levee first). Gameplay shifts from Gangsters week-loop to **real-time strategy** in the spirit of *Age of Empires* and *Command & Conquer*.

## Product lock

- **Map:** Reuse dressed districts (Levee → Brickyard → …). Iso / high camera stays.
- **Mode:** Competitive or co-op skirmish, not the single-player story week director.
- **Feel:** Base → economy → army → take the map. Not turn-Plan/Working-Week.

## Pillars (AoE + C&C)

| Pillar | AoE-like | C&C-like | Lost Empire read |
|---|---|---|---|
| Economy | Villagers / drop-off | Harvesters / Tiberium fields | Hoods + rackets / docks as resource nodes |
| Build | Town center, barracks | Construction yard, war factory | Safe house → garage → armory on owned blocks |
| Army | Soft counters | Units + vehicles | Enforcers, bagmen crews, cars later |
| Victory | Ruins / wonder / score | Destroy opponent CY | Wipe rival safe house **or** control majority of blocks |

## Slice exit (multiplayer phase)

1. 2-player listen-server or Steam/EOS session on `Levee_Greybox`.
2. Each player owns a starting block + safe house.
3. Real-time select / move / attack (box select later).
4. One resource (cash) from held businesses; spend on hoods or a building.
5. Win: destroy enemy safe house **or** hold 5/8 sites for 60s.
6. SP week-loop remains a separate GameMode; MP uses `LESkirmishGameMode`.

## Shipped slice (complete)

| Gate | Evidence |
|---|---|
| `LESkirmishGameMode` | Separate from `LEGameMode` |
| Map | `/Game/Maps/Empire/Levee_Skirmish` |
| Select / move / attack | LMB / RMB via `LESkirmishPlayerController` |
| Economy | Cash tick from owned sites; N/M train |
| Capture | Stand on block ~3.5s to flip ownership |
| Victory | Capture rival safe house **or** majority hold 60s |
| 2p / AI | Listen-server teams; AI fills Red until join |
| Net | Steam OSS + IpNetDriver fallback |

## Out of scope for first MP slice

Crafting, RPG trees, full Fog of War polish, 8-player, campaign co-op story.
