#include "LEWeekDirector.h"

#include "LEHoodAgent.h"
#include "LESiteActor.h"
#include "Engine/Engine.h"
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
	GatherWorldActors();
	EnsureDefaultAssignments();
	ApplyHeatDecay();
	BindInput();
	Phase = ELEWeekPhase::Plan;
	UE_LOG(LogTemp, Log, TEXT("Lost Empire empire week %d — Plan phase. Beat %d."), WeekIndex, StoryBeat);
}

void ALEWeekDirector::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	if (!bInputBound)
	{
		BindInput();
	}

	if (Phase != ELEWeekPhase::Working)
	{
		return;
	}

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

	if (WeekTimeRemaining <= 0.f || bAllDone)
	{
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
		if (StoryBeat == 0 && Hood->HoodId == TEXT("H01") && FindSite(TEXT("S02")))
		{
			Row.Order = ELEOrderType::Collect;
			Row.SiteId = TEXT("S02");
		}
		else if (StoryBeat == 0 && Hood->HoodId == TEXT("H02") && FindSite(TEXT("S01")))
		{
			Row.Order = ELEOrderType::Watch;
			Row.SiteId = TEXT("S01");
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
	ALEHoodAgent* Hood = GetSelectedHood();
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
	SitesPlayerTouchedLastWeek.Reset();
	bHadHitLastWeek = false;

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
		Hood->BeginAssignment(Row.Order, Site);
		Row.State = ELEAssignmentState::Moving;
	}

	RunRivalScript();
	Phase = ELEWeekPhase::Working;
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
		break;
	}
	case ELEOrderType::Watch:
		Site->OwnerFaction = ELEOwner::Player;
		Site->RefreshColor();
		break;
	case ELEOrderType::Recruit:
		if (Site->SiteId == TEXT("S05"))
		{
			int32 PlayerCount = 0;
			for (ALEHoodAgent* H : Hoods)
			{
				if (H && H->Faction == ELEOwner::Player && H->AssignmentState != ELEAssignmentState::Dead)
				{
					++PlayerCount;
				}
			}
			if (PlayerCount < 5)
			{
				// Slice: mark success as cash proxy + loyalty bump; spawning extra hoods is map-authored.
				Hood->Loyalty = FMath::Min(100, Hood->Loyalty + 5);
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
		if (Hood->HoodRole != ELEHoodRole::Enforcer && FMath::FRand() < 0.35f)
		{
			bSuccess = false;
		}

		if (Heat >= 3 && FMath::FRand() < 0.4f)
		{
			Hood->AssignmentState = ELEAssignmentState::Arrested;
			Hood->WeeksOut = 2;
			Assignment.State = ELEAssignmentState::Arrested;
			++WeekArrests;
			break;
		}

		if (!bSuccess && FMath::FRand() < 0.25f)
		{
			Hood->AssignmentState = ELEAssignmentState::Dead;
			Assignment.State = ELEAssignmentState::Dead;
			++WeekDeaths;
			break;
		}

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
}

void ALEWeekDirector::RunRivalScript()
{
	if (RivalHoods.Num() == 0)
	{
		return;
	}

	const bool bEven = (WeekIndex % 2) == 0;
	ALESiteActor* Target = nullptr;

	if (bEven)
	{
		Target = FindSite(TEXT("S04"));
		if (!Target || Target->OwnerFaction == ELEOwner::Player)
		{
			Target = FindSite(TEXT("S08"));
		}
		if (!Target || Target->OwnerFaction == ELEOwner::Player)
		{
			Target = FindSite(TEXT("S07"));
		}
	}
	else
	{
		for (const FName& Id : SitesPlayerTouchedLastWeek)
		{
			if (ALESiteActor* Touched = FindSite(Id))
			{
				if (Touched->OwnerFaction == ELEOwner::Contested || Touched->OwnerFaction == ELEOwner::Player)
				{
					Target = Touched;
					break;
				}
			}
		}
		if (!Target)
		{
			Target = FindSite(TEXT("S03"));
		}
	}

	if (!Target)
	{
		return;
	}

	ELEOrderType RivalOrder = bEven ? ELEOrderType::Collect : ELEOrderType::Hit;
	if (Target->Kind == ELESiteKind::Block || Target->CollectPayout == 0)
	{
		RivalOrder = ELEOrderType::Watch;
	}

	for (int32 i = 0; i < RivalHoods.Num(); ++i)
	{
		ALEHoodAgent* Rival = RivalHoods[i];
		if (!Rival || !Rival->IsAvailable())
		{
			continue;
		}
		if (i == 0)
		{
			Rival->BeginAssignment(RivalOrder, Target);
		}
		else
		{
			ALESiteActor* WatchSite = FindSite(TEXT("S07"));
			Rival->BeginAssignment(ELEOrderType::Watch, WatchSite ? WatchSite : Target);
		}
	}
}

void ALEWeekDirector::FinishWeek()
{
	if (Phase != ELEWeekPhase::Working)
	{
		return;
	}

	for (FLEHoodAssignment& Row : Assignments)
	{
		ALEHoodAgent* Hood = FindHood(Row.HoodId);
		ALESiteActor* Site = FindSite(Row.SiteId);
		if (Hood && Site && Hood->AssignmentState == ELEAssignmentState::Working && Row.Order == ELEOrderType::Watch)
		{
			Hood->AssignmentState = ELEAssignmentState::Done;
			ResolveAssignment(Row, Hood, Site);
		}
		else if (Hood && Site && Hood->AssignmentState == ELEAssignmentState::Done && Row.State != ELEAssignmentState::Done
			&& Row.State != ELEAssignmentState::Arrested && Row.State != ELEAssignmentState::Dead)
		{
			ResolveAssignment(Row, Hood, Site);
		}
	}

	// Rival collect resolution (simple): if rival still working Collect on a site they reach, flip owner.
	for (ALEHoodAgent* Rival : RivalHoods)
	{
		if (!Rival || Rival->AssignmentState != ELEAssignmentState::Done)
		{
			continue;
		}
		if (Rival->ActiveOrder == ELEOrderType::Collect || Rival->ActiveOrder == ELEOrderType::Watch
			|| Rival->ActiveOrder == ELEOrderType::Hit)
		{
			// Find nearest site
			ALESiteActor* Nearest = nullptr;
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
					Nearest = Site;
				}
			}
			if (Nearest && Best < 400.f && Nearest->OwnerFaction != ELEOwner::Player)
			{
				Nearest->OwnerFaction = ELEOwner::Rival;
				Nearest->RefreshColor();
			}
			else if (Nearest && Best < 400.f && Rival->ActiveOrder == ELEOrderType::Hit)
			{
				Nearest->OwnerFaction = ELEOwner::Rival;
				Nearest->RefreshColor();
			}
		}
	}

	LifetimeCashEarned += FMath::Max(0, WeekCashDelta);
	if (WeekCashDelta > 0 && WeekDeaths == 0)
	{
		++SuccessfulWeeks;
	}

	EvaluateStoryGates();

	LastResultsSummary = FString::Printf(
		TEXT("Week %d closed. Cash %+d (total %d). Heat %d. Arrests %d. Deaths %d. Beat %d%s"),
		WeekIndex,
		WeekCashDelta,
		Cash,
		Heat,
		WeekArrests,
		WeekDeaths,
		StoryBeat,
		bBrickyardStubUnlocked ? TEXT(" | Brickyard stub unlocked") : TEXT(""));

	Phase = ELEWeekPhase::Results;
	TimeDilation = 1.f;
}

