#pragma once

#include "CoreMinimal.h"
#include "LEStreetCharacter.h"
#include "LEHoodlumCharacter.generated.h"

class ALESiteActor;
class ALEStreetCar;

/** Player or rival gang member — dossier + street orders. */
UCLASS()
class LOSTEMPIRE_API ALEHoodlumCharacter : public ALEStreetCharacter
{
	GENERATED_BODY()

public:
	ALEHoodlumCharacter();

	virtual void Tick(float DeltaSeconds) override;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Street")
	FName HoodId;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Street")
	ELEHoodRole HoodRole = ELEHoodRole::Bagman;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Street")
	int32 Loyalty = 50;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Street")
	ELEStreetOrder ActiveStreetOrder = ELEStreetOrder::None;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Street")
	ELEAssignmentState OrderState = ELEAssignmentState::Idle;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Street")
	bool bInBuilding = false;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Street")
	bool bInCar = false;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Street")
	bool bWounded = false;

	UFUNCTION(BlueprintCallable, Category = "Street")
	void ConfigureHoodlum(FName InId, FText InName, uint8 InRole, uint8 InFaction, int32 InLoyalty);

	void IssueEnterBuilding(ALESiteActor* Site);
	void IssueEnterCar(ALEStreetCar* Car);
	void IssueScout(FVector WorldLocation);
	void IssueHitAndRun(AActor* Target);
	void IssueDriveBy(AActor* Target);
	void CancelStreetOrder();

	ALESiteActor* GetOccupiedSite() const { return OccupiedSite; }
	ALEStreetCar* GetBoardedCar() const { return BoardedCar; }
	AActor* GetOrderTarget() const { return OrderTarget; }

	FString GetOrderLabel() const;

protected:
	void ResolveOrderProximity(float DeltaSeconds);

	UPROPERTY()
	TObjectPtr<ALESiteActor> OccupiedSite;

	UPROPERTY()
	TObjectPtr<ALEStreetCar> BoardedCar;

	UPROPERTY()
	TObjectPtr<AActor> OrderTarget;

	float OrderWorkTimer = 0.f;
};
