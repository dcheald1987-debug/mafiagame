#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LESkirmishTypes.h"
#include "LESkirmishDirector.generated.h"

class ALESiteActor;
class ALESkirmishUnit;
class ALEWeekDirector;

/**
 * Real-time skirmish on a dressed district: cash from held sites, train units,
 * capture blocks, win by wiping the rival safe house or holding majority.
 */
UCLASS()
class LOSTEMPIRE_API ALESkirmishDirector : public AActor
{
	GENERATED_BODY()

public:
	ALESkirmishDirector();

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;
	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Replicated, Category = "Skirmish")
	ELESkirmishPhase Phase = ELESkirmishPhase::Playing;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Replicated, Category = "Skirmish")
	ELESkirmishTeam Winner = ELESkirmishTeam::None;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Replicated, Category = "Skirmish")
	int32 BlueCash = 150;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Replicated, Category = "Skirmish")
	int32 RedCash = 150;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Replicated, Category = "Skirmish")
	float MajorityHoldTimer = 0.f;

	UPROPERTY(EditAnywhere, Category = "Skirmish")
	int32 TrainEnforcerCost = 60;

	UPROPERTY(EditAnywhere, Category = "Skirmish")
	int32 TrainBagmanCost = 40;

	UPROPERTY(EditAnywhere, Category = "Skirmish")
	float IncomeInterval = 4.f;

	UPROPERTY(EditAnywhere, Category = "Skirmish")
	float CaptureSeconds = 3.5f;

	UPROPERTY(EditAnywhere, Category = "Skirmish")
	float MajorityHoldRequired = 60.f;

	UPROPERTY(EditAnywhere, Category = "Skirmish")
	bool bSpawnAIOpponent = true;

	UFUNCTION(BlueprintCallable, Category = "Skirmish")
	bool TryTrainUnit(ELESkirmishTeam Team, ELESkirmishUnitRole InRole);

	UFUNCTION(BlueprintCallable, Category = "Skirmish")
	void SelectUnit(ALESkirmishUnit* Unit, ELESkirmishTeam ForTeam);

	UFUNCTION(BlueprintCallable, Category = "Skirmish")
	void ClearSelection(ELESkirmishTeam ForTeam);

	UFUNCTION(BlueprintCallable, Category = "Skirmish")
	void CommandSelectedMove(ELESkirmishTeam Team, FVector WorldLocation);

	UFUNCTION(BlueprintCallable, Category = "Skirmish")
	void CommandSelectedAttack(ELESkirmishTeam Team, ALESkirmishUnit* Target);

	UFUNCTION(BlueprintPure, Category = "Skirmish")
	ALESkirmishUnit* GetSelectedUnit(ELESkirmishTeam Team) const;

	UFUNCTION(BlueprintPure, Category = "Skirmish")
	FText GetHudBlock() const;

	UFUNCTION(BlueprintPure, Category = "Skirmish")
	int32 CountOwnedSites(ELESkirmishTeam Team) const;

protected:
	void DisableWeekDirector();
	void GatherSites();
	void AssignStartingBlocks();
	void SpawnStartingUnits();
	void TickIncome(float DeltaSeconds);
	void TickCapture(float DeltaSeconds);
	void TickAI(float DeltaSeconds);
	void TickVictory(float DeltaSeconds);
	void DeclareWinner(ELESkirmishTeam Team);
	ALESiteActor* FindSafeHouse(ELESkirmishTeam Team) const;
	ELESkirmishTeam OwnerToTeam(uint8 InOwner) const;
	uint8 TeamToOwner(ELESkirmishTeam Team) const;
	int32& CashRef(ELESkirmishTeam Team);
	void RefreshSiteColors();

	UPROPERTY()
	TArray<TObjectPtr<ALESiteActor>> Sites;

	UPROPERTY()
	TArray<TObjectPtr<ALESkirmishUnit>> Units;

	UPROPERTY()
	TObjectPtr<ALESiteActor> BlueSafeHouse;

	UPROPERTY()
	TObjectPtr<ALESiteActor> RedSafeHouse;

	UPROPERTY()
	TObjectPtr<ALESkirmishUnit> SelectedBlue;

	UPROPERTY()
	TObjectPtr<ALESkirmishUnit> SelectedRed;

	TMap<FName, float> CaptureProgress;
	TMap<FName, ELESkirmishTeam> CaptureTeam;

	float IncomeTimer = 0.f;
	float AITimer = 0.f;
	int32 BlueTrainCount = 0;
	int32 RedTrainCount = 0;
};
