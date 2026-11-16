#include "LESkirmishHUD.h"

#include "LESkirmishDirector.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "Kismet/GameplayStatics.h"

void ALESkirmishHUD::DrawHUD()
{
	Super::DrawHUD();
	if (!Canvas || !GEngine)
	{
		return;
	}

	const ALESkirmishDirector* Director = Cast<ALESkirmishDirector>(
		UGameplayStatics::GetActorOfClass(GetWorld(), ALESkirmishDirector::StaticClass()));
	if (!Director)
	{
		DrawText(TEXT("Skirmish loading…"), FLinearColor::White, 36.f, 36.f, GEngine->GetMediumFont(), 1.2f, false);
		return;
	}

	const FString Block = Director->GetHudBlock().ToString();
	TArray<FString> Lines;
	Block.ParseIntoArrayLines(Lines);

	float Y = 28.f;
	for (const FString& Line : Lines)
	{
		DrawText(Line, FLinearColor(0.95f, 0.92f, 0.82f), 28.f, Y, GEngine->GetMediumFont(), 1.15f, false);
		Y += 22.f;
	}
}
