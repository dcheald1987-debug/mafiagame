#include "LEServiceEntranceDirector.h"

#include "../LostEmpire.h"
#include "Engine/Engine.h"

ALEServiceEntranceDirector::ALEServiceEntranceDirector()
{
	PrimaryActorTick.bCanEverTick = true;
}

void ALEServiceEntranceDirector::BeginPlay()
{
	Super::BeginPlay();
	if (bStartEscapeOnPlay)
	{
		CloseRearDoorAndDepart();
	}
}

void ALEServiceEntranceDirector::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	if (State != ELEServiceEntranceState::Escape)
	{
		return;
	}

	EscapeElapsed += DeltaSeconds;
	if (EscapeElapsed >= BleedDuration)
	{
		FailChapter(ELEServiceEntranceFail::BleedOut);
		return;
	}

	if (!bPlayedHillWarning && EscapeElapsed >= 30.f && bOnAmesHill && !bEnteredCut && !bEnteredAvenue)
	{
		bPlayedHillWarning = true;
		PlayLine(TEXT("C01_0030"));
	}

	if (!bPlayedNicky && EscapeElapsed >= 40.f)
	{
		bPlayedNicky = true;
		PlayLine(TEXT("C01_0040"));
		PlayLine(TEXT("C01_0041"));
	}

	if (!bPlayedBleedWarning && (BleedDuration - EscapeElapsed) <= 90.f)
	{
		bPlayedBleedWarning = true;
		PlayLine(TEXT("C01_0042"));
		PlayLine(TEXT("C01_0043"));
	}
}

void ALEServiceEntranceDirector::PlayColdOpen()
{
	PlayLine(TEXT("C01_0001"));
	PlayLine(TEXT("C01_0002"));
	PlayLine(TEXT("C01_0003"));
	PlayLine(TEXT("C01_0004"));
}

void ALEServiceEntranceDirector::StartAmbush()
{
	if (State == ELEServiceEntranceState::Failed || State == ELEServiceEntranceState::Arrived)
	{
		return;
	}

	State = ELEServiceEntranceState::Ambush;
	PlayLine(TEXT("C01_0020"));
	PlayLine(TEXT("C01_0021"));
	PlayLine(TEXT("C01_0022"));
}

void ALEServiceEntranceDirector::CloseRearDoorAndDepart()
{
	if (State != ELEServiceEntranceState::Ambush && State != ELEServiceEntranceState::DockDrive)
	{
		return;
	}

	State = ELEServiceEntranceState::Escape;
	EscapeElapsed = 0.f;
	ReachCheckpoint(TEXT("CP1"));
	PlayLine(TEXT("C01_0023"));
	PlayLine(TEXT("C01_0024"));
	PlayLine(TEXT("C01_0025"));
}

void ALEServiceEntranceDirector::NotifyZone(FName ZoneId, bool bEntered)
{
	if (ZoneId == TEXT("AmesHill"))
	{
		bOnAmesHill = bEntered;
		return;
	}

	if (!bEntered || State != ELEServiceEntranceState::Escape)
	{
		return;
	}

	if (ZoneId == TEXT("Avenue"))
	{
		bEnteredAvenue = true;
		PlayLine(TEXT("C01_0031"));
	}
	else if (ZoneId == TEXT("Cut"))
	{
		bEnteredCut = true;
		ReachCheckpoint(TEXT("CP2"));
		PlayLine(TEXT("C01_0050"));
	}
	else if (ZoneId == TEXT("MissedTurn"))
	{
		PlayLine(TEXT("C01_0051"));
	}
	else if (ZoneId == TEXT("Garage"))
	{
		Succeed();
	}
}

void ALEServiceEntranceDirector::NotifyVehicleWrecked()
{
	if (State == ELEServiceEntranceState::Escape || State == ELEServiceEntranceState::Ambush)
	{
		FailChapter(ELEServiceEntranceFail::Wreck);
	}
}

