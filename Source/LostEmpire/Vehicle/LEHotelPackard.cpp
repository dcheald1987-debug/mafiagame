#include "LEHotelPackard.h"

#include "LEPackardWheelFront.h"
#include "LEPackardWheelRear.h"
#include "LEServiceEntranceDirector.h"

#include "Camera/CameraComponent.h"
#include "ChaosWheeledVehicleMovementComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/SpringArmComponent.h"
#include "Kismet/GameplayStatics.h"
#include "UObject/ConstructorHelpers.h"

ALEHotelPackard::ALEHotelPackard(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
	GetMesh()->SetSimulatePhysics(true);
	GetMesh()->SetCollisionProfileName(TEXT("Vehicle"));
	GetMesh()->SetNotifyRigidBodyCollision(true);

	// Temporary body. Same Phys_Wheel_* bones Chaos expects. Replace when the Packard mesh exists.
	static ConstructorHelpers::FObjectFinder<USkeletalMesh> MeshFinder(
		TEXT("/ChaosModularVehicleExamples/Models/SportsCar/SKM_SportsCar.SKM_SportsCar"));
	if (MeshFinder.Succeeded())
	{
		GetMesh()->SetSkeletalMesh(MeshFinder.Object);
	}

	ChaosMovement = CastChecked<UChaosWheeledVehicleMovementComponent>(GetVehicleMovement());
	ChaosMovement->Mass = 1850.f;
	ChaosMovement->ChassisWidth = 180.f;
	ChaosMovement->ChassisHeight = 140.f;
	ChaosMovement->DragCoefficient = 0.55f;
	ChaosMovement->DownforceCoefficient = 0.1f;
	ChaosMovement->bLegacyWheelFrictionPosition = true;

	ChaosMovement->WheelSetups.SetNum(4);
	ChaosMovement->WheelSetups[0].WheelClass = ULEPackardWheelFront::StaticClass();
	ChaosMovement->WheelSetups[0].BoneName = FName(TEXT("Phys_Wheel_FL"));
	ChaosMovement->WheelSetups[1].WheelClass = ULEPackardWheelFront::StaticClass();
	ChaosMovement->WheelSetups[1].BoneName = FName(TEXT("Phys_Wheel_FR"));
	ChaosMovement->WheelSetups[2].WheelClass = ULEPackardWheelRear::StaticClass();
	ChaosMovement->WheelSetups[2].BoneName = FName(TEXT("Phys_Wheel_BL"));
	ChaosMovement->WheelSetups[3].WheelClass = ULEPackardWheelRear::StaticClass();
	ChaosMovement->WheelSetups[3].BoneName = FName(TEXT("Phys_Wheel_BR"));

	// Slow hotel car. Automatic only removes the clutch; it does not add power.
	ChaosMovement->EngineSetup.MaxTorque = 380.f;
	ChaosMovement->EngineSetup.MaxRPM = 3400.f;
	ChaosMovement->EngineSetup.EngineIdleRPM = 500.f;
	ChaosMovement->EngineSetup.EngineBrakeEffect = 0.35f;
	ChaosMovement->EngineSetup.EngineRevUpMOI = 4.0f;
	ChaosMovement->EngineSetup.EngineRevDownRate = 400.f;

	ChaosMovement->TransmissionSetup.bUseAutomaticGears = true;
	ChaosMovement->TransmissionSetup.bUseAutoReverse = true;
	ChaosMovement->TransmissionSetup.FinalRatio = 3.4f;
	ChaosMovement->TransmissionSetup.ChangeUpRPM = 2800.f;
	ChaosMovement->TransmissionSetup.ChangeDownRPM = 1200.f;
	ChaosMovement->TransmissionSetup.GearChangeTime = 0.35f;
	ChaosMovement->TransmissionSetup.TransmissionEfficiency = 0.85f;
	ChaosMovement->TransmissionSetup.ForwardGearRatios = { 3.6f, 1.9f, 1.0f };
	ChaosMovement->TransmissionSetup.ReverseGearRatios = { 3.8f };

	ChaosMovement->SteeringSetup.SteeringType = ESteeringType::Ackermann;
	ChaosMovement->SteeringSetup.AngleRatio = 0.65f;

	InteriorCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("InteriorCamera"));
	InteriorCamera->SetupAttachment(GetMesh());
	InteriorCamera->SetRelativeLocation(FVector(10.f, -30.f, 110.f));
	InteriorCamera->SetRelativeRotation(FRotator(-5.f, 0.f, 0.f));
	InteriorCamera->bAutoActivate = true;
	InteriorCamera->SetFieldOfView(75.f);

	ExteriorBoom = CreateDefaultSubobject<USpringArmComponent>(TEXT("ExteriorBoom"));
	ExteriorBoom->SetupAttachment(GetMesh());
	ExteriorBoom->TargetArmLength = 420.f;
	ExteriorBoom->SocketOffset = FVector(0.f, 0.f, 90.f);
	ExteriorBoom->bDoCollisionTest = false;
	ExteriorBoom->bInheritPitch = false;
	ExteriorBoom->bInheritRoll = false;
	ExteriorBoom->bEnableCameraRotationLag = true;
	ExteriorBoom->CameraRotationLagSpeed = 2.f;

	ExteriorCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("ExteriorCamera"));
	ExteriorCamera->SetupAttachment(ExteriorBoom);
	ExteriorCamera->bAutoActivate = false;
}

