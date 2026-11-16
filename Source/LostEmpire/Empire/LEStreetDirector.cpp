#include "LEStreetDirector.h"

#include "LECivilianCharacter.h"
#include "LEHoodAgent.h"
#include "LEHoodlumCharacter.h"
#include "LESiteActor.h"
#include "LEStreetCar.h"
#include "LEWeekDirector.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "InputCoreTypes.h"
#include "Kismet/GameplayStatics.h"

ALEStreetDirector::ALEStreetDirector()
{
	PrimaryActorTick.bCanEverTick = true;
}

void ALEStreetDirector::BeginPlay()
{
	Super::BeginPlay();
	Week = Cast<ALEWeekDirector>(
		UGameplayStatics::GetActorOfClass(GetWorld(), ALEWeekDirector::StaticClass()));
	BootstrapStreetCast();
	RefreshMissionBrief();
	BindInput();
	UE_LOG(LogTemp, Log, TEXT("Lost Empire street — free move + missions. Active %d"),
		static_cast<int32>(ActiveMission));
}

void ALEStreetDirector::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	if (!bInputBound)
	{
		BindInput();
	}
	if (!bBootstrapped)
	{
		BootstrapStreetCast();
	}

	// Poll mouse with edge detect — works even when action mappings / CommonUI flake
	if (APlayerController* PC = UGameplayStatics::GetPlayerController(GetWorld(), 0))
	{
		PC->bShowMouseCursor = true;
		const bool bLMB = PC->IsInputKeyDown(EKeys::LeftMouseButton);
		const bool bRMB = PC->IsInputKeyDown(EKeys::RightMouseButton);
		static bool bWasLMB = false;
		static bool bWasRMB = false;
		if (bLMB && !bWasLMB)
		{
			OnSelectPressed();
		}
		if (bRMB && !bWasRMB)
		{
			OnCancelPressed();
		}
		bWasLMB = bLMB;
		bWasRMB = bRMB;
		if (PC->WasInputKeyJustPressed(EKeys::One)) { OnArmEnterBuilding(); }
		if (PC->WasInputKeyJustPressed(EKeys::Two)) { OnArmEnterCar(); }
		if (PC->WasInputKeyJustPressed(EKeys::Three)) { OnArmScout(); }
		if (PC->WasInputKeyJustPressed(EKeys::Four)) { OnArmHitAndRun(); }
		if (PC->WasInputKeyJustPressed(EKeys::Five)) { OnArmDriveBy(); }
	}

	MissionCheckTimer += DeltaSeconds;
	if (MissionCheckTimer >= 0.75f)
	{
		MissionCheckTimer = 0.f;
		EvaluateMission();
	}

	// Keep selected hood patrolling so walk bob / facing stay visible in playtests
	static float PatrolTimer = 0.f;
	PatrolTimer += DeltaSeconds;
	if (SelectedHoodlum && PatrolTimer >= 4.0f && !SelectedHoodlum->HasGoal())
	{
		PatrolTimer = 0.f;
		const float Axes[] = { -1200.f, 0.f, 1200.f };
		const FVector Dest(
			Axes[FMath::RandRange(0, 2)] + FMath::FRandRange(-200.f, 200.f),
			Axes[FMath::RandRange(0, 2)] + FMath::FRandRange(-200.f, 200.f),
			110.f);
		SelectedHoodlum->IssueScout(Dest);
		UE_LOG(LogTemp, Warning, TEXT("PATROL %s -> %s"), *SelectedHoodlum->HoodId.ToString(), *Dest.ToCompactString());
	}

	// Resolve finished street orders into economy.
	for (ALEHoodlumCharacter* Hood : Hoodlums)
	{
		if (!Hood)
		{
			continue;
		}
		if (Hood->OrderState == ELEAssignmentState::Done
			|| (Hood->bInBuilding && Hood->OrderState == ELEAssignmentState::Working))
		{
			ApplyOrderResult(Hood);
		}
	}
}

