#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LEDayNightDirector.generated.h"

class UDirectionalLightComponent;
class USkyLightComponent;
class UPostProcessComponent;

/**
 * Chicago day/night — owns its own sun/sky/moon lights (does not depend on map labels).
 * 1 real second = GameMinutesPerRealSecond at 1x. ToggleSpeed: 1x / 4x / 16x.
 */
UCLASS()
class LOSTEMPIRE_API ALEDayNightDirector : public AActor
{
	GENERATED_BODY()

public:
	ALEDayNightDirector();

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "DayNight")
	int32 TimeOfDayMinutes = 12 * 60;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "DayNight")
	int32 Year = 1930;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "DayNight")
	int32 Month = 11;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "DayNight")
	int32 Day = 15;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "DayNight")
	bool bIsNight = false;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "DayNight")
	float SpeedMultiplier = 1.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "DayNight")
	float GameMinutesPerRealSecond = 1.f;

	UFUNCTION(BlueprintCallable, Category = "DayNight")
	void ToggleSpeed();

	UFUNCTION(BlueprintCallable, Category = "DayNight")
	void SetTimeOfDayMinutes(int32 Minutes);

	UFUNCTION(BlueprintPure, Category = "DayNight")
	FText GetClockText() const;

	UFUNCTION(BlueprintPure, Category = "DayNight")
	FText GetDateText() const;

	UFUNCTION(BlueprintPure, Category = "DayNight")
	FText GetSpeedText() const;

	UFUNCTION(BlueprintPure, Category = "DayNight")
	int32 GetSunriseMinutes() const;

	UFUNCTION(BlueprintPure, Category = "DayNight")
	int32 GetSunsetMinutes() const;

protected:
	void BindInput();
	void SilenceMapLights();
	void AdvanceTime(float DeltaSeconds);
	void ApplyLighting();
	void SyncStreetLamps(bool bNight);
	float SunElevationFactor() const;

	UFUNCTION()
	void InputToggleSpeed();

	UPROPERTY(VisibleAnywhere, Category = "DayNight")
	TObjectPtr<USceneComponent> Root;

	UPROPERTY(VisibleAnywhere, Category = "DayNight")
	TObjectPtr<UDirectionalLightComponent> SunLight;

	UPROPERTY(VisibleAnywhere, Category = "DayNight")
	TObjectPtr<UDirectionalLightComponent> MoonLight;

	UPROPERTY(VisibleAnywhere, Category = "DayNight")
	TObjectPtr<USkyLightComponent> SkyLight;

	UPROPERTY(VisibleAnywhere, Category = "DayNight")
	TObjectPtr<UPostProcessComponent> DayNightPP;

	float TimeAccumulator = 0.f;
	bool bInputBound = false;
	int32 SpeedIndex = 0;
	bool bSilencedMapLights = false;
};
