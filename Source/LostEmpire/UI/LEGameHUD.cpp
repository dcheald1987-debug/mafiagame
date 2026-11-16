#include "LEGameHUD.h"

#include "LEDayNightDirector.h"
#include "LEEmpireOrganizerWidget.h"
#include "LEGangDossierWidget.h"
#include "LEServiceEntranceDirector.h"
#include "LEStreetDirector.h"
#include "LEWeekDirector.h"
#include "Blueprint/UserWidget.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "Kismet/GameplayStatics.h"

void ALEGameHUD::BeginPlay()
{
	Super::BeginPlay();

	APlayerController* PC = GetOwningPlayerController();
	if (!PC)
	{
		return;
	}

	DossierWidget = CreateWidget<ULEGangDossierWidget>(PC, ULEGangDossierWidget::StaticClass());
	if (DossierWidget)
	{
		DossierWidget->AddToViewport(20);
	}

	// Compact organizer stays for cash/heat; street dossier is primary.
	OrganizerWidget = CreateWidget<ULEEmpireOrganizerWidget>(PC, ULEEmpireOrganizerWidget::StaticClass());
	if (OrganizerWidget)
	{
		OrganizerWidget->AddToViewport(10);
	}
}

void ALEGameHUD::DrawHUD()
{
	Super::DrawHUD();

	if (!Canvas || !GEngine)
	{
		return;
	}

	// Always draw Chicago clock / date / day-night / speed (top-right).
	if (ALEDayNightDirector* Clock = Cast<ALEDayNightDirector>(
			UGameplayStatics::GetActorOfClass(GetWorld(), ALEDayNightDirector::StaticClass())))
	{
		const FString Line = FString::Printf(
			TEXT("%s   %s   %s   %s"),
			*Clock->GetDateText().ToString(),
			*Clock->GetClockText().ToString(),
			Clock->bIsNight ? TEXT("NIGHT") : TEXT("DAY"),
			*Clock->GetSpeedText().ToString());
		const float X = FMath::Max(40.f, Canvas->ClipX - 520.f);
		DrawText(Line, FLinearColor(0.95f, 0.9f, 0.78f), X, 48.f, GEngine->GetMediumFont(), 1.15f, false);

		const int32 Rise = Clock->GetSunriseMinutes();
		const int32 Set = Clock->GetSunsetMinutes();
		const FString SunLine = FString::Printf(
			TEXT("Chicago sunrise %d:%02d  sunset %d:%02d"),
			Rise / 60, Rise % 60, Set / 60, Set % 60);
		DrawText(SunLine, FLinearColor(0.75f, 0.72f, 0.62f), X, 72.f, GEngine->GetMediumFont(), 0.95f, false);
	}

	// Empire UI lives in UMG. Canvas DrawHUD only covers legacy C01 maps without a WeekDirector.
	if (OrganizerWidget)
	{
		return;
	}

	if (UGameplayStatics::GetActorOfClass(GetWorld(), ALEWeekDirector::StaticClass()))
	{
		return;
	}

	if (UGameplayStatics::GetActorOfClass(GetWorld(), ALEServiceEntranceDirector::StaticClass()))
	{
		DrawText(TEXT("C01 legacy map"), FLinearColor::White, 40.f, 40.f, GEngine->GetMediumFont(), 1.f, false);
	}
}