void ALEStreetDirector::BindInput()
{
	APlayerController* PC = UGameplayStatics::GetPlayerController(GetWorld(), 0);
	if (!PC || !PC->InputComponent)
	{
		return;
	}
	PC->bShowMouseCursor = true;
	PC->bEnableClickEvents = true;
	PC->bEnableMouseOverEvents = true;
	// GameOnly so UMG parchment doesn't swallow street LMB
	FInputModeGameOnly Mode;
	Mode.SetConsumeCaptureMouseDown(false);
	PC->SetInputMode(Mode);

	PC->InputComponent->BindAction(TEXT("StreetSelect"), IE_Pressed, this, &ALEStreetDirector::OnSelectPressed);
	PC->InputComponent->BindAction(TEXT("StreetCancel"), IE_Pressed, this, &ALEStreetDirector::OnCancelPressed);
	PC->InputComponent->BindAction(TEXT("StreetScout"), IE_Pressed, this, &ALEStreetDirector::OnArmScout);
	PC->InputComponent->BindAction(TEXT("StreetEnterBuilding"), IE_Pressed, this, &ALEStreetDirector::OnArmEnterBuilding);
	PC->InputComponent->BindAction(TEXT("StreetEnterCar"), IE_Pressed, this, &ALEStreetDirector::OnArmEnterCar);
	PC->InputComponent->BindAction(TEXT("StreetHitRun"), IE_Pressed, this, &ALEStreetDirector::OnArmHitAndRun);
	PC->InputComponent->BindAction(TEXT("StreetDriveBy"), IE_Pressed, this, &ALEStreetDirector::OnArmDriveBy);
	bInputBound = true;
}

void ALEStreetDirector::BootstrapStreetCast()
{
	if (!GetWorld())
	{
		return;
	}

	Sites.Reset();
	TArray<AActor*> FoundSites;
	UGameplayStatics::GetAllActorsOfClass(GetWorld(), ALESiteActor::StaticClass(), FoundSites);
	for (AActor* A : FoundSites)
	{
		if (ALESiteActor* S = Cast<ALESiteActor>(A))
		{
			Sites.Add(S);
		}
	}

	HideLegacyHoodAgents();

	if (Hoodlums.Num() == 0)
	{
		SpawnHoodlumsFromSites();
	}
	if (Civilians.Num() == 0)
	{
		SpawnCivilians();
	}
	if (Cars.Num() == 0)
	{
		SpawnCars();
	}

	bBootstrapped = Hoodlums.Num() > 0;
}

void ALEStreetDirector::HideLegacyHoodAgents()
{
	TArray<AActor*> Found;
	UGameplayStatics::GetAllActorsOfClass(GetWorld(), ALEHoodAgent::StaticClass(), Found);
	for (AActor* A : Found)
	{
		if (A)
		{
			A->SetActorHiddenInGame(true);
			A->SetActorEnableCollision(false);
			A->SetActorTickEnabled(false);
		}
	}
}

void ALEStreetDirector::SpawnHoodlumsFromSites()
{
	struct FSpawn
	{
		const TCHAR* Id;
		const TCHAR* Name;
		ELEHoodRole Role;
		ELEOwner Faction;
		int32 Loyalty;
		FVector Loc;
		const TCHAR* SpriteMat;
	};

	// Curbs: State & 18th (player), Clark & Cermak (rival Levee) — 1200uu grid
	// Z above road curb (~-28) + capsule half-height so feet sit on asphalt
	const FSpawn Spawns[] = {
		{ TEXT("H01"), TEXT("Eddie Voss"), ELEHoodRole::Bagman, ELEOwner::Player, 60,
			FVector(120.f, -120.f, 110.f), nullptr },
		{ TEXT("H02"), TEXT("Nicky Ferro"), ELEHoodRole::Enforcer, ELEOwner::Player, 50,
			FVector(280.f, 120.f, 110.f), nullptr },
		{ TEXT("H03"), TEXT("Nora Pell"), ELEHoodRole::Recruiter, ELEOwner::Player, 70,
			FVector(-160.f, 160.f, 110.f), nullptr },
		{ TEXT("R01"), TEXT("Quinn"), ELEHoodRole::Enforcer, ELEOwner::Rival, 40,
			FVector(-2280.f, -1320.f, 110.f), nullptr },
		{ TEXT("R02"), TEXT("Bridget"), ELEHoodRole::Bagman, ELEOwner::Rival, 45,
			FVector(-2100.f, -1080.f, 110.f), nullptr },
	};

	FActorSpawnParameters Params;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	for (const FSpawn& S : Spawns)
	{
		ALEHoodlumCharacter* H = GetWorld()->SpawnActor<ALEHoodlumCharacter>(
			ALEHoodlumCharacter::StaticClass(), S.Loc, FRotator::ZeroRotator, Params);
		if (!H)
		{
			UE_LOG(LogTemp, Error, TEXT("HOOD SPAWN FAIL %s at %s"), S.Id, *S.Loc.ToString());
			continue;
		}
		H->ConfigureHoodlum(S.Id, FText::FromString(S.Name), static_cast<uint8>(S.Role),
			static_cast<uint8>(S.Faction), S.Loyalty);
		H->SetActorHiddenInGame(false);
		H->SetActorEnableCollision(true);
		H->SetActorScale3D(FVector(1.2f)); // street-readable silhouette
		UE_LOG(LogTemp, Warning, TEXT("HOOD SPAWN OK %s loc=%s"), S.Id, *H->GetActorLocation().ToString());
		Hoodlums.Add(H);
	}
	UE_LOG(LogTemp, Warning, TEXT("HOOD CAST size=%d"), Hoodlums.Num());

	// Auto-demo walk so street movement is visible without fighting UI focus
	if (Hoodlums.Num() > 0 && Hoodlums[0])
	{
		SelectHoodlum(Hoodlums[0]);
		Hoodlums[0]->IssueScout(FVector(900.f, 700.f, 110.f));
		UE_LOG(LogTemp, Warning, TEXT("AUTO WALK %s toward 900,700"), *Hoodlums[0]->HoodId.ToString());
	}
}

