#include "LECityCameraPawn.h"

#include "Camera/CameraComponent.h"
#include "GameFramework/SpringArmComponent.h"

ALECityCameraPawn::ALECityCameraPawn()
{
	PrimaryActorTick.bCanEverTick = true;

	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));

	// Gangsters-style fixed isometric: ~45 yaw, steep pitch, orthographic read of the grid.
	Boom = CreateDefaultSubobject<USpringArmComponent>(TEXT("Boom"));
	Boom->SetupAttachment(RootComponent);
	Boom->TargetArmLength = 0.f;
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
	Camera->SetOrthoWidth(4200.f);
	Camera->bConstrainAspectRatio = false;
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

	// Pan along the isometric ground axes (screen-aligned to the fixed -45 yaw).
	const FRotator IsoYaw(0.f, -45.f, 0.f);
	const FVector Forward = FRotationMatrix(IsoYaw).GetUnitAxis(EAxis::X);
	const FVector Right = FRotationMatrix(IsoYaw).GetUnitAxis(EAxis::Y);
	const FVector Delta = (Forward * ForwardAxis + Right * RightAxis) * PanSpeed * DeltaSeconds;
	AddActorWorldOffset(FVector(Delta.X, Delta.Y, 0.f), false);
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