void ALEHotelPackard::BeginPlay()
{
	Super::BeginPlay();
	GetMesh()->OnComponentHit.AddDynamic(this, &ALEHotelPackard::HandleMeshHit);
}

void ALEHotelPackard::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);

	PlayerInputComponent->BindAxis(TEXT("MoveForward"), this, &ALEHotelPackard::MoveForward);
	PlayerInputComponent->BindAxis(TEXT("MoveRight"), this, &ALEHotelPackard::MoveRight);
	PlayerInputComponent->BindAction(TEXT("Handbrake"), IE_Pressed, this, &ALEHotelPackard::OnHandbrakePressed);
	PlayerInputComponent->BindAction(TEXT("Handbrake"), IE_Released, this, &ALEHotelPackard::OnHandbrakeReleased);
	PlayerInputComponent->BindAction(TEXT("ToggleCamera"), IE_Pressed, this, &ALEHotelPackard::ToggleCamera);
	PlayerInputComponent->BindAction(TEXT("LeaveVehicle"), IE_Pressed, this, &ALEHotelPackard::LeaveVehicle);
}

void ALEHotelPackard::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	if (!ChaosMovement || bReportedTerminal)
	{
		return;
	}

	GetMesh()->SetAngularDamping(ChaosMovement->IsMovingOnGround() ? 0.f : 3.f);

	const float UpDot = FVector::DotProduct(GetMesh()->GetUpVector(), FVector::UpVector);
	if (UpDot < -0.2f)
	{
		UpsideDownSeconds += DeltaSeconds;
		if (UpsideDownSeconds >= FlipFailSeconds)
		{
			ReportWreck();
		}
	}
	else
	{
		UpsideDownSeconds = 0.f;
	}
}

void ALEHotelPackard::MoveForward(float Value)
{
	if (!ChaosMovement || bReportedTerminal)
	{
		return;
	}

	ChaosMovement->SetThrottleInput(FMath::Max(Value, 0.f));
	ChaosMovement->SetBrakeInput(Value < 0.f ? -Value : 0.f);
}

void ALEHotelPackard::MoveRight(float Value)
{
	if (ChaosMovement && !bReportedTerminal)
	{
		ChaosMovement->SetSteeringInput(Value);
	}
}

void ALEHotelPackard::OnHandbrakePressed()
{
	if (ChaosMovement && !bReportedTerminal)
	{
		ChaosMovement->SetHandbrakeInput(true);
	}
}

void ALEHotelPackard::OnHandbrakeReleased()
{
	if (ChaosMovement)
	{
		ChaosMovement->SetHandbrakeInput(false);
	}
}

void ALEHotelPackard::ToggleCamera()
{
	bInteriorCameraActive = !bInteriorCameraActive;
	InteriorCamera->SetActive(bInteriorCameraActive);
	ExteriorCamera->SetActive(!bInteriorCameraActive);
}

void ALEHotelPackard::LeaveVehicle()
{
	ReportAbandoned();
}

void ALEHotelPackard::HandleMeshHit(
	UPrimitiveComponent* HitComponent,
	AActor* OtherActor,
	UPrimitiveComponent* OtherComp,
	FVector NormalImpulse,
	const FHitResult& Hit)
{
	if (bReportedTerminal || OtherActor == this)
	{
		return;
	}

	if (NormalImpulse.Size() >= WreckImpulseThreshold)
	{
		ReportWreck();
	}
}

void ALEHotelPackard::ReportWreck()
{
	if (bReportedTerminal)
	{
		return;
	}

	bReportedTerminal = true;
	if (ChaosMovement)
	{
		ChaosMovement->SetThrottleInput(0.f);
		ChaosMovement->SetSteeringInput(0.f);
		ChaosMovement->SetBrakeInput(1.f);
		ChaosMovement->SetHandbrakeInput(true);
	}

	if (ALEServiceEntranceDirector* Director = FindDirector())
	{
		Director->NotifyVehicleWrecked();
	}
}

void ALEHotelPackard::ReportAbandoned()
{
	if (bReportedTerminal)
	{
		return;
	}

	bReportedTerminal = true;
	if (ChaosMovement)
	{
		ChaosMovement->SetThrottleInput(0.f);
		ChaosMovement->SetSteeringInput(0.f);
		ChaosMovement->SetBrakeInput(1.f);
		ChaosMovement->SetHandbrakeInput(true);
	}

	if (ALEServiceEntranceDirector* Director = FindDirector())
	{
		Director->NotifyPlayerLeftVehicle();
	}
}

ALEServiceEntranceDirector* ALEHotelPackard::FindDirector() const
{
	return Cast<ALEServiceEntranceDirector>(
		UGameplayStatics::GetActorOfClass(GetWorld(), ALEServiceEntranceDirector::StaticClass()));
}
