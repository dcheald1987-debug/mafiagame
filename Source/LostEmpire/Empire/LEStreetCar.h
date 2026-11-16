#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LEStreetCar.generated.h"

class ALEHoodlumCharacter;
class UStaticMeshComponent;
class USkeletalMeshComponent;
class USkeletalMesh;
class UTextRenderComponent;
class UMaterialInterface;

/** Full-3D street car — free-roams the avenue/street grid; scripted drive-by overrides. */
UCLASS()
class LOSTEMPIRE_API ALEStreetCar : public AActor
{
	GENERATED_BODY()

public:
	ALEStreetCar();

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
	TObjectPtr<UStaticMeshComponent> Body;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
	TObjectPtr<UStaticMeshComponent> Cabin;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
	TObjectPtr<UStaticMeshComponent> WheelFL;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
	TObjectPtr<UStaticMeshComponent> WheelFR;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
	TObjectPtr<UStaticMeshComponent> WheelRL;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
	TObjectPtr<UStaticMeshComponent> WheelRR;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
	TObjectPtr<UStaticMeshComponent> SpritePlane;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
	TObjectPtr<USkeletalMeshComponent> VehicleMesh;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
	TObjectPtr<UTextRenderComponent> Label;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Street")
	FName CarId;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Street")
	FText DisplayName;

	/** Period lacquer tint for the 3D vehicle mesh (Packard black, taxi yellow, etc.). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Street|Art")
	FLinearColor BodyPaint = FLinearColor(0.05f, 0.05f, 0.06f, 1.f);

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Street|Art")
	TSoftObjectPtr<UMaterialInterface> SpriteMaterial;

	/** Cruise along the Chicago grid when not in a scripted pass. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Street|Traffic")
	bool bFreeRoam = true;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Street|Traffic")
	float CruiseSpeed = 900.f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Street|Traffic")
	float RoadZ = 45.f;

	void SetOccupant(ALEHoodlumCharacter* Hood);
	ALEHoodlumCharacter* GetOccupant() const { return Occupant; }

	void SetSpriteMaterialPath(const FString& SoftPath);

	void BeginDrivePass(FVector From, FVector To, FVector LookAt);
	bool IsPassComplete() const { return bPassComplete; }
	bool IsDriving() const { return bDriving; }

protected:
	void ApplyLoadedSprite();
	void FaceSpriteToCamera();
	void ApplyBodyColors();
	void TickFreeRoam(float DeltaSeconds);
	void PickNextRoamGoal();
	float SnapToRoadAxis(float Value) const;

	UPROPERTY()
	TObjectPtr<ALEHoodlumCharacter> Occupant;

	bool bDriving = false;
	bool bPassComplete = false;
	bool bUsingSprite = false;
	bool bRoamPaused = false;
	FVector PassFrom = FVector::ZeroVector;
	FVector PassTo = FVector::ZeroVector;
	float PassAlpha = 0.f;
	float PassDuration = 2.4f;

	FVector RoamGoal = FVector::ZeroVector;
	bool bHasRoamGoal = false;
};
