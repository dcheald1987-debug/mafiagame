#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LEEmpireTypes.h"
#include "LEStreetDirector.generated.h"

class ALEHoodAgent;
class ALEHoodlumCharacter;
class ALECivilianCharacter;
class ALEStreetCar;
class ALESiteActor;
class ALEStreetCharacter;
class ALEWeekDirector;

/**
 * Gangsters street play: free move, click orders, story missions.
 * WeekDirector keeps cash/heat/spine numbers; this owns real-time command.
 */
UCLASS()
class LOSTEMPIRE_API ALEStreetDirector : public AActor
{
	GENERATED_BODY()

public:
	ALEStreetDirector();

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Street")
	ELEMissionId ActiveMission = ELEMissionId::M0_Favor;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Street")
	ELEStreetOrder ArmedOrder = ELEStreetOrder::None;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Street")
	FString CornerLabel = TEXT("On the corner of HAWSER RD & BOARDWALK");

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Street")
	FString MissionBrief;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Street")
	bool bMissionComplete = false;

	UFUNCTION(BlueprintCallable, Category = "Street")
	void ArmOrder(ELEStreetOrder Order);

	UFUNCTION(BlueprintCallable, Category = "Street")
	void SelectHoodlum(ALEHoodlumCharacter* Hood);

	UFUNCTION(BlueprintCallable, Category = "Street")
	void ClearSelection();

	UFUNCTION(BlueprintPure, Category = "Street")
	ALEHoodlumCharacter* GetSelectedHoodlum() const { return SelectedHoodlum; }

	UFUNCTION(BlueprintPure, Category = "Street")
	FText GetDossierBlock() const;

	UFUNCTION(BlueprintPure, Category = "Street")
	FText GetMissionBlock() const;

	void NotifyViolenceAt(FVector Location);

protected:
	void BindInput();
	void BootstrapStreetCast();
	void HideLegacyHoodAgents();
	void SpawnHoodlumsFromSites();
	void SpawnCivilians();
	void SpawnCars();
	void RefreshMissionBrief();
	void EvaluateMission();
	void ApplyOrderResult(ALEHoodlumCharacter* Hood);
	bool TraceCursor(FHitResult& OutHit) const;
	void UpdateCornerLabel(FVector WorldPos);

	UFUNCTION()
	void OnSelectPressed();
	UFUNCTION()
	void OnCancelPressed();
	UFUNCTION()
	void OnArmScout();
	UFUNCTION()
	void OnArmEnterBuilding();
	UFUNCTION()
	void OnArmEnterCar();
	UFUNCTION()
	void OnArmHitAndRun();
	UFUNCTION()
	void OnArmDriveBy();

	UPROPERTY()
	TObjectPtr<ALEHoodlumCharacter> SelectedHoodlum;

	UPROPERTY()
	TArray<TObjectPtr<ALEHoodlumCharacter>> Hoodlums;

	UPROPERTY()
	TArray<TObjectPtr<ALECivilianCharacter>> Civilians;

	UPROPERTY()
	TArray<TObjectPtr<ALEStreetCar>> Cars;

	UPROPERTY()
	TArray<TObjectPtr<ALESiteActor>> Sites;

	UPROPERTY()
	TObjectPtr<ALEWeekDirector> Week;

	bool bInputBound = false;
	bool bBootstrapped = false;
	float MissionCheckTimer = 0.f;
};
