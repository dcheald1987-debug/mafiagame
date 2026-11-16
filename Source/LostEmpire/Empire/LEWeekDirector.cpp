#include "LEWeekDirector.h"

#include "LEEmpireGameInstance.h"
#include "LEHoodAgent.h"
#include "LESiteActor.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"

ALEWeekDirector::ALEWeekDirector()
{
	PrimaryActorTick.bCanEverTick = true;
}

void ALEWeekDirector::BeginPlay()
{
	Super::BeginPlay();
	DetectCurrentDistrictFromMap();
	PullStateFromGameInstance();
	GatherWorldActors();
	EnsureDefaultAssignments();
	ApplyAssignmentToSelection();
	if (WeekIndex <= 1 && !bFullOrdersUnlocked)
	{
		ApplyHeatDecay();
	}
	SyncDistrictUnlocks();
	TravelPreviewDistrict = CurrentDistrict;
	BindInput();
	Phase = ELEWeekPhase::Plan;
	UE_LOG(LogTemp, Log, TEXT("Lost Empire %s week %d — Plan. Beat %d."),
		*ULEEmpireGameInstance::DistrictDisplayName(CurrentDistrict).ToString(),
		WeekIndex,
		StoryBeat);
}

void ALEWeekDirector::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	if (!bInputBound)
	{
		BindInput();
	}

	// Soft-lock escapes (ship candidate): never leave the player stuck in Results / Working.
	if (Phase == ELEWeekPhase::Results)
	{
		ResultsIdleSeconds += DeltaSeconds;
		if (ResultsIdleSeconds >= 90.f)
		{
			++SoftLockEscapes;
			UE_LOG(LogTemp, Warning, TEXT("Soft-lock escape: auto BeginNextPlan after %.0fs Results idle"), ResultsIdleSeconds);
			ResultsIdleSeconds = 0.f;
			BeginNextPlan();
		}
		return;
	}

	if (Phase != ELEWeekPhase::Working)
	{
		ResultsIdleSeconds = 0.f;
		WorkingElapsedSeconds = 0.f;
		return;
	}

	WorkingElapsedSeconds += DeltaSeconds;
	WeekTimeRemaining -= DeltaSeconds * TimeDilation;
	ResolveFinishedAssignments();

	bool bAllDone = true;
	for (const FLEHoodAssignment& A : Assignments)
	{
		if (A.Order == ELEOrderType::None)
		{
			continue;
		}
		if (ALEHoodAgent* Hood = FindHood(A.HoodId))
		{
			if (Hood->Faction == ELEOwner::Player
				&& Hood->AssignmentState != ELEAssignmentState::Done
				&& Hood->AssignmentState != ELEAssignmentState::Failed
				&& Hood->AssignmentState != ELEAssignmentState::Arrested
				&& Hood->AssignmentState != ELEAssignmentState::Dead
				&& A.Order != ELEOrderType::Watch)
			{
				bAllDone = false;
				break;
			}
		}
	}

	const bool bOverrun = WorkingElapsedSeconds > (WeekDurationSeconds * 3.f + 5.f);
	if (WeekTimeRemaining <= 0.f || bAllDone || bOverrun)
	{
		if (bOverrun)
		{
			++SoftLockEscapes;
			UE_LOG(LogTemp, Warning, TEXT("Soft-lock escape: force FinishWeek after Working overrun"));
		}
		FinishWeek();
	}
}

void ALEWeekDirector::GatherWorldActors()
{
	Hoods.Reset();
	Sites.Reset();
	RivalHoods.Reset();

	TArray<AActor*> FoundHoods;
	UGameplayStatics::GetAllActorsOfClass(GetWorld(), ALEHoodAgent::StaticClass(), FoundHoods);
	for (AActor* Actor : FoundHoods)
	{
		if (ALEHoodAgent* Hood = Cast<ALEHoodAgent>(Actor))
		{
			Hoods.Add(Hood);
			if (Hood->Faction == ELEOwner::Rival)
			{
				RivalHoods.Add(Hood);
			}
		}
	}

	TArray<AActor*> FoundSites;
	UGameplayStatics::GetAllActorsOfClass(GetWorld(), ALESiteActor::StaticClass(), FoundSites);
	for (AActor* Actor : FoundSites)
	{
		if (ALESiteActor* Site = Cast<ALESiteActor>(Actor))
		{
			Sites.Add(Site);
			Site->RefreshColor();
		}
	}

	Hoods.Sort([](const ALEHoodAgent& A, const ALEHoodAgent& B)
	{
		return A.HoodId.LexicalLess(B.HoodId);
	});
	Sites.Sort([](const ALESiteActor& A, const ALESiteActor& B)
	{
		return A.SiteId.LexicalLess(B.SiteId);
	});
}

void ALEWeekDirector::EnsureDefaultAssignments()
{
	Assignments.Reset();
	for (ALEHoodAgent* Hood : Hoods)
	{
		if (!Hood || Hood->Faction != ELEOwner::Player || !Hood->IsAvailable())
		{
			continue;
		}

		FLEHoodAssignment Row;
		Row.HoodId = Hood->HoodId;
		if (StoryBeat == 0 && !bFullOrdersUnlocked)
		{
			if (Hood->HoodId == TEXT("H01") && FindSite(TEXT("S02")))
			{
				Row.Order = ELEOrderType::Collect;
				Row.SiteId = TEXT("S02");
			}
			else if (Hood->HoodId == TEXT("H03") && FindSite(TEXT("S01")))
			{
				Row.Order = ELEOrderType::Watch;
				Row.SiteId = TEXT("S01");
			}
		}
		Assignments.Add(Row);
	}

	if (Assignments.Num() == 0)
	{
		return;
	}

	SelectedHoodIndex = 0;
	SelectedSiteIndex = 0;
	for (int32 i = 0; i < Sites.Num(); ++i)
	{
		if (Sites[i] && Sites[i]->SiteId == Assignments[0].SiteId)
		{
			SelectedSiteIndex = i;
			break;
		}
	}
}

void ALEWeekDirector::ApplyAssignmentToSelection()
{
	ALEHoodAgent* SelectedHood = GetSelectedHood();
	for (ALEHoodAgent* HoodIt : Hoods)
	{
		if (HoodIt)
		{
			HoodIt->SetSelected(HoodIt == SelectedHood);
		}
	}

	for (ALESiteActor* SiteIt : Sites)
	{
		if (SiteIt)
		{
			SiteIt->SetSelected(Sites.IsValidIndex(SelectedSiteIndex) && SiteIt == Sites[SelectedSiteIndex]);
		}
	}

	ALEHoodAgent* Hood = SelectedHood;
	ALESiteActor* Site = GetSelectedSite();
	if (!Hood || !Site || Hood->Faction != ELEOwner::Player)
	{
		return;
	}

	for (FLEHoodAssignment& Row : Assignments)
	{
		if (Row.HoodId == Hood->HoodId)
		{
			if (Hood->HoodRole == ELEHoodRole::Recruiter && Row.Order == ELEOrderType::Hit)
			{
				Row.Order = ELEOrderType::None;
			}
			Row.SiteId = Site->SiteId;
			return;
		}
	}

	FLEHoodAssignment Row;
	Row.HoodId = Hood->HoodId;
	Row.SiteId = Site->SiteId;
	Assignments.Add(Row);
}

