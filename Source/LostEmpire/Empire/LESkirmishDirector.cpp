#include "LESkirmishDirector.h"

#include "LESiteActor.h"
#include "LESkirmishUnit.h"
#include "LEWeekDirector.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"
#include "Net/UnrealNetwork.h"

ALESkirmishDirector::ALESkirmishDirector()
{
	PrimaryActorTick.bCanEverTick = true;
	bReplicates = true;
	bAlwaysRelevant = true;
}

void ALESkirmishDirector::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(ALESkirmishDirector, Phase);
	DOREPLIFETIME(ALESkirmishDirector, Winner);
	DOREPLIFETIME(ALESkirmishDirector, BlueCash);
	DOREPLIFETIME(ALESkirmishDirector, RedCash);
	DOREPLIFETIME(ALESkirmishDirector, MajorityHoldTimer);
}

void ALESkirmishDirector::BeginPlay()
{
	Super::BeginPlay();
	DisableWeekDirector();
	GatherSites();
	if (HasAuthority())
	{
		AssignStartingBlocks();
		SpawnStartingUnits();
	}
	RefreshSiteColors();
	UE_LOG(LogTemp, Log, TEXT("Lost Empire skirmish — sites=%d cash Blue=%d Red=%d"),
		Sites.Num(), BlueCash, RedCash);
}

void ALESkirmishDirector::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	if (!HasAuthority() || Phase != ELESkirmishPhase::Playing)
	{
		return;
	}
	TickIncome(DeltaSeconds);
	TickCapture(DeltaSeconds);
	if (bSpawnAIOpponent)
	{
		TickAI(DeltaSeconds);
	}
	TickVictory(DeltaSeconds);
}

void ALESkirmishDirector::DisableWeekDirector()
{
	TArray<AActor*> Found;
	UGameplayStatics::GetAllActorsOfClass(GetWorld(), ALEWeekDirector::StaticClass(), Found);
	for (AActor* Actor : Found)
	{
		if (Actor)
		{
			Actor->SetActorTickEnabled(false);
			Actor->SetActorHiddenInGame(true);
			Actor->SetActorEnableCollision(false);
		}
	}
}

void ALESkirmishDirector::GatherSites()
{
	Sites.Reset();
	TArray<AActor*> Found;
	UGameplayStatics::GetAllActorsOfClass(GetWorld(), ALESiteActor::StaticClass(), Found);
	for (AActor* Actor : Found)
	{
		if (ALESiteActor* Site = Cast<ALESiteActor>(Actor))
		{
			Sites.Add(Site);
		}
	}
}

void ALESkirmishDirector::AssignStartingBlocks()
{
	if (Sites.Num() == 0)
	{
		return;
	}

	Sites.Sort([](const ALESiteActor& A, const ALESiteActor& B)
	{
		return A.GetActorLocation().Y < B.GetActorLocation().Y;
	});

	BlueSafeHouse = Sites[0];
	RedSafeHouse = Sites[Sites.Num() - 1];

	for (ALESiteActor* Site : Sites)
	{
		if (!Site)
		{
			continue;
		}
		Site->OwnerFaction = ELEOwner::Neutral;
	}

	if (BlueSafeHouse)
	{
		BlueSafeHouse->OwnerFaction = ELEOwner::Player;
		BlueSafeHouse->DisplayName = FText::FromString(TEXT("Blue Safe House"));
		BlueSafeHouse->CollectPayout = FMath::Max(12, BlueSafeHouse->CollectPayout);
	}
	if (RedSafeHouse)
	{
		RedSafeHouse->OwnerFaction = ELEOwner::Rival;
		RedSafeHouse->DisplayName = FText::FromString(TEXT("Red Safe House"));
		RedSafeHouse->CollectPayout = FMath::Max(12, RedSafeHouse->CollectPayout);
	}

	// Seed one extra block each toward mid-map so economy starts.
	if (Sites.Num() >= 4)
	{
		Sites[1]->OwnerFaction = ELEOwner::Player;
		Sites[Sites.Num() - 2]->OwnerFaction = ELEOwner::Rival;
	}
}

