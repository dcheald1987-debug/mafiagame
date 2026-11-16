#include "LESkirmishGameMode.h"

#include "LECityCameraPawn.h"
#include "LESkirmishDirector.h"
#include "LESkirmishHUD.h"
#include "LESkirmishPlayerController.h"
#include "LostEmpire.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"

ALESkirmishGameMode::ALESkirmishGameMode()
{
	DefaultPawnClass = ALECityCameraPawn::StaticClass();
	PlayerControllerClass = ALESkirmishPlayerController::StaticClass();
	HUDClass = ALESkirmishHUD::StaticClass();
	bUseSeamlessTravel = false;
}

void ALESkirmishGameMode::StartPlay()
{
	Super::StartPlay();
	EnsureDirector();
	UE_LOG(LogLostEmpire, Log, TEXT("Lost Empire skirmish GameMode — AoE/C&C real-time on this district."));
}

void ALESkirmishGameMode::PostLogin(APlayerController* NewPlayer)
{
	Super::PostLogin(NewPlayer);
	EnsureDirector();
	if (ALESkirmishPlayerController* SkirmishPC = Cast<ALESkirmishPlayerController>(NewPlayer))
	{
		// Host/listen Blue; first join Red. Extra joins stay Red (2p slice).
		const ELESkirmishTeam Team = (GetNumPlayers() <= 1) ? ELESkirmishTeam::Blue : ELESkirmishTeam::Red;
		SkirmishPC->AssignTeam(Team);
		if (Team == ELESkirmishTeam::Red)
		{
			if (ALESkirmishDirector* Dir = Director)
			{
				Dir->bSpawnAIOpponent = false;
			}
		}
	}
}

void ALESkirmishGameMode::EnsureDirector()
{
	if (Director || !GetWorld())
	{
		return;
	}
	if (AActor* Existing = UGameplayStatics::GetActorOfClass(GetWorld(), ALESkirmishDirector::StaticClass()))
	{
		Director = Cast<ALESkirmishDirector>(Existing);
		return;
	}
	FActorSpawnParameters Params;
	Params.Name = TEXT("SkirmishDirector");
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	Director = GetWorld()->SpawnActor<ALESkirmishDirector>(
		ALESkirmishDirector::StaticClass(),
		FVector::ZeroVector,
		FRotator::ZeroRotator,
		Params);
}
