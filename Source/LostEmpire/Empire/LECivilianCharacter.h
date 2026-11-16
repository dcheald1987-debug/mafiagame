#pragma once

#include "CoreMinimal.h"
#include "LEStreetCharacter.h"
#include "LECivilianCharacter.generated.h"

/** Ambient sidewalk crowd — wanders, flees gunfire. */
UCLASS()
class LOSTEMPIRE_API ALECivilianCharacter : public ALEStreetCharacter
{
	GENERATED_BODY()

public:
	ALECivilianCharacter();

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	UFUNCTION(BlueprintCallable, Category = "Street")
	void PanicFlee(FVector FromLocation);

	UPROPERTY(EditAnywhere, Category = "Street")
	float WanderRadius = 900.f;

protected:
	void PickWanderGoal();

	FVector HomeLocation = FVector::ZeroVector;
	float WanderTimer = 0.f;
	float PanicTimer = 0.f;
};
