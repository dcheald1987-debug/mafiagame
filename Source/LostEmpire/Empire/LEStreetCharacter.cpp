#include "LEStreetCharacter.h"

#include "Camera/PlayerCameraManager.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Engine/StaticMesh.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"

namespace
{
	UMaterialInterface* StreetSolidMat()
	{
		static UMaterialInterface* Cached = nullptr;
		if (!Cached)
		{
			Cached = LoadObject<UMaterialInterface>(nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
		}
		return Cached;
	}

	void TintMesh(UStaticMeshComponent* Mesh, const FLinearColor& Color)
	{
		if (!Mesh)
		{
			return;
		}
		UMaterialInterface* Base = StreetSolidMat();
		UMaterialInstanceDynamic* Mid = Base
			? UMaterialInstanceDynamic::Create(Base, Mesh)
			: Mesh->CreateAndSetMaterialInstanceDynamic(0);
		if (!Mid)
		{
			return;
		}
		const FLinearColor Lit(
			FMath::Clamp(Color.R, 0.f, 1.f),
			FMath::Clamp(Color.G, 0.f, 1.f),
			FMath::Clamp(Color.B, 0.f, 1.f),
			1.f);
		// BasicShapeMaterial exposes "Color"; also hit common PBR aliases
		Mid->SetVectorParameterValue(TEXT("Color"), Lit);
		Mid->SetVectorParameterValue(TEXT("BaseColor"), Lit);
		Mid->SetVectorParameterValue(TEXT("DiffuseColor"), Lit);
		Mid->SetVectorParameterValue(TEXT("Tint"), Lit);
		Mesh->SetMaterial(0, Mid);
		Mesh->SetHiddenInGame(false);
		Mesh->SetVisibility(true);
		Mesh->SetCastShadow(false);
		Mesh->SetRenderCustomDepth(true);
	}

	void HideSpriteCard(UStaticMeshComponent* SpritePlane)
	{
		if (!SpritePlane)
		{
			return;
		}
		SpritePlane->SetHiddenInGame(true);
		SpritePlane->SetVisibility(false);
		SpritePlane->SetStaticMesh(nullptr);
	}
}

ALEStreetCharacter::ALEStreetCharacter()
{
	PrimaryActorTick.bCanEverTick = true;
	bUseControllerRotationYaw = false;
	AutoPossessAI = EAutoPossessAI::Disabled;

	// Larger capsule so iso picks + curb collision feel solid
	GetCapsuleComponent()->InitCapsuleSize(42.f, 96.f);
	GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
	GetCapsuleComponent()->SetCollisionObjectType(ECC_Pawn);
	GetCapsuleComponent()->SetCollisionResponseToAllChannels(ECR_Block);
	GetCapsuleComponent()->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
	GetCapsuleComponent()->SetCollisionResponseToChannel(ECC_Camera, ECR_Ignore);
	GetCapsuleComponent()->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);

	GetCharacterMovement()->bOrientRotationToMovement = true;
	GetCharacterMovement()->RotationRate = FRotator(0.f, 720.f, 0.f);
	GetCharacterMovement()->MaxWalkSpeed = MoveSpeed;
	GetCharacterMovement()->MaxAcceleration = 2400.f;
	GetCharacterMovement()->BrakingDecelerationWalking = 2800.f;
	GetCharacterMovement()->bRunPhysicsWithNoController = true;
	// Iso street pawns slide on curb plane — gravity drops them through road cubes
	GetCharacterMovement()->GravityScale = 0.f;
	GetCharacterMovement()->SetMovementMode(MOVE_Flying);
	GetCharacterMovement()->DefaultLandMovementMode = MOVE_Flying;
	GetCharacterMovement()->MaxFlySpeed = MoveSpeed;
	GetCharacterMovement()->BrakingDecelerationFlying = 2800.f;

	if (USkeletalMeshComponent* Skel = GetMesh())
	{
		Skel->SetHiddenInGame(true);
		Skel->SetVisibility(false);
		Skel->SetCastShadow(false);
	}

