#include "LECivilianCharacter.h"

#include "GameFramework/CharacterMovementComponent.h"

namespace
{
	struct FCivPalette
	{
		FLinearColor Coat;
		FLinearColor Legs;
		FLinearColor Hat;
	};

	static void PickRandomPalette(FLinearColor& OutCoat, FLinearColor& OutLegs, FLinearColor& OutHat)
	{
		static const FCivPalette Palettes[] = {
			{ FLinearColor(0.62f, 0.55f, 0.42f), FLinearColor(0.38f, 0.34f, 0.30f), FLinearColor(0.22f, 0.18f, 0.14f) }, // tan coat
			{ FLinearColor(0.28f, 0.30f, 0.36f), FLinearColor(0.20f, 0.20f, 0.24f), FLinearColor(0.10f, 0.10f, 0.12f) }, // grey suit
			{ FLinearColor(0.18f, 0.22f, 0.40f), FLinearColor(0.16f, 0.18f, 0.28f), FLinearColor(0.08f, 0.08f, 0.10f) }, // navy
			{ FLinearColor(0.42f, 0.18f, 0.16f), FLinearColor(0.28f, 0.16f, 0.14f), FLinearColor(0.14f, 0.06f, 0.05f) }, // burgundy
			{ FLinearColor(0.55f, 0.48f, 0.38f), FLinearColor(0.72f, 0.68f, 0.58f), FLinearColor(0.35f, 0.28f, 0.18f) }, // cream dress
			{ FLinearColor(0.22f, 0.28f, 0.22f), FLinearColor(0.18f, 0.20f, 0.16f), FLinearColor(0.12f, 0.14f, 0.10f) }, // olive work
			{ FLinearColor(0.70f, 0.58f, 0.48f), FLinearColor(0.40f, 0.32f, 0.28f), FLinearColor(0.55f, 0.40f, 0.25f) }, // peach / straw hat
			{ FLinearColor(0.35f, 0.35f, 0.32f), FLinearColor(0.25f, 0.24f, 0.22f), FLinearColor(0.08f, 0.08f, 0.08f) }, // charcoal
			{ FLinearColor(0.48f, 0.22f, 0.28f), FLinearColor(0.30f, 0.18f, 0.20f), FLinearColor(0.20f, 0.10f, 0.12f) }, // rose coat
			{ FLinearColor(0.25f, 0.35f, 0.42f), FLinearColor(0.20f, 0.24f, 0.28f), FLinearColor(0.12f, 0.14f, 0.16f) }, // steel blue
		};
		const int32 Idx = FMath::RandRange(0, UE_ARRAY_COUNT(Palettes) - 1);
		OutCoat = Palettes[Idx].Coat;
		OutLegs = Palettes[Idx].Legs;
		OutHat = Palettes[Idx].Hat;
		// Slight per-person jitter so the crowd isn't clone-stamped
		const float J = FMath::FRandRange(-0.04f, 0.06f);
		OutCoat.R = FMath::Clamp(OutCoat.R + J, 0.05f, 1.f);
		OutCoat.G = FMath::Clamp(OutCoat.G + J * 0.8f, 0.05f, 1.f);
		OutCoat.B = FMath::Clamp(OutCoat.B + J * 0.6f, 0.05f, 1.f);
	}
}

ALECivilianCharacter::ALECivilianCharacter()
{
	Faction = ELEOwner::Neutral;
	MoveSpeed = 320.f;
	WanderRadius = 1100.f;
}

void ALECivilianCharacter::BeginPlay()
{
	Super::BeginPlay();
	HomeLocation = GetActorLocation();
	if (DisplayName.IsEmpty())
	{
		static const TCHAR* Names[] = {
			TEXT("Passerby"), TEXT("Shop girl"), TEXT("Dock hand"), TEXT("Clerk"),
			TEXT("Widow"), TEXT("Newsie"), TEXT("Porter"), TEXT("Nurse"),
			TEXT("Delivery boy"), TEXT("Bookkeeper"), TEXT("Seamstress"), TEXT("Cabbie"),
			TEXT("Barfly"), TEXT("Church lady"), TEXT("Stevedore"), TEXT("Typist")
		};
		DisplayName = FText::FromString(Names[FMath::RandRange(0, UE_ARRAY_COUNT(Names) - 1)]);
	}

	bUseCustomPalette = true;
	PickRandomPalette(CoatTint, LegsTint, HatTint);
	MoveSpeed = FMath::FRandRange(280.f, 400.f);
	GetCharacterMovement()->MaxWalkSpeed = MoveSpeed;
	WanderRadius = FMath::FRandRange(700.f, 1400.f);

	// Keep lit 3D mannequins — portrait plates read as dark ortho blobs
	RefreshAppearance();
	PickWanderGoal();
}

void ALECivilianCharacter::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	if (PanicTimer > 0.f)
	{
		PanicTimer -= DeltaSeconds;
		if (PanicTimer <= 0.f)
		{
			bFleeing = false;
			PickWanderGoal();
		}
		return;
	}

	WanderTimer -= DeltaSeconds;
	if (!bHasGoal || WanderTimer <= 0.f)
	{
		PickWanderGoal();
	}
}

void ALECivilianCharacter::PanicFlee(FVector FromLocation)
{
	bFleeing = true;
	PanicTimer = 6.f;
	MoveSpeed = 520.f;
	GetCharacterMovement()->MaxWalkSpeed = MoveSpeed;
	const FVector Away = (GetActorLocation() - FromLocation).GetSafeNormal2D() * 1200.f + GetActorLocation();
	CommandMoveTo(Away + FVector(FMath::FRandRange(-200.f, 200.f), FMath::FRandRange(-200.f, 200.f), 0.f));
}

void ALECivilianCharacter::PickWanderGoal()
{
	WanderTimer = FMath::FRandRange(2.0f, 5.5f);
	const FVector Offset(
		FMath::FRandRange(-WanderRadius, WanderRadius),
		FMath::FRandRange(-WanderRadius, WanderRadius),
		0.f);
	FVector Dest = HomeLocation + Offset;
	Dest.Z = 110.f;
	CommandMoveTo(Dest);
}
