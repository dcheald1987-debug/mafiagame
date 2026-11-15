#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "LEGameMode.generated.h"

UCLASS()
class LOSTEMPIRE_API ALEGameMode : public AGameModeBase
{
	GENERATED_BODY()

public:
	virtual void StartPlay() override;
};