void ALEStreetDirector::SpawnCivilians()
{
	// Gangsters-density sidewalk crowd — enough variety to watch wander / panic reactions.
	// Curbs + mid-block walks on the 1200uu Near South grid (keep center intersection open).
	TArray<FVector> Spots;
	const float Z = 110.f;
	const float Avenues[] = { -2400.f, -1200.f, 0.f, 1200.f, 2400.f };
	const float Streets[] = { -2400.f, -1200.f, 0.f, 1200.f, 2400.f };
	for (float X : Avenues)
	{
		for (float Y : Streets)
		{
			// Skip exact crossroads center so orders stay readable
			if (FMath::IsNearlyZero(X) && FMath::IsNearlyZero(Y))
			{
				continue;
			}
			// NE / SW curb offsets per intersection
			Spots.Add(FVector(X + 180.f, Y + 220.f, Z));
			Spots.Add(FVector(X - 200.f, Y - 180.f, Z));
			if (FMath::RandBool())
			{
				Spots.Add(FVector(X + FMath::FRandRange(-90.f, 90.f), Y + 400.f, Z));
			}
		}
	}
	// Extra mid-block wanderers on State / Michigan / Clark
	const FVector Extras[] = {
		FVector(80.f, 700.f, Z), FVector(-90.f, -750.f, Z), FVector(1300.f, 350.f, Z),
		FVector(1250.f, -400.f, Z), FVector(-1300.f, 450.f, Z), FVector(-1250.f, -500.f, Z),
		FVector(2350.f, 200.f, Z), FVector(2450.f, -900.f, Z), FVector(-2350.f, -900.f, Z),
		FVector(600.f, 50.f, Z), FVector(-600.f, -80.f, Z), FVector(1800.f, 600.f, Z),
		FVector(-1800.f, -600.f, Z), FVector(900.f, -1200.f, Z), FVector(-900.f, 1200.f, Z),
	};
	for (const FVector& E : Extras)
	{
		Spots.Add(E);
	}

	FActorSpawnParameters Params;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	int32 CivOk = 0;
	for (const FVector& Loc : Spots)
	{
		if (ALECivilianCharacter* C = GetWorld()->SpawnActor<ALECivilianCharacter>(
				ALECivilianCharacter::StaticClass(), Loc, FRotator::ZeroRotator, Params))
		{
			C->SetActorHiddenInGame(false);
			C->SetActorScale3D(FVector(1.1f));
			Civilians.Add(C);
			++CivOk;
		}
	}
	UE_LOG(LogTemp, Warning, TEXT("CIV SPAWN ok=%d"), CivOk);
}

