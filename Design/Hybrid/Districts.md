# Lost Empire — Open districts

Unlockable maps beyond The Levee. Same week-loop GameMode; campaign state persists in `ULEEmpireGameInstance`.

## Districts

| ID | Map | Unlock | Character |
|---|---|---|---|
| Levee | `/Game/Maps/Empire/Levee_Greybox` | Always | Docks, Corvo, Harlan fight |
| Brickyard | `/Game/Maps/Empire/Brickyard_Greybox` | Dock held for Sal (beat 2+) | Kilns, union yards, brick dust |
| Halden Row | `/Game/Maps/Empire/HaldenRow_Greybox` | Dock war won (beat 3+) | Brownstones, boarding, soft money |
| Ames Hill | `/Game/Maps/Empire/AmesHill_Greybox` | Story spine complete (beat 5) | Mill overlook, company cops |

## Travel

- Plan phase only. Cycle unlocked districts with `[` / `]`, confirm travel with `T`.
- Working / Results stay on the current map.
- Cash, heat, story beat, unlocks, week index carry via GameInstance.

## Slice exit

Four maps exist and load. Unlock gates fire from story. Travel works without soft-lock. Each district has WeekDirector + sites + hoods readable from iso.
