# Ship candidate — exit gates

## Soft-locks

- Working week ends on timer, all-done, or **3× duration overrun** force-finish.
- Results idle **≥ 90s** auto-advances to next Plan.
- `FinishWeek` re-entry guarded (`bFinishWeekGuard`).

## Perf

- Target **60 fps** isometric (`t.MaxFPS=60`, smoothed frame range capped at 60, VSync on).
- Ortho camera + greybox meshes; no cinematic post stack required for candidate.

## VO

- Cue list locked in `Design/Voice/VOLock.md` / `EmpireBriefings.md`.
- Text briefings ship without WAV; generate ElevenLabs takes before store build.

## Windows + Steam

- Package: `Scripts/PackageWin64.ps1` (Shipping / Win64 / Pak).
- OSS Steam AppId **480** for local; replace before depot upload (`SteamWindows.md`).
- Root `steam_appid.txt` for editor/packaged local tests only.

## Multiplayer stability (candidate)

- Skirmish uses listen-server + Steam net driver fallback to IpNetDriver.
- AI fills Red until a second player joins.
- Separate GameMode from SP week-loop — no shared soft-lock surface.