void ALEServiceEntranceDirector::NotifyPlayerLeftVehicle()
{
	if (State == ELEServiceEntranceState::Escape)
	{
		FailChapter(ELEServiceEntranceFail::AbandonedCar);
	}
}

void ALEServiceEntranceDirector::NotifyPatrolStop()
{
	if (State == ELEServiceEntranceState::Escape)
	{
		PlayLine(TEXT("C01_0032"));
		FailChapter(ELEServiceEntranceFail::StoppedForPatrol);
	}
}

float ALEServiceEntranceDirector::GetBleedSecondsRemaining() const
{
	if (State != ELEServiceEntranceState::Escape)
	{
		return 0.f;
	}

	return FMath::Max(0.f, BleedDuration - EscapeElapsed);
}

void ALEServiceEntranceDirector::PlayLine(FName LineId)
{
	if (LineId.IsNone() || FiredLines.Contains(LineId))
	{
		return;
	}

	FiredLines.Add(LineId);
	const FText Subtitle = SubtitleFor(LineId);
	OnLine.Broadcast(LineId, Subtitle);

	UE_LOG(LogLostEmpire, Log, TEXT("%s: %s"), *LineId.ToString(), *Subtitle.ToString());

	if (GEngine)
	{
		GEngine->AddOnScreenDebugMessage(
			-1,
			5.f,
			FColor::White,
			FString::Printf(TEXT("%s  %s"), *LineId.ToString(), *Subtitle.ToString()));
	}
}

void ALEServiceEntranceDirector::ReachCheckpoint(FName CheckpointId)
{
	CurrentCheckpoint = CheckpointId;
	OnCheckpoint.Broadcast(CheckpointId);
	UE_LOG(LogLostEmpire, Log, TEXT("Checkpoint %s"), *CheckpointId.ToString());
}

void ALEServiceEntranceDirector::FailChapter(ELEServiceEntranceFail Reason)
{
	if (State == ELEServiceEntranceState::Failed || State == ELEServiceEntranceState::Arrived)
	{
		return;
	}

	State = ELEServiceEntranceState::Failed;
	FailReason = Reason;
	OnChapterFailed.Broadcast(Reason);
	UE_LOG(LogLostEmpire, Warning, TEXT("C01 failed: %d"), static_cast<int32>(Reason));
}

void ALEServiceEntranceDirector::Succeed()
{
	if (State != ELEServiceEntranceState::Escape)
	{
		return;
	}

	State = ELEServiceEntranceState::Arrived;
	PlayLine(TEXT("C01_0060"));
	PlayLine(TEXT("C01_0061"));
	PlayLine(TEXT("C01_0062"));
	PlayLine(TEXT("C01_0063"));
	PlayLine(TEXT("C01_0064"));
	PlayLine(TEXT("C01_0065"));
	PlayLine(TEXT("C01_0066"));
	PlayLine(TEXT("C01_0067"));
	PlayLine(TEXT("C01_0070"));
	PlayLine(TEXT("C01_0071"));
	OnChapterSucceeded.Broadcast();
	UE_LOG(LogLostEmpire, Log, TEXT("C01 arrived at Pell's."));
}