void ALESkirmishDirector::SpawnStartingUnits()
{
	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}

	auto SpawnAt = [&](ALESiteActor* Site, ELESkirmishTeam Team, ELESkirmishUnitRole InRole, const TCHAR* Name, float OffsetY)
	{
		if (!Site)
		{
			return;
		}
		const FVector Loc = Site->GetActorLocation() + FVector(120.f, OffsetY, 40.f);
		FActorSpawnParameters Params;
		Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;
		if (ALESkirmishUnit* Unit = World->SpawnActor<ALESkirmishUnit>(ALESkirmishUnit::StaticClass(), Loc, FRotator::ZeroRotator, Params))
		{
			Unit->Configure(Team, InRole, FText::FromString(Name));
			Units.Add(Unit);
		}
	};

	SpawnAt(BlueSafeHouse, ELESkirmishTeam::Blue, ELESkirmishUnitRole::Enforcer, TEXT("Nora"), -80.f);
	SpawnAt(BlueSafeHouse, ELESkirmishTeam::Blue, ELESkirmishUnitRole::Bagman, TEXT("Eddie"), 80.f);
	SpawnAt(RedSafeHouse, ELESkirmishTeam::Red, ELESkirmishUnitRole::Enforcer, TEXT("Harlan"), -80.f);
	SpawnAt(RedSafeHouse, ELESkirmishTeam::Red, ELESkirmishUnitRole::Bagman, TEXT("Vince"), 80.f);
}

bool ALESkirmishDirector::TryTrainUnit(ELESkirmishTeam Team, ELESkirmishUnitRole InRole)
{
	if (!HasAuthority() || Phase != ELESkirmishPhase::Playing)
	{
		return false;
	}

	const int32 Cost = InRole == ELESkirmishUnitRole::Bagman ? TrainBagmanCost : TrainEnforcerCost;
	int32& Cash = CashRef(Team);
	if (Cash < Cost)
	{
		return false;
	}

	ALESiteActor* House = FindSafeHouse(Team);
	if (!House || !GetWorld())
	{
		return false;
	}

	Cash -= Cost;
	const int32 Serial = (Team == ELESkirmishTeam::Blue) ? ++BlueTrainCount : ++RedTrainCount;
	const FString Name = InRole == ELESkirmishUnitRole::Bagman
		? FString::Printf(TEXT("Bagman %d"), Serial)
		: FString::Printf(TEXT("Enforcer %d"), Serial);

	const FVector Loc = House->GetActorLocation() + FVector(180.f + Serial * 40.f, Serial * 35.f, 40.f);
	FActorSpawnParameters Params;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;
	if (ALESkirmishUnit* Unit = GetWorld()->SpawnActor<ALESkirmishUnit>(ALESkirmishUnit::StaticClass(), Loc, FRotator::ZeroRotator, Params))
	{
		Unit->Configure(Team, InRole, FText::FromString(Name));
		Units.Add(Unit);
		return true;
	}
	return false;
}

void ALESkirmishDirector::SelectUnit(ALESkirmishUnit* Unit, ELESkirmishTeam ForTeam)
{
	if (!Unit || !Unit->IsAlive() || Unit->Team != ForTeam)
	{
		return;
	}
	if (ALESkirmishUnit* Prev = GetSelectedUnit(ForTeam))
	{
		Prev->SetSelected(false);
	}
	if (ForTeam == ELESkirmishTeam::Blue)
	{
		SelectedBlue = Unit;
	}
	else
	{
		SelectedRed = Unit;
	}
	Unit->SetSelected(true);
}

void ALESkirmishDirector::ClearSelection(ELESkirmishTeam ForTeam)
{
	if (ALESkirmishUnit* Prev = GetSelectedUnit(ForTeam))
	{
		Prev->SetSelected(false);
	}
	if (ForTeam == ELESkirmishTeam::Blue)
	{
		SelectedBlue = nullptr;
	}
	else
	{
		SelectedRed = nullptr;
	}
}

void ALESkirmishDirector::CommandSelectedMove(ELESkirmishTeam Team, FVector WorldLocation)
{
	if (ALESkirmishUnit* Unit = GetSelectedUnit(Team))
	{
		Unit->CommandMoveTo(WorldLocation);
	}
}