void ALEStreetDirector::SpawnCars()
{
	// Curb lane — YOUR ElevenLabs car plates via sprite materials
	struct FCarSpot
	{
		FVector Loc;
		const TCHAR* Name;
		FLinearColor Paint;
		const TCHAR* SpriteMat;
	};
	// Bright period paints on 3D chassis — no sprite plates (dark ortho smears)
	const FCarSpot Spots[] = {
		{ FVector(140.f, -280.f, 50.f), TEXT("Eddie's Packard"), FLinearColor(0.12f, 0.12f, 0.16f), nullptr },
		{ FVector(-2400.f, -1100.f, 50.f), TEXT("Harlan Sedan"), FLinearColor(0.42f, 0.10f, 0.12f), nullptr },
		{ FVector(2400.f, 200.f, 50.f), TEXT("Curbside Ford"), FLinearColor(0.18f, 0.32f, 0.20f), nullptr },
		{ FVector(1200.f, -140.f, 50.f), TEXT("Model A"), FLinearColor(0.16f, 0.36f, 0.22f), nullptr },
		{ FVector(-1200.f, 400.f, 50.f), TEXT("Yellow Cab"), FLinearColor(0.85f, 0.72f, 0.12f), nullptr },
		{ FVector(1800.f, -900.f, 55.f), TEXT("Stake Truck"), FLinearColor(0.22f, 0.34f, 0.24f), nullptr },
		{ FVector(-600.f, 2400.f, 50.f), TEXT("Police Cruiser"), FLinearColor(0.18f, 0.20f, 0.28f), nullptr },
	};
	FActorSpawnParameters Params;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	for (const FCarSpot& Spot : Spots)
	{
		if (ALEStreetCar* Car = GetWorld()->SpawnActor<ALEStreetCar>(
				ALEStreetCar::StaticClass(), Spot.Loc, FRotator(0.f, 0.f, 0.f), Params))
		{
			Car->DisplayName = FText::FromString(Spot.Name);
			Car->CarId = Spot.Name;
			Car->BodyPaint = Spot.Paint;
			Car->RoadZ = 50.f;
			Cars.Add(Car);
		}
	}
}

void ALEStreetDirector::ArmOrder(ELEStreetOrder Order)
{
	ArmedOrder = Order;
}

void ALEStreetDirector::SelectHoodlum(ALEHoodlumCharacter* Hood)
{
	if (!Hood || Hood->Faction != ELEOwner::Player)
	{
		return;
	}
	if (SelectedHoodlum)
	{
		SelectedHoodlum->SetSelected(false);
	}
	SelectedHoodlum = Hood;
	Hood->SetSelected(true);
	UpdateCornerLabel(Hood->GetActorLocation());
}

void ALEStreetDirector::ClearSelection()
{
	if (SelectedHoodlum)
	{
		SelectedHoodlum->SetSelected(false);
	}
	SelectedHoodlum = nullptr;
	ArmedOrder = ELEStreetOrder::None;
}

bool ALEStreetDirector::TraceCursor(FHitResult& OutHit) const
{
	APlayerController* PC = UGameplayStatics::GetPlayerController(GetWorld(), 0);
	if (!PC)
	{
		return false;
	}
	FVector Origin, Dir;
	if (!PC->DeprojectMousePositionToWorld(Origin, Dir))
	{
		return false;
	}
	const FVector End = Origin + Dir * 100000.f;
	FCollisionQueryParams Params(SCENE_QUERY_STAT(StreetTrace), true);
	if (GetWorld()->LineTraceSingleByChannel(OutHit, Origin, End, ECC_Visibility, Params))
	{
		return true;
	}
	// Ground plane Z~0 for ortho misses
	if (!FMath::IsNearlyZero(Dir.Z))
	{
		const float T = -Origin.Z / Dir.Z;
		OutHit.ImpactPoint = Origin + Dir * T;
		OutHit.bBlockingHit = true;
		return true;
	}
	return false;
}

void ALEStreetDirector::UpdateCornerLabel(FVector WorldPos)
{
	const bool bEast = WorldPos.X >= 0.f;
	const bool bNorth = WorldPos.Y >= 0.f;
	const TCHAR* A = bEast ? TEXT("FREIGHT AVE") : TEXT("HAWSER RD");
	const TCHAR* B = bNorth ? TEXT("BOARDWALK") : TEXT("WHARF ST");
	CornerLabel = FString::Printf(TEXT("On the corner of %s & %s"), A, B);
}

