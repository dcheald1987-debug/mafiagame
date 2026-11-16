#include "LESkirmishUnit.h"

#include "Components/CapsuleComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Net/UnrealNetwork.h"
#include "UObject/ConstructorHelpers.h"

ALESkirmishUnit::ALESkirmishUnit()
{
	PrimaryActorTick.bCanEverTick = true;
	bReplicates = true;
	SetReplicateMovement(true);
	bUseControllerRotationYaw = false;
	AutoPossessAI = EAutoPossessAI::Disabled;

	GetCapsuleComponent()->InitCapsuleSize(42.f, 60.f);
	GetCapsuleComponent()->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
	GetCharacterMovement()->bOrientRotationToMovement = true;
	GetCharacterMovement()->MaxWalkSpeed = MoveSpeed;
	GetCharacterMovement()->bRunPhysicsWithNoController = true;
	GetCharacterMovement()->DefaultLandMovementMode = MOVE_Walking;

	IsoMarker = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("IsoMarker"));
	IsoMarker->SetupAttachment(RootComponent);
	IsoMarker->SetRelativeLocation(FVector(0.f, 0.f, 40.f));
	IsoMarker->SetRelativeScale3D(FVector(1.1f, 1.1f, 2.0f));
	IsoMarker->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	IsoMarker->SetCollisionResponseToAllChannels(ECR_Ignore);
	IsoMarker->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
	static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeFinder(TEXT("/Engine/BasicShapes/Cube.Cube"));
	if (CubeFinder.Succeeded())
	{
		IsoMarker->SetStaticMesh(CubeFinder.Object);
	}

	NameLabel = CreateDefaultSubobject<UTextRenderComponent>(TEXT("NameLabel"));
	NameLabel->SetupAttachment(RootComponent);
	NameLabel->SetRelativeLocation(FVector(0.f, 0.f, 150.f));
	NameLabel->SetHorizontalAlignment(EHTA_Center);
	NameLabel->SetWorldSize(42.f);
	NameLabel->SetTextRenderColor(FColor(20, 18, 12));
}

void ALESkirmishUnit::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(ALESkirmishUnit, Team);
	DOREPLIFETIME(ALESkirmishUnit, UnitRole);
	DOREPLIFETIME(ALESkirmishUnit, Health);
	DOREPLIFETIME(ALESkirmishUnit, GoalLocation);
	DOREPLIFETIME(ALESkirmishUnit, AttackTarget);
}

void ALESkirmishUnit::BeginPlay()
{
	Super::BeginPlay();
	GetCharacterMovement()->MaxWalkSpeed = MoveSpeed;
	RefreshAppearance();
}

void ALESkirmishUnit::Configure(ELESkirmishTeam InTeam, ELESkirmishUnitRole InRole, FText InName)
{
	Team = InTeam;
	UnitRole = InRole;
	DisplayName = InName;
	Health = MaxHealth;
	if (UnitRole == ELESkirmishUnitRole::Bagman)
	{
		MaxHealth = 70;
		Health = 70;
		AttackDamage = 10;
		MoveSpeed = 540.f;
	}
	GetCharacterMovement()->MaxWalkSpeed = MoveSpeed;
	RefreshAppearance();
}

void ALESkirmishUnit::SetSelected(bool bInSelected)
{
	bSelected = bInSelected;
	RefreshAppearance();
}

void ALESkirmishUnit::CommandMoveTo(FVector WorldLocation)
{
	AttackTarget = nullptr;
	GoalLocation = FVector(WorldLocation.X, WorldLocation.Y, GetActorLocation().Z);
	bHasGoal = true;
}

void ALESkirmishUnit::CommandAttack(ALESkirmishUnit* Target)
{
	if (!Target || Target == this || !Target->IsAlive() || Target->Team == Team)
	{
		return;
	}
	AttackTarget = Target;
	bHasGoal = false;
}

