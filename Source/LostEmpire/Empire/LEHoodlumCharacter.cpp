#include "LEHoodlumCharacter.h"

#include "LESiteActor.h"
#include "LEStreetCar.h"

ALEHoodlumCharacter::ALEHoodlumCharacter()
{
	MoveSpeed = 560.f; // snappy street orders for iso click-to-move
}

void ALEHoodlumCharacter::ConfigureHoodlum(FName InId, FText InName, uint8 InRole, uint8 InFaction, int32 InLoyalty)
{
	HoodId = InId;
	DisplayName = InName;
	HoodRole = static_cast<ELEHoodRole>(InRole);
	Faction = static_cast<ELEOwner>(InFaction);
	Loyalty = InLoyalty;
	RefreshAppearance();
}

void ALEHoodlumCharacter::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	ResolveOrderProximity(DeltaSeconds);
}

void ALEHoodlumCharacter::IssueEnterBuilding(ALESiteActor* Site)
{
	if (!Site)
	{
		return;
	}
	CancelStreetOrder();
	ActiveStreetOrder = ELEStreetOrder::EnterBuilding;
	OrderState = ELEAssignmentState::Moving;
	OccupiedSite = nullptr;
	OrderTarget = Site;
	bInBuilding = false;
	CommandMoveTo(Site->GetActorLocation());
}

void ALEHoodlumCharacter::IssueEnterCar(ALEStreetCar* Car)
{
	if (!Car)
	{
		return;
	}
	CancelStreetOrder();
	ActiveStreetOrder = ELEStreetOrder::EnterCar;
	OrderState = ELEAssignmentState::Moving;
	BoardedCar = nullptr;
	OrderTarget = Car;
	bInCar = false;
	CommandMoveTo(Car->GetActorLocation());
}

void ALEHoodlumCharacter::IssueScout(FVector WorldLocation)
{
	CancelStreetOrder();
	ActiveStreetOrder = ELEStreetOrder::MoveScout;
	OrderState = ELEAssignmentState::Moving;
	OrderTarget = nullptr;
	CommandMoveTo(WorldLocation);
}

void ALEHoodlumCharacter::IssueHitAndRun(AActor* Target)
{
	if (!Target)
	{
		return;
	}
	CancelStreetOrder();
	ActiveStreetOrder = ELEStreetOrder::HitAndRun;
	OrderState = ELEAssignmentState::Moving;
	OrderTarget = Target;
	OrderWorkTimer = 0.f;
	CommandMoveTo(Target->GetActorLocation());
}

void ALEHoodlumCharacter::IssueDriveBy(AActor* Target)
{
	if (!Target || !bInCar || !BoardedCar)
	{
		return;
	}
	ActiveStreetOrder = ELEStreetOrder::DriveBy;
	OrderState = ELEAssignmentState::Moving;
	OrderTarget = Target;
	OrderWorkTimer = 0.f;
	const FVector Pass = Target->GetActorLocation() + FVector(400.f, 200.f, 0.f);
	BoardedCar->BeginDrivePass(GetActorLocation(), Pass, Target->GetActorLocation());
	SetActorHiddenInGame(true);
	SetActorEnableCollision(false);
}

void ALEHoodlumCharacter::CancelStreetOrder()
{
	ActiveStreetOrder = ELEStreetOrder::None;
	OrderState = ELEAssignmentState::Idle;
	OrderTarget = nullptr;
	OrderWorkTimer = 0.f;
	ClearGoal();
	if (bInCar && BoardedCar)
	{
		SetActorHiddenInGame(false);
		SetActorEnableCollision(true);
		SetActorLocation(BoardedCar->GetActorLocation() + FVector(80.f, 0.f, 40.f));
		bInCar = false;
		BoardedCar->SetOccupant(nullptr);
		BoardedCar = nullptr;
	}
}

void ALEHoodlumCharacter::ResolveOrderProximity(float DeltaSeconds)
{
	if (ActiveStreetOrder == ELEStreetOrder::None || OrderState == ELEAssignmentState::Done)
	{
		return;
	}

	if (ActiveStreetOrder == ELEStreetOrder::DriveBy && BoardedCar)
	{
		SetActorLocation(BoardedCar->GetActorLocation() + FVector(0.f, 0.f, 60.f));
		if (BoardedCar->IsPassComplete())
		{
			OrderState = ELEAssignmentState::Done;
			OrderWorkTimer = 0.f;
			SetActorHiddenInGame(false);
			SetActorEnableCollision(true);
			SetActorLocation(BoardedCar->GetActorLocation() + FVector(120.f, 0.f, 40.f));
			bInCar = false;
			BoardedCar->SetOccupant(nullptr);
			BoardedCar = nullptr;
			ActiveStreetOrder = ELEStreetOrder::None;
		}
		return;
	}

	if (bHasGoal)
	{
		return;
	}

	if (ActiveStreetOrder == ELEStreetOrder::EnterBuilding)
	{
		if (ALESiteActor* Site = Cast<ALESiteActor>(OrderTarget))
		{
			OccupiedSite = Site;
			bInBuilding = true;
			OrderState = ELEAssignmentState::Working;
			SetActorLocation(Site->GetActorLocation() + FVector(0.f, 0.f, 30.f));
			SetActorHiddenInGame(true);
		}
		return;
	}

	if (ActiveStreetOrder == ELEStreetOrder::EnterCar)
	{
		if (ALEStreetCar* Car = Cast<ALEStreetCar>(OrderTarget))
		{
			BoardedCar = Car;
			bInCar = true;
			Car->SetOccupant(this);
			OrderState = ELEAssignmentState::Done;
			ActiveStreetOrder = ELEStreetOrder::None;
			SetActorHiddenInGame(true);
			SetActorEnableCollision(false);
			SetActorLocation(Car->GetActorLocation() + FVector(0.f, 0.f, 60.f));
		}
		return;
	}

	if (ActiveStreetOrder == ELEStreetOrder::MoveScout)
	{
		OrderState = ELEAssignmentState::Done;
		ActiveStreetOrder = ELEStreetOrder::None;
		return;
	}

	if (ActiveStreetOrder == ELEStreetOrder::HitAndRun)
	{
		OrderState = ELEAssignmentState::Working;
		OrderWorkTimer += DeltaSeconds;
		if (OrderWorkTimer >= 1.2f)
		{
			OrderState = ELEAssignmentState::Done;
			ActiveStreetOrder = ELEStreetOrder::None;
			OrderWorkTimer = 0.f;
			// Peel off after the hit.
			const FVector Away = GetActorLocation() + FVector(350.f, -200.f, 0.f);
			CommandMoveTo(Away);
		}
	}
}

FString ALEHoodlumCharacter::GetOrderLabel() const
{
	if (bInCar)
	{
		return TEXT("In car");
	}
	if (bInBuilding && OccupiedSite)
	{
		return FString::Printf(TEXT("Inside %s"), *OccupiedSite->DisplayName.ToString());
	}
	switch (ActiveStreetOrder)
	{
	case ELEStreetOrder::MoveScout: return TEXT("Scouting");
	case ELEStreetOrder::EnterBuilding: return TEXT("Entering building");
	case ELEStreetOrder::EnterCar: return TEXT("Boarding car");
	case ELEStreetOrder::HitAndRun: return TEXT("Hit and run");
	case ELEStreetOrder::DriveBy: return TEXT("Drive-by");
	default: return TEXT("Idle");
	}
}
