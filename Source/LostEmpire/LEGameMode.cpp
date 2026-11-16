#include "LEGameMode.h"

#include "LostEmpire.h"
#include "LECityCameraPawn.h"
#include "LEDayNightDirector.h"
#include "LEGameHUD.h"
#include "LEStreetDirector.h"
#include "LEWeekDirector.h"
#include "Kismet/GameplayStatics.h"

ALEGameMode::ALEGameMode()
{
	DefaultPawnClass = ALECityCameraPawn::StaticClass();
	HUDClass = ALEGameHUD::StaticClass();
}

void ALEGameMode::StartPlay()
{
	Super::StartPlay();

	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}

	if (UGameplayStatics::GetActorOfClass(World, ALEWeekDirector::StaticClass())
		&& !UGameplayStatics::GetActorOfClass(World, ALEStreetDirector::StaticClass()))
	{
		FActorSpawnParameters Params;
		Params.Name = TEXT("StreetDirector");
		Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		World->SpawnActor<ALEStreetDirector>(
			ALEStreetDirector::StaticClass(), FVector::ZeroVector, FRotator::ZeroRotator, Params);
	}

	if (!UGameplayStatics::GetActorOfClass(World, ALEDayNightDirector::StaticClass()))
	{
		FActorSpawnParameters Params;
		Params.Name = TEXT("DayNightDirector");
		Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		World->SpawnActor<ALEDayNightDirector>(
			ALEDayNightDirector::StaticClass(), FVector::ZeroVector, FRotator::ZeroRotator, Params);
	}

	UE_LOG(LogLostEmpire, Log, TEXT("Lost Empire. Street play — 1930s Saint Lorne."));
}