void ALESkirmishUnit::ApplyDamageFrom(int32 Amount, ALESkirmishUnit* /*InstigatorUnit*/)
{
	if (!HasAuthority() || Health <= 0)
	{
		return;
	}
	Health = FMath::Max(0, Health - Amount);
	OnRep_Health();
	if (Health <= 0)
	{
		SetActorHiddenInGame(true);
		SetActorEnableCollision(false);
		SetActorTickEnabled(false);
	}
}

void ALESkirmishUnit::OnRep_Team()
{
	RefreshAppearance();
}

void ALESkirmishUnit::OnRep_Health()
{
	RefreshAppearance();
	if (Health <= 0)
	{
		SetActorHiddenInGame(true);
		SetActorEnableCollision(false);
	}
}

void ALESkirmishUnit::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	if (!IsAlive())
	{
		return;
	}
	if (HasAuthority())
	{
		TryAttack(DeltaSeconds);
		ChaseGoal(DeltaSeconds);
	}
}

void ALESkirmishUnit::ChaseGoal(float DeltaSeconds)
{
	FVector Dest = GoalLocation;
	if (AttackTarget && AttackTarget->IsAlive())
	{
		Dest = AttackTarget->GetActorLocation();
		bHasGoal = true;
	}
	else if (!bHasGoal)
	{
		return;
	}

	const FVector Loc = GetActorLocation();
	FVector Delta = Dest - Loc;
	Delta.Z = 0.f;
	const float Dist = Delta.Size();
	const float StopDist = (AttackTarget && AttackTarget->IsAlive()) ? AttackRange * 0.85f : 40.f;
	if (Dist <= StopDist)
	{
		if (!AttackTarget)
		{
			bHasGoal = false;
		}
		return;
	}

	const FVector Dir = Delta / Dist;
	const FVector Step = Dir * MoveSpeed * DeltaSeconds;
	SetActorLocation(Loc + Step, true);
	SetActorRotation(Dir.Rotation());
}

void ALESkirmishUnit::TryAttack(float DeltaSeconds)
{
	AttackTimer = FMath::Max(0.f, AttackTimer - DeltaSeconds);
	if (!AttackTarget || !AttackTarget->IsAlive())
	{
		AttackTarget = nullptr;
		return;
	}
	const float Dist = FVector::Dist2D(GetActorLocation(), AttackTarget->GetActorLocation());
	if (Dist > AttackRange)
	{
		return;
	}
	if (AttackTimer > 0.f)
	{
		return;
	}
	AttackTarget->ApplyDamageFrom(AttackDamage, this);
	AttackTimer = AttackCooldown;
}

void ALESkirmishUnit::RefreshAppearance()
{
	if (NameLabel)
	{
		const FString Label = DisplayName.IsEmpty()
			? (UnitRole == ELESkirmishUnitRole::Bagman ? TEXT("Bagman") : TEXT("Enforcer"))
			: DisplayName.ToString();
		NameLabel->SetText(FText::FromString(FString::Printf(TEXT("%s %d"), *Label, Health)));
		NameLabel->SetTextRenderColor(bSelected ? FColor(200, 50, 20) : FColor(20, 18, 12));
		NameLabel->SetWorldSize(bSelected ? 52.f : 42.f);
	}

	if (!IsoMarker)
	{
		return;
	}

	FLinearColor Color = Team == ELESkirmishTeam::Red
		? FLinearColor(0.85f, 0.16f, 0.12f)
		: FLinearColor(0.18f, 0.42f, 0.88f);
	if (!IsAlive())
	{
		Color = FLinearColor(0.2f, 0.2f, 0.2f);
	}
	if (bSelected)
	{
		Color *= 1.35f;
		IsoMarker->SetRelativeScale3D(FVector(1.4f, 1.4f, 2.4f));
	}
	else
	{
		IsoMarker->SetRelativeScale3D(FVector(1.1f, 1.1f, 2.0f));
	}

	if (UMaterialInstanceDynamic* Dyn = IsoMarker->CreateAndSetMaterialInstanceDynamic(0))
	{
		Dyn->SetVectorParameterValue(TEXT("Color"), Color);
		Dyn->SetVectorParameterValue(TEXT("BaseColor"), Color);
	}
}