	// Legs — slightly oversized for ortho readability
	BodyMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("BodyMesh"));
	BodyMesh->SetupAttachment(RootComponent);
	BodyMesh->SetRelativeLocation(FVector(0.f, 0.f, -40.f));
	BodyMesh->SetRelativeScale3D(FVector(0.48f, 0.42f, 0.85f));
	BodyMesh->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	BodyMesh->SetCollisionResponseToAllChannels(ECR_Ignore);
	BodyMesh->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
	BodyMesh->SetCastShadow(false);

	CoatMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("CoatMesh"));
	CoatMesh->SetupAttachment(RootComponent);
	CoatMesh->SetRelativeLocation(FVector(0.f, 0.f, 18.f));
	CoatMesh->SetRelativeScale3D(FVector(0.68f, 0.58f, 0.85f));
	CoatMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	CoatMesh->SetCastShadow(false);

	HeadMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("HeadMesh"));
	HeadMesh->SetupAttachment(RootComponent);
	HeadMesh->SetRelativeLocation(FVector(0.f, 0.f, 78.f));
	HeadMesh->SetRelativeScale3D(FVector(0.46f, 0.46f, 0.46f));
	HeadMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	HeadMesh->SetCastShadow(false);

	HatMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("HatMesh"));
	HatMesh->SetupAttachment(RootComponent);
	HatMesh->SetRelativeLocation(FVector(0.f, 0.f, 102.f));
	HatMesh->SetRelativeScale3D(FVector(0.72f, 0.72f, 0.18f));
	HatMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	HatMesh->SetCastShadow(false);

	// Portrait cards stay off — full 3D mannequin only (no ortho wedges / dark plates)
	SpritePlane = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("SpritePlane"));
	SpritePlane->SetupAttachment(RootComponent);
	SpritePlane->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	SpritePlane->SetCastShadow(false);
	SpritePlane->SetHiddenInGame(true);
	SpritePlane->SetVisibility(false);

	static ConstructorHelpers::FObjectFinder<UStaticMesh> CylinderFinder(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> SphereFinder(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	if (CylinderFinder.Succeeded())
	{
		BodyMesh->SetStaticMesh(CylinderFinder.Object);
		CoatMesh->SetStaticMesh(CylinderFinder.Object);
		HatMesh->SetStaticMesh(CylinderFinder.Object);
	}
	if (SphereFinder.Succeeded())
	{
		HeadMesh->SetStaticMesh(SphereFinder.Object);
	}
	// Do NOT assign Plane mesh to SpritePlane — ortho wedges

	NameLabel = CreateDefaultSubobject<UTextRenderComponent>(TEXT("NameLabel"));
	NameLabel->SetupAttachment(RootComponent);
	NameLabel->SetRelativeLocation(FVector(0.f, 0.f, 175.f));
	NameLabel->SetHorizontalAlignment(EHTA_Center);
	NameLabel->SetWorldSize(42.f);
	NameLabel->SetTextRenderColor(FColor(20, 18, 12));
}

void ALEStreetCharacter::BeginPlay()
{
	Super::BeginPlay();
	if (UCharacterMovementComponent* Move = GetCharacterMovement())
	{
		Move->MaxWalkSpeed = MoveSpeed;
		Move->MaxFlySpeed = MoveSpeed;
		Move->GravityScale = 0.f;
		Move->SetMovementMode(MOVE_Flying);
	}
	// Pin to curb height so pawns never sink into asphalt / void
	FVector Loc = GetActorLocation();
	Loc.Z = 110.f;
	SetActorLocation(Loc);
	ApplyLoadedSprite();
	RefreshAppearance();
}

void ALEStreetCharacter::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	// Keep every street pawn on the curb plane (civilians wander, hoods order)
	FVector Loc = GetActorLocation();
	if (!FMath::IsNearlyEqual(Loc.Z, 110.f, 1.f))
	{
		Loc.Z = 110.f;
		SetActorLocation(Loc, false);
	}
	const bool bMoving = bHasGoal;
	StepTowardGoal(DeltaSeconds);
	UpdateWalkPose(DeltaSeconds, bMoving);
}

