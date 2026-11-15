#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LEEmpireTypes.h"
#include "LEWeekDirector.generated.h"

class ALEHoodAgent;
class ALESiteActor;

/**
 * Plan → Working Week → Results. Owns cash, heat, story beat, rival script.
 * Keyboard during Plan: 1-3 select hood, C/W/R/H set order, Q/E cycle site, Enter start week.
 * During Working: Space toggles 1x/3x. During Results: Enter next plan.
 */
UCLASS()
class LOSTEMPIRE_API ALEWeekDirector : public AActor
{
	GENERATED_BODY()

public:
	ALEWeekDirector();

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	UFUNCTION(BlueprintCallable, Category = "Empire")
	void StartWorkingWeek();

	UFUNCTION(BlueprintCallable, Category = "Empire")
	void FinishWeek();

	UFUNCTION(BlueprintCallable, Category = "Empire")
	void BeginNextPlan();

	UFUNCTION(BlueprintCallable, Category = "Empire")
	void CycleSelectedHood(int32 Direction);

	UFUNCTION(BlueprintCallable, Category = "Empire")
	void SelectHoodIndex(int32 Index);

	UFUNCTION(BlueprintCallable, Category = "Empire")
	void SetSelectedOrder(ELEOrderType Order);

	UFUNCTION(BlueprintCallable, Category = "Empire")
	void CycleSelectedSite(int32 Direction);

	UFUNCTION(BlueprintCallable, Category = "Empire")
	void ToggleSpeed();

	UFUNCTION(BlueprintPure, Category = "Empire")
	FText GetHudBlock() const;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Empire")
	ELEWeekPhase Phase = ELEWeekPhase::Plan;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Empire")
	int32 WeekIndex = 1;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Empire")
	int32 Cash = 100;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Empire")
	int32 Heat = 0;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Empire")
	int32 StoryBeat = 0;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Empire")
	int32 SuccessfulWeeks = 0;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Empire")
	int32 LifetimeCashEarned = 0;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Empire")
	bool bDockDemanded = false;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Empire")
	bool bDockHeldForSal = false;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Empire")
	bool bBrickyardStubUnlocked = false;

	UPROPERTY(EditAnywhere, Category = "Empire")
	float WeekDurationSeconds = 45.f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Empire")
	float WeekTimeRemaining = 0.f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Empire")
	float TimeDilation = 1.f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Empire")
	int32 SelectedHoodIndex = 0;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Empire")
	int32 SelectedSiteIndex = 0;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Empire")
	TArray<FLEHoodAssignment> Assignments;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Empire")
	FString LastResultsSummary;

protected:
	void GatherWorldActors();
	void EnsureDefaultAssignments();
	void ApplyAssignmentToSelection();
	void ResolveFinishedAssignments();
	void ResolveAssignment(FLEHoodAssignment& Assignment, ALEHoodAgent* Hood, ALESiteActor* Site);
	void RunRivalScript();
	void ApplyHeatDecay();
	void EvaluateStoryGates();
	void BindInput();
	ALEHoodAgent* FindHood(FName Id) const;
	ALESiteActor* FindSite(FName Id) const;
	ALEHoodAgent* GetSelectedHood() const;
	ALESiteActor* GetSelectedSite() const;

	UFUNCTION()
	void InputSelectHood1();
	UFUNCTION()
	void InputSelectHood2();
	UFUNCTION()
	void InputSelectHood3();
	UFUNCTION()
	void InputOrderCollect();
	UFUNCTION()
	void InputOrderWatch();
	UFUNCTION()
	void InputOrderRecruit();
	UFUNCTION()
	void InputOrderHit();
	UFUNCTION()
	void InputSitePrev();
	UFUNCTION()
	void InputSiteNext();
	UFUNCTION()
	void InputConfirm();
	UFUNCTION()
	void InputToggleSpeed();

	UPROPERTY()
	TArray<TObjectPtr<ALEHoodAgent>> Hoods;

	UPROPERTY()
	TArray<TObjectPtr<ALESiteActor>> Sites;

	UPROPERTY()
	TArray<TObjectPtr<ALEHoodAgent>> RivalHoods;

	TSet<FName> SitesPlayerTouchedLastWeek;
	bool bHadHitLastWeek = false;
	bool bInputBound = false;
	int32 WeekCashDelta = 0;
	int32 WeekArrests = 0;
	int32 WeekDeaths = 0;
};