void ALESkirmishDirector::CommandSelectedAttack(ELESkirmishTeam Team, ALESkirmishUnit* Target)
{
	if (ALESkirmishUnit* Unit = GetSelectedUnit(Team))
	{
		Unit->CommandAttack(Target);
	}
}

ALESkirmishUnit* ALESkirmishDirector::GetSelectedUnit(ELESkirmishTeam Team) const
{
	return Team == ELESkirmishTeam::Blue ? SelectedBlue.Get() : SelectedRed.Get();
}

int32 ALESkirmishDirector::CountOwnedSites(ELESkirmishTeam Team) const
{
	const ELEOwner Wanted = static_cast<ELEOwner>(TeamToOwner(Team));
	int32 Count = 0;
	for (const ALESiteActor* Site : Sites)
	{
		if (Site && Site->OwnerFaction == Wanted)
		{
			++Count;
		}
	}
	return Count;
}

void ALESkirmishDirector::TickIncome(float DeltaSeconds)
{
	IncomeTimer += DeltaSeconds;
	if (IncomeTimer < IncomeInterval)
	{
		return;
	}
	IncomeTimer = 0.f;

	for (ALESiteActor* Site : Sites)
	{
		if (!Site)
		{
			continue;
		}
		const int32 Pay = FMath::Max(8, Site->CollectPayout > 0 ? Site->CollectPayout : 10);
		if (Site->OwnerFaction == ELEOwner::Player)
		{
			BlueCash += Pay;
		}
		else if (Site->OwnerFaction == ELEOwner::Rival)
		{
			RedCash += Pay;
		}
	}
}

void ALESkirmishDirector::TickCapture(float DeltaSeconds)
{
	TArray<AActor*> FoundUnits;
	UGameplayStatics::GetAllActorsOfClass(GetWorld(), ALESkirmishUnit::StaticClass(), FoundUnits);
	Units.Reset();
	for (AActor* Actor : FoundUnits)
	{
		if (ALESkirmishUnit* Unit = Cast<ALESkirmishUnit>(Actor))
		{
			if (Unit->IsAlive())
			{
				Units.Add(Unit);
			}
		}
	}

	for (ALESiteActor* Site : Sites)
	{
		if (!Site)
		{
			continue;
		}

		ELESkirmishTeam Contester = ELESkirmishTeam::None;
		int32 BlueNear = 0;
		int32 RedNear = 0;
		for (ALESkirmishUnit* Unit : Units)
		{
			if (!Unit || !Unit->IsAlive())
			{
				continue;
			}
			if (FVector::Dist2D(Unit->GetActorLocation(), Site->GetActorLocation()) > 280.f)
			{
				continue;
			}
			if (Unit->Team == ELESkirmishTeam::Blue)
			{
				++BlueNear;
			}
			else if (Unit->Team == ELESkirmishTeam::Red)
			{
				++RedNear;
			}
		}

		if (BlueNear > 0 && RedNear == 0)
		{
			Contester = ELESkirmishTeam::Blue;
		}
		else if (RedNear > 0 && BlueNear == 0)
		{
			Contester = ELESkirmishTeam::Red;
		}

		const ELESkirmishTeam Current = OwnerToTeam(static_cast<uint8>(Site->OwnerFaction));
		if (Contester == ELESkirmishTeam::None || Contester == Current)
		{
			CaptureProgress.Remove(Site->SiteId);
			CaptureTeam.Remove(Site->SiteId);
			continue;
		}

		if (!CaptureTeam.Contains(Site->SiteId) || CaptureTeam[Site->SiteId] != Contester)
		{
			CaptureTeam.Add(Site->SiteId, Contester);
			CaptureProgress.Add(Site->SiteId, 0.f);
		}

		float& Progress = CaptureProgress.FindOrAdd(Site->SiteId);
		Progress += DeltaSeconds;
		if (Progress >= CaptureSeconds)
		{
			Site->OwnerFaction = static_cast<ELEOwner>(TeamToOwner(Contester));
			Site->RefreshColor();
			CaptureProgress.Remove(Site->SiteId);
			CaptureTeam.Remove(Site->SiteId);

			// Capturing the enemy safe house wins immediately.
			if (Site == BlueSafeHouse && Contester == ELESkirmishTeam::Red)
			{
				DeclareWinner(ELESkirmishTeam::Red);
				return;
			}
			if (Site == RedSafeHouse && Contester == ELESkirmishTeam::Blue)
			{
				DeclareWinner(ELESkirmishTeam::Blue);
				return;
			}
		}
	}
}