void ALEWeekDirector::StartWorkingWeek()
{
	if (Phase != ELEWeekPhase::Plan)
	{
		return;
	}

	GatherWorldActors();
	WeekCashDelta = 0;
	WeekArrests = 0;
	WeekDeaths = 0;
	WeekTimeRemaining = WeekDurationSeconds;
	TimeDilation = 1.f;
	bRecruitedThisWeek = false;
	bBribedThisWeek = false;
	bCallBoxWatchedLastWeek = bCallBoxWatched;
	bCallBoxWatched = false;
	WeekRivalFlips = 0;
	WeekRivalBlocked = 0;
	// Keep SitesPlayerTouchedLastWeek until after rival script reads it.
	bHadHitLastWeek = false;
	bRaidThisWeek = (Heat >= 4);
	bRaidForecast = (Heat >= 3);
	EnsureHarlanWarCrew();

	for (FLEHoodAssignment& Row : Assignments)
	{
		Row.State = ELEAssignmentState::Idle;
		Row.CashDelta = 0;
		Row.HeatDelta = 0;
		ALEHoodAgent* Hood = FindHood(Row.HoodId);
		ALESiteActor* Site = FindSite(Row.SiteId);
		if (!Hood || !Site || Row.Order == ELEOrderType::None || !Hood->IsAvailable())
		{
			continue;
		}
		if (Hood->HoodRole == ELEHoodRole::Recruiter && Row.Order == ELEOrderType::Hit)
		{
			Row.Order = ELEOrderType::None;
			continue;
		}
		if (!bFullOrdersUnlocked
			&& (Row.Order == ELEOrderType::Recruit || Row.Order == ELEOrderType::Hit))
		{
			Row.Order = ELEOrderType::None;
			continue;
		}
		Hood->BeginAssignment(Row.Order, Site);
		Row.State = ELEAssignmentState::Moving;
	}

	RunRivalScript();
	SitesPlayerTouchedLastWeek.Reset();
	Phase = ELEWeekPhase::Working;
	UpdatePolicePresence();
}

void ALEWeekDirector::ResolveFinishedAssignments()
{
	for (FLEHoodAssignment& Row : Assignments)
	{
		ALEHoodAgent* Hood = FindHood(Row.HoodId);
		ALESiteActor* Site = FindSite(Row.SiteId);
		if (!Hood || !Site)
		{
			continue;
		}

		if (Hood->AssignmentState == ELEAssignmentState::Done && Row.State != ELEAssignmentState::Done)
		{
			ResolveAssignment(Row, Hood, Site);
		}
	}
}

void ALEWeekDirector::ResolveAssignment(FLEHoodAssignment& Assignment, ALEHoodAgent* Hood, ALESiteActor* Site)
{
	Assignment.State = ELEAssignmentState::Done;
	SitesPlayerTouchedLastWeek.Add(Site->SiteId);

	switch (Assignment.Order)
	{
	case ELEOrderType::Collect:
	{
		int32 Pay = Site->CollectPayout;
		if (Hood->HoodRole == ELEHoodRole::Bagman)
		{
			Pay = FMath::RoundToInt(Pay * 1.25f);
		}
		int32 HeatGain = Site->CollectHeat;
		if (Site->OwnerFaction == ELEOwner::Rival || Site->OwnerFaction == ELEOwner::Contested)
		{
			HeatGain += 1;
		}
		if (Site->OwnerFaction == ELEOwner::Player)
		{
			HeatGain = FMath::Max(0, HeatGain - 1);
		}
		Cash += Pay;
		WeekCashDelta += Pay;
		Heat += HeatGain;
		Assignment.CashDelta = Pay;
		Assignment.HeatDelta = HeatGain;
		Site->OwnerFaction = ELEOwner::Player;
		Site->RefreshColor();
		if (TryHeatArrest(Hood, Assignment))
		{
			break;
		}
		break;
	}
	case ELEOrderType::Watch:
		Site->OwnerFaction = ELEOwner::Player;
		Site->RefreshColor();
		if (Site->SiteId == TEXT("S05"))
		{
			bCallBoxWatched = true;
		}
		break;
	case ELEOrderType::Recruit:
		if (Site->SiteId == TEXT("S05") && !bRecruitedThisWeek)
		{
			int32 PlayerCount = 0;
			for (ALEHoodAgent* H : Hoods)
			{
				if (H && H->Faction == ELEOwner::Player && H->AssignmentState != ELEAssignmentState::Dead)
				{
					++PlayerCount;
				}
			}
			const bool bRecruiterBonus = Hood->HoodRole == ELEHoodRole::Recruiter;
			const float FailChance = bRecruiterBonus ? 0.05f : 0.28f;
			if (PlayerCount < 5 && FMath::FRand() >= FailChance)
			{
				bRecruitedThisWeek = true;
				Hood->Loyalty = FMath::Min(100, Hood->Loyalty + (bRecruiterBonus ? 8 : 5));
				const FName NewId(*FString::Printf(TEXT("H%02d"), PlayerCount + 1));
				if (!FindHood(NewId))
				{
					FActorSpawnParameters Params;
					Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
					const FVector SpawnLoc = Site->GetActorLocation() + FVector(180.f * PlayerCount, 120.f, 0.f);
					if (ALEHoodAgent* Newbie = GetWorld()->SpawnActor<ALEHoodAgent>(
							ALEHoodAgent::StaticClass(), SpawnLoc, FRotator::ZeroRotator, Params))
					{
						static const TCHAR* Names[] = { TEXT("Tommy Rhee"), TEXT("Ada Moss"), TEXT("Cal Byrne") };
						const int32 NameIdx = FMath::Clamp(PlayerCount - 3, 0, 2);
						Newbie->Configure(
							NewId,
							FText::FromString(Names[NameIdx]),
							static_cast<uint8>(ELEHoodRole::Bagman),
							static_cast<uint8>(ELEOwner::Player),
							45);
						Hoods.Add(Newbie);
					}
				}
				Cash += 10;
				WeekCashDelta += 10;
				Assignment.CashDelta = 10;
			}
		}
		break;
	case ELEOrderType::Hit:
	{
		bHadHitLastWeek = true;
		int32 HeatGain = 2;
		Heat += HeatGain;
		Assignment.HeatDelta = HeatGain;

		bool bSuccess = true;
		float FailChance = (Hood->HoodRole != ELEHoodRole::Enforcer) ? 0.35f : 0.12f;
		if (Hood->bWounded)
		{
			FailChance += 0.2f;
		}
		if (FMath::FRand() < FailChance)
		{
			bSuccess = false;
		}

		if (TryHeatArrest(Hood, Assignment))
		{
			break;
		}

		const float DeathChance = Hood->bWounded ? 0.4f : 0.25f;
		if (!bSuccess && FMath::FRand() < DeathChance)
		{
			Hood->AssignmentState = ELEAssignmentState::Dead;
			Assignment.State = ELEAssignmentState::Dead;
			++WeekDeaths;
			break;
		}
		if (!bSuccess)
		{
			Hood->bWounded = true;
			Hood->RefreshAppearance();
			Assignment.State = ELEAssignmentState::Failed;
			break;
		}

		Hood->bWounded = false;
		Site->OwnerFaction = ELEOwner::Player;
		Site->RefreshColor();
		Cash += 25;
		WeekCashDelta += 25;
		Assignment.CashDelta = 25;

		for (ALEHoodAgent* Rival : RivalHoods)
		{
			if (Rival && FVector::Dist2D(Rival->GetActorLocation(), Site->GetActorLocation()) < 600.f)
			{
				if (FMath::FRand() < 0.5f)
				{
					Rival->AssignmentState = ELEAssignmentState::Dead;
					++WeekDeaths;
				}
			}
		}
		break;
	}
	default:
		break;
	}

	Heat = FMath::Clamp(Heat, 0, 4);
	UpdatePolicePresence();
}

