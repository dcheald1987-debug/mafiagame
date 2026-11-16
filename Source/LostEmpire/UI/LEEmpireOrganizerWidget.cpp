#include "LEEmpireOrganizerWidget.h"

#include "LEDayNightDirector.h"
#include "LEEmpireGameInstance.h"
#include "LEHoodAgent.h"
#include "LEWeekDirector.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Kismet/GameplayStatics.h"

namespace LEEmpireUI
{
	static const FLinearColor Parchment(0.78f, 0.70f, 0.55f, 0.94f);
	static const FLinearColor ParchmentDark(0.42f, 0.34f, 0.24f, 0.96f);
	static const FLinearColor Ink(0.12f, 0.09f, 0.06f, 1.f);
	static const FLinearColor Cream(0.96f, 0.92f, 0.82f, 1.f);
	static const FLinearColor Accent(0.85f, 0.55f, 0.15f, 1.f);
}

bool ULEEmpireOrganizerWidget::Initialize()
{
	const bool bOk = Super::Initialize();
	if (bOk && WidgetTree && !WidgetTree->RootWidget)
	{
		BuildLayout();
	}
	return bOk;
}

void ULEEmpireOrganizerWidget::NativeConstruct()
{
	Super::NativeConstruct();
	SetIsFocusable(false);
	RefreshFromWorld();
}

void ULEEmpireOrganizerWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);
	RefreshFromWorld();
}

UTextBlock* ULEEmpireOrganizerWidget::MakeText(const FString& InText, FLinearColor Color, float Size)
{
	UTextBlock* Block = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
	Block->SetText(FText::FromString(InText));
	Block->SetColorAndOpacity(FSlateColor(Color));
	FSlateFontInfo Font = Block->GetFont();
	Font.Size = Size;
	Block->SetFont(Font);
	Block->SetAutoWrapText(true);
	return Block;
}

UBorder* ULEEmpireOrganizerWidget::MakeParchment(UWidget* Child, FLinearColor Fill, FMargin InPadding)
{
	UBorder* Border = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
	Border->SetBrushColor(Fill);
	Border->SetPadding(InPadding);
	if (Child)
	{
		Border->SetContent(Child);
	}
	return Border;
}

