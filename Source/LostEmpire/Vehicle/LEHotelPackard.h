#pragma once

#include "CoreMinimal.h"
#include "WheeledVehiclePawn.h"
#include "LEHotelPackard.generated.h"

/** The Grand Halcyon's 1930 Packard. Chaos vehicle. Mesh and torque live on the Blueprint child. */
UCLASS(Blueprintable)
class LOSTEMPIRE_API ALEHotelPackard : public AWheeledVehiclePawn
{
	GENERATED_BODY()

public:
	ALEHotelPackard(const FObjectInitializer& ObjectInitializer);
};
