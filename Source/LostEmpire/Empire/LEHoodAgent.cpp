#include "LEHoodAgent.h"

#include "LESiteActor.h"
#include "Components/CapsuleComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "UObject/ConstructorHelpers.h"

ALEHoodAgent::ALEHoodAgent()
{
	PrimaryActorTick.bCanEverTick = true;
	bUseControllerRotationYaw = false;
	AutoPossessAI = EAutoPossessAI::Disabled;

	GetCapsuleComponent()->InitCapsuleSize(42.f, 60.f);
	GetCharacterMovement()->bOrientRotationToMovement = true;
	GetCharacterMovement()->MaxWalkSpeed = MoveSpeed;
	GetCharacterMovement()->bRunPhysicsWithNoController = true;
	GetCharacterMovement()->DefaultLandMovementMode = MOVE_Walking;

	IsoMarker = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("IsoMarker"));
	IsoMarker->SetupAttachment(RootComponent);
	IsoMarker->SetRelativeLocation(FVector(0.f, 0.f, 40.f));
	IsoMarker->SetRelativeScale3D(FVector(1.2f, 1.2f, 2.2f));
	IsoMarker->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeFinder(TEXT("/Engine/BasicShapes/Cube.Cube"));
	if (CubeFinder.Succeeded())
	{
		IsoMarker->SetStaticMesh(CubeFinder.Object);
	}

	NameLabel = CreateDefaultSubobject<UTextRenderComponent>(TEXT("NameLabel"));
	NameLabel->SetupAttachment(RootComponent);
	NameLabel->SetRelativeLocation(FVector(0.f, 0.f, 160.f));
	NameLabel->SetHorizontalAlignment(EHTA_Center);
	NameLabel->SetWorldSize(48.f);
	NameLabel->SetTextRenderColor(FColor(20, 18, 12));
}

void ALEHoodAgent::BeginPlay()
{
	Super::BeginPlay();
	RefreshAppearance();
}

void ALEHoodAgent::Configure(FName InHoodId, FText InDisplayName, uint8 InRole, uint8 InFaction, int32 InLoyalty)
{
	HoodId = InHoodId;
	DisplayName = InDisplayName;
	HoodRole = static_cast<ELEHoodRole>(InRole);
	Faction = static_cast<ELEOwner>(InFaction);
	Loyalty = InLoyalty;
	RefreshAppearance();
}

void ALEHoodAgent::SetSelected(bool bInSelected)
{
	bSelected = bInSelected;
	RefreshAppearance();
}

void ALEHoodAgent::RefreshAppearance()
{
	if (NameLabel)
	{
		NameLabel->SetText(DisplayName.IsEmpty() ? FText::FromName(HoodId) : DisplayName);
		NameLabel->SetTextRenderColor(bSelected ? FColor(180, 40, 20) : FColor(20, 18, 12));
		NameLabel->SetWorldSize(bSelected ? 58.f : 48.f);
	}

	if (!IsoMarker)
	{
		return;
	}

	FLinearColor Color(0.6f, 0.6f, 0.6f);
	if (Faction == ELEOwner::Player)
	{
		Color = FLinearColor(0.2f, 0.45f, 0.9f);
	}
	else if (Faction == ELEOwner::Rival)
	{
		Color = FLinearColor(0.85f, 0.18f, 0.12f);
	}

	if (AssignmentState == ELEAssignmentState::Dead)
	{
		Color = FLinearColor(0.15f, 0.15f, 0.15f);
	}
	else if (AssignmentState == ELEAssignmentState::Arrested)
	{
		Color = FLinearColor(0.5f, 0.35f, 0.1f);
	}

	if (bSelected)
	{
		Color = Color * 1.35f;
		IsoMarker->SetRelativeScale3D(FVector(1.55f, 1.55f, 2.6f));
	}
	else
	{
		IsoMarker->SetRelativeScale3D(FVector(1.2f, 1.2f, 2.2f));
	}

	UMaterialInterface* BaseMat = IsoMarker->GetMaterial(0);
	if (BaseMat)
	{
		UMaterialInstanceDynamic* Mid = IsoMarker->CreateAndSetMaterialInstanceDynamic(0);
		if (Mid)
		{
			Mid->SetVectorParameterValue(TEXT("Color"), Color);
			Mid->SetVectorParameterValue(TEXT("BaseColor"), Color);
		}
	}
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
	RefreshAppearance();
}

void ALEHoodAgent::CancelAssignment()
{
	ActiveOrder = ELEOrderType::None;
	TargetSite = nullptr;
	AssignmentState = ELEAssignmentState::Idle;
	WorkTimer = 0.f;
	RefreshAppearance();
}

void ALEHoodAgent::MoveTowardTarget(float DeltaSeconds)
{
	if (!TargetSite)
	{
		return;
	}

	const FVector Here = GetActorLocation();
	const FVector Goal = TargetSite->GetActorLocation();
	FVector Delta = Goal - Here;
	Delta.Z = 0.f;
	const float Dist = Delta.Size();
	if (Dist <= 110.f)
	{
		AssignmentState = ELEAssignmentState::Working;
		WorkTimer = 0.f;
		WorkDuration = (ActiveOrder == ELEOrderType::Watch) ? 9999.f : 2.5f;
		RefreshAppearance();
		return;
	}

	const FVector Dir = Delta / Dist;
	const FVector Step = Dir * MoveSpeed * DeltaSeconds;
	SetActorLocation(Here + Step, true);
	SetActorRotation(Dir.Rotation());
}

void ALEHoodAgent::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	if (AssignmentState == ELEAssignmentState::Moving)
	{
		MoveTowardTarget(DeltaSeconds);
	}
	else if (AssignmentState == ELEAssignmentState::Working)
	{
		WorkTimer += DeltaSeconds;
		if (ActiveOrder != ELEOrderType::Watch && WorkTimer >= WorkDuration)
		{
			AssignmentState = ELEAssignmentState::Done;
			RefreshAppearance();
		}
	}
}