void ALEStreetDirector::OnSelectPressed()
{
	FHitResult Hit;
	if (!TraceCursor(Hit))
	{
		return;
	}

	AActor* HitActor = Hit.GetActor();
	if (!HitActor && Hit.GetComponent())
	{
		HitActor = Hit.GetComponent()->GetOwner();
	}

	// Ortho clicks often miss thin capsules — pick nearest player hood in 220uu
	ALEHoodlumCharacter* Hood = Cast<ALEHoodlumCharacter>(HitActor);
	if (!Hood)
	{
		float BestDistSq = 220.f * 220.f;
		for (ALEHoodlumCharacter* Candidate : Hoodlums)
		{
			if (!Candidate || Candidate->Faction != ELEOwner::Player)
			{
				continue;
			}
			const float DistSq = FVector::DistSquared2D(Candidate->GetActorLocation(), Hit.ImpactPoint);
			if (DistSq < BestDistSq)
			{
				BestDistSq = DistSq;
				Hood = Candidate;
			}
		}
		// Only auto-pick when click is near a hood (not a far ground command)
		if (Hood && BestDistSq > 180.f * 180.f)
		{
			Hood = nullptr;
		}
	}

	if (Hood)
	{
		if (Hood->Faction == ELEOwner::Player)
		{
			SelectHoodlum(Hood);
			UE_LOG(LogTemp, Warning, TEXT("SELECTED %s"), *Hood->HoodId.ToString());
			return;
		}
		if (SelectedHoodlum && ArmedOrder == ELEStreetOrder::HitAndRun)
		{
			SelectedHoodlum->IssueHitAndRun(Hood);
			ArmedOrder = ELEStreetOrder::None;
			NotifyViolenceAt(Hood->GetActorLocation());
			return;
		}
		if (SelectedHoodlum && ArmedOrder == ELEStreetOrder::DriveBy)
		{
			SelectedHoodlum->IssueDriveBy(Hood);
			ArmedOrder = ELEStreetOrder::None;
			NotifyViolenceAt(Hood->GetActorLocation());
			return;
		}
	}

	if (!SelectedHoodlum)
	{
		return;
	}

	if (ArmedOrder == ELEStreetOrder::EnterBuilding || ArmedOrder == ELEStreetOrder::None)
	{
		if (ALESiteActor* Site = Cast<ALESiteActor>(HitActor))
		{
			SelectedHoodlum->IssueEnterBuilding(Site);
			ArmedOrder = ELEStreetOrder::None;
			UpdateCornerLabel(Site->GetActorLocation());
			return;
		}
	}

	if (ArmedOrder == ELEStreetOrder::EnterCar || SelectedHoodlum->bInCar == false)
	{
		if (ALEStreetCar* Car = Cast<ALEStreetCar>(HitActor))
		{
			if (ArmedOrder == ELEStreetOrder::EnterCar || ArmedOrder == ELEStreetOrder::None)
			{
				SelectedHoodlum->IssueEnterCar(Car);
				ArmedOrder = ELEStreetOrder::None;
				return;
			}
		}
	}

	if (SelectedHoodlum->bInCar && ArmedOrder == ELEStreetOrder::DriveBy)
	{
		if (ALESiteActor* Site = Cast<ALESiteActor>(HitActor))
		{
			SelectedHoodlum->IssueDriveBy(Site);
			ArmedOrder = ELEStreetOrder::None;
			NotifyViolenceAt(Site->GetActorLocation());
			return;
		}
	}

	if (ArmedOrder == ELEStreetOrder::HitAndRun)
	{
		if (ALESiteActor* Site = Cast<ALESiteActor>(HitActor))
		{
			SelectedHoodlum->IssueHitAndRun(Site);
			ArmedOrder = ELEStreetOrder::None;
			NotifyViolenceAt(Site->GetActorLocation());
			return;
		}
	}

	// Default / scout: free move on curb plane
	FVector Dest = Hit.ImpactPoint;
	Dest.Z = 110.f;
	SelectedHoodlum->IssueScout(Dest);
	UE_LOG(LogTemp, Warning, TEXT("MOVE %s -> %s"), *SelectedHoodlum->HoodId.ToString(), *Dest.ToCompactString());
	ArmedOrder = ELEStreetOrder::None;
	UpdateCornerLabel(Dest);
}

void ALEStreetDirector::OnCancelPressed()
{
	if (SelectedHoodlum)
	{
		SelectedHoodlum->CancelStreetOrder();
	}
	ArmedOrder = ELEStreetOrder::None;
}

