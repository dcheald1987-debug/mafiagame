#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "LEEmpireTypes.h"
#include "LEHoodAgent.generated.h"

class ALESiteActor;
class UTextRenderComponent;
class UStaticMeshComponent;

UCLASS()
class LOSTEMPIRE_API ALEHoodAgent : public ACharacter
{
	GENERATED_BODY()

public:
	ALEHoodAgent();

	virtual void BeginPlay() override;
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

	/** Hit that went badly — next Hit is riskier (Nicky / any wounded). */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Empire")
	bool bWounded = false;

	void BeginAssignment(ELEOrderType Order, ALESiteActor* Site);
	void CancelAssignment();
	bool IsAvailable() const { return WeeksOut <= 0 && AssignmentState != ELEAssignmentState::Dead; }
	ALESiteActor* GetTargetSite() const { return TargetSite; }

	UFUNCTION(BlueprintCallable, Category = "Empire")
	void Configure(FName InHoodId, FText InDisplayName, uint8 InRole, uint8 InFaction, int32 InLoyalty);

	UFUNCTION(BlueprintCallable, Category = "Empire")
	void SetSelected(bool bSelected);

	void RefreshAppearance();

protected:
	void MoveTowardTarget(float DeltaSeconds);

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<UStaticMeshComponent> IsoMarker;

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<UTextRenderComponent> NameLabel;

	UPROPERTY()
	TObjectPtr<ALESiteActor> TargetSite;

	UPROPERTY(EditAnywhere, Category = "Empire")
	float MoveSpeed = 520.f;

	bool bSelected = false;
	float WorkTimer = 0.f;
	float WorkDuration = 2.5f;
};
