#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LEEmpireTypes.h"
#include "LEWeekDirector.generated.h"

class ALEHoodAgent;
class ALESiteActor;

/**
 * Plan → Working Week → Results. Owns cash, heat, story spine, rival AI, police raids.
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

	UFUNCTION(BlueprintCallable, Category = "Empire")
	void TryBribePolice();

	UFUNCTION(BlueprintCallable, Category = "Empire")
	void CycleTravelDistrict(int32 Direction);

	UFUNCTION(BlueprintCallable, Category = "Empire")
	void ConfirmDistrictTravel();

	UFUNCTION(BlueprintPure, Category = "Empire")
	FText GetHudBlock() const;

	UFUNCTION(BlueprintPure, Category = "Empire")
	ALEHoodAgent* GetSelectedHood() const;

	UFUNCTION(BlueprintPure, Category = "Empire")
	ALESiteActor* GetSelectedSite() const;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Empire")
	ELEWeekPhase Phase = ELEWeekPhase::Plan;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Empire")
	int32 WeekIndex = 1;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Empire")
	int32 Cash = 100;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Empire")
	int32 Heat = 0;

	/** 0 Favor, 1 Sal dock, 2 Harlan answers, 3 Dock war, 4 Ames quiet, 5 spine complete. */
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

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Empire")
	bool bBrickyardUnlocked = false;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Empire")
	bool bHaldenRowUnlocked = false;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Empire")
	bool bAmesHillUnlocked = false;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Empire")
	ELEDistrictId CurrentDistrict = ELEDistrictId::Levee;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Empire")
	ELEDistrictId TravelPreviewDistrict = ELEDistrictId::Levee;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Empire")
	bool bDockWarOpen = false;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Empire")
	bool bDockWarWon = false;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Empire")
	bool bStorySpineComplete = false;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Empire")
	bool bFullOrdersUnlocked = false;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Empire")
	bool bPoliceOnStreet = false;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Empire")
	bool bRaidThisWeek = false;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Empire")
	bool bRaidForecast = false;

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
	void PickRivalJob(ALEHoodAgent* Rival, TSet<FName>& ClaimedSites);
	int32 ScoreRivalSite(const ALEHoodAgent* Rival, const ALESiteActor* Site) const;
	ELEOrderType PreferRivalOrder(const ALEHoodAgent* Rival, const ALESiteActor* Site) const;
	void EnsureHarlanWarCrew();
	void ApplyHeatDecay();
	void EvaluateStoryGates();
	void SyncDistrictUnlocks();
	void PushStateToGameInstance();
	void PullStateFromGameInstance();
	void DetectCurrentDistrictFromMap();
	void UpdatePolicePresence();
	void ResolvePoliceRaid(const TSet<FName>& PlayerWatchedSites);
	bool TryHeatArrest(ALEHoodAgent* Hood, FLEHoodAssignment& Assignment);
	void BindInput();
	bool IsDistrictUnlocked(ELEDistrictId District) const;
	void CollectUnlockedDistricts(TArray<ELEDistrictId>& Out) const;
	ALEHoodAgent* FindHood(FName Id) const;
	ALESiteActor* FindSite(FName Id) const;
	FString GetBeatBriefing() const;
	FString GetStoryBeatName() const;
	bool PlayerOwns(FName SiteId) const;

	UFUNCTION()
	void InputSelectHood1();
	UFUNCTION()
	void InputSelectHood2();
	UFUNCTION()
	void InputSelectHood3();
	UFUNCTION()
	void InputSelectHood4();
	UFUNCTION()
	void InputSelectHood5();
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
	UFUNCTION()
	void InputBribe();
	UFUNCTION()
	void InputDistrictPrev();
	UFUNCTION()
	void InputDistrictNext();
	UFUNCTION()
	void InputDistrictTravel();

	UPROPERTY()
	TArray<TObjectPtr<ALEHoodAgent>> Hoods;

	UPROPERTY()
	TArray<TObjectPtr<ALESiteActor>> Sites;

	UPROPERTY()
	TArray<TObjectPtr<ALEHoodAgent>> RivalHoods;

	TSet<FName> SitesPlayerTouchedLastWeek;
	bool bHadHitLastWeek = false;
	bool bRecruitedThisWeek = false;
	bool bBribedThisWeek = false;
	bool bCallBoxWatched = false;
	bool bCallBoxWatchedLastWeek = false;
	bool bInputBound = false;
	int32 WeekCashDelta = 0;
	int32 WeekArrests = 0;
	int32 WeekDeaths = 0;
	int32 DockHoldWeeks = 0;
	int32 WeekRivalFlips = 0;
	int32 WeekRivalBlocked = 0;
	FString WeekRaidNote;

	/** Ship polish: Results idle auto-advance; Working overrun force-finish. */
	float ResultsIdleSeconds = 0.f;
	float WorkingElapsedSeconds = 0.f;
	int32 SoftLockEscapes = 0;
	bool bFinishWeekGuard = false;

	UPROPERTY()
	TObjectPtr<AActor> PoliceMarker;
};
