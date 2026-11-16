#pragma once

#include "CoreMinimal.h"
#include "Engine/GameInstance.h"
#include "LEEmpireTypes.h"
#include "LEEmpireGameInstance.generated.h"

/** Persists campaign state across district map travels. */
UCLASS()
class LOSTEMPIRE_API ULEEmpireGameInstance : public UGameInstance
{
	GENERATED_BODY()

public:
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Empire")
	ELEDistrictId CurrentDistrict = ELEDistrictId::Levee;

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
	bool bBrickyardUnlocked = false;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Empire")
	bool bHaldenRowUnlocked = false;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Empire")
	bool bAmesHillUnlocked = false;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Empire")
	bool bDockWarOpen = false;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Empire")
	bool bDockWarWon = false;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Empire")
	bool bStorySpineComplete = false;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Empire")
	bool bFullOrdersUnlocked = false;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Empire")
	bool bCampaignSeeded = false;

	UFUNCTION(BlueprintPure, Category = "Empire")
	static FName DistrictToMapName(ELEDistrictId District);

	UFUNCTION(BlueprintPure, Category = "Empire")
	static FText DistrictDisplayName(ELEDistrictId District);

	UFUNCTION(BlueprintPure, Category = "Empire")
	bool IsDistrictUnlocked(ELEDistrictId District) const;
};
