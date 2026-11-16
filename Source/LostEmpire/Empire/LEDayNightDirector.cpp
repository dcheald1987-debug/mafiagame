#include "LEDayNightDirector.h"

#include "Components/DirectionalLightComponent.h"
#include "Components/LightComponent.h"
#include "Components/PostProcessComponent.h"
#include "Components/SkyLightComponent.h"
#include "Engine/DirectionalLight.h"
#include "Engine/PostProcessVolume.h"
#include "Engine/SkyLight.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "HAL/IConsoleManager.h"
#include "Kismet/GameplayStatics.h"

namespace LEChicagoSun
{
	static const int32 SunriseMin[12] = {
		7 * 60 + 15, 6 * 60 + 46, 7 * 60 + 2, 6 * 60 + 10, 5 * 60 + 30, 5 * 60 + 14,
		5 * 60 + 28, 5 * 60 + 58, 6 * 60 + 30, 7 * 60 + 2, 6 * 60 + 40, 7 * 60 + 11
	};
	static const int32 SunsetMin[12] = {
		16 * 60 + 44, 17 * 60 + 23, 18 * 60 + 57, 19 * 60 + 31, 20 * 60 + 4, 20 * 60 + 27,
		20 * 60 + 23, 19 * 60 + 50, 18 * 60 + 59, 18 * 60 + 8, 16 * 60 + 29, 16 * 60 + 20
	};
	static const float SpeedSteps[3] = { 1.f, 4.f, 16.f };

	static int32 DaysInMonth(int32 InYear, int32 InMonth)
	{
		static const int32 Dim[12] = { 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31 };
		if (InMonth == 2)
		{
			const bool bLeap = (InYear % 4 == 0 && InYear % 100 != 0) || (InYear % 400 == 0);
			return bLeap ? 29 : 28;
		}
		return Dim[FMath::Clamp(InMonth, 1, 12) - 1];
	}
}

ALEDayNightDirector::ALEDayNightDirector()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.bStartWithTickEnabled = true;

	Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(Root);

	// Key light — plain directional, NO atmosphere/sun-sky coupling (that was going black)
	SunLight = CreateDefaultSubobject<UDirectionalLightComponent>(TEXT("SunLight"));
	SunLight->SetupAttachment(Root);
	SunLight->SetMobility(EComponentMobility::Movable);
	SunLight->SetIntensity(28.f);
	SunLight->SetLightColor(FLinearColor(1.f, 0.97f, 0.9f));
	SunLight->SetAtmosphereSunLight(false);
	SunLight->SetCastShadows(false);
	SunLight->SetForwardShadingPriority(0);
	// ONE directional only — a second light caused forward-shading wedges

	MoonLight = nullptr;

	SkyLight = CreateDefaultSubobject<USkyLightComponent>(TEXT("SkyLight"));
	SkyLight->SetupAttachment(Root);
	SkyLight->SetMobility(EComponentMobility::Movable);
	SkyLight->bRealTimeCapture = false;
	SkyLight->bLowerHemisphereIsBlack = false;
	SkyLight->LowerHemisphereColor = FLinearColor(0.35f, 0.38f, 0.42f);
	SkyLight->SetIntensity(0.f);
	SkyLight->SetVisibility(false);

	DayNightPP = CreateDefaultSubobject<UPostProcessComponent>(TEXT("DayNightPP"));
	DayNightPP->SetupAttachment(Root);
	DayNightPP->bUnbound = true;
	DayNightPP->Priority = 50.f;
	DayNightPP->BlendWeight = 1.f;
	DayNightPP->Settings.bOverride_AutoExposureMethod = true;
	DayNightPP->Settings.AutoExposureMethod = EAutoExposureMethod::AEM_Manual;
	DayNightPP->Settings.bOverride_AutoExposureBias = true;
	DayNightPP->Settings.AutoExposureBias = 6.0f;
	DayNightPP->Settings.bOverride_BloomIntensity = true;
	DayNightPP->Settings.BloomIntensity = 0.05f;
	// Soft fill so empty sky pixels aren't a pure black void
	DayNightPP->Settings.bOverride_SceneColorTint = true;
	DayNightPP->Settings.SceneColorTint = FLinearColor(1.08f, 1.04f, 0.98f);
	DayNightPP->Settings.bOverride_AmbientCubemapIntensity = true;
	DayNightPP->Settings.AmbientCubemapIntensity = 0.35f;
}