void ALEStreetDirector::OnArmScout() { ArmOrder(ELEStreetOrder::MoveScout); }
void ALEStreetDirector::OnArmEnterBuilding() { ArmOrder(ELEStreetOrder::EnterBuilding); }
void ALEStreetDirector::OnArmEnterCar() { ArmOrder(ELEStreetOrder::EnterCar); }
void ALEStreetDirector::OnArmHitAndRun() { ArmOrder(ELEStreetOrder::HitAndRun); }
void ALEStreetDirector::OnArmDriveBy() { ArmOrder(ELEStreetOrder::DriveBy); }

void ALEStreetDirector::NotifyViolenceAt(FVector Location)
{
	for (ALECivilianCharacter* C : Civilians)
	{
		if (C && FVector::Dist2D(C->GetActorLocation(), Location) < 1600.f)
		{
			C->PanicFlee(Location);
		}
	}
	if (Week)
	{
		Week->Heat = FMath::Min(4, Week->Heat + 1);
	}
}

void ALEStreetDirector::ApplyOrderResult(ALEHoodlumCharacter* Hood)
{
	if (!Hood)
	{
		return;
	}
	// Always clear Done → Idle so street patrols / new orders can resume
	if (Hood->OrderState == ELEAssignmentState::Done && Hood->Faction == ELEOwner::Player
		&& !(Hood->bInBuilding && Hood->GetOccupiedSite()))
	{
		Hood->OrderState = ELEAssignmentState::Idle;
	}
	if (!Week)
	{
		return;
	}

	if (Hood->bInBuilding && Hood->GetOccupiedSite()
		&& Hood->OrderState == ELEAssignmentState::Working
		&& Hood->Faction == ELEOwner::Player)
	{
		ALESiteActor* Site = Hood->GetOccupiedSite();
		// Passive collect while inside owned/contested business
		if (Site->Kind == ELESiteKind::Business || Site->Kind == ELESiteKind::Racket)
		{
			if (Site->OwnerFaction == ELEOwner::Player || Site->OwnerFaction == ELEOwner::Contested)
			{
				const int32 Pay = FMath::Max(10, Site->CollectPayout / 2);
				Week->Cash += Pay;
				Week->LifetimeCashEarned += Pay;
				if (Site->OwnerFaction == ELEOwner::Contested)
				{
					Site->OwnerFaction = ELEOwner::Player;
					Site->RefreshColor();
					Week->Heat = FMath::Min(4, Week->Heat + Site->CollectHeat);
				}
				Hood->OrderState = ELEAssignmentState::Done;
			}
		}
	}

	if (Hood->OrderState == ELEAssignmentState::Done
		&& Hood->Faction == ELEOwner::Player)
	{
		// One-shot consume Done so we don't double-pay
		Hood->OrderState = ELEAssignmentState::Idle;
	}
}

void ALEStreetDirector::RefreshMissionBrief()
{
	switch (ActiveMission)
	{
	case ELEMissionId::M0_Favor:
		MissionBrief = TEXT("MISSION — The Favor\nSend Eddie into Corvo Cafe (Collect).\nPut Nora or Nicky watching Pell's Garage.\nClick hood → 1 Enter building → click site.");
		break;
	case ELEMissionId::M1_Dock:
		MissionBrief = TEXT("MISSION — Sal wants the dock\nTake Dock Warehouse A. Hold it.");
		break;
	case ELEMissionId::M2_Answer:
		MissionBrief = TEXT("MISSION — Harlan answers\nKeep the dock. Hit back if they push.");
		break;
	case ELEMissionId::M3_DockWar:
		MissionBrief = TEXT("MISSION — Dock war\nOwn Warehouse A and Hawser Bar.");
		break;
	case ELEMissionId::M4_Cool:
		MissionBrief = TEXT("MISSION — Ames watches\nHold dock + bar. Keep Heat at 2 or less.");
		break;
	default:
		MissionBrief = TEXT("MISSION — Spine complete\nBrickyard waits when you are ready.");
		break;
	}
}

