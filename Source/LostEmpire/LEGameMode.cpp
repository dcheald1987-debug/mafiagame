#include "LEGameMode.h"

#include "LostEmpire.h"
#include "LECityCameraPawn.h"
#include "LEGameHUD.h"

ALEGameMode::ALEGameMode()
{
	DefaultPawnClass = ALECityCameraPawn::StaticClass();
	HUDClass = ALEGameHUD::StaticClass();
}

void ALEGameMode::StartPlay()
{
	Super::StartPlay();
	UE_LOG(LogLostEmpire, Log, TEXT("Lost Empire. Empire week — bird's-eye Levee."));
}