void ALEDayNightDirector::BeginPlay()
{
	Super::BeginPlay();
	SilenceMapLights();
	// Hard-kill shadow slabs / AO voids that crush façade plates
	auto SetCVar = [](const TCHAR* Name, int32 Value)
	{
		if (IConsoleVariable* Var = IConsoleManager::Get().FindConsoleVariable(Name))
		{
			Var->Set(Value, ECVF_SetByCode);
		}
	};
	SetCVar(TEXT("r.ShadowQuality"), 0);
	SetCVar(TEXT("r.Shadow.MaxResolution"), 0);
	SetCVar(TEXT("r.ContactShadows"), 0);
	SetCVar(TEXT("r.DistanceFieldAO"), 0);
	SetCVar(TEXT("r.AmbientOcclusionLevels"), 0);
	SetCVar(TEXT("r.Shadow.Virtual.Enable"), 0);
	TimeOfDayMinutes = 12 * 60;
	ApplyLighting();
	BindInput();
}

void ALEDayNightDirector::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	if (!bInputBound)
	{
		BindInput();
	}
	if (!bSilencedMapLights)
	{
		SilenceMapLights();
	}
	AdvanceTime(DeltaSeconds);
	ApplyLighting();
}

void ALEDayNightDirector::BindInput()
{
	if (bInputBound || !GetWorld())
	{
		return;
	}
	APlayerController* PC = UGameplayStatics::GetPlayerController(GetWorld(), 0);
	if (!PC || !PC->InputComponent)
	{
		return;
	}
	PC->InputComponent->BindAction(TEXT("StreetToggleSpeed"), IE_Pressed, this, &ALEDayNightDirector::InputToggleSpeed);
	PC->InputComponent->BindAction(TEXT("ToggleSpeed"), IE_Pressed, this, &ALEDayNightDirector::InputToggleSpeed);
	bInputBound = true;
}

void ALEDayNightDirector::InputToggleSpeed()
{
	ToggleSpeed();
}

void ALEDayNightDirector::ToggleSpeed()
{
	SpeedIndex = (SpeedIndex + 1) % 3;
	SpeedMultiplier = LEChicagoSun::SpeedSteps[SpeedIndex];
}

void ALEDayNightDirector::SetTimeOfDayMinutes(int32 Minutes)
{
	TimeOfDayMinutes = ((Minutes % 1440) + 1440) % 1440;
	ApplyLighting();
}

int32 ALEDayNightDirector::GetSunriseMinutes() const
{
	return LEChicagoSun::SunriseMin[FMath::Clamp(Month, 1, 12) - 1];
}

int32 ALEDayNightDirector::GetSunsetMinutes() const
{
	return LEChicagoSun::SunsetMin[FMath::Clamp(Month, 1, 12) - 1];
}

FText ALEDayNightDirector::GetClockText() const
{
	const int32 H = TimeOfDayMinutes / 60;
	const int32 M = TimeOfDayMinutes % 60;
	const bool bPM = H >= 12;
	int32 H12 = H % 12;
	if (H12 == 0)
	{
		H12 = 12;
	}
	return FText::FromString(FString::Printf(TEXT("%d:%02d %s"), H12, M, bPM ? TEXT("PM") : TEXT("AM")));
}

FText ALEDayNightDirector::GetDateText() const
{
	static const TCHAR* Months[] = {
		TEXT("Jan"), TEXT("Feb"), TEXT("Mar"), TEXT("Apr"), TEXT("May"), TEXT("Jun"),
		TEXT("Jul"), TEXT("Aug"), TEXT("Sep"), TEXT("Oct"), TEXT("Nov"), TEXT("Dec")
	};
	return FText::FromString(FString::Printf(TEXT("%s %d, %d"), Months[FMath::Clamp(Month, 1, 12) - 1], Day, Year));
}

FText ALEDayNightDirector::GetSpeedText() const
{
	return FText::FromString(FString::Printf(TEXT("%.0fx"), SpeedMultiplier));
}

void ALEDayNightDirector::SilenceMapLights()
{
	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}

	// DESTROY map directionals/skylights — dual directionals = ForwardShadingPriority wedges.
	TArray<AActor*> ToDestroy;
	for (TActorIterator<ADirectionalLight> It(World); It; ++It)
	{
		ToDestroy.Add(*It);
	}
	for (TActorIterator<ASkyLight> It(World); It; ++It)
	{
		ToDestroy.Add(*It);
	}
	for (AActor* A : ToDestroy)
	{
		if (IsValid(A))
		{
			A->Destroy();
		}
	}

	// Kill ANY leftover directional components that are not our single SunLight.
	for (TActorIterator<AActor> It(World); It; ++It)
	{
		TArray<UDirectionalLightComponent*> Dirs;
		It->GetComponents<UDirectionalLightComponent>(Dirs);
		for (UDirectionalLightComponent* Comp : Dirs)
		{
			if (Comp && Comp != SunLight)
			{
				Comp->SetVisibility(false);
				Comp->SetIntensity(0.f);
				Comp->SetAtmosphereSunLight(false);
				Comp->DestroyComponent();
			}
		}
	}

	bSilencedMapLights = true;
}

