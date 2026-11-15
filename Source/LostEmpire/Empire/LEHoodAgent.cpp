#include "LEHoodAgent.h"

#include "LESiteActor.h"
#include "AIController.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Navigation/PathFollowingComponent.h"

ALEHoodAgent::ALEHoodAgent()
{
	PrimaryActorTick.bCanEverTick = true;
	bUseControllerRotationYaw = false;
	GetCharacterMovement()->bOrientRotationToMovement = true;
	GetCharacterMovement()->MaxWalkSpeed = 320.f;
	AutoPossessAI = EAutoPossessAI::PlacedInWorldOrSpawned;
	AIControllerClass = AAIController::StaticClass();
}

void ALEHoodAgent::Configure(FName InHoodId, FText InDisplayName, uint8 InRole, uint8 InFaction, int32 InLoyalty)
{
	HoodId = InHoodId;
	DisplayName = InDisplayName;
	HoodRole = static_cast<ELEHoodRole>(InRole);
	Faction = static_cast<ELEOwner>(InFaction);
	Loyalty = InLoyalty;
}

void ALEHoodAgent::BeginAssignment(ELEOrderType Order, ALESiteActor* Site)
{
	if (!IsAvailable() || !Site || Order == ELEOrderType::None)
	{
		return;
	}

	ActiveOrder = Order;
	TargetSite = Site;
	WorkTimer = 0.f;
	AssignmentState = ELEAssignmentState::Moving;

	if (AAIController* AI = Cast<AAIController>(GetController()))
	{
		AI->MoveToActor(Site, 80.f);
	}
}

void ALEHoodAgent::CancelAssignment()
{
	ActiveOrder = ELEOrderType::None;
	TargetSite = nullptr;
	AssignmentState = ELEAssignmentState::Idle;
	WorkTimer = 0.f;
	if (AAIController* AI = Cast<AAIController>(GetController()))
	{
		AI->StopMovement();
	}
}

void ALEHoodAgent::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	if (AssignmentState == ELEAssignmentState::Moving && TargetSite)
	{
		const float Dist = FVector::Dist2D(GetActorLocation(), TargetSite->GetActorLocation());
		if (Dist <= 120.f)
		{
			if (AAIController* AI = Cast<AAIController>(GetController()))
			{
				AI->StopMovement();
			}
			AssignmentState = ELEAssignmentState::Working;
			WorkTimer = 0.f;
			WorkDuration = (ActiveOrder == ELEOrderType::Watch) ? 9999.f : 2.5f;
		}
	}
	else if (AssignmentState == ELEAssignmentState::Working)
	{
		WorkTimer += DeltaSeconds;
		if (ActiveOrder != ELEOrderType::Watch && WorkTimer >= WorkDuration)
		{
			AssignmentState = ELEAssignmentState::Done;
		}
	}
}
