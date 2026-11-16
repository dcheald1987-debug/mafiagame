#include "LEStreetCar.h"

#include "LEHoodlumCharacter.h"
#include "Camera/PlayerCameraManager.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"

namespace
{
	static const float RoadAxes[] = { -2400.f, -1200.f, 0.f, 1200.f, 2400.f };

	void TintMesh(UStaticMeshComponent* Mesh, const FLinearColor& Color)
	{
		if (!Mesh)
		{
			return;
		}
		if (UMaterialInstanceDynamic* Mid = Mesh->CreateAndSetMaterialInstanceDynamic(0))
		{
			const FLinearColor Lit(FMath::Min(1.f, Color.R * 1.5f + 0.1f),
				FMath::Min(1.f, Color.G * 1.5f + 0.1f),
				FMath::Min(1.f, Color.B * 1.5f + 0.1f), 1.f);
			Mid->SetVectorParameterValue(TEXT("Color"), Lit);
			Mid->SetVectorParameterValue(TEXT("BaseColor"), Lit);
			Mid->SetVectorParameterValue(TEXT("EmissiveColor"), Color * 0.25f);
		}
	}

	void SetupWheel(UStaticMeshComponent* Wheel, USceneComponent* Attach, const FVector& Loc)
	{
		Wheel->SetupAttachment(Attach);
		Wheel->SetRelativeLocation(Loc);
		Wheel->SetRelativeRotation(FRotator(0.f, 0.f, 90.f));
		Wheel->SetRelativeScale3D(FVector(0.55f, 0.55f, 0.22f));
		Wheel->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Wheel->SetCastShadow(true);
	}
}

