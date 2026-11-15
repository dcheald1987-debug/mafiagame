#include "LERouteZone.h"

#include "LEServiceEntranceDirector.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"

ALERouteZone::ALERouteZone()
{
	bReplicates = false;
}

void ALERouteZone::NotifyActorBeginOverlap(AActor* OtherActor)
{
	Super::NotifyActorBeginOverlap(OtherActor);
	Report(true, OtherActor);
}

void ALERouteZone::NotifyActorEndOverlap(AActor* OtherActor)
{
	Super::NotifyActorEndOverlap(OtherActor);
	Report(false, OtherActor);
}

bool ALERouteZone::IsPlayer(const AActor* OtherActor) const
{
	const APawn* Pawn = Cast<APawn>(OtherActor);
	return Pawn && Pawn->IsPlayerControlled();
}

void ALERouteZone::Report(bool bEntered, AActor* OtherActor) const
{
	if (ZoneId.IsNone() || !IsPlayer(OtherActor))
	{
		return;
	}

	ALEServiceEntranceDirector* Director = Cast<ALEServiceEntranceDirector>(
		UGameplayStatics::GetActorOfClass(this, ALEServiceEntranceDirector::StaticClass()));
	if (Director)
	{
		Director->NotifyZone(ZoneId, bEntered);
	}
}
