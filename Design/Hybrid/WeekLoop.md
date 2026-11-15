# Lost Empire — Gangsters hybrid lock

Bird’s-eye empire week over Saint Lorne. Story is a spine of weeks, not a driving campaign.

## Loop

1. **Story beat** (short text / VO) sets the week’s demand.
2. **Plan week** — assign each hood one order and one site. Unlimited time.
3. **Working week** — real-time bird’s-eye. Hoods walk to sites and resolve. Clock 1x / 3x. Space starts/ends when ready; week also ends when all assignments resolve or the timer hits zero.
4. **Results** — cash, heat, arrests, dead, blocks held. Then next plan, or a story gate.

## The Levee — eight sites

| ID | Name | Kind | Owner start | Collect $ | Notes |
|---|---|---|---|---|---|
| S01 | Pell’s Garage | Racket | Player | 40 | Safe house. Watch holds the block. |
| S02 | Corvo Cafe | Business | Player | 55 | Sal’s front. Low heat on Collect. |
| S03 | Dock Warehouse A | Racket | Contested | 80 | Story beat 1 target. |
| S04 | Hawser Bar | Business | Rival | 50 | Harlan crew drinks here. |
| S05 | Call Box Corner | Street | Neutral | 0 | Recruit only. |
| S06 | Levee Boarding | Business | Contested | 35 | Soft Collect. |
| S07 | Rope Walk | Block | Rival | 0 | Watch / Hit turf. |
| S08 | Freight Office | Racket | Rival | 70 | High Collect, high heat. |

Blocks: GarageBlock (S01–S02), DockBlock (S03), BarBlock (S04–S05), RopeBlock (S06–S07), FreightBlock (S08).

## Hoods (player start)

| ID | Name | Role | Loyalty | Notes |
|---|---|---|---|---|
| H01 | Eddie Voss | Bagman | 60 | Player face. Better Collect. |
| H02 | Nicky Ferro | Enforcer | 50 | Better Hit. Fragile after wounds. |
| H03 | Nora Pell | Recruiter | 70 | Better Recruit. Will not Hit. |

Roster cap for slice: 5. Recruit from S05 only in v1.

## Orders

| Order | Who | Resolves when | Effect |
|---|---|---|---|
| Collect | Bagman preferred | Arrive + short shake | +cash, +heat if site rival/contested |
| Watch | Any | Stand until week end | Block resists rival claim |
| Recruit | Recruiter preferred | Arrive + contact | +1 hood if under cap (once per week) |
| Hit | Enforcer preferred | Arrive + fight | Rival hood/site damaged; +heat; risk of death |

## Rival stub — Harlan crew

Two hoods: **Quinn** (enforcer), **Bridget** (bagman). Weekly script:

- Week N even: Collect S04 or S08 if they hold it; else Watch RopeBlock.
- Week N odd: Hit a contested site the player Collected last week, or Watch DockBlock.

No full AI brain. Script reads last week’s player actions from the Week Director.

## Heat

0 clean → 1 noticed → 2 watched → 3 raid risk → 4 bust. Collect on rival sites and Hits raise heat. Watch does not. At 3+, a patrol can arrest one hood on a Hit/Collect for 2 weeks. Heat decays by 1 at the start of each Plan if no Hit last week.

## Story beats

- **Beat 0 — The Favor owed.** Eddie is Corvo’s man on the Levee. Tutorial week: Collect S02, Watch S01. Unlock full orders after results.
- **Beat 1 — Sal wants the dock.** After 2 successful weeks (cash ≥ 100 total across weeks, player still free), Sal demands Dock Warehouse A (S03). Gate: hold S03 at week end (Watch or Collect that resolved, block owner Player). Then briefing unlocks Brickyard as “next district” stub (map marker only for now).

## Camera

Fixed **isometric** view matching *Gangsters: Organized Crime*: orthographic camera, ~50° pitch, −45° yaw, pan on the ground plane, zoom changes ortho width. No free tilt. No driving in the slice. Plan assigns via keys (sites cycle Q/E); click-to-assign can come later.

## Slice exit

One Levee greybox, Plan → Week → Results, four orders, heat, rival script, beat 0→1. Readable from altitude.