FText ALEServiceEntranceDirector::SubtitleFor(FName LineId)
{
	// Mirrors Design/Script/C01.md. Strike a line there first, then here.
	if (LineId == TEXT("C01_0001")) return NSLOCTEXT("C01", "C01_0001", "Your sister is down the hall. She's all right. She doesn't know you're in the building.");
	if (LineId == TEXT("C01_0002")) return NSLOCTEXT("C01", "C01_0002", "Then that's the reason I'm sitting here.");
	if (LineId == TEXT("C01_0003")) return NSLOCTEXT("C01", "C01_0003", "Start with the night at the hotel.");
	if (LineId == TEXT("C01_0004")) return NSLOCTEXT("C01", "C01_0004", "I was still parking their car.");
	if (LineId == TEXT("C01_0010")) return NSLOCTEXT("C01", "C01_0010", "Kitchen's closed. Mr. Ames is still up there, sitting over coffee like it owes him money.");
	if (LineId == TEXT("C01_0011")) return NSLOCTEXT("C01", "C01_0011", "He'll ring when he wants the door.");
	if (LineId == TEXT("C01_0012")) return NSLOCTEXT("C01", "C01_0012", "Then get that car out of my light.");
	if (LineId == TEXT("C01_0020")) return NSLOCTEXT("C01", "C01_0020", "Open the back.");
	if (LineId == TEXT("C01_0021")) return NSLOCTEXT("C01", "C01_0021", "I'm the night man. I don't—");
	if (LineId == TEXT("C01_0022")) return NSLOCTEXT("C01", "C01_0022", "Open it, or he dies on the hotel steps.");
	if (LineId == TEXT("C01_0023")) return NSLOCTEXT("C01", "C01_0023", "Drive. Not the avenue. They've got a man on the avenue.");
	if (LineId == TEXT("C01_0024")) return NSLOCTEXT("C01", "C01_0024", "The hill is one way.");
	if (LineId == TEXT("C01_0025")) return NSLOCTEXT("C01", "C01_0025", "So is bleeding. Go.");
	if (LineId == TEXT("C01_0030")) return NSLOCTEXT("C01", "C01_0030", "Down the hill. Lights off when you hit the Cut.");
	if (LineId == TEXT("C01_0031")) return NSLOCTEXT("C01", "C01_0031", "I said not the avenue.");
	if (LineId == TEXT("C01_0032")) return NSLOCTEXT("C01", "C01_0032", "You stop, he stops breathing.");
	if (LineId == TEXT("C01_0040")) return NSLOCTEXT("C01", "C01_0040", "Tell Sal it was Harlan's cousin. The one from the brewery.");
	if (LineId == TEXT("C01_0041")) return NSLOCTEXT("C01", "C01_0041", "Tell him yourself.");
	if (LineId == TEXT("C01_0042")) return NSLOCTEXT("C01", "C01_0042", "Leo. I'm going.");
	if (LineId == TEXT("C01_0043")) return NSLOCTEXT("C01", "C01_0043", "Eddie. Faster.");
	if (LineId == TEXT("C01_0050")) return NSLOCTEXT("C01", "C01_0050", "Under the bridge and left. Green bulb. Pell's.");
	if (LineId == TEXT("C01_0051")) return NSLOCTEXT("C01", "C01_0051", "Left. The green bulb.");
	if (LineId == TEXT("C01_0060")) return NSLOCTEXT("C01", "C01_0060", "I don't know you.");
	if (LineId == TEXT("C01_0061")) return NSLOCTEXT("C01", "C01_0061", "You're going to. Get him on a table.");
	if (LineId == TEXT("C01_0062")) return NSLOCTEXT("C01", "C01_0062", "That's the hotel's Packard.");
	if (LineId == TEXT("C01_0063")) return NSLOCTEXT("C01", "C01_0063", "I know what it is.");
	if (LineId == TEXT("C01_0064")) return NSLOCTEXT("C01", "C01_0064", "Two hundred. You were never on that dock.");
	if (LineId == TEXT("C01_0065")) return NSLOCTEXT("C01", "C01_0065", "And tomorrow?");
	if (LineId == TEXT("C01_0066")) return NSLOCTEXT("C01", "C01_0066", "Tomorrow you were never on that dock either. Noon, if you want this car to survive its owner.");
	if (LineId == TEXT("C01_0067")) return NSLOCTEXT("C01", "C01_0067", "Wipe the wheel before you go.");
	if (LineId == TEXT("C01_0070")) return NSLOCTEXT("C01", "C01_0070", "He paid me for the night.");
	if (LineId == TEXT("C01_0071")) return NSLOCTEXT("C01", "C01_0071", "I kept the money. That's the part I can't dress up.");
	return FText::GetEmpty();
}