void ALEStreetCharacter::SetSelected(bool bInSelected)
{
	bSelected = bInSelected;
	RefreshAppearance();
}

void ALEStreetCharacter::CommandMoveTo(FVector WorldLocation)
{
	GoalLocation = FVector(WorldLocation.X, WorldLocation.Y, GetActorLocation().Z);
	bHasGoal = true;
	bFleeing = false;
}

void ALEStreetCharacter::ClearGoal()
{
	bHasGoal = false;
}

void ALEStreetCharacter::StepTowardGoal(float DeltaSeconds)
{
	if (!bHasGoal)
	{
		return;
	}

	const FVector Loc = GetActorLocation();
	FVector Delta = GoalLocation - Loc;
	Delta.Z = 0.f;
	const float Dist = Delta.Size();
	if (Dist <= 55.f)
	{
		bHasGoal = false;
		if (UCharacterMovementComponent* Move = GetCharacterMovement())
		{
			Move->StopMovementImmediately();
		}
		return;
	}

	const FVector Dir = Delta / Dist;
	const float Speed = (bFleeing ? MoveSpeed * 1.45f : MoveSpeed);
	FVector Next = Loc + Dir * Speed * DeltaSeconds;
	Next.Z = 110.f; // lock curb plane
	SetActorLocation(Next, false);
	const FRotator Desired = Dir.Rotation();
	SetActorRotation(FMath::RInterpTo(GetActorRotation(), Desired, DeltaSeconds, 12.f));
}

void ALEStreetCharacter::SetSpriteMaterialPath(const FString& SoftPath)
{
	SpriteMaterial = TSoftObjectPtr<UMaterialInterface>(FSoftObjectPath(SoftPath));
	ApplyLoadedSprite();
	RefreshAppearance();
}

void ALEStreetCharacter::ApplyLoadedSprite()
{
	// Full-3D rule: never replace mannequin with portrait cards (dark ortho plates).
	bUsingSprite = false;
	HideSpriteCard(SpritePlane);
	if (BodyMesh) { BodyMesh->SetHiddenInGame(false); BodyMesh->SetVisibility(true); }
	if (CoatMesh) { CoatMesh->SetHiddenInGame(false); CoatMesh->SetVisibility(true); }
	if (HeadMesh) { HeadMesh->SetHiddenInGame(false); HeadMesh->SetVisibility(true); }
	if (HatMesh) { HatMesh->SetHiddenInGame(false); HatMesh->SetVisibility(true); }
}

void ALEStreetCharacter::FacePortraitToCamera()
{
	if (!bUsingSprite || !SpritePlane || !GetWorld())
	{
		return;
	}
	APlayerCameraManager* Cam = UGameplayStatics::GetPlayerCameraManager(GetWorld(), 0);
	if (!Cam)
	{
		return;
	}
	// Match iso ortho camera so portraits read full-face, not edge-on shadows
	const FRotator CamRot = Cam->GetCameraRotation();
	SpritePlane->SetWorldRotation(FRotator(CamRot.Pitch, CamRot.Yaw, 0.f));
}

void ALEStreetCharacter::UpdateWalkPose(float DeltaSeconds, bool bMoving)
{
	// Goal-driven move uses SetActorLocation — bob from bHasGoal, not velocity
	const bool bReallyMoving = bMoving && bHasGoal;
	if (bReallyMoving)
	{
		WalkPhase += DeltaSeconds * 14.f;
	}
	else
	{
		WalkPhase = FMath::FInterpTo(WalkPhase, 0.f, DeltaSeconds, 10.f);
	}

	const float Bob = bReallyMoving ? FMath::Sin(WalkPhase) * 12.f : 0.f;
	const float Sway = bReallyMoving ? FMath::Sin(WalkPhase * 0.5f) * 9.f : 0.f;
	const float Stride = bReallyMoving ? FMath::Sin(WalkPhase) * 8.f : 0.f;
	if (BodyMesh)
	{
		BodyMesh->SetRelativeLocation(FVector(Stride * 0.3f, 0.f, -40.f + Bob));
		BodyMesh->SetRelativeRotation(FRotator(0.f, 0.f, Sway));
	}
	if (CoatMesh)
	{
		CoatMesh->SetRelativeLocation(FVector(0.f, 0.f, 18.f + Bob * 0.55f));
		CoatMesh->SetRelativeRotation(FRotator(0.f, 0.f, -Sway * 0.7f));
	}
	if (HeadMesh)
	{
		HeadMesh->SetRelativeLocation(FVector(0.f, 0.f, 78.f + Bob * 0.35f));
	}
	if (HatMesh)
	{
		HatMesh->SetRelativeLocation(FVector(0.f, 0.f, 102.f + Bob * 0.35f));
	}
}

