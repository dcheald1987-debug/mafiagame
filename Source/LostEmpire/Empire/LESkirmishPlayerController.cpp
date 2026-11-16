#include "LESkirmishPlayerController.h"

#include "LESkirmishDirector.h"
#include "LESkirmishUnit.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"

ALESkirmishPlayerController::ALESkirmishPlayerController()
{
	bShowMouseCursor = true;
	bEnableClickEvents = true;
	bEnableMouseOverEvents = true;
	DefaultMouseCursor = EMouseCursor::Crosshairs;
}

void ALESkirmishPlayerController::BeginPlay()
{
	Super::BeginPlay();
	FInputModeGameAndUI Mode;
	Mode.SetHideCursorDuringCapture(false);
	Mode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
	SetInputMode(Mode);
	bShowMouseCursor = true;
}

void ALESkirmishPlayerController::AssignTeam(ELESkirmishTeam InTeam)
{
	LocalTeam = InTeam;
	ClientAssignTeam(InTeam);
}

void ALESkirmishPlayerController::ClientAssignTeam_Implementation(ELESkirmishTeam InTeam)
{
	LocalTeam = InTeam;
}

void ALESkirmishPlayerController::SetupInputComponent()
{
	Super::SetupInputComponent();
	if (!InputComponent)
	{
		return;
	}
	InputComponent->BindAction(TEXT("SkirmishSelect"), IE_Pressed, this, &ALESkirmishPlayerController::OnSelectPressed);
	InputComponent->BindAction(TEXT("SkirmishCommand"), IE_Pressed, this, &ALESkirmishPlayerController::OnCommandPressed);
	InputComponent->BindAction(TEXT("SkirmishTrainEnforcer"), IE_Pressed, this, &ALESkirmishPlayerController::OnTrainEnforcer);
	InputComponent->BindAction(TEXT("SkirmishTrainBagman"), IE_Pressed, this, &ALESkirmishPlayerController::OnTrainBagman);
}

ALESkirmishDirector* ALESkirmishPlayerController::GetDirector() const
{
	return Cast<ALESkirmishDirector>(
		UGameplayStatics::GetActorOfClass(GetWorld(), ALESkirmishDirector::StaticClass()));
}

bool ALESkirmishPlayerController::TraceCursor(FHitResult& OutHit) const
{
	FVector WorldOrigin;
	FVector WorldDir;
	if (!DeprojectMousePositionToWorld(WorldOrigin, WorldDir))
	{
		return false;
	}
	const FVector End = WorldOrigin + WorldDir * 100000.f;
	FCollisionQueryParams Params(SCENE_QUERY_STAT(SkirmishTrace), true);
	Params.bTraceComplex = true;
	return GetWorld()->LineTraceSingleByChannel(OutHit, WorldOrigin, End, ECC_Visibility, Params);
}

void ALESkirmishPlayerController::OnSelectPressed()
{
	FHitResult Hit;
	if (!TraceCursor(Hit))
	{
		if (ALESkirmishDirector* Dir = GetDirector())
		{
			Dir->ClearSelection(LocalTeam);
		}
		return;
	}

	ALESkirmishUnit* Unit = Cast<ALESkirmishUnit>(Hit.GetActor());
	if (!Unit && Hit.GetComponent())
	{
		Unit = Cast<ALESkirmishUnit>(Hit.GetComponent()->GetOwner());
	}
	if (Unit)
	{
		ServerSelectUnit(Unit);
	}
	else if (ALESkirmishDirector* Dir = GetDirector())
	{
		Dir->ClearSelection(LocalTeam);
	}
}

void ALESkirmishPlayerController::OnCommandPressed()
{
	FHitResult Hit;
	if (!TraceCursor(Hit))
	{
		return;
	}

	ALESkirmishUnit* Unit = Cast<ALESkirmishUnit>(Hit.GetActor());
	if (!Unit && Hit.GetComponent())
	{
		Unit = Cast<ALESkirmishUnit>(Hit.GetComponent()->GetOwner());
	}
	if (Unit && Unit->Team != LocalTeam)
	{
		ServerCommandAttack(Unit);
		return;
	}

	FVector Dest = Hit.ImpactPoint;
	if (!Hit.bBlockingHit)
	{
		// Ortho camera: intersect ground plane Z=0.
		FVector Origin, Dir;
		if (DeprojectMousePositionToWorld(Origin, Dir) && !FMath::IsNearlyZero(Dir.Z))
		{
			const float T = -Origin.Z / Dir.Z;
			Dest = Origin + Dir * T;
		}
	}
	Dest.Z = 40.f;
	ServerCommandMove(Dest);
}

void ALESkirmishPlayerController::OnTrainEnforcer()
{
	ServerTrain(ELESkirmishUnitRole::Enforcer);
}

void ALESkirmishPlayerController::OnTrainBagman()
{
	ServerTrain(ELESkirmishUnitRole::Bagman);
}

void ALESkirmishPlayerController::ServerSelectUnit_Implementation(ALESkirmishUnit* Unit)
{
	if (ALESkirmishDirector* Dir = GetDirector())
	{
		Dir->SelectUnit(Unit, LocalTeam);
	}
}

void ALESkirmishPlayerController::ServerCommandMove_Implementation(FVector_NetQuantize WorldLocation)
{
	if (ALESkirmishDirector* Dir = GetDirector())
	{
		Dir->CommandSelectedMove(LocalTeam, WorldLocation);
	}
}

void ALESkirmishPlayerController::ServerCommandAttack_Implementation(ALESkirmishUnit* Target)
{
	if (ALESkirmishDirector* Dir = GetDirector())
	{
		Dir->CommandSelectedAttack(LocalTeam, Target);
	}
}

void ALESkirmishPlayerController::ServerTrain_Implementation(ELESkirmishUnitRole InRole)
{
	if (ALESkirmishDirector* Dir = GetDirector())
	{
		Dir->TryTrainUnit(LocalTeam, InRole);
	}
}
