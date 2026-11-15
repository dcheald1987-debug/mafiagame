#include "LEGameHUD.h"

#include "LEWeekDirector.h"
#include "LEServiceEntranceDirector.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "Kismet/GameplayStatics.h"

void ALEGameHUD::DrawHUD()
{
	Super::DrawHUD();
	if (!Canvas || !GEngine)
	{
		return;
	}

	if (ALEWeekDirector* Week = Cast<ALEWeekDirector>(
			UGameplayStatics::GetActorOfClass(GetWorld(), ALEWeekDirector::StaticClass())))
	{
		const float W = Canvas->ClipX;
		const float TopH = 36.f;
		const float SideW = FMath::Min(420.f, W * 0.32f);
		const float SideH = Canvas->ClipY * 0.55f;

		// Top bar (Gangsters header strip)
		DrawRect(FLinearColor(0.45f, 0.38f, 0.28f, 0.92f), 0.f, 0.f, W, TopH);
		DrawText(
			TEXT("SAINT LORNE  —  THE LEVEE"),
			FLinearColor(0.95f, 0.9f, 0.78f),
			24.f,
			8.f,
			GEngine->GetMediumFont(),
			1.1f,
			false);

		// Left plan / status panel
		DrawRect(FLinearColor(0.55f, 0.48f, 0.36f, 0.88f), 12.f, TopH + 12.f, SideW, SideH);
		DrawRect(FLinearColor(0.35f, 0.3f, 0.22f, 0.95f), 12.f, TopH + 12.f, SideW, 28.f);

		const FString Block = Week->GetHudBlock().ToString();
		TArray<FString> Lines;
		Block.ParseIntoArrayLines(Lines);
		float Y = TopH + 48.f;
		for (const FString& Line : Lines)
		{
			DrawText(Line, FLinearColor(0.1f, 0.08f, 0.05f), 24.f, Y, GEngine->GetSmallFont(), 1.05f, false);
			Y += 16.f;
			if (Y > TopH + SideH)
			{
				break;
			}
		}

		// Bottom-right clock / speed
		const float BoxW = 160.f;
		const float BoxH = 64.f;
		DrawRect(FLinearColor(0.55f, 0.48f, 0.36f, 0.9f), W - BoxW - 16.f, Canvas->ClipY - BoxH - 16.f, BoxW, BoxH);
		DrawText(
			FString::Printf(TEXT("%.0fx"), Week->TimeDilation),
			FLinearColor(0.1f, 0.08f, 0.05f),
			W - BoxW + 40.f,
			Canvas->ClipY - BoxH + 4.f,
			GEngine->GetLargeFont(),
			1.4f,
			false);
		return;
	}

	// Legacy C01 HUD if that director is present instead.
	ALEServiceEntranceDirector* Director = Cast<ALEServiceEntranceDirector>(
		UGameplayStatics::GetActorOfClass(GetWorld(), ALEServiceEntranceDirector::StaticClass()));
	if (!Director)
	{
		return;
	}

	DrawText(TEXT("C01 legacy map"), FLinearColor::White, 40.f, 40.f, GEngine->GetMediumFont(), 1.f, false);
}