void ALEStreetCharacter::RefreshAppearance()
{
	// Legs slightly lifted vs coat so thighs stay readable under moon/sun
	FLinearColor Coat(0.55f, 0.55f, 0.52f);
	FLinearColor Legs(0.42f, 0.39f, 0.36f);
	FLinearColor Skin(0.78f, 0.62f, 0.48f);
	FLinearColor Hat(0.12f, 0.1f, 0.09f);
	if (bUseCustomPalette)
	{
		Coat = CoatTint;
		Legs = LegsTint;
		Hat = HatTint;
	}
	else if (Faction == ELEOwner::Player)
	{
		// Bright navy — readable at iso distance
		Coat = FLinearColor(0.28f, 0.48f, 0.92f);
		Legs = FLinearColor(0.35f, 0.40f, 0.55f);
		Hat = FLinearColor(0.18f, 0.18f, 0.22f);
		Skin = FLinearColor(0.92f, 0.74f, 0.58f);
	}
	else if (Faction == ELEOwner::Rival)
	{
		Coat = FLinearColor(0.82f, 0.22f, 0.18f);
		Legs = FLinearColor(0.48f, 0.24f, 0.20f);
		Hat = FLinearColor(0.28f, 0.08f, 0.08f);
		Skin = FLinearColor(0.90f, 0.72f, 0.56f);
	}
	else
	{
		Coat = FLinearColor(0.78f, 0.68f, 0.52f);
		Legs = FLinearColor(0.55f, 0.48f, 0.40f);
		Hat = FLinearColor(0.42f, 0.34f, 0.24f);
		Skin = FLinearColor(0.90f, 0.72f, 0.56f);
	}

	if (bSelected)
	{
		Coat *= 1.45f;
		Legs *= 1.25f;
		BodyMesh->SetRelativeScale3D(FVector(0.70f, 0.58f, 1.15f));
		CoatMesh->SetRelativeScale3D(FVector(0.95f, 0.78f, 1.15f));
		HeadMesh->SetRelativeScale3D(FVector(0.58f, 0.58f, 0.58f));
		HatMesh->SetRelativeScale3D(FVector(0.88f, 0.88f, 0.22f));
	}
	else
	{
		BodyMesh->SetRelativeScale3D(FVector(0.60f, 0.52f, 1.05f));
		CoatMesh->SetRelativeScale3D(FVector(0.82f, 0.70f, 1.05f));
		HeadMesh->SetRelativeScale3D(FVector(0.52f, 0.52f, 0.52f));
		HatMesh->SetRelativeScale3D(FVector(0.78f, 0.78f, 0.20f));
	}

	TintMesh(BodyMesh, Legs);
	TintMesh(CoatMesh, Coat);
	TintMesh(HeadMesh, Skin);
	TintMesh(HatMesh, Hat);
	HideSpriteCard(SpritePlane);

	if (NameLabel)
	{
		NameLabel->SetText(DisplayName.IsEmpty() ? FText::FromString(TEXT("?")) : DisplayName);
		NameLabel->SetTextRenderColor(bSelected ? FColor(200, 50, 30) : FColor(28, 24, 18));
		NameLabel->SetWorldSize(bSelected ? 52.f : 42.f);
		NameLabel->SetRelativeLocation(FVector(0.f, 0.f, 175.f));
	}
}