ALEStreetCar::ALEStreetCar()
{
	PrimaryActorTick.bCanEverTick = true;

	Body = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Body"));
	SetRootComponent(Body);
	Body->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
	Body->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
	Body->SetRelativeScale3D(FVector(2.6f, 1.15f, 0.55f));
	Body->SetCastShadow(true);

	Cabin = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Cabin"));
	Cabin->SetupAttachment(RootComponent);
	Cabin->SetRelativeLocation(FVector(-15.f, 0.f, 55.f));
	Cabin->SetRelativeScale3D(FVector(1.4f, 1.05f, 0.7f));
	Cabin->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Cabin->SetCastShadow(true);

	WheelFL = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("WheelFL"));
	WheelFR = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("WheelFR"));
	WheelRL = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("WheelRL"));
	WheelRR = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("WheelRR"));
	SetupWheel(WheelFL, RootComponent, FVector(70.f, -55.f, -25.f));
	SetupWheel(WheelFR, RootComponent, FVector(70.f, 55.f, -25.f));
	SetupWheel(WheelRL, RootComponent, FVector(-70.f, -55.f, -25.f));
	SetupWheel(WheelRR, RootComponent, FVector(-70.f, 55.f, -25.f));

	SpritePlane = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("SpritePlane"));
	SpritePlane->SetupAttachment(RootComponent);
	SpritePlane->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	SpritePlane->SetCastShadow(false);
	SpritePlane->SetHiddenInGame(true);
	SpritePlane->SetVisibility(false);

	VehicleMesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("VehicleMesh"));
	VehicleMesh->SetupAttachment(RootComponent);
	VehicleMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	VehicleMesh->SetCastShadow(true);
	VehicleMesh->SetRelativeScale3D(FVector(0.55f));
	VehicleMesh->SetRelativeLocation(FVector(0.f, 0.f, -40.f));

	static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeFinder(TEXT("/Engine/BasicShapes/Cube.Cube"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> CylinderFinder(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	static ConstructorHelpers::FObjectFinder<USkeletalMesh> VehicleFinder(
		TEXT("/ChaosModularVehicleExamples/Models/SportsCar/SKM_SportsCar.SKM_SportsCar"));
	if (CubeFinder.Succeeded())
	{
		Body->SetStaticMesh(CubeFinder.Object);
		Cabin->SetStaticMesh(CubeFinder.Object);
	}
	if (CylinderFinder.Succeeded())
	{
		WheelFL->SetStaticMesh(CylinderFinder.Object);
		WheelFR->SetStaticMesh(CylinderFinder.Object);
		WheelRL->SetStaticMesh(CylinderFinder.Object);
		WheelRR->SetStaticMesh(CylinderFinder.Object);
	}
	if (VehicleFinder.Succeeded() && VehicleMesh)
	{
		VehicleMesh->SetSkeletalMesh(VehicleFinder.Object);
	}

	Label = CreateDefaultSubobject<UTextRenderComponent>(TEXT("Label"));
	Label->SetupAttachment(RootComponent);
	Label->SetRelativeLocation(FVector(0.f, 0.f, 130.f));
	Label->SetHorizontalAlignment(EHTA_Center);
	Label->SetWorldSize(40.f);
	Label->SetTextRenderColor(FColor(25, 22, 18));
	DisplayName = FText::FromString(TEXT("Sedan"));
	Label->SetText(DisplayName);
}

void ALEStreetCar::BeginPlay()
{
	Super::BeginPlay();
	ApplyLoadedSprite();
	ApplyBodyColors();

	// Snap onto nearest avenue/street centerline
	FVector Loc = GetActorLocation();
	const float SnapX = SnapToRoadAxis(Loc.X);
	const float SnapY = SnapToRoadAxis(Loc.Y);
	const bool bCloserToAvenue = FMath::Abs(Loc.X - SnapX) <= FMath::Abs(Loc.Y - SnapY);
	if (bCloserToAvenue)
	{
		Loc.X = SnapX;
	}
	else
	{
		Loc.Y = SnapY;
	}
	Loc.Z = RoadZ;
	SetActorLocation(Loc);

	if (bFreeRoam)
	{
		PickNextRoamGoal();
	}
}

void ALEStreetCar::SetOccupant(ALEHoodlumCharacter* Hood)
{
	Occupant = Hood;
}

void ALEStreetCar::SetSpriteMaterialPath(const FString& SoftPath)
{
	SpriteMaterial = TSoftObjectPtr<UMaterialInterface>(FSoftObjectPath(SoftPath));
	ApplyLoadedSprite();
}

void ALEStreetCar::ApplyBodyColors()
{
	const FLinearColor Lacquer = BodyPaint;
	const FLinearColor CabinColor(0.12f, 0.12f, 0.14f);
	const FLinearColor Tire(0.02f, 0.02f, 0.02f);

	// Tint period colors onto the full-3D skeletal stand-in when present
	if (VehicleMesh && VehicleMesh->GetSkeletalMeshAsset())
	{
		const int32 NumMats = VehicleMesh->GetNumMaterials();
		for (int32 i = 0; i < NumMats; ++i)
		{
			if (UMaterialInstanceDynamic* Mid = VehicleMesh->CreateAndSetMaterialInstanceDynamic(i))
			{
				Mid->SetVectorParameterValue(TEXT("Color"), Lacquer);
				Mid->SetVectorParameterValue(TEXT("BaseColor"), Lacquer);
				Mid->SetVectorParameterValue(TEXT("PaintColor"), Lacquer);
			}
		}
	}

	TintMesh(Body, Lacquer);
	TintMesh(Cabin, CabinColor);
	TintMesh(WheelFL, Tire);
	TintMesh(WheelFR, Tire);
	TintMesh(WheelRL, Tire);
	TintMesh(WheelRR, Tire);
}

void ALEStreetCar::ApplyLoadedSprite()
{
	// Full-3D rule: never replace chassis with dark portrait plates
	bUsingSprite = false;
	if (SpritePlane)
	{
		SpritePlane->SetHiddenInGame(true);
		SpritePlane->SetVisibility(false);
		SpritePlane->SetStaticMesh(nullptr);
	}

	const bool bHasVehicle = VehicleMesh && VehicleMesh->GetSkeletalMeshAsset() != nullptr;
	if (VehicleMesh)
	{
		VehicleMesh->SetHiddenInGame(!bHasVehicle);
		VehicleMesh->SetVisibility(bHasVehicle);
		VehicleMesh->SetCastShadow(false);
	}
	// Always keep cube chassis visible as readable fallback (iso scale)
	if (Body)
	{
		Body->SetHiddenInGame(false);
		Body->SetVisibility(true);
		Body->SetCastShadow(false);
		if (bHasVehicle)
		{
			Body->SetRelativeScale3D(FVector(0.01f)); // hide under skeletal
			Body->SetHiddenInGame(true);
		}
		else
		{
			Body->SetRelativeScale3D(FVector(2.8f, 1.25f, 0.65f));
		}
	}
	if (Cabin)
	{
		Cabin->SetHiddenInGame(bHasVehicle);
		Cabin->SetVisibility(!bHasVehicle);
		Cabin->SetCastShadow(false);
	}
	const bool bShowWheels = !bHasVehicle;
	if (WheelFL) { WheelFL->SetHiddenInGame(!bShowWheels); WheelFL->SetCastShadow(false); }
	if (WheelFR) { WheelFR->SetHiddenInGame(!bShowWheels); WheelFR->SetCastShadow(false); }
	if (WheelRL) { WheelRL->SetHiddenInGame(!bShowWheels); WheelRL->SetCastShadow(false); }
	if (WheelRR) { WheelRR->SetHiddenInGame(!bShowWheels); WheelRR->SetCastShadow(false); }
}

void ALEStreetCar::FaceSpriteToCamera()
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
	// Screen-aligned to iso ortho camera so the card face is fully visible (not edge-on shadow)
	const FRotator CamRot = Cam->GetCameraRotation();
	SpritePlane->SetWorldRotation(FRotator(CamRot.Pitch, CamRot.Yaw, 0.f));
}

float ALEStreetCar::SnapToRoadAxis(float Value) const
{
	float Best = RoadAxes[0];
	float BestDist = FMath::Abs(Value - Best);
	for (float Axis : RoadAxes)
	{
		const float D = FMath::Abs(Value - Axis);
		if (D < BestDist)
		{
			BestDist = D;
			Best = Axis;
		}
	}
	return Best;
}

void ALEStreetCar::PickNextRoamGoal()
{
	FVector Loc = GetActorLocation();
	const float SnapX = SnapToRoadAxis(Loc.X);
	const float SnapY = SnapToRoadAxis(Loc.Y);
	const bool bOnAvenue = FMath::Abs(Loc.X - SnapX) <= FMath::Abs(Loc.Y - SnapY) + 1.f;

	// At an intersection: sometimes turn onto the crossing street
	const bool bAtIntersection = FMath::Abs(Loc.X - SnapX) < 80.f && FMath::Abs(Loc.Y - SnapY) < 80.f;
	bool bTravelNS = bOnAvenue; // avenue = fixed X, travel along Y
	if (bAtIntersection && FMath::RandBool())
	{
		bTravelNS = !bTravelNS;
	}

	const float DestAxis = RoadAxes[FMath::RandRange(0, UE_ARRAY_COUNT(RoadAxes) - 1)];
	if (bTravelNS)
	{
		RoamGoal = FVector(SnapX, DestAxis, RoadZ);
		Loc.X = SnapX;
	}
	else
	{
		RoamGoal = FVector(DestAxis, SnapY, RoadZ);
		Loc.Y = SnapY;
	}
	Loc.Z = RoadZ;
	SetActorLocation(Loc);
	bHasRoamGoal = true;
}

void ALEStreetCar::TickFreeRoam(float DeltaSeconds)
{
	if (!bHasRoamGoal)
	{
		PickNextRoamGoal();
		return;
	}

	FVector Loc = GetActorLocation();
	const FVector Delta = RoamGoal - Loc;
	const float Dist = Delta.Size2D();
	if (Dist < 40.f)
	{
		PickNextRoamGoal();
		return;
	}

	const FVector Dir = Delta.GetSafeNormal2D();
	const float Step = FMath::Min(Dist, CruiseSpeed * DeltaSeconds);
	Loc += Dir * Step;
	Loc.Z = RoadZ;
	// Keep locked to current road axis while traveling
	if (FMath::Abs(Dir.X) > FMath::Abs(Dir.Y))
	{
		Loc.Y = SnapToRoadAxis(Loc.Y);
	}
	else
	{
		Loc.X = SnapToRoadAxis(Loc.X);
	}
	SetActorLocation(Loc);
	if (!Dir.IsNearlyZero())
	{
		SetActorRotation(Dir.Rotation());
	}
}

void ALEStreetCar::BeginDrivePass(FVector From, FVector To, FVector /*LookAt*/)
{
	PassFrom = From;
	PassTo = To;
	PassAlpha = 0.f;
	bDriving = true;
	bPassComplete = false;
	bRoamPaused = true;
	bHasRoamGoal = false;
	SetActorLocation(FVector(From.X, From.Y, RoadZ));
}

void ALEStreetCar::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	if (Label && !DisplayName.IsEmpty())
	{
		Label->SetText(DisplayName);
		Label->SetRelativeLocation(FVector(0.f, 0.f, 130.f));
	}

	if (bUsingSprite)
	{
		FaceSpriteToCamera();
	}
	else
	{
		ApplyBodyColors();
	}

	if (bDriving)
	{
		PassAlpha += DeltaSeconds / PassDuration;
		if (PassAlpha >= 1.f)
		{
			PassAlpha = 1.f;
			bDriving = false;
			bPassComplete = true;
			bRoamPaused = false;
			if (bFreeRoam)
			{
				PickNextRoamGoal();
			}
		}

		const FVector Pos = FMath::Lerp(PassFrom, PassTo, PassAlpha);
		SetActorLocation(FVector(Pos.X, Pos.Y, RoadZ));
		const FVector Dir = (PassTo - PassFrom).GetSafeNormal2D();
		if (!Dir.IsNearlyZero())
		{
			SetActorRotation(Dir.Rotation());
		}
		return;
	}

	if (bFreeRoam && !bRoamPaused)
	{
		TickFreeRoam(DeltaSeconds);
	}
}