void ALESkirmishDirector::TickAI(float DeltaSeconds)
{
	AITimer += DeltaSeconds;
	if (AITimer < 2.2f)
	{
		return;
	}
	AITimer = 0.f;

	// Train if rich.
	if (RedCash >= TrainEnforcerCost + 20)
	{
		TryTrainUnit(ELESkirmishTeam::Red, ELESkirmishUnitRole::Enforcer);
	}
	else if (RedCash >= TrainBagmanCost)
	{
		TryTrainUnit(ELESkirmishTeam::Red, ELESkirmishUnitRole::Bagman);
	}

	// Idle red units push toward nearest unowned / blue site, or attack nearest blue unit.
	for (ALESkirmishUnit* Unit : Units)
	{
		if (!Unit || Unit->Team != ELESkirmishTeam::Red || !Unit->IsAlive())
		{
			continue;
		}
		if (Unit->AttackTarget && Unit->AttackTarget->IsAlive())
		{
			continue;
		}

		ALESkirmishUnit* BestEnemy = nullptr;
		float BestEnemyDist = TNumericLimits<float>::Max();
		for (ALESkirmishUnit* Other : Units)
		{
			if (!Other || Other->Team != ELESkirmishTeam::Blue || !Other->IsAlive())
			{
				continue;
			}
			const float D = FVector::Dist2D(Unit->GetActorLocation(), Other->GetActorLocation());
			if (D < BestEnemyDist)
			{
				BestEnemyDist = D;
				BestEnemy = Other;
			}
		}
		if (BestEnemy && BestEnemyDist < 900.f)
		{
			Unit->CommandAttack(BestEnemy);
			continue;
		}

		ALESiteActor* BestSite = nullptr;
		float BestSiteDist = TNumericLimits<float>::Max();
		for (ALESiteActor* Site : Sites)
		{
			if (!Site || Site->OwnerFaction == ELEOwner::Rival)
			{
				continue;
			}
			const float D = FVector::Dist2D(Unit->GetActorLocation(), Site->GetActorLocation());
			if (D < BestSiteDist)
			{
				BestSiteDist = D;
				BestSite = Site;
			}
		}
		if (BestSite)
		{
			Unit->CommandMoveTo(BestSite->GetActorLocation());
		}
	}
}

void ALESkirmishDirector::TickVictory(float DeltaSeconds)
{
	const int32 Total = Sites.Num();
	if (Total <= 0)
	{
		return;
	}
	const int32 Need = FMath::Max(1, (Total * 5 + 7) / 8); // ceil(5/8 * N) style for N sites
	const int32 Blue = CountOwnedSites(ELESkirmishTeam::Blue);
	const int32 Red = CountOwnedSites(ELESkirmishTeam::Red);

	if (Blue >= Need)
	{
		MajorityHoldTimer += DeltaSeconds;
		if (MajorityHoldTimer >= MajorityHoldRequired)
		{
			DeclareWinner(ELESkirmishTeam::Blue);
		}
	}
	else if (Red >= Need)
	{
		MajorityHoldTimer += DeltaSeconds;
		if (MajorityHoldTimer >= MajorityHoldRequired)
		{
			DeclareWinner(ELESkirmishTeam::Red);
		}
	}
	else
	{
		MajorityHoldTimer = FMath::Max(0.f, MajorityHoldTimer - DeltaSeconds * 0.5f);
	}

	// Wipe: no living units on a team and safe house lost already handled; also wipe if no units + no cash path.
	int32 BlueAlive = 0;
	int32 RedAlive = 0;
	for (ALESkirmishUnit* Unit : Units)
	{
		if (!Unit || !Unit->IsAlive())
		{
			continue;
		}
		if (Unit->Team == ELESkirmishTeam::Blue)
		{
			++BlueAlive;
		}
		else
		{
			++RedAlive;
		}
	}
	if (BlueAlive == 0 && BlueCash < TrainBagmanCost)
	{
		DeclareWinner(ELESkirmishTeam::Red);
	}
	else if (RedAlive == 0 && RedCash < TrainBagmanCost)
	{
		DeclareWinner(ELESkirmishTeam::Blue);
	}
}

