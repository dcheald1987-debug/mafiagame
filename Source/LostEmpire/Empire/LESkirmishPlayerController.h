#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerController.h"
#include "LESkirmishTypes.h"
#include "LESkirmishPlayerController.generated.h"

class ALESkirmishDirector;
class ALESkirmishUnit;

UCLASS()
class LOSTEMPIRE_API ALESkirmishPlayerController : public APlayerController
{
	GENERATED_BODY()

public:
	ALESkirmishPlayerController();

	virtual void BeginPlay() override;
	virtual void SetupInputComponent() override;

	UFUNCTION(BlueprintCallable, Category = "Skirmish")
	void AssignTeam(ELESkirmishTeam InTeam);

	UFUNCTION(Client, Reliable)
	void ClientAssignTeam(ELESkirmishTeam InTeam);

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Skirmish")
	ELESkirmishTeam LocalTeam = ELESkirmishTeam::Blue;

protected:
	void OnSelectPressed();
	void OnCommandPressed();
	void OnTrainEnforcer();
	void OnTrainBagman();

	UFUNCTION(Server, Reliable)
	void ServerSelectUnit(ALESkirmishUnit* Unit);

	UFUNCTION(Server, Reliable)
	void ServerCommandMove(FVector_NetQuantize WorldLocation);

	UFUNCTION(Server, Reliable)
	void ServerCommandAttack(ALESkirmishUnit* Target);

	UFUNCTION(Server, Reliable)
	void ServerTrain(ELESkirmishUnitRole InRole);

	bool TraceCursor(FHitResult& OutHit) const;
	ALESkirmishDirector* GetDirector() const;
};
