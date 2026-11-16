#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "LEEmpireTypes.h"
#include "LEStreetCharacter.generated.h"

class UStaticMeshComponent;
class UTextRenderComponent;
class UCapsuleComponent;
class UMaterialInterface;

/** Clickable street pawn — free move toward a goal. */
UCLASS()
class LOSTEMPIRE_API ALEStreetCharacter : public ACharacter
{
	GENERATED_BODY()

public:
	ALEStreetCharacter();

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Street")
	FText DisplayName;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Street")
	ELEOwner Faction = ELEOwner::Neutral;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Street")
	float MoveSpeed = 480.f;

	/** When true, CoatTint/LegsTint/HatTint drive RefreshAppearance (civilians / extras). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Street|Art")
	bool bUseCustomPalette = false;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Street|Art")
	FLinearColor CoatTint = FLinearColor(0.58f, 0.52f, 0.42f);

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Street|Art")
	FLinearColor LegsTint = FLinearColor(0.45f, 0.4f, 0.34f);

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Street|Art")
	FLinearColor HatTint = FLinearColor(0.3f, 0.24f, 0.16f);

	/** Soft path to unlit sprite material (from Art/Refs import). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Street|Art")
	TSoftObjectPtr<UMaterialInterface> SpriteMaterial;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Street")
	bool bSelected = false;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Street")
	bool bFleeing = false;

	UFUNCTION(BlueprintCallable, Category = "Street")
	virtual void SetSelected(bool bInSelected);

	UFUNCTION(BlueprintCallable, Category = "Street")
	void CommandMoveTo(FVector WorldLocation);

	UFUNCTION(BlueprintCallable, Category = "Street")
	void ClearGoal();

	UFUNCTION(BlueprintCallable, Category = "Street|Art")
	void SetSpriteMaterialPath(const FString& SoftPath);

	bool HasGoal() const { return bHasGoal; }
	FVector GetGoal() const { return GoalLocation; }

	virtual void RefreshAppearance();

protected:
	void StepTowardGoal(float DeltaSeconds);
	void ApplyLoadedSprite();
	void FacePortraitToCamera();
	void UpdateWalkPose(float DeltaSeconds, bool bMoving);

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<UStaticMeshComponent> BodyMesh;

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<UStaticMeshComponent> CoatMesh;

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<UStaticMeshComponent> HeadMesh;

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<UStaticMeshComponent> HatMesh;

	/** Optional front portrait card — never replaces the 3D body. */
	UPROPERTY(VisibleAnywhere)
	TObjectPtr<UStaticMeshComponent> SpritePlane;

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<UTextRenderComponent> NameLabel;

	FVector GoalLocation = FVector::ZeroVector;
	bool bHasGoal = false;
	bool bUsingSprite = false;
	float WalkPhase = 0.f;
};