void ULEEmpireOrganizerWidget::BuildLayout()
{
	RootCanvas = WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass(), TEXT("RootCanvas"));
	WidgetTree->RootWidget = RootCanvas;

	// Header bar
	UHorizontalBox* HeaderRow = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
	HeaderText = MakeText(TEXT("SAINT LORNE  —  THE LEVEE"), LEEmpireUI::Cream, 16.f);
	WeekText = MakeText(TEXT("Week 1"), LEEmpireUI::Cream, 16.f);
	if (UHorizontalBoxSlot* HS = HeaderRow->AddChildToHorizontalBox(HeaderText))
	{
		HS->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
		HS->SetVerticalAlignment(VAlign_Center);
		HS->SetPadding(FMargin(16.f, 0.f, 0.f, 0.f));
	}
	if (UHorizontalBoxSlot* WS = HeaderRow->AddChildToHorizontalBox(WeekText))
	{
		WS->SetHorizontalAlignment(HAlign_Right);
		WS->SetVerticalAlignment(VAlign_Center);
		WS->SetPadding(FMargin(0.f, 0.f, 16.f, 0.f));
	}
	UBorder* HeaderBorder = MakeParchment(HeaderRow, LEEmpireUI::ParchmentDark, FMargin(0.f, 8.f));
	if (UCanvasPanelSlot* CanvasSlot = RootCanvas->AddChildToCanvas(HeaderBorder))
	{
		CanvasSlot->SetAnchors(FAnchors(0.f, 0.f, 1.f, 0.f));
		CanvasSlot->SetOffsets(FMargin(0.f, 0.f, 0.f, 40.f));
	}

	// Left ledger
	UVerticalBox* LedgerCol = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	LedgerTitle = MakeText(TEXT("GANG ORGANIZER"), LEEmpireUI::Cream, 13.f);
	UBorder* LedgerTitleBar = MakeParchment(LedgerTitle, LEEmpireUI::ParchmentDark, FMargin(12.f, 8.f));
	LedgerBody = MakeText(TEXT(""), LEEmpireUI::Ink, 12.f);
	if (UVerticalBoxSlot* TS = LedgerCol->AddChildToVerticalBox(LedgerTitleBar))
	{
		TS->SetPadding(FMargin(0.f, 0.f, 0.f, 6.f));
	}
	if (UVerticalBoxSlot* BS = LedgerCol->AddChildToVerticalBox(LedgerBody))
	{
		BS->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
		BS->SetPadding(FMargin(10.f, 4.f));
	}
	UBorder* LedgerBorder = MakeParchment(LedgerCol, LEEmpireUI::Parchment, FMargin(0.f));
	if (UCanvasPanelSlot* CanvasSlot = RootCanvas->AddChildToCanvas(LedgerBorder))
	{
		CanvasSlot->SetAnchors(FAnchors(0.f, 0.f, 0.f, 0.f));
		CanvasSlot->SetPosition(FVector2D(10.f, 54.f));
		CanvasSlot->SetSize(FVector2D(420.f, 420.f));
	}

	// Roster strip
	UVerticalBox* RosterCol = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	RosterTitle = MakeText(TEXT("ROSTER"), LEEmpireUI::Ink, 12.f);
	RosterRow = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
	RosterCol->AddChildToVerticalBox(RosterTitle);
	if (UVerticalBoxSlot* RS = RosterCol->AddChildToVerticalBox(RosterRow))
	{
		RS->SetPadding(FMargin(0.f, 6.f, 0.f, 0.f));
	}
	UBorder* RosterBorder = MakeParchment(RosterCol, LEEmpireUI::Parchment, FMargin(12.f, 8.f));
	if (UCanvasPanelSlot* CanvasSlot = RootCanvas->AddChildToCanvas(RosterBorder))
	{
		CanvasSlot->SetAnchors(FAnchors(0.f, 1.f, 0.f, 1.f));
		CanvasSlot->SetAlignment(FVector2D(0.f, 1.f));
		CanvasSlot->SetPosition(FVector2D(10.f, -10.f));
		CanvasSlot->SetSize(FVector2D(420.f, 78.f));
	}

	// Street clock — Chicago date / time / day-night / speed
	UVerticalBox* ClockCol = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	ClockTitle = MakeText(TEXT("CHICAGO CLOCK"), LEEmpireUI::Cream, 11.f);
	UBorder* ClockTitleBar = MakeParchment(ClockTitle, LEEmpireUI::ParchmentDark, FMargin(10.f, 6.f));
	ClockBody = MakeText(TEXT("—"), LEEmpireUI::Ink, 13.f);
	ClockCol->AddChildToVerticalBox(ClockTitleBar);
	if (UVerticalBoxSlot* CS = ClockCol->AddChildToVerticalBox(ClockBody))
	{
		CS->SetHorizontalAlignment(HAlign_Center);
		CS->SetPadding(FMargin(8.f, 6.f));
	}
	UBorder* ClockBorder = MakeParchment(ClockCol, LEEmpireUI::Parchment, FMargin(0.f));
	if (UCanvasPanelSlot* CanvasSlot = RootCanvas->AddChildToCanvas(ClockBorder))
	{
		CanvasSlot->SetAnchors(FAnchors(1.f, 1.f, 1.f, 1.f));
		CanvasSlot->SetAlignment(FVector2D(1.f, 1.f));
		CanvasSlot->SetPosition(FVector2D(-14.f, -14.f));
		CanvasSlot->SetSize(FVector2D(220.f, 110.f));
	}

	// Hint line
	HintText = MakeText(TEXT(""), LEEmpireUI::Cream, 12.f);
	if (UCanvasPanelSlot* CanvasSlot = RootCanvas->AddChildToCanvas(HintText))
	{
		CanvasSlot->SetAnchors(FAnchors(0.f, 1.f, 1.f, 1.f));
		CanvasSlot->SetAlignment(FVector2D(0.f, 1.f));
		CanvasSlot->SetOffsets(FMargin(450.f, -28.f, 180.f, 22.f));
	}

	// Results dim + sheet
	DimOverlay = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
	DimOverlay->SetBrushColor(FLinearColor(0.f, 0.f, 0.f, 0.4f));
	DimOverlay->SetVisibility(ESlateVisibility::Collapsed);
	if (UCanvasPanelSlot* CanvasSlot = RootCanvas->AddChildToCanvas(DimOverlay))
	{
		CanvasSlot->SetAnchors(FAnchors(0.f, 0.f, 1.f, 1.f));
		CanvasSlot->SetOffsets(FMargin(0.f, 40.f, 0.f, 0.f));
	}

	UVerticalBox* ResultsCol = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	ResultsTitle = MakeText(TEXT("WEEK — RESULTS"), LEEmpireUI::Cream, 16.f);
	UBorder* ResultsTitleBar = MakeParchment(ResultsTitle, LEEmpireUI::ParchmentDark, FMargin(16.f, 10.f));
	ResultsBody = MakeText(TEXT(""), LEEmpireUI::Ink, 14.f);
	ResultsCol->AddChildToVerticalBox(ResultsTitleBar);
	if (UVerticalBoxSlot* RBS = ResultsCol->AddChildToVerticalBox(ResultsBody))
	{
		RBS->SetPadding(FMargin(20.f, 16.f));
		RBS->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
	}
	ResultsSheet = MakeParchment(ResultsCol, LEEmpireUI::Parchment, FMargin(0.f));
	ResultsSheet->SetVisibility(ESlateVisibility::Collapsed);
	if (UCanvasPanelSlot* CanvasSlot = RootCanvas->AddChildToCanvas(ResultsSheet))
	{
		CanvasSlot->SetAnchors(FAnchors(0.5f, 0.45f, 0.5f, 0.45f));
		CanvasSlot->SetAlignment(FVector2D(0.5f, 0.5f));
		CanvasSlot->SetSize(FVector2D(480.f, 280.f));
		CanvasSlot->SetPosition(FVector2D(0.f, 0.f));
	}
}

