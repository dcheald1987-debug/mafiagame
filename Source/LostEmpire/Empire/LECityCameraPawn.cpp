#include "LECityCameraPawn.h"

#include "Camera/CameraComponent.h"
#include "GameFramework/SpringArmComponent.h"
#include "GameFramework/WorldSettings.h"

ALECityCameraPawn::ALECityCameraPawn()
{
	PrimaryActorTick.bCanEverTick = true;

	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));

	// Gangsters-style fixed isometric: ~45 yaw, steep pitch, orthographic read of the grid.
	Boom = CreateDefaultSubobject<USpringArmComponent>(TEXT("Boom"));
	Boom->SetupAttachment(RootComponent);
	// Pull camera back along the iso boom so near-clip cannot slice the grid.
	Boom->TargetArmLength = 4500.f;
	Boom->bDoCollisionTest = false;
	Boom->bEnableCameraLag = false;
	Boom->bInheritPitch = false;
	Boom->bInheritYaw = false;
	Boom->bInheritRoll = false;
	Boom->SetUsingAbsoluteRotation(true);
	Boom->SetWorldRotation(FRotator(-50.f, -45.f, 0.f));

	Camera = CreateDefaultSubobject<UCameraComponent>(TEXT("Camera"));
	Camera->SetupAttachment(Boom);
	Camera->SetProjectionMode(ECameraProjectionMode::Orthographic);
	Camera->SetOrthoWidth(4800.f);
	Camera->bConstrainAspectRatio = false;
	// Camera sits on a long boom — keep near/far wide so clip never wedges the grid.
	Camera->SetOrthoNearClipPlane(-100.f);
	Camera->SetOrthoFarClipPlane(100000.f);
	// Force readable exposure even if world PP / eye-adapt is broken
	Camera->PostProcessSettings.bOverride_AutoExposureMethod = true;
	Camera->PostProcessSettings.AutoExposureMethod = EAutoExposureMethod::AEM_Manual;
	Camera->PostProcessSettings.bOverride_AutoExposureBias = true;
	Camera->PostProcessSettings.AutoExposureBias = 5.5f;
	Camera->PostProcessBlendWeight = 1.f;
}

void ALECityCameraPawn::BeginPlay()
{
	Super::BeginPlay();
	// Center over the Levee greybox crossroads.
	SetActorLocation(FVector(0.f, 0.f, 50.f));
	if (Camera)
	{
		Camera->SetProjectionMode(ECameraProjectionMode::Orthographic);
		Camera->SetOrthoWidth(4800.f);
		Camera->SetOrthoNearClipPlane(-100.f);
		Camera->SetOrthoFarClipPlane(100000.f);
		Camera->PostProcessSettings.bOverride_AutoExposureMethod = true;
		Camera->PostProcessSettings.AutoExposureMethod = EAutoExposureMethod::AEM_Manual;
		Camera->PostProcessSettings.bOverride_AutoExposureBias = true;
		Camera->PostProcessSettings.AutoExposureBias = 6.5f;
		// Soft day sky so anything past the ground isn't a black wedge
		Camera->PostProcessSettings.bOverride_SceneColorTint = true;
		Camera->PostProcessSettings.SceneColorTint = FLinearColor(1.1f, 1.05f, 0.98f);
		Camera->PostProcessBlendWeight = 1.f;
	}
	if (UWorld* World = GetWorld())
	{
		if (AWorldSettings* WS = World->GetWorldSettings())
		{
			WS->bEnableWorldBoundsChecks = false;
		}
	}
}

void ALECityCameraPawn::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);
	PlayerInputComponent->BindAxis(TEXT("MoveForward"), this, &ALECityCameraPawn::MoveForward);
	PlayerInputComponent->BindAxis(TEXT("MoveRight"), this, &ALECityCameraPawn::MoveRight);
	PlayerInputComponent->BindAxis(TEXT("CameraZoom"), this, &ALECityCameraPawn::Zoom);
}

void ALECityCameraPawn::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	if (FMath::IsNearlyZero(ForwardAxis) && FMath::IsNearlyZero(RightAxis))
	{
		return;
	}

	// Pan along the isometric ground axes; speed scales with zoom so the map stays readable.
	const float ZoomFactor = Camera ? FMath::Clamp(Camera->OrthoWidth / 4200.f, 0.55f, 1.8f) : 1.f;
	const FRotator IsoYaw(0.f, -45.f, 0.f);
	const FVector Forward = FRotationMatrix(IsoYaw).GetUnitAxis(EAxis::X);
	const FVector Right = FRotationMatrix(IsoYaw).GetUnitAxis(EAxis::Y);
	const FVector Delta = (Forward * ForwardAxis + Right * RightAxis) * PanSpeed * ZoomFactor * DeltaSeconds;

	FVector Next = GetActorLocation() + FVector(Delta.X, Delta.Y, 0.f);
	Next.X = FMath::Clamp(Next.X, BoundsMin.X, BoundsMax.X);
	Next.Y = FMath::Clamp(Next.Y, BoundsMin.Y, BoundsMax.Y);
	Next.Z = 50.f;
	SetActorLocation(Next, false);
}

void ALECityCameraPawn::MoveForward(float Value)
{
	ForwardAxis = Value;
}

void ALECityCameraPawn::MoveRight(float Value)
{
	RightAxis = Value;
}

void ALECityCameraPawn::Zoom(float Value)
{
	if (FMath::IsNearlyZero(Value) || !Camera)
	{
		return;
	}

	const float Next = FMath::Clamp(Camera->OrthoWidth - Value * ZoomSpeed, MinArmLength, MaxArmLength);
	Camera->SetOrthoWidth(Next);
}
