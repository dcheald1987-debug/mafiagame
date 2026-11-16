#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "LESkirmishGameMode.generated.h"

/** 2-player listen-server RTS skirmish. Separate from SP week-loop GameMode. */
UCLASS()
class LOSTEMPIRE_API ALESkirmishGameMode : public AGameModeBase
{
	GENERATED_BODY()

public:
	ALESkirmishGameMode();

	virtual void StartPlay() override;
	virtual void PostLogin(APlayerController* NewPlayer) override;

protected:
	void EnsureDirector();

	UPROPERTY()
	TObjectPtr<class ALESkirmishDirector> Director;
};
