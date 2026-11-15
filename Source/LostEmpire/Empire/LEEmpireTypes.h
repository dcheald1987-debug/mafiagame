#pragma once

#include "CoreMinimal.h"
#include "LEEmpireTypes.generated.h"

UENUM(BlueprintType)
enum class ELEWeekPhase : uint8
{
	Plan,
	Working,
	Results
};

UENUM(BlueprintType)
enum class ELEOrderType : uint8
{
	None,
	Collect,
	Watch,
	Recruit,
	Hit
};

UENUM(BlueprintType)
enum class ELEHoodRole : uint8
{
	Bagman,
	Enforcer,
	Recruiter
};

UENUM(BlueprintType)
enum class ELESiteKind : uint8
{
	Racket,
	Business,
	Street,
	Block
};

UENUM(BlueprintType)
enum class ELEOwner : uint8
{
	Neutral,
	Player,
	Rival,
	Contested
};

UENUM(BlueprintType)
enum class ELEAssignmentState : uint8
{
	Idle,
	Moving,
	Working,
	Done,
	Failed,
	Arrested,
	Dead
};

USTRUCT(BlueprintType)
struct FLEHoodAssignment
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	FName HoodId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	ELEOrderType Order = ELEOrderType::None;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	FName SiteId;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
	ELEAssignmentState State = ELEAssignmentState::Idle;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
	int32 CashDelta = 0;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
	int32 HeatDelta = 0;
};
