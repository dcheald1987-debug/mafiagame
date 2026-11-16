#pragma once

#include "CoreMinimal.h"
#include "LESkirmishTypes.generated.h"

UENUM(BlueprintType)
enum class ELESkirmishTeam : uint8
{
	None UMETA(DisplayName = "None"),
	Blue UMETA(DisplayName = "Blue"),
	Red UMETA(DisplayName = "Red")
};

UENUM(BlueprintType)
enum class ELESkirmishPhase : uint8
{
	Playing,
	Victory,
	Defeat
};

UENUM(BlueprintType)
enum class ELESkirmishUnitRole : uint8
{
	Enforcer,
	Bagman
};
