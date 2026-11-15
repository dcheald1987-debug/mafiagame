#pragma once

#include "CoreMinimal.h"
#include "Engine/TriggerBox.h"
#include "LERouteZone.generated.h"

/** Overlap volume that tells the C01 director which part of the route the player entered. */
UCLASS()
class LOSTEMPIRE_API ALERouteZone : public ATriggerBox
{
	GENERATED_BODY()

public:
	ALERouteZone();

	virtual void NotifyActorBeginOverlap(AActor* OtherActor) override;
	virtual void NotifyActorEndOverlap(AActor* OtherActor) override;

	/** AmesHill, Avenue, Cut, MissedTurn, or Garage. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "C01")
	FName ZoneId = TEXT("AmesHill");

protected:
	bool IsPlayer(const AActor* OtherActor) const;
	void Report(bool bEntered, AActor* OtherActor) const;
};
