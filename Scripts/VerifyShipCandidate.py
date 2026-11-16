import unreal
import os

ROOT = unreal.Paths.project_dir()


def must_exist(rel, failures):
    path = os.path.join(ROOT, rel.replace("/", os.sep))
    if not os.path.isfile(path):
        failures.append("missing " + rel)


def main():
    failures = []

    must_exist("Design/Voice/VOLock.md", failures)
    must_exist("Design/Voice/EmpireBriefings.md", failures)
    must_exist("Design/Platform/ShipCandidate.md", failures)
    must_exist("Design/Platform/SteamWindows.md", failures)
    must_exist("Design/Hybrid/MultiplayerRTS.md", failures)
    must_exist("Scripts/PackageWin64.ps1", failures)
    must_exist("steam_appid.txt", failures)

    if not unreal.EditorAssetLibrary.does_asset_exist("/Game/Maps/Empire/Levee_Greybox"):
        failures.append("Levee_Greybox missing")
    if not unreal.EditorAssetLibrary.does_asset_exist("/Game/Maps/Empire/Levee_Skirmish"):
        failures.append("Levee_Skirmish missing")

    for path in (
        "/Script/LostEmpire.LESkirmishGameMode",
        "/Script/LostEmpire.LEWeekDirector",
    ):
        if unreal.load_class(None, path) is None:
            failures.append("class " + path)

    # Soft-lock symbols exist via WeekDirector class load; map cook list sanity via ini read
    ini = os.path.join(ROOT, "Config", "DefaultGame.ini")
    with open(ini, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
    for needle in (
        "Levee_Greybox",
        "Brickyard_Greybox",
        "HaldenRow_Greybox",
        "AmesHill_Greybox",
        "Levee_Skirmish",
    ):
        if needle not in text:
            failures.append("MapsToCook missing " + needle)

    engine_ini = os.path.join(ROOT, "Config", "DefaultEngine.ini")
    with open(engine_ini, "r", encoding="utf-8", errors="ignore") as f:
        etext = f.read()
    if "t.MaxFPS=60" not in etext:
        failures.append("t.MaxFPS=60 not set")
    if "SteamDevAppId=480" not in etext:
        failures.append("Steam AppId missing")

    if failures:
        unreal.log_error("SHIP FAIL " + "; ".join(failures))
        raise RuntimeError("Ship candidate verification failed")
    unreal.log("SHIP VERIFY OK")


main()
