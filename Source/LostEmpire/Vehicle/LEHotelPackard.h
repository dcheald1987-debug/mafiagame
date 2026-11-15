#pragma once

#include "CoreMinimal.h"
#include "WheeledVehiclePawn.h"
#include "LEHotelPackard.generated.h"

class UCameraComponent;
class USpringArmComponent;
class UChaosWheeledVehicleMovementComponent;
class UPrimitiveComponent;

/**
 * Grand Halcyon Packard for C01. Temporary sports-car mesh, period-slow Chaos tune,
 * interior camera by default. WASD + Space. E leaves (fails the escape). Hard hits wreck it.
 */
UCLASS()
class LOSTEMPIRE_API ALEHotelPackard : public AWheeledVehiclePawn
{
	GENERATED_BODY()

public:
	ALEHotelPackard(const FObjectInitializer& ObjectInitializer);

	virtual void BeginPlay() override;
	virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;
	virtual void Tick(float DeltaSeconds) override;

protected:
	void MoveForward(float Value);
	void MoveRight(float Value);
	void OnHandbrakePressed();
	void OnHandbrakeReleased();
	void ToggleCamera();
	void LeaveVehicle();

	UFUNCTION()
	void HandleMeshHit(
		UPrimitiveComponent* HitComponent,
		AActor* OtherActor,
		UPrimitiveComponent* OtherComp,
		FVector NormalImpulse,
		const FHitResult& Hit);

	void ReportWreck();
	void ReportAbandoned();
	class ALEServiceEntranceDirector* FindDirector() const;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Camera")
	TObjectPtr<USpringArmComponent> ExteriorBoom;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Camera")
	TObjectPtr<UCameraComponent> ExteriorCamera;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Camera")
	TObjectPtr<UCameraComponent> InteriorCamera;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Vehicle")
	TObjectPtr<UChaosWheeledVehicleMovementComponent> ChaosMovement;

	/** Impulse magnitude that counts as a wreck during the escape. */
	UPROPERTY(EditAnywhere, Category = "C01")
	float WreckImpulseThreshold = 120000.f;

	/** Seconds upside-down before the escape counts as a wreck. */
	UPROPERTY(EditAnywhere, Category = "C01")
	float FlipFailSeconds = 2.5f;

	bool bInteriorCameraActive = true;
	bool bReportedTerminal = false;
	float UpsideDownSeconds = 0.f;
};
