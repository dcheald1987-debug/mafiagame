#include "LEGameMode.h"
#include "LostEmpire.h"

void ALEGameMode::StartPlay()
{
	Super::StartPlay();
	UE_LOG(LogLostEmpire, Log, TEXT("Lost Empire. Chapter in production: C01 Service Entrance."));
}
