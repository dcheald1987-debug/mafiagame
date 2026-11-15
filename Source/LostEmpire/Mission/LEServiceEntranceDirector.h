#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LEServiceEntranceDirector.generated.h"

UENUM(BlueprintType)
enum class ELEServiceEntranceState : uint8
{
	DockDrive,
	Ambush,
	Escape,
	Arrived,
	Failed
};

UENUM(BlueprintType)
enum class ELEServiceEntranceFail : uint8
{
	None,
	BleedOut,
	Wreck,
	AbandonedCar,
	StoppedForPatrol
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FLELineSignature, FName, LineId, FText, Subtitle);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FLECheckpointSignature, FName, CheckpointId);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FLEFailSignature, ELEServiceEntranceFail, Reason);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FLESuccessSignature);

/**
 * Runs C01 Service Entrance: cold open, ambush, the 4:30 bleed, and the route zones.
 * Subtitles match Design/Script/C01.md. Volumes report zones by name:
 * AmesHill, Avenue, Cut, MissedTurn, Garage.
 */
UCLASS(Blueprintable)
class LOSTEMPIRE_API ALEServiceEntranceDirector : public AActor
{
	GENERATED_BODY()

public:
	ALEServiceEntranceDirector();

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	UFUNCTION(BlueprintCallable, Category = "C01")
	void PlayColdOpen();

	UFUNCTION(BlueprintCallable, Category = "C01")
	void StartAmbush();

	/** CP1. Starts the bleed timer and the drive lines. */
	UFUNCTION(BlueprintCallable, Category = "C01")
	void CloseRearDoorAndDepart();

	UFUNCTION(BlueprintCallable, Category = "C01")
	void NotifyZone(FName ZoneId, bool bEntered);

	UFUNCTION(BlueprintCallable, Category = "C01")
	void NotifyVehicleWrecked();

	UFUNCTION(BlueprintCallable, Category = "C01")
	void NotifyPlayerLeftVehicle();

	UFUNCTION(BlueprintCallable, Category = "C01")
	void NotifyPatrolStop();

	UFUNCTION(BlueprintPure, Category = "C01")
	float GetBleedSecondsRemaining() const;

	UPROPERTY(BlueprintAssignable, Category = "C01")
	FLELineSignature OnLine;

	UPROPERTY(BlueprintAssignable, Category = "C01")
	FLECheckpointSignature OnCheckpoint;

	UPROPERTY(BlueprintAssignable, Category = "C01")
	FLEFailSignature OnChapterFailed;

	UPROPERTY(BlueprintAssignable, Category = "C01")
	FLESuccessSignature OnChapterSucceeded;

	/** Greybox switch. The dock and ambush will call CloseRearDoorAndDepart themselves later. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "C01")
	bool bStartEscapeOnPlay = true;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "C01")
	float BleedDuration = 270.f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "C01")
	ELEServiceEntranceState State = ELEServiceEntranceState::DockDrive;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "C01")
	ELEServiceEntranceFail FailReason = ELEServiceEntranceFail::None;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "C01")
	FName CurrentCheckpoint;

protected:
	void PlayLine(FName LineId);
	void ReachCheckpoint(FName CheckpointId);
	void FailChapter(ELEServiceEntranceFail Reason);
	void Succeed();
	static FText SubtitleFor(FName LineId);

	UPROPERTY(VisibleAnywhere, Category = "C01")
	float EscapeElapsed = 0.f;

	bool bOnAmesHill = false;
	bool bEnteredAvenue = false;
	bool bEnteredCut = false;
	bool bPlayedHillWarning = false;
	bool bPlayedNicky = false;
	bool bPlayedBleedWarning = false;

	TSet<FName> FiredLines;
};
