#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LEEmpireTypes.h"
#include "LESiteActor.generated.h"

UCLASS()
class LOSTEMPIRE_API ALESiteActor : public AActor
{
	GENERATED_BODY()

public:
	ALESiteActor();

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
	TObjectPtr<USceneComponent> Root;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
	TObjectPtr<UStaticMeshComponent> Marker;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Empire")
	FName SiteId;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Empire")
	FText DisplayName;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Empire")
	ELESiteKind Kind = ELESiteKind::Business;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Empire")
	ELEOwner OwnerFaction = ELEOwner::Neutral;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Empire")
	FName BlockId;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Empire")
	int32 CollectPayout = 0;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Empire")
	int32 CollectHeat = 1;

	void RefreshColor();

	/** Python-friendly setup (enums as bytes). */
	UFUNCTION(BlueprintCallable, Category = "Empire")
	void Configure(FName InSiteId, FText InDisplayName, uint8 InKind, uint8 InOwner, FName InBlockId, int32 InPayout, int32 InHeat);
};