void ALEWeekDirector::EvaluateStoryGates()
{
	if (!bDockDemanded && SuccessfulWeeks >= 2 && LifetimeCashEarned >= 100)
	{
		bDockDemanded = true;
		StoryBeat = 1;
	}

	if (bDockDemanded && !bDockHeldForSal)
	{
		if (ALESiteActor* Dock = FindSite(TEXT("S03")))
		{
			if (Dock->OwnerFaction == ELEOwner::Player)
			{
				bDockHeldForSal = true;
				bBrickyardStubUnlocked = true;
			}
		}
	}
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
	Phase = ELEWeekPhase::Plan;
}

void ALEWeekDirector::ApplyHeatDecay()
{
	if (!bHadHitLastWeek && Heat > 0)
	{
		--Heat;
	}
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
	Lines += FString::Printf(TEXT("LOST EMPIRE  |  %s  |  Week %d\n"), *PhaseName, WeekIndex);
	Lines += FString::Printf(TEXT("Cash $%d   Heat %d/4   Beat %d\n"), Cash, Heat, StoryBeat);

	if (StoryBeat == 0)
	{
		Lines += TEXT("Beat 0: Collect Corvo Cafe, Watch Pell's.\n");
	}
	else if (bDockDemanded && !bDockHeldForSal)
	{
		Lines += TEXT("Sal wants Dock Warehouse A. Hold S03.\n");
	}
	else if (bBrickyardStubUnlocked)
	{
		Lines += TEXT("Brickyard stub unlocked on the map.\n");
	}

	if (Phase == ELEWeekPhase::Plan)
	{
		Lines += TEXT("1-3 hood  C/W/R/H order  Q/E site  Enter run week\n");
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
	PC->InputComponent->BindAction(TEXT("EmpireOrderCollect"), IE_Pressed, this, &ALEWeekDirector::InputOrderCollect);
	PC->InputComponent->BindAction(TEXT("EmpireOrderWatch"), IE_Pressed, this, &ALEWeekDirector::InputOrderWatch);
	PC->InputComponent->BindAction(TEXT("EmpireOrderRecruit"), IE_Pressed, this, &ALEWeekDirector::InputOrderRecruit);
	PC->InputComponent->BindAction(TEXT("EmpireOrderHit"), IE_Pressed, this, &ALEWeekDirector::InputOrderHit);
	PC->InputComponent->BindAction(TEXT("EmpireSitePrev"), IE_Pressed, this, &ALEWeekDirector::InputSitePrev);
	PC->InputComponent->BindAction(TEXT("EmpireSiteNext"), IE_Pressed, this, &ALEWeekDirector::InputSiteNext);
	PC->InputComponent->BindAction(TEXT("EmpireConfirm"), IE_Pressed, this, &ALEWeekDirector::InputConfirm);
	PC->InputComponent->BindAction(TEXT("EmpireSpeed"), IE_Pressed, this, &ALEWeekDirector::InputToggleSpeed);
	bInputBound = true;
}

void ALEWeekDirector::InputSelectHood1() { if (Phase == ELEWeekPhase::Plan) { SelectHoodIndex(0); } }
void ALEWeekDirector::InputSelectHood2() { if (Phase == ELEWeekPhase::Plan) { SelectHoodIndex(1); } }
void ALEWeekDirector::InputSelectHood3() { if (Phase == ELEWeekPhase::Plan) { SelectHoodIndex(2); } }
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