void ALEStreetDirector::EvaluateMission()
{
	auto Owns = [this](FName Id) -> bool
	{
		for (ALESiteActor* S : Sites)
		{
			if (S && S->SiteId == Id && S->OwnerFaction == ELEOwner::Player)
			{
				return true;
			}
		}
		return false;
	};

	bool bPlayerInCorvo = false;
	bool bPlayerAtGarage = false;
	for (ALEHoodlumCharacter* H : Hoodlums)
	{
		if (!H || H->Faction != ELEOwner::Player)
		{
			continue;
		}
		if (H->bInBuilding && H->GetOccupiedSite())
		{
			if (H->GetOccupiedSite()->SiteId == TEXT("S02"))
			{
				bPlayerInCorvo = true;
			}
			if (H->GetOccupiedSite()->SiteId == TEXT("S01"))
			{
				bPlayerAtGarage = true;
			}
		}
	}

	const ELEMissionId Prev = ActiveMission;
	switch (ActiveMission)
	{
	case ELEMissionId::M0_Favor:
		if (bPlayerInCorvo && bPlayerAtGarage)
		{
			ActiveMission = ELEMissionId::M1_Dock;
			if (Week)
			{
				Week->StoryBeat = FMath::Max(Week->StoryBeat, 1);
				Week->bDockDemanded = true;
				Week->Cash += 25;
			}
		}
		break;
	case ELEMissionId::M1_Dock:
		if (Owns(TEXT("S03")))
		{
			ActiveMission = ELEMissionId::M2_Answer;
			if (Week)
			{
				Week->bDockHeldForSal = true;
				Week->StoryBeat = FMath::Max(Week->StoryBeat, 2);
			}
		}
		break;
	case ELEMissionId::M2_Answer:
		if (Owns(TEXT("S03")))
		{
			ActiveMission = ELEMissionId::M3_DockWar;
			if (Week)
			{
				Week->StoryBeat = FMath::Max(Week->StoryBeat, 3);
			}
		}
		break;
	case ELEMissionId::M3_DockWar:
		if (Owns(TEXT("S03")) && Owns(TEXT("S04")))
		{
			ActiveMission = ELEMissionId::M4_Cool;
			if (Week)
			{
				Week->StoryBeat = FMath::Max(Week->StoryBeat, 4);
			}
		}
		break;
	case ELEMissionId::M4_Cool:
		if (Owns(TEXT("S03")) && Owns(TEXT("S04")) && Week && Week->Heat <= 2)
		{
			ActiveMission = ELEMissionId::M5_Complete;
			bMissionComplete = true;
			if (Week)
			{
				Week->StoryBeat = 5;
				Week->bStorySpineComplete = true;
				Week->bBrickyardUnlocked = true;
			}
		}
		break;
	default:
		break;
	}

	if (Prev != ActiveMission)
	{
		RefreshMissionBrief();
	}
}

FText ALEStreetDirector::GetDossierBlock() const
{
	if (!SelectedHoodlum)
	{
		return FText::FromString(TEXT("GANG DOSSIER\n\nClick a hoodlum on the street.\n1 Enter building  2 Enter car\n3 Scout  4 Hit-and-run  5 Drive-by\nLMB command  RMB cancel"));
	}

	const TCHAR* RoleName = TEXT("Bagman");
	if (SelectedHoodlum->HoodRole == ELEHoodRole::Enforcer)
	{
		RoleName = TEXT("Enforcer");
	}
	else if (SelectedHoodlum->HoodRole == ELEHoodRole::Recruiter)
	{
		RoleName = TEXT("Recruiter");
	}

	FString Armed = TEXT("none");
	switch (ArmedOrder)
	{
	case ELEStreetOrder::MoveScout: Armed = TEXT("Scout"); break;
	case ELEStreetOrder::EnterBuilding: Armed = TEXT("Enter building"); break;
	case ELEStreetOrder::EnterCar: Armed = TEXT("Enter car"); break;
	case ELEStreetOrder::HitAndRun: Armed = TEXT("Hit and run"); break;
	case ELEStreetOrder::DriveBy: Armed = TEXT("Drive-by"); break;
	default: break;
	}

	return FText::FromString(FString::Printf(
		TEXT("GANG DOSSIER\n%s\n%s  Loyalty %d\nStatus: %s\nArmed: %s\n\n1 Building  2 Car\n3 Scout  4 Hit  5 Drive-by"),
		*SelectedHoodlum->DisplayName.ToString(),
		RoleName,
		SelectedHoodlum->Loyalty,
		*SelectedHoodlum->GetOrderLabel(),
		*Armed));
}

FText ALEStreetDirector::GetMissionBlock() const
{
	return FText::FromString(FString::Printf(TEXT("%s\n\n%s"), *CornerLabel, *MissionBrief));
}
