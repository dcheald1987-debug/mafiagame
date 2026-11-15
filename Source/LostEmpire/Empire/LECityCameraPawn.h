#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Pawn.h"
#include "LECityCameraPawn.generated.h"

class UCameraComponent;
class USpringArmComponent;

/** Bird's-eye empire camera. Pan WASD, zoom wheel, no driving. */
UCLASS()
class LOSTEMPIRE_API ALECityCameraPawn : public APawn
{
	GENERATED_BODY()

public:
	ALECityCameraPawn();

	virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;
	virtual void Tick(float DeltaSeconds) override;

protected:
	void MoveForward(float Value);
	void MoveRight(float Value);
	void Zoom(float Value);

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Camera")
	TObjectPtr<USpringArmComponent> Boom;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Camera")
	TObjectPtr<UCameraComponent> Camera;

	UPROPERTY(EditAnywhere, Category = "Camera")
	float PanSpeed = 2200.f;

	/** Ortho width limits (Gangsters-style zoom, not perspective arm length). */
	UPROPERTY(EditAnywhere, Category = "Camera")
	float MinArmLength = 1800.f;

	UPROPERTY(EditAnywhere, Category = "Camera")
	float MaxArmLength = 7000.f;

	UPROPERTY(EditAnywhere, Category = "Camera")
	float ZoomSpeed = 350.f;

	float ForwardAxis = 0.f;
	float RightAxis = 0.f;
};