void ALESkirmishDirector::DeclareWinner(ELESkirmishTeam Team)
{
	if (Phase != ELESkirmishPhase::Playing)
	{
		return;
	}
	Winner = Team;
	Phase = Team == ELESkirmishTeam::Blue ? ELESkirmishPhase::Victory : ELESkirmishPhase::Defeat;
	UE_LOG(LogTemp, Log, TEXT("SKIRMISH WINNER %s"), Team == ELESkirmishTeam::Blue ? TEXT("Blue") : TEXT("Red"));
}

ALESiteActor* ALESkirmishDirector::FindSafeHouse(ELESkirmishTeam Team) const
{
	return Team == ELESkirmishTeam::Blue ? BlueSafeHouse.Get() : RedSafeHouse.Get();
}

ELESkirmishTeam ALESkirmishDirector::OwnerToTeam(uint8 InOwner) const
{
	if (InOwner == static_cast<uint8>(ELEOwner::Player))
	{
		return ELESkirmishTeam::Blue;
	}
	if (InOwner == static_cast<uint8>(ELEOwner::Rival))
	{
		return ELESkirmishTeam::Red;
	}
	return ELESkirmishTeam::None;
}

uint8 ALESkirmishDirector::TeamToOwner(ELESkirmishTeam Team) const
{
	if (Team == ELESkirmishTeam::Blue)
	{
		return static_cast<uint8>(ELEOwner::Player);
	}
	if (Team == ELESkirmishTeam::Red)
	{
		return static_cast<uint8>(ELEOwner::Rival);
	}
	return static_cast<uint8>(ELEOwner::Neutral);
}

int32& ALESkirmishDirector::CashRef(ELESkirmishTeam Team)
{
	return Team == ELESkirmishTeam::Blue ? BlueCash : RedCash;
}

void ALESkirmishDirector::RefreshSiteColors()
{
	for (ALESiteActor* Site : Sites)
	{
		if (Site)
		{
			Site->RefreshColor();
		}
	}
}

FText ALESkirmishDirector::GetHudBlock() const
{
	const int32 BlueSites = CountOwnedSites(ELESkirmishTeam::Blue);
	const int32 RedSites = CountOwnedSites(ELESkirmishTeam::Red);
	const int32 Need = Sites.Num() > 0 ? FMath::Max(1, (Sites.Num() * 5 + 7) / 8) : 5;

	FString PhaseName = TEXT("SKIRMISH");
	if (Phase == ELESkirmishPhase::Victory)
	{
		PhaseName = TEXT("BLUE WINS");
	}
	else if (Phase == ELESkirmishPhase::Defeat)
	{
		PhaseName = Winner == ELESkirmishTeam::Red ? TEXT("RED WINS") : TEXT("DEFEAT");
	}

	FString Selected = TEXT("none");
	if (SelectedBlue)
	{
		Selected = SelectedBlue->GetName();
	}

	return FText::FromString(FString::Printf(
		TEXT("LOST EMPIRE — RTS SKIRMISH\n%s\nBlue $%d  sites %d/%d\nRed  $%d  sites %d/%d\nMajority hold %.0f / %.0fs (need %d)\nSelected: %s\nLMB select  RMB move/attack\nN enforcer ($%d)  M bagman ($%d)\nListen-server: host + join; AI fills Red."),
		*PhaseName,
		BlueCash, BlueSites, Sites.Num(),
		RedCash, RedSites, Sites.Num(),
		MajorityHoldTimer, MajorityHoldRequired, Need,
		*Selected,
		TrainEnforcerCost, TrainBagmanCost));
}