void ULEEmpireOrganizerWidget::RefreshFromWorld()
{
	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}

	ALEWeekDirector* Week = Cast<ALEWeekDirector>(
		UGameplayStatics::GetActorOfClass(World, ALEWeekDirector::StaticClass()));
	if (!Week)
	{
		SetVisibility(ESlateVisibility::Collapsed);
		return;
	}
	SetVisibility(ESlateVisibility::HitTestInvisible);

	FString Header = FString::Printf(
		TEXT("SAINT LORNE  —  %s"),
		*ULEEmpireGameInstance::DistrictDisplayName(Week->CurrentDistrict).ToString().ToUpper());
	if (Week->Heat >= 4)
	{
		Header += TEXT("  |  RAID");
	}
	else if (Week->bPoliceOnStreet)
	{
		Header += TEXT("  |  PATROL");
	}
	if (Week->bDockWarOpen && !Week->bDockWarWon)
	{
		Header += TEXT("  |  DOCK WAR");
	}
	else if (Week->bStorySpineComplete)
	{
		Header += TEXT("  |  SPINE DONE");
	}
	if (Week->bBrickyardUnlocked || Week->bBrickyardStubUnlocked)
	{
		Header += TEXT("  |  BRICKYARD");
	}
	if (Week->bHaldenRowUnlocked)
	{
		Header += TEXT("  |  HALDEN");
	}
	if (Week->bAmesHillUnlocked)
	{
		Header += TEXT("  |  AMES");
	}
	if (HeaderText && Header != LastHeaderText)
	{
		HeaderText->SetText(FText::FromString(Header));
		LastHeaderText = Header;
	}
	if (WeekText)
	{
		WeekText->SetText(FText::FromString(FString::Printf(TEXT("Week %d"), Week->WeekIndex)));
	}
	if (LedgerBody)
	{
		const FString Ledger = Week->GetHudBlock().ToString();
		if (Ledger != LastLedgerText)
		{
			LedgerBody->SetText(FText::FromString(Ledger));
			LastLedgerText = Ledger;
		}
	}

	if (ClockBody)
	{
		if (ALEDayNightDirector* DayNight = Cast<ALEDayNightDirector>(
				UGameplayStatics::GetActorOfClass(World, ALEDayNightDirector::StaticClass())))
		{
			const int32 Rise = DayNight->GetSunriseMinutes();
			const int32 Set = DayNight->GetSunsetMinutes();
			ClockBody->SetText(FText::FromString(FString::Printf(
				TEXT("%s\n%s  %s  %s\nRise %d:%02d  Set %d:%02d"),
				*DayNight->GetDateText().ToString(),
				*DayNight->GetClockText().ToString(),
				DayNight->bIsNight ? TEXT("NIGHT") : TEXT("DAY"),
				*DayNight->GetSpeedText().ToString(),
				Rise / 60, Rise % 60, Set / 60, Set % 60)));
		}
		else if (Week->Phase == ELEWeekPhase::Working)
		{
			ClockBody->SetText(FText::FromString(FString::Printf(TEXT("%.0fs"), Week->WeekTimeRemaining)));
		}
		else if (Week->Phase == ELEWeekPhase::Plan)
		{
			ClockBody->SetText(FText::FromString(TEXT("PLAN")));
		}
		else
		{
			ClockBody->SetText(FText::FromString(TEXT("END")));
		}
	}

	if (HintText)
	{
		if (Week->Phase == ELEWeekPhase::Plan)
		{
			HintText->SetText(FText::FromString(
				Week->bFullOrdersUnlocked
					? (Week->Heat >= 3
						? TEXT("[ ] district  T travel  |  C/V/R/H  |  B bribe  |  Enter run")
						: TEXT("[ ] district  T travel  |  C/V/R/H  |  Q/E site  |  Enter run"))
					: TEXT("Tutorial: C collect  V watch | Enter run week")));
		}
		else if (Week->Phase == ELEWeekPhase::Working)
		{
			HintText->SetText(FText::FromString(TEXT("Space = 1x/3x  |  week ends on clock or jobs finish")));
		}
		else
		{
			HintText->SetText(FText::FromString(TEXT("Enter — next plan")));
		}
	}

	const bool bResults = Week->Phase == ELEWeekPhase::Results;
	if (DimOverlay)
	{
		DimOverlay->SetVisibility(bResults ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
	}
	if (ResultsSheet)
	{
		ResultsSheet->SetVisibility(bResults ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
	}
	if (bResults && ResultsTitle && ResultsBody)
	{
		ResultsTitle->SetText(FText::FromString(FString::Printf(TEXT("WEEK %d — RESULTS"), Week->WeekIndex)));
		ResultsBody->SetText(FText::FromString(Week->LastResultsSummary + TEXT("\n\nEnter — next plan")));
	}

	if (RosterRow)
	{
		TArray<AActor*> HoodActors;
		UGameplayStatics::GetAllActorsOfClass(World, ALEHoodAgent::StaticClass(), HoodActors);
		ALEHoodAgent* Selected = Week->GetSelectedHood();
		FString RosterSig;
		for (AActor* Actor : HoodActors)
		{
			ALEHoodAgent* Hood = Cast<ALEHoodAgent>(Actor);
			if (!Hood || Hood->Faction != ELEOwner::Player)
			{
				continue;
			}
			RosterSig += FString::Printf(
				TEXT("%s:%d:%d:%d;"),
				*Hood->HoodId.ToString(),
				static_cast<int32>(Hood->AssignmentState),
				Hood->WeeksOut,
				Hood == Selected ? 1 : 0);
		}
		if (RosterSig != LastRosterSignature)
		{
			LastRosterSignature = RosterSig;
			RosterRow->ClearChildren();
			int32 Shown = 0;
			for (AActor* Actor : HoodActors)
			{
				ALEHoodAgent* Hood = Cast<ALEHoodAgent>(Actor);
				if (!Hood || Hood->Faction != ELEOwner::Player || Shown >= 5)
				{
					continue;
				}

				FLinearColor Chip = FLinearColor(0.25f, 0.45f, 0.85f, 1.f);
				if (Hood->AssignmentState == ELEAssignmentState::Dead)
				{
					Chip = FLinearColor(0.2f, 0.2f, 0.2f, 1.f);
				}
				else if (Hood->AssignmentState == ELEAssignmentState::Arrested || Hood->WeeksOut > 0)
				{
					Chip = FLinearColor(0.55f, 0.4f, 0.15f, 1.f);
				}

				UTextBlock* ChipText = MakeText(Hood->HoodId.ToString(), LEEmpireUI::Cream, 12.f);
				UBorder* Inner = MakeParchment(ChipText, Chip, FMargin(10.f, 8.f));
				UWidget* ChipWidget = Inner;
				if (Hood == Selected)
				{
					ChipWidget = MakeParchment(Inner, LEEmpireUI::Accent, FMargin(3.f));
				}
				if (UHorizontalBoxSlot* BoxSlot = RosterRow->AddChildToHorizontalBox(ChipWidget))
				{
					BoxSlot->SetPadding(FMargin(0.f, 0.f, 8.f, 0.f));
				}
				++Shown;
			}
		}
	}
}