void ALEDayNightDirector::AdvanceTime(float DeltaSeconds)
{
	const float GameMinutes = DeltaSeconds * GameMinutesPerRealSecond * SpeedMultiplier;
	TimeAccumulator += GameMinutes;
	while (TimeAccumulator >= 1.f)
	{
		TimeAccumulator -= 1.f;
		++TimeOfDayMinutes;
		if (TimeOfDayMinutes >= 1440)
		{
			TimeOfDayMinutes = 0;
			++Day;
			const int32 Dim = LEChicagoSun::DaysInMonth(Year, Month);
			if (Day > Dim)
			{
				Day = 1;
				++Month;
				if (Month > 12)
				{
					Month = 1;
					++Year;
				}
			}
		}
	}
}

float ALEDayNightDirector::SunElevationFactor() const
{
	const int32 Rise = GetSunriseMinutes();
	const int32 Set = GetSunsetMinutes();
	const int32 T = TimeOfDayMinutes;
	const int32 DawnStart = Rise - 40;
	const int32 DawnEnd = Rise + 25;
	const int32 DuskStart = Set - 25;
	const int32 DuskEnd = Set + 40;

	if (T >= DawnEnd && T <= DuskStart)
	{
		return 1.f;
	}
	if (T <= DawnStart || T >= DuskEnd)
	{
		return 0.f;
	}
	if (T < DawnEnd)
	{
		return FMath::Clamp(float(T - DawnStart) / float(DawnEnd - DawnStart), 0.f, 1.f);
	}
	return FMath::Clamp(1.f - float(T - DuskStart) / float(DuskEnd - DuskStart), 0.f, 1.f);
}

void ALEDayNightDirector::ApplyLighting()
{
	const float DayAmt = SunElevationFactor();
	bIsNight = DayAmt < 0.35f;

	if (SunLight)
	{
		if (!bIsNight)
		{
			SunLight->SetWorldRotation(FRotator(-55.f, 40.f, 0.f));
			SunLight->SetIntensity(110.f);
			SunLight->SetLightColor(FLinearColor(1.f, 0.98f, 0.92f));
		}
		else
		{
			SunLight->SetWorldRotation(FRotator(-40.f, 210.f, 0.f));
			SunLight->SetIntensity(22.f);
			SunLight->SetLightColor(FLinearColor(0.7f, 0.78f, 0.95f));
		}
		SunLight->SetVisibility(true);
		SunLight->SetCastShadows(false);
		SunLight->SetAtmosphereSunLight(false);
		SunLight->SetForwardShadingPriority(5);
	}

	if (SkyLight)
	{
		// Soft fill so building sides aren't pitch-black voids (no capture / no wedges).
		SkyLight->bRealTimeCapture = false;
		SkyLight->bLowerHemisphereIsBlack = false;
		SkyLight->LowerHemisphereColor = FLinearColor(0.45f, 0.48f, 0.52f);
		SkyLight->SetVisibility(true);
		SkyLight->SetIntensity(bIsNight ? 1.2f : 3.5f);
		SkyLight->SetCastShadows(false);
	}

	if (DayNightPP)
	{
		DayNightPP->bUnbound = true;
		DayNightPP->BlendWeight = 1.f;
		DayNightPP->Settings.bOverride_AutoExposureMethod = true;
		DayNightPP->Settings.AutoExposureMethod = EAutoExposureMethod::AEM_Manual;
		DayNightPP->Settings.bOverride_AutoExposureBias = true;
		DayNightPP->Settings.AutoExposureBias = FMath::Lerp(5.0f, 6.5f, DayAmt);
		DayNightPP->Settings.bOverride_BloomIntensity = true;
		DayNightPP->Settings.BloomIntensity = 0.04f;
		DayNightPP->Settings.bOverride_SceneColorTint = true;
		DayNightPP->Settings.SceneColorTint = bIsNight
			? FLinearColor(0.85f, 0.9f, 1.05f)
			: FLinearColor(1.08f, 1.04f, 0.98f);
	}

	SyncStreetLamps(bIsNight);
}

void ALEDayNightDirector::SyncStreetLamps(bool bNight)
{
	if (!GetWorld())
	{
		return;
	}
	const float Target = bNight ? 700.f : 0.f;
	for (TActorIterator<AActor> It(GetWorld()); It; ++It)
	{
		const FString Name = It->GetName();
#if WITH_EDITOR
		const FString Label = It->GetActorLabel();
#else
		const FString Label;
#endif
		if (!Name.Contains(TEXT("FabLight_")) && !Label.StartsWith(TEXT("FabLight_")))
		{
			continue;
		}
		if (ULightComponent* Light = It->FindComponentByClass<ULightComponent>())
		{
			Light->SetIntensity(Target);
			Light->SetVisibility(bNight);
		}
	}
}
