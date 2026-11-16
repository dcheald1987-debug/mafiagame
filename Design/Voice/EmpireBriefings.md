# Week briefing — ElevenLabs

Generate after script lock. 48 kHz mono WAV. Dry. Import to `Content/Audio/Voice/Radio/WLOR/` and `Content/Audio/Voice/Dialogue/Empire/`.

## Voices

| ID | Use | Direction |
|---|---|---|
| Eddie | Player briefing echo | Dry, working-class, same as C01 bible |
| Sal | Beat 1 dock demand | Quiet, formal |
| WLOR | Week open / war sting | Local station, flat |
| Ames contact | Beat 4 cool-down | Soft, bureaucratic |

## Lines

### Beat 0 — Plan open

- EMP_0001 Eddie: The Levee is small. That is why Sal put me here.
- EMP_0002 Eddie: Cafe money first. Nora keeps the garage door watched.
- EMP_0003 WLOR: Morning in Saint Lorne. The docks report a quiet week. For now.

### Beat 1 — Sal wants the dock

- EMP_0010 Sal: The warehouse on the water. Hold it until I say otherwise.
- EMP_0011 Eddie: And if Harlan is already inside?
- EMP_0012 Sal: Then you were not watching hard enough.

### Beat 2 — Harlan answers

- EMP_0020 Eddie: Harlan answered. He brought a third gun.
- EMP_0021 Eddie: Hold the dock one more week. Do not give it back.

### Beat 3 — Dock war

- EMP_0030 WLOR: Gunfire on the waterfront. The Levee is choosing sides.
- EMP_0031 Eddie: Warehouse and Hawser Bar. Both. Or we lose the street.

### Beat 4 — Ames watches

- EMP_0040 Ames: Cool the street. We are watching the heat.
- EMP_0041 Eddie: Hold what we took. No more noise than we need.

### Beat 5 — Spine complete

- EMP_0050 Eddie: Dock war is over. Brickyard waits when you are ready.

### Working week barks (Flash model, one take each)

- EMP_BARK_Collect_01: Money on the table.
- EMP_BARK_Watch_01: Nobody moves this corner.
- EMP_BARK_Hit_01: Do it clean.
- EMP_BARK_Recruit_01: You work for us now.

## Settings

- Hero: stability ~40, similarity ~75, three takes on EMP_0010–0012
- Barks: stability ~65, one take
- Files: `LE_DLG_EMP_<ID>_<Speaker>_T<n>.wav`

Pipeline: lock this page → generate → MetaSounds distance only for world barks; briefings play dry in the plan panel.
