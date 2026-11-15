#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "LEEmpireTypes.h"
#include "LEHoodAgent.generated.h"

class ALESiteActor;

UCLASS()
class LOSTEMPIRE_API ALEHoodAgent : public ACharacter
{
	GENERATED_BODY()

public:
	ALEHoodAgent();

	virtual void Tick(float DeltaSeconds) override;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Empire")
	FName HoodId;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Empire")
	FText DisplayName;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Empire")
	ELEHoodRole HoodRole = ELEHoodRole::Bagman;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Empire")
	ELEOwner Faction = ELEOwner::Player;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Empire")
	int32 Loyalty = 50;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Empire")
	ELEAssignmentState AssignmentState = ELEAssignmentState::Idle;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Empire")
	ELEOrderType ActiveOrder = ELEOrderType::None;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Empire")
	int32 WeeksOut = 0;

	void BeginAssignment(ELEOrderType Order, ALESiteActor* Site);
	void CancelAssignment();
	bool IsAvailable() const { return WeeksOut <= 0 && AssignmentState != ELEAssignmentState::Dead; }

	UFUNCTION(BlueprintCallable, Category = "Empire")
	void Configure(FName InHoodId, FText InDisplayName, uint8 InRole, uint8 InFaction, int32 InLoyalty);

protected:
	UPROPERTY()
	TObjectPtr<ALESiteActor> TargetSite;

	float WorkTimer = 0.f;
	float WorkDuration = 2.5f;
};
