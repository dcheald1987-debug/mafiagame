# Lost Empire — Gangsters hybrid lock

Bird’s-eye Saint Lorne. **Not a wait-week sim.** Play is real-time street command; the story advances by **missions**, not by clocking Plan→Working→Results.

## Core feel (Gangsters)

- Dense isometric streets, hoodlums + civilians, cars and buildings you can enter.
- **Click a gang member** → left dossier → give orders. Characters **move freely** at all times.
- Storyline = mission chain (Sal / dock / Harlan / Ames). Completing objectives unlocks the next beat — you do not sit through empty weeks to progress.

## Loop

1. **Mission briefing** (text / VO) — what Sal (or the street) wants now.
2. **Street play (real-time)** — select hoods, walk/drive, enter buildings, scout, hit-and-run, drive-by. No phase lock that freezes movement.
3. **Mission resolve** — objective met (or failed): cash, heat, arrests, story gate.
4. **Next mission** — spine advances. Optional “week” stamp is flavor/economy tick, not a gate you wait on.

Legacy Plan/Working/Results remains as a soft economy overlay (collect routes, heat decay) but **must not block free move or mission play**.

## Street orders (always available)

| Order | Input | Behavior |
|---|---|---|
| Move / Scout | Click hood → ground/block | Free path; scout scores the block (low heat) |
| Enter building | Click hood → building/site | Path to door; occupy; Collect/Watch/mission interact |
| Enter car | Click hood → car | Board; enables drive-by |
| Hit and run | Click hood → rival/site | Approach, brief fight, leave |
| Drive-by | Hood in car → target | Scripted pass, heat spike, pressure |

Economy mapping: building Collect/Watch; Hit-and-run / Drive-by → Hit pressure; Scout → intel / soft Watch.

## Characters

| Type | Role |
|---|---|
| **Hoodlum** | Player / rival gang. Clickable. Dossier + orders. |
| **Civilian** | Ambient. Wander sidewalks; flee on gunfire/heat. |

Player start hoods: Eddie Voss (bagman), Nicky Ferro (enforcer), Nora Pell (recruiter). Rival: Harlan crew on the street.

## The Levee — eight sites (mission anchors)

| ID | Name | Kind | Owner start | Notes |
|---|---|---|---|---|
| S01 | Pell’s Garage | Racket | Player | Safe house |
| S02 | Corvo Cafe | Business | Player | Sal’s front |
| S03 | Dock Warehouse A | Racket | Contested | Mission beat 1–3 focus |
| S04 | Hawser Bar | Business | Rival | Dock war |
| S05 | Call Box Corner | Street | Neutral | Recruit / cool heat |
| S06 | Levee Boarding | Business | Contested | Soft collect |
| S07 | Rope Walk | Block | Rival | Turf |
| S08 | Freight Office | Racket | Rival | High risk collect |

## Story missions (spine)

Full table: `Design/Hybrid/StorySpine.md`. Delivered as **active missions**, not “survive N weeks”:

- **M0 Favor** — Collect Corvo, Watch Garage (tutorial click orders).
- **M1 Dock** — Hold / take Dock Warehouse for Sal.
- **M2 Answer** — Keep dock under Harlan pressure.
- **M3 Dock war** — Warehouse + Hawser Bar.
- **M4 Cool** — Hold both with Heat ≤ 2.
- **M5 Complete** — Spine done; districts open.

## Heat

0→4 as before. Hits and drive-bys raise heat. Scout/Watch do not. Bribe / Call Box still cool the street.

## Look — full 3D, 1920s / 1930s

- **Full 3D** world (UE meshes, lights, characters) — not flat sprites, not sparse grey cubes as the final read.
- Period Saint Lorne: brick / sandstone façades, dark asphalt, warm tungsten street mood, fedora hoodlums, civilians in coats, period sedans.
- Palette lock: brick reds, soot greys, cream stone, olive/navy coats, black cars. Avoid neon / modern glass.
- Camera stays isometric ortho (Gangsters read) over a **real 3D street**, closer so people and cars read.

## Camera

Fixed isometric (Gangsters): ortho, ~50° pitch, −45° yaw, pan + zoom. Closer default ortho so people read. No free tilt.

## Slice exit

1. Levee reads as a **period 3D** street city (brick blocks, labels, people, cars, warm light).
2. Click hoods anytime → dossier → street orders; free movement.
3. Active mission panel drives story; completing M0–M1 without waiting on a week timer.
4. Civilians wander and flee on violence.
5. Enter car + drive-by stub works.