bool ALEWeekDirector::TryHeatArrest(ALEHoodAgent* Hood, FLEHoodAssignment& Assignment)
{
	if (!Hood || Heat < 3)
	{
		return false;
	}

	// Fair curve: heat 3 = noticed risk, heat 4 = raid week pressure.
	const float ArrestChance = (Heat >= 4) ? 0.45f : 0.22f;
	if (FMath::FRand() >= ArrestChance)
	{
		return false;
	}

	Hood->AssignmentState = ELEAssignmentState::Arrested;
	Hood->WeeksOut = 2;
	Assignment.State = ELEAssignmentState::Arrested;
	++WeekArrests;
	UpdatePolicePresence();
	return true;
}

void ALEWeekDirector::UpdatePolicePresence()
{
	bPoliceOnStreet = Heat >= 3;
	bRaidForecast = Heat >= 3;
	if (!bPoliceOnStreet)
	{
		if (PoliceMarker)
		{
			PoliceMarker->Destroy();
			PoliceMarker = nullptr;
		}
		return;
	}

	const FVector PatrolLoc = (Heat >= 4)
		? FVector(900.f, 500.f, 180.f)   // Call Box — raid staging
		: FVector(0.f, 0.f, 180.f);

	if (PoliceMarker)
	{
		PoliceMarker->SetActorLocation(PatrolLoc);
		PoliceMarker->SetActorScale3D(Heat >= 4 ? FVector(1.8f, 1.8f, 3.6f) : FVector(1.4f, 1.4f, 3.2f));
		return;
	}

	if (!GetWorld())
	{
		return;
	}

	FActorSpawnParameters Params;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	AStaticMeshActor* Marker = GetWorld()->SpawnActor<AStaticMeshActor>(
		AStaticMeshActor::StaticClass(),
		PatrolLoc,
		FRotator::ZeroRotator,
		Params);
	if (!Marker)
	{
		return;
	}

#if WITH_EDITOR
	Marker->SetActorLabel(TEXT("Police_Patrol"));
#endif
	Marker->SetActorScale3D(Heat >= 4 ? FVector(1.8f, 1.8f, 3.6f) : FVector(1.4f, 1.4f, 3.2f));
	if (UStaticMeshComponent* Mesh = Marker->GetStaticMeshComponent())
	{
		if (UStaticMesh* Cube = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube")))
		{
			Mesh->SetStaticMesh(Cube);
		}
		Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	}
	PoliceMarker = Marker;
}

void ALEWeekDirector::ResolvePoliceRaid(const TSet<FName>& PlayerWatchedSites)
{
	WeekRaidNote.Reset();
	if (!bRaidThisWeek || Heat < 4)
	{
		return;
	}

	// Fair outs: Watch the Call Box, or bribe already lowered heat before the week.
	if (bCallBoxWatched || PlayerWatchedSites.Contains(TEXT("S05")))
	{
		WeekRaidNote = TEXT("\nRaid broken — Call Box watched.");
		bRaidThisWeek = false;
		return;
	}

	ALEHoodAgent* Victim = nullptr;
	for (const FLEHoodAssignment& Row : Assignments)
	{
		if (Row.Order != ELEOrderType::Collect && Row.Order != ELEOrderType::Hit)
		{
			continue;
		}
		ALEHoodAgent* Hood = FindHood(Row.HoodId);
		if (Hood && Hood->Faction == ELEOwner::Player
			&& Hood->AssignmentState != ELEAssignmentState::Arrested
			&& Hood->AssignmentState != ELEAssignmentState::Dead
			&& Hood->WeeksOut <= 0)
		{
			Victim = Hood;
			break;
		}
	}
	if (!Victim)
	{
		for (ALEHoodAgent* Hood : Hoods)
		{
			if (Hood && Hood->Faction == ELEOwner::Player && Hood->IsAvailable())
			{
				Victim = Hood;
				break;
			}
		}
	}
	if (!Victim)
	{
		WeekRaidNote = TEXT("\nRaid came — nobody left to cuff.");
		bRaidThisWeek = false;
		return;
	}

	Victim->AssignmentState = ELEAssignmentState::Arrested;
	Victim->WeeksOut = 2;
	++WeekArrests;
	Heat = FMath::Max(0, Heat - 1); // Raid cools the street after a bust
	bRaidThisWeek = false;
	WeekRaidNote = FString::Printf(TEXT("\nRAID — %s arrested for 2 weeks."), *Victim->DisplayName.ToString());
	UpdatePolicePresence();
}

int32 ALEWeekDirector::ScoreRivalSite(const ALEHoodAgent* Rival, const ALESiteActor* Site) const
{
	if (!Rival || !Site || Site->Kind == ELESiteKind::Street)
	{
		return -1000;
	}

	int32 Score = Site->CollectPayout / 5;

	if (Site->OwnerFaction == ELEOwner::Player)
	{
		Score += 45;
		if (SitesPlayerTouchedLastWeek.Contains(Site->SiteId))
		{
			Score += 30;
		}
		if (StoryBeat >= 2 && Site->SiteId == TEXT("S03"))
		{
			Score += 55; // Dock war — press Sal's warehouse
		}
		if (StoryBeat >= 3 && (Site->SiteId == TEXT("S03") || Site->SiteId == TEXT("S04")))
		{
			Score += 40;
		}
	}
	else if (Site->OwnerFaction == ELEOwner::Contested)
	{
		Score += 35;
	}
	else if (Site->OwnerFaction == ELEOwner::Rival)
	{
		Score += 12; // Milk owned rackets
	}

	if (Rival->HoodRole == ELEHoodRole::Enforcer && Site->OwnerFaction == ELEOwner::Player)
	{
		Score += 20;
	}
	if (Rival->HoodRole == ELEHoodRole::Bagman && Site->CollectPayout > 0
		&& Site->OwnerFaction != ELEOwner::Player)
	{
		Score += 18;
	}
	if (Site->SiteId == TEXT("S07") && Site->OwnerFaction != ELEOwner::Rival)
	{
		Score += 8;
	}
	return Score;
}

ELEOrderType ALEWeekDirector::PreferRivalOrder(const ALEHoodAgent* Rival, const ALESiteActor* Site) const
{
	if (!Rival || !Site)
	{
		return ELEOrderType::Watch;
	}
	if (Site->Kind == ELESiteKind::Block || Site->CollectPayout <= 0)
	{
		return ELEOrderType::Watch;
	}
	if (Site->OwnerFaction == ELEOwner::Player)
	{
		return (Rival->HoodRole == ELEHoodRole::Enforcer || StoryBeat >= 2)
			? ELEOrderType::Hit
			: ELEOrderType::Watch;
	}
	if (Site->OwnerFaction == ELEOwner::Contested)
	{
		return Rival->HoodRole == ELEHoodRole::Enforcer ? ELEOrderType::Hit : ELEOrderType::Collect;
	}
	return ELEOrderType::Collect;
}

void ALEWeekDirector::PickRivalJob(ALEHoodAgent* Rival, TSet<FName>& ClaimedSites)
{
	if (!Rival || !Rival->IsAvailable())
	{
		return;
	}

	ALESiteActor* Best = nullptr;
	int32 BestScore = -9999;
	for (ALESiteActor* Site : Sites)
	{
		if (!Site || ClaimedSites.Contains(Site->SiteId))
		{
			continue;
		}
		const int32 Score = ScoreRivalSite(Rival, Site);
		if (Score > BestScore)
		{
			BestScore = Score;
			Best = Site;
		}
	}
	if (!Best)
	{
		return;
	}

	ClaimedSites.Add(Best->SiteId);
	Rival->BeginAssignment(PreferRivalOrder(Rival, Best), Best);
}

void ALEWeekDirector::EnsureHarlanWarCrew()
{
	if (StoryBeat < 2 || FindHood(TEXT("R03")) || !GetWorld())
	{
		return;
	}

	FActorSpawnParameters Params;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	const FVector Loc(1600.f, 700.f, 100.f);
	if (ALEHoodAgent* Harlan = GetWorld()->SpawnActor<ALEHoodAgent>(
			ALEHoodAgent::StaticClass(), Loc, FRotator::ZeroRotator, Params))
	{
		Harlan->Configure(
			TEXT("R03"),
			FText::FromString(TEXT("Harlan")),
			static_cast<uint8>(ELEHoodRole::Enforcer),
			static_cast<uint8>(ELEOwner::Rival),
			80);
		Hoods.Add(Harlan);
		RivalHoods.Add(Harlan);
	}
}

void ALEWeekDirector::RunRivalScript()
{
	GatherWorldActors();
	if (RivalHoods.Num() == 0)
	{
		return;
	}

	TSet<FName> Claimed;
	// Enforcers first so Hits claim the war sites, bagmen milk second.
	TArray<ALEHoodAgent*> Ordered = RivalHoods;
	Ordered.Sort([](const ALEHoodAgent& A, const ALEHoodAgent& B)
	{
		const int32 RA = (A.HoodRole == ELEHoodRole::Enforcer) ? 0 : 1;
		const int32 RB = (B.HoodRole == ELEHoodRole::Enforcer) ? 0 : 1;
		return RA < RB;
	});
	for (ALEHoodAgent* Rival : Ordered)
	{
		PickRivalJob(Rival, Claimed);
	}
}

void ALEWeekDirector::FinishWeek()
{
	if (Phase != ELEWeekPhase::Working || bFinishWeekGuard)
	{
		return;
	}
	bFinishWeekGuard = true;
	WorkingElapsedSeconds = 0.f;

	TSet<FName> PlayerWatchedSites;

	for (FLEHoodAssignment& Row : Assignments)
	{
		ALEHoodAgent* Hood = FindHood(Row.HoodId);
		ALESiteActor* Site = FindSite(Row.SiteId);
		if (!Hood || !Site)
		{
			continue;
		}

		if (Row.Order == ELEOrderType::Watch
			&& (Hood->AssignmentState == ELEAssignmentState::Working
				|| Hood->AssignmentState == ELEAssignmentState::Moving
				|| Hood->AssignmentState == ELEAssignmentState::Done))
		{
			// Arrived or close enough to hold the corner counts as a Watch.
			if (Hood->AssignmentState == ELEAssignmentState::Moving
				&& FVector::Dist2D(Hood->GetActorLocation(), Site->GetActorLocation()) > 250.f)
			{
				continue;
			}
			PlayerWatchedSites.Add(Site->SiteId);
			if (Hood->AssignmentState != ELEAssignmentState::Done
				&& Row.State != ELEAssignmentState::Done
				&& Row.State != ELEAssignmentState::Arrested
				&& Row.State != ELEAssignmentState::Dead)
			{
				Hood->AssignmentState = ELEAssignmentState::Done;
				ResolveAssignment(Row, Hood, Site);
			}
		}
		else if (Hood->AssignmentState == ELEAssignmentState::Done && Row.State != ELEAssignmentState::Done
			&& Row.State != ELEAssignmentState::Arrested && Row.State != ELEAssignmentState::Dead)
		{
			ResolveAssignment(Row, Hood, Site);
		}
	}

	// Rival end-of-week claims — Watch blocks player-held corners.
	WeekRivalFlips = 0;
	WeekRivalBlocked = 0;
	WeekRaidNote.Reset();
	for (ALEHoodAgent* Rival : RivalHoods)
	{
		if (!Rival || Rival->AssignmentState == ELEAssignmentState::Dead
			|| Rival->AssignmentState == ELEAssignmentState::Arrested)
		{
			continue;
		}

		ALESiteActor* Target = Rival->GetTargetSite();
		if (!Target)
		{
			float Best = TNumericLimits<float>::Max();
			for (ALESiteActor* Site : Sites)
			{
				if (!Site)
				{
					continue;
				}
				const float D = FVector::Dist2D(Rival->GetActorLocation(), Site->GetActorLocation());
				if (D < Best)
				{
					Best = D;
					Target = Site;
				}
			}
			if (!Target || Best > 400.f)
			{
				continue;
			}
		}
		else if (FVector::Dist2D(Rival->GetActorLocation(), Target->GetActorLocation()) > 400.f)
		{
			continue;
		}

		Rival->AssignmentState = ELEAssignmentState::Done;

		if (PlayerWatchedSites.Contains(Target->SiteId))
		{
			++WeekRivalBlocked;
			continue;
		}

		if (Rival->ActiveOrder == ELEOrderType::Collect || Rival->ActiveOrder == ELEOrderType::Watch)
		{
			if (Target->OwnerFaction != ELEOwner::Player)
			{
				Target->OwnerFaction = ELEOwner::Rival;
				Target->RefreshColor();
				++WeekRivalFlips;
			}
		}
		else if (Rival->ActiveOrder == ELEOrderType::Hit)
		{
			Target->OwnerFaction = ELEOwner::Rival;
			Target->RefreshColor();
			++WeekRivalFlips;
		}
	}

	ResolvePoliceRaid(PlayerWatchedSites);

	LifetimeCashEarned += FMath::Max(0, WeekCashDelta);
	if (WeekCashDelta > 0 && WeekDeaths == 0)
	{
		++SuccessfulWeeks;
	}

	EvaluateStoryGates();

	LastResultsSummary = FString::Printf(
		TEXT("Cash %+d (bank $%d)\nHeat %d/4\nArrests %d  Deaths %d\nRival claims %d  Watch held %d\nBeat %d — %s%s%s%s"),
		WeekCashDelta,
		Cash,
		Heat,
		WeekArrests,
		WeekDeaths,
		WeekRivalFlips,
		WeekRivalBlocked,
		StoryBeat,
		*GetStoryBeatName(),
		*WeekRaidNote,
		bBrickyardStubUnlocked ? TEXT("\nBrickyard stub unlocked") : TEXT(""),
		bStorySpineComplete ? TEXT("\nDock war closed — story spine complete") : TEXT(""));

	bFullOrdersUnlocked = true;
	Phase = ELEWeekPhase::Results;
	TimeDilation = 1.f;
	ResultsIdleSeconds = 0.f;
	bFinishWeekGuard = false;
	UpdatePolicePresence();
}

bool ALEWeekDirector::PlayerOwns(FName SiteId) const
{
	if (const ALESiteActor* Site = FindSite(SiteId))
	{
		return Site->OwnerFaction == ELEOwner::Player;
	}
	return false;
}

FString ALEWeekDirector::GetBeatBriefing() const
{
	// VO IDs locked in Design/Voice/EmpireBriefings.md + Design/Voice/VOLock.md
	switch (StoryBeat)
	{
	case 0:
		return TEXT("BRIEFING [EMP_0001/0002] — Eddie: The Levee is small. That is why Sal put me here.\nCafe money first. Nora keeps the garage door watched.\n");
	case 1:
		return TEXT("BRIEFING [EMP_0010–0012] — Sal: The warehouse on the water. Hold it until I say otherwise.\nEddie: And if Harlan is already inside?  Sal: Then you were not watching hard enough.\n");
	case 2:
		return TEXT("BRIEFING [EMP_0020/0021] — Eddie: Harlan answered. He brought a third gun. Hold the dock one more week.\n");
	case 3:
		return TEXT("BRIEFING [EMP_0030/0031] — WLOR: Gunfire on the waterfront. Dock war is open — take Hawser Bar and keep the warehouse.\n");
	case 4:
		return TEXT("BRIEFING [EMP_0040/0041] — Ames: Cool the street. Heat at 2 or less while you hold dock and bar.\n");
	default:
		return TEXT("BRIEFING [EMP_0050] — Dock war is over. Brickyard waits when you are ready.\n");
	}
}

FString ALEWeekDirector::GetStoryBeatName() const
{
	switch (StoryBeat)
	{
	case 0: return TEXT("Favor owed");
	case 1: return TEXT("Sal wants the dock");
	case 2: return TEXT("Harlan answers");
	case 3: return TEXT("Dock war");
	case 4: return TEXT("Ames watches");
	default: return TEXT("Spine complete");
	}
}

void ALEWeekDirector::EvaluateStoryGates()
{
	bool bEnteredBeat2ThisResolve = false;

	if (!bDockDemanded && SuccessfulWeeks >= 2 && LifetimeCashEarned >= 100)
	{
		bDockDemanded = true;
		StoryBeat = 1;
	}

	if (bDockDemanded && !bDockHeldForSal && PlayerOwns(TEXT("S03")))
	{
		bDockHeldForSal = true;
		bBrickyardStubUnlocked = true;
		bBrickyardUnlocked = true;
		StoryBeat = FMath::Max(StoryBeat, 2);
		DockHoldWeeks = 0;
		bEnteredBeat2ThisResolve = true;
		EnsureHarlanWarCrew();
	}

	// Beat 2 requires holding the dock through a later week — not the capture week itself.
	if (StoryBeat == 2 && bDockHeldForSal && !bEnteredBeat2ThisResolve)
	{
		if (PlayerOwns(TEXT("S03")))
		{
			++DockHoldWeeks;
			if (DockHoldWeeks >= 1)
			{
				StoryBeat = 3;
				bDockWarOpen = true;
			}
		}
		else
		{
			DockHoldWeeks = 0;
		}
	}

	if (StoryBeat == 3 && PlayerOwns(TEXT("S03")) && PlayerOwns(TEXT("S04")))
	{
		bDockWarWon = true;
		bHaldenRowUnlocked = true;
		StoryBeat = 4;
	}

	if (StoryBeat == 4 && PlayerOwns(TEXT("S03")) && PlayerOwns(TEXT("S04")) && Heat <= 2)
	{
		bStorySpineComplete = true;
		bAmesHillUnlocked = true;
		StoryBeat = 5;
	}

	SyncDistrictUnlocks();
	PushStateToGameInstance();
}

void ALEWeekDirector::DetectCurrentDistrictFromMap()
{
	if (!GetWorld())
	{
		return;
	}
	const FString Map = GetWorld()->GetMapName();
	if (Map.Contains(TEXT("Brickyard")))
	{
		CurrentDistrict = ELEDistrictId::Brickyard;
	}
	else if (Map.Contains(TEXT("HaldenRow")))
	{
		CurrentDistrict = ELEDistrictId::HaldenRow;
	}
	else if (Map.Contains(TEXT("AmesHill")))
	{
		CurrentDistrict = ELEDistrictId::AmesHill;
	}
	else
	{
		CurrentDistrict = ELEDistrictId::Levee;
	}
}

void ALEWeekDirector::SyncDistrictUnlocks()
{
	if (bBrickyardStubUnlocked)
	{
		bBrickyardUnlocked = true;
	}
	if (bDockWarWon)
	{
		bHaldenRowUnlocked = true;
	}
	if (bStorySpineComplete)
	{
		bAmesHillUnlocked = true;
	}
}

void ALEWeekDirector::PushStateToGameInstance()
{
	if (ULEEmpireGameInstance* GI = GetGameInstance<ULEEmpireGameInstance>())
	{
		GI->CurrentDistrict = CurrentDistrict;
		GI->WeekIndex = WeekIndex;
		GI->Cash = Cash;
		GI->Heat = Heat;
		GI->StoryBeat = StoryBeat;
		GI->SuccessfulWeeks = SuccessfulWeeks;
		GI->LifetimeCashEarned = LifetimeCashEarned;
		GI->bDockDemanded = bDockDemanded;
		GI->bDockHeldForSal = bDockHeldForSal;
		GI->bBrickyardUnlocked = bBrickyardUnlocked || bBrickyardStubUnlocked;
		GI->bHaldenRowUnlocked = bHaldenRowUnlocked;
		GI->bAmesHillUnlocked = bAmesHillUnlocked;
		GI->bDockWarOpen = bDockWarOpen;
		GI->bDockWarWon = bDockWarWon;
		GI->bStorySpineComplete = bStorySpineComplete;
		GI->bFullOrdersUnlocked = bFullOrdersUnlocked;
		GI->bCampaignSeeded = true;
	}
}

void ALEWeekDirector::PullStateFromGameInstance()
{
	ULEEmpireGameInstance* GI = GetGameInstance<ULEEmpireGameInstance>();
	if (!GI || !GI->bCampaignSeeded)
	{
		PushStateToGameInstance();
		return;
	}

	WeekIndex = GI->WeekIndex;
	Cash = GI->Cash;
	Heat = GI->Heat;
	StoryBeat = GI->StoryBeat;
	SuccessfulWeeks = GI->SuccessfulWeeks;
	LifetimeCashEarned = GI->LifetimeCashEarned;
	bDockDemanded = GI->bDockDemanded;
	bDockHeldForSal = GI->bDockHeldForSal;
	bBrickyardUnlocked = GI->bBrickyardUnlocked;
	bBrickyardStubUnlocked = GI->bBrickyardUnlocked;
	bHaldenRowUnlocked = GI->bHaldenRowUnlocked;
	bAmesHillUnlocked = GI->bAmesHillUnlocked;
	bDockWarOpen = GI->bDockWarOpen;
	bDockWarWon = GI->bDockWarWon;
	bStorySpineComplete = GI->bStorySpineComplete;
	bFullOrdersUnlocked = GI->bFullOrdersUnlocked;
	GI->CurrentDistrict = CurrentDistrict;
}

bool ALEWeekDirector::IsDistrictUnlocked(ELEDistrictId District) const
{
	switch (District)
	{
	case ELEDistrictId::Levee:
		return true;
	case ELEDistrictId::Brickyard:
		return bBrickyardUnlocked || bBrickyardStubUnlocked;
	case ELEDistrictId::HaldenRow:
		return bHaldenRowUnlocked;
	case ELEDistrictId::AmesHill:
		return bAmesHillUnlocked;
	default:
		return false;
	}
}

void ALEWeekDirector::CollectUnlockedDistricts(TArray<ELEDistrictId>& Out) const
{
	Out.Reset();
	const ELEDistrictId All[] = {
		ELEDistrictId::Levee,
		ELEDistrictId::Brickyard,
		ELEDistrictId::HaldenRow,
		ELEDistrictId::AmesHill};
	for (ELEDistrictId Id : All)
	{
		if (IsDistrictUnlocked(Id))
		{
			Out.Add(Id);
		}
	}
}

void ALEWeekDirector::CycleTravelDistrict(int32 Direction)
{
	if (Phase != ELEWeekPhase::Plan)
	{
		return;
	}
	TArray<ELEDistrictId> Unlocked;
	CollectUnlockedDistricts(Unlocked);
	if (Unlocked.Num() == 0)
	{
		return;
	}
	int32 Index = Unlocked.IndexOfByKey(TravelPreviewDistrict);
	if (Index == INDEX_NONE)
	{
		Index = Unlocked.IndexOfByKey(CurrentDistrict);
	}
	if (Index == INDEX_NONE)
	{
		Index = 0;
	}
	Index = (Index + Direction + Unlocked.Num()) % Unlocked.Num();
	TravelPreviewDistrict = Unlocked[Index];
}

void ALEWeekDirector::ConfirmDistrictTravel()
{
	if (Phase != ELEWeekPhase::Plan || TravelPreviewDistrict == CurrentDistrict)
	{
		return;
	}
	if (!IsDistrictUnlocked(TravelPreviewDistrict) || !GetWorld())
	{
		return;
	}

	PushStateToGameInstance();
	if (ULEEmpireGameInstance* GI = GetGameInstance<ULEEmpireGameInstance>())
	{
		GI->CurrentDistrict = TravelPreviewDistrict;
	}

	const FName MapName = ULEEmpireGameInstance::DistrictToMapName(TravelPreviewDistrict);
	UGameplayStatics::OpenLevel(this, MapName);
}

void ALEWeekDirector::TryBribePolice()
{
	if (Phase != ELEWeekPhase::Plan || bBribedThisWeek || Heat < 2 || Cash < 40)
	{
		return;
	}
	Cash -= 40;
	Heat = FMath::Max(0, Heat - 1);
	bBribedThisWeek = true;
	bRaidForecast = Heat >= 3;
	bRaidThisWeek = Heat >= 4;
	UpdatePolicePresence();
}

void ALEWeekDirector::BeginNextPlan()
{
	if (Phase != ELEWeekPhase::Results)
	{
		return;
	}

	++WeekIndex;
	ApplyHeatDecay();

	for (ALEHoodAgent* Hood : Hoods)
	{
		if (!Hood)
		{
			continue;
		}
		if (Hood->WeeksOut > 0)
		{
			--Hood->WeeksOut;
		}
		if (Hood->AssignmentState != ELEAssignmentState::Dead)
		{
			Hood->CancelAssignment();
		}
	}

	GatherWorldActors();
	EnsureDefaultAssignments();
	ApplyAssignmentToSelection();
	PushStateToGameInstance();
	Phase = ELEWeekPhase::Plan;
	ResultsIdleSeconds = 0.f;
	WorkingElapsedSeconds = 0.f;
	bFinishWeekGuard = false;
}

void ALEWeekDirector::ApplyHeatDecay()
{
	if (!bHadHitLastWeek && Heat > 0)
	{
		--Heat;
	}
	// Watching the Call Box last week cools the street one extra notch.
	if (bCallBoxWatchedLastWeek && Heat > 0)
	{
		--Heat;
	}
	bCallBoxWatchedLastWeek = false;
	UpdatePolicePresence();
}

void ALEWeekDirector::CycleSelectedHood(int32 Direction)
{
	TArray<ALEHoodAgent*> PlayerHoods;
	for (ALEHoodAgent* H : Hoods)
	{
		if (H && H->Faction == ELEOwner::Player && H->IsAvailable())
		{
			PlayerHoods.Add(H);
		}
	}
	if (PlayerHoods.Num() == 0)
	{
		return;
	}
	SelectedHoodIndex = (SelectedHoodIndex + Direction + PlayerHoods.Num()) % PlayerHoods.Num();
	ApplyAssignmentToSelection();
}

void ALEWeekDirector::SelectHoodIndex(int32 Index)
{
	SelectedHoodIndex = FMath::Max(0, Index);
	ApplyAssignmentToSelection();
}

void ALEWeekDirector::SetSelectedOrder(ELEOrderType Order)
{
	ALEHoodAgent* Hood = GetSelectedHood();
	if (!Hood)
	{
		return;
	}
	if (!bFullOrdersUnlocked && (Order == ELEOrderType::Recruit || Order == ELEOrderType::Hit))
	{
		return;
	}
	if (Hood->HoodRole == ELEHoodRole::Recruiter && Order == ELEOrderType::Hit)
	{
		return;
	}

	bool bFound = false;
	for (FLEHoodAssignment& Row : Assignments)
	{
		if (Row.HoodId == Hood->HoodId)
		{
			Row.Order = Order;
			bFound = true;
			break;
		}
	}
	if (!bFound)
	{
		FLEHoodAssignment Row;
		Row.HoodId = Hood->HoodId;
		Row.Order = Order;
		if (ALESiteActor* Site = GetSelectedSite())
		{
			Row.SiteId = Site->SiteId;
		}
		Assignments.Add(Row);
	}
	ApplyAssignmentToSelection();
}

void ALEWeekDirector::CycleSelectedSite(int32 Direction)
{
	if (Sites.Num() == 0)
	{
		return;
	}
	SelectedSiteIndex = (SelectedSiteIndex + Direction + Sites.Num()) % Sites.Num();
	ApplyAssignmentToSelection();
}

void ALEWeekDirector::ToggleSpeed()
{
	if (Phase != ELEWeekPhase::Working)
	{
		return;
	}
	TimeDilation = FMath::IsNearlyEqual(TimeDilation, 1.f) ? 3.f : 1.f;
}

FText ALEWeekDirector::GetHudBlock() const
{
	FString PhaseName = TEXT("PLAN");
	if (Phase == ELEWeekPhase::Working)
	{
		PhaseName = TEXT("WORKING WEEK");
	}
	else if (Phase == ELEWeekPhase::Results)
	{
		PhaseName = TEXT("RESULTS");
	}

	FString Lines;
	Lines += FString::Printf(
		TEXT("LOST EMPIRE  |  %s  |  %s  |  Week %d\n"),
		*ULEEmpireGameInstance::DistrictDisplayName(CurrentDistrict).ToString(),
		*PhaseName,
		WeekIndex);
	Lines += FString::Printf(
		TEXT("Cash $%d   Heat %d/4   Beat %d — %s\n"),
		Cash,
		Heat,
		StoryBeat,
		*GetStoryBeatName());

	Lines += GetBeatBriefing();
	{
		FString Unlocks = TEXT("Districts: Levee");
		if (bBrickyardUnlocked || bBrickyardStubUnlocked)
		{
			Unlocks += TEXT(" | Brickyard");
		}
		if (bHaldenRowUnlocked)
		{
			Unlocks += TEXT(" | Halden Row");
		}
		if (bAmesHillUnlocked)
		{
			Unlocks += TEXT(" | Ames Hill");
		}
		Lines += Unlocks + TEXT("\n");
	}
	if (Phase == ELEWeekPhase::Plan)
	{
		Lines += FString::Printf(
			TEXT("Travel preview: %s  ([ ] cycle, T go)\n"),
			*ULEEmpireGameInstance::DistrictDisplayName(TravelPreviewDistrict).ToString());
	}
	if (bDockWarOpen && !bDockWarWon)
	{
		Lines += TEXT("WAR — Hold S03 and take S04 (Hawser Bar).\n");
	}
	else if (bDockWarWon && !bStorySpineComplete)
	{
		Lines += TEXT("AMES — Hold S03+S04 with Heat 2 or less.\n");
	}
	else if (bStorySpineComplete)
	{
		Lines += TEXT("SPINE COMPLETE — Dock war closed.\n");
	}

	if (Heat >= 4)
	{
		Lines += TEXT("HEAT — RAID WEEK. Watch Call Box (S05) or bribe (B, $40) before it lands.\n");
	}
	else if (bPoliceOnStreet)
	{
		Lines += TEXT("HEAT — Patrol on the street. Collect/Hit risk arrest. B = bribe $40.\n");
	}

	if (Phase == ELEWeekPhase::Plan)
	{
		if (!bFullOrdersUnlocked)
		{
			Lines += TEXT("Tutorial: C collect  V watch only. Recruit/Hit unlock after week 1.\n");
		}
		else
		{
			Lines += TEXT("1-5 hood  C/V/R/H order  Q/E site  Enter run week\n");
		}
		if (const ALEHoodAgent* Hood = GetSelectedHood())
		{
			Lines += FString::Printf(TEXT("Hood: %s (%s)\n"), *Hood->DisplayName.ToString(), *Hood->HoodId.ToString());
		}
		if (const ALESiteActor* Site = GetSelectedSite())
		{
			Lines += FString::Printf(
				TEXT("Site: %s [%s] owner=%d pay=%d\n"),
				*Site->DisplayName.ToString(),
				*Site->SiteId.ToString(),
				static_cast<int32>(Site->OwnerFaction),
				Site->CollectPayout);
		}
		for (const FLEHoodAssignment& Row : Assignments)
		{
			Lines += FString::Printf(
				TEXT("  %s -> %s @ %s\n"),
				*Row.HoodId.ToString(),
				*UEnum::GetValueAsString(Row.Order),
				*Row.SiteId.ToString());
		}
	}
	else if (Phase == ELEWeekPhase::Working)
	{
		Lines += FString::Printf(TEXT("Clock %.0fs  Speed %.0fx  Space = speed\n"), WeekTimeRemaining, TimeDilation);
	}
	else
	{
		Lines += LastResultsSummary + TEXT("\nEnter = next plan\n");
	}

	return FText::FromString(Lines);
}

ALEHoodAgent* ALEWeekDirector::FindHood(FName Id) const
{
	for (ALEHoodAgent* Hood : Hoods)
	{
		if (Hood && Hood->HoodId == Id)
		{
			return Hood;
		}
	}
	return nullptr;
}

ALESiteActor* ALEWeekDirector::FindSite(FName Id) const
{
	for (ALESiteActor* Site : Sites)
	{
		if (Site && Site->SiteId == Id)
		{
			return Site;
		}
	}
	return nullptr;
}

ALEHoodAgent* ALEWeekDirector::GetSelectedHood() const
{
	TArray<ALEHoodAgent*> PlayerHoods;
	for (ALEHoodAgent* H : Hoods)
	{
		if (H && H->Faction == ELEOwner::Player && H->IsAvailable())
		{
			PlayerHoods.Add(H);
		}
	}
	if (!PlayerHoods.IsValidIndex(SelectedHoodIndex))
	{
		return PlayerHoods.Num() > 0 ? PlayerHoods[0] : nullptr;
	}
	return PlayerHoods[SelectedHoodIndex];
}

ALESiteActor* ALEWeekDirector::GetSelectedSite() const
{
	if (!Sites.IsValidIndex(SelectedSiteIndex))
	{
		return nullptr;
	}
	return Sites[SelectedSiteIndex];
}

void ALEWeekDirector::BindInput()
{
	if (bInputBound)
	{
		return;
	}
	APlayerController* PC = UGameplayStatics::GetPlayerController(GetWorld(), 0);
	if (!PC || !PC->InputComponent)
	{
		return;
	}

	PC->InputComponent->BindAction(TEXT("EmpireHood1"), IE_Pressed, this, &ALEWeekDirector::InputSelectHood1);
	PC->InputComponent->BindAction(TEXT("EmpireHood2"), IE_Pressed, this, &ALEWeekDirector::InputSelectHood2);
	PC->InputComponent->BindAction(TEXT("EmpireHood3"), IE_Pressed, this, &ALEWeekDirector::InputSelectHood3);
	PC->InputComponent->BindAction(TEXT("EmpireHood4"), IE_Pressed, this, &ALEWeekDirector::InputSelectHood4);
	PC->InputComponent->BindAction(TEXT("EmpireHood5"), IE_Pressed, this, &ALEWeekDirector::InputSelectHood5);
	PC->InputComponent->BindAction(TEXT("EmpireOrderCollect"), IE_Pressed, this, &ALEWeekDirector::InputOrderCollect);
	PC->InputComponent->BindAction(TEXT("EmpireOrderWatch"), IE_Pressed, this, &ALEWeekDirector::InputOrderWatch);
	PC->InputComponent->BindAction(TEXT("EmpireOrderRecruit"), IE_Pressed, this, &ALEWeekDirector::InputOrderRecruit);
	PC->InputComponent->BindAction(TEXT("EmpireOrderHit"), IE_Pressed, this, &ALEWeekDirector::InputOrderHit);
	PC->InputComponent->BindAction(TEXT("EmpireSitePrev"), IE_Pressed, this, &ALEWeekDirector::InputSitePrev);
	PC->InputComponent->BindAction(TEXT("EmpireSiteNext"), IE_Pressed, this, &ALEWeekDirector::InputSiteNext);
	PC->InputComponent->BindAction(TEXT("EmpireConfirm"), IE_Pressed, this, &ALEWeekDirector::InputConfirm);
	PC->InputComponent->BindAction(TEXT("EmpireSpeed"), IE_Pressed, this, &ALEWeekDirector::InputToggleSpeed);
	PC->InputComponent->BindAction(TEXT("EmpireBribe"), IE_Pressed, this, &ALEWeekDirector::InputBribe);
	PC->InputComponent->BindAction(TEXT("EmpireDistrictPrev"), IE_Pressed, this, &ALEWeekDirector::InputDistrictPrev);
	PC->InputComponent->BindAction(TEXT("EmpireDistrictNext"), IE_Pressed, this, &ALEWeekDirector::InputDistrictNext);
	PC->InputComponent->BindAction(TEXT("EmpireDistrictTravel"), IE_Pressed, this, &ALEWeekDirector::InputDistrictTravel);
	bInputBound = true;
}

void ALEWeekDirector::InputSelectHood1() { if (Phase == ELEWeekPhase::Plan) { SelectHoodIndex(0); } }
void ALEWeekDirector::InputSelectHood2() { if (Phase == ELEWeekPhase::Plan) { SelectHoodIndex(1); } }
void ALEWeekDirector::InputSelectHood3() { if (Phase == ELEWeekPhase::Plan) { SelectHoodIndex(2); } }
void ALEWeekDirector::InputSelectHood4() { if (Phase == ELEWeekPhase::Plan) { SelectHoodIndex(3); } }
void ALEWeekDirector::InputSelectHood5() { if (Phase == ELEWeekPhase::Plan) { SelectHoodIndex(4); } }
void ALEWeekDirector::InputOrderCollect() { if (Phase == ELEWeekPhase::Plan) { SetSelectedOrder(ELEOrderType::Collect); } }
void ALEWeekDirector::InputOrderWatch() { if (Phase == ELEWeekPhase::Plan) { SetSelectedOrder(ELEOrderType::Watch); } }
void ALEWeekDirector::InputOrderRecruit() { if (Phase == ELEWeekPhase::Plan) { SetSelectedOrder(ELEOrderType::Recruit); } }
void ALEWeekDirector::InputOrderHit() { if (Phase == ELEWeekPhase::Plan) { SetSelectedOrder(ELEOrderType::Hit); } }
void ALEWeekDirector::InputSitePrev() { if (Phase == ELEWeekPhase::Plan) { CycleSelectedSite(-1); } }
void ALEWeekDirector::InputSiteNext() { if (Phase == ELEWeekPhase::Plan) { CycleSelectedSite(1); } }
void ALEWeekDirector::InputConfirm()
{
	if (Phase == ELEWeekPhase::Plan)
	{
		StartWorkingWeek();
	}
	else if (Phase == ELEWeekPhase::Results)
	{
		BeginNextPlan();
	}
}
void ALEWeekDirector::InputToggleSpeed() { ToggleSpeed(); }
void ALEWeekDirector::InputBribe() { if (Phase == ELEWeekPhase::Plan) { TryBribePolice(); } }
void ALEWeekDirector::InputDistrictPrev() { if (Phase == ELEWeekPhase::Plan) { CycleTravelDistrict(-1); } }
void ALEWeekDirector::InputDistrictNext() { if (Phase == ELEWeekPhase::Plan) { CycleTravelDistrict(1); } }
void ALEWeekDirector::InputDistrictTravel() { if (Phase == ELEWeekPhase::Plan) { ConfirmDistrictTravel(); } }
