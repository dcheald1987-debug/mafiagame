#pragma once

#include "CoreMinimal.h"
#include "GameFramework/HUD.h"
#include "LEGameHUD.generated.h"

/** Empire HUD — parchment strip inspired by Gangsters' management chrome. */
UCLASS()
class LOSTEMPIRE_API ALEGameHUD : public AHUD
{
	GENERATED_BODY()

public:
	virtual void DrawHUD() override;
};
