# Lost Empire — Windows + Steam

## Windows

- Target: **Win64** (UE 5.8, DX12 default).
- Package with `Scripts/PackageWin64.ps1` or Editor → Platforms → Windows → Package Project.
- Shipping build uses Pak + IoStore + Oodle (see `Config/DefaultGame.ini`).

## Steam

- Plugin: **Online Subsystem Steam** enabled in `LostEmpire.uproject`.
- Config: `Config/DefaultEngine.ini` → `DefaultPlatformService=Steam`, net driver + auth.
- **Dev App ID `480`** (Spacewar) until you create a Steamworks app. Then set `SteamDevAppId` to your real ID.
- Root `steam_appid.txt` = `480` for editor / local packaged tests. **Do not upload that file** with a Steam depot; Steam sets the App ID when launched from the client.

### Checklist before Steam ship

1. Steamworks partner account + App ID.
2. Replace `480` in `DefaultEngine.ini` and drop real App ID into Steam launch config.
3. Package Win64 Shipping; upload via SteamPipe / Steamworks depot tools.
4. Optional later: achievements, cloud saves, rich presence, MP lobbies (uses Steam net driver already).

### Local Steam test

1. Steam client running and logged in.
2. Package or Standalone PIE.
3. Log should show `Creating online subsystem instance for: STEAM` / Steamworks loaded.
