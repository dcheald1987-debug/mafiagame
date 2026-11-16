#pragma once

#include "CoreMinimal.h"
#include "GameFramework/HUD.h"
#include "LESkirmishHUD.generated.h"

UCLASS()
class LOSTEMPIRE_API ALESkirmishHUD : public AHUD
{
	GENERATED_BODY()

public:
	virtual void DrawHUD() override;
};
