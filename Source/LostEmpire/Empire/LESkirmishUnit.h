#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "LESkirmishTypes.h"
#include "LESkirmishUnit.generated.h"

class UStaticMeshComponent;
class UTextRenderComponent;
class ALESkirmishUnit;

/** Real-time skirmish fighter — select, move, attack. */
UCLASS()
class LOSTEMPIRE_API ALESkirmishUnit : public ACharacter
{
	GENERATED_BODY()

public:
	ALESkirmishUnit();

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;
	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, ReplicatedUsing = OnRep_Team, Category = "Skirmish")
	ELESkirmishTeam Team = ELESkirmishTeam::Blue;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Replicated, Category = "Skirmish")
	ELESkirmishUnitRole UnitRole = ELESkirmishUnitRole::Enforcer;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, ReplicatedUsing = OnRep_Health, Category = "Skirmish")
	int32 Health = 100;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Skirmish")
	int32 MaxHealth = 100;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Skirmish")
	int32 AttackDamage = 18;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Skirmish")
	float AttackRange = 220.f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Skirmish")
	float AttackCooldown = 0.85f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Skirmish")
	float MoveSpeed = 620.f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Replicated, Category = "Skirmish")
	FVector GoalLocation = FVector::ZeroVector;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Replicated, Category = "Skirmish")
	TObjectPtr<ALESkirmishUnit> AttackTarget;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Skirmish")
	bool bSelected = false;

	UFUNCTION(BlueprintCallable, Category = "Skirmish")
	void Configure(ELESkirmishTeam InTeam, ELESkirmishUnitRole InRole, FText InName);

	UFUNCTION(BlueprintCallable, Category = "Skirmish")
	void SetSelected(bool bInSelected);

	UFUNCTION(BlueprintCallable, Category = "Skirmish")
	void CommandMoveTo(FVector WorldLocation);

	UFUNCTION(BlueprintCallable, Category = "Skirmish")
	void CommandAttack(ALESkirmishUnit* Target);

	UFUNCTION(BlueprintCallable, Category = "Skirmish")
	void ApplyDamageFrom(int32 Amount, ALESkirmishUnit* InstigatorUnit);

	bool IsAlive() const { return Health > 0; }

	UFUNCTION()
	void OnRep_Team();

	UFUNCTION()
	void OnRep_Health();

protected:
	void RefreshAppearance();
	void ChaseGoal(float DeltaSeconds);
	void TryAttack(float DeltaSeconds);

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<UStaticMeshComponent> IsoMarker;

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<UTextRenderComponent> NameLabel;

	UPROPERTY(EditAnywhere, Category = "Skirmish")
	FText DisplayName;

	float AttackTimer = 0.f;
	bool bHasGoal = false;
};
