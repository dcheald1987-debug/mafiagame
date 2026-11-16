#include "LEGangDossierWidget.h"

#include "LEHoodlumCharacter.h"
#include "LEStreetDirector.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/Image.h"
#include "Components/TextBlock.h"
#include "Engine/Texture2D.h"
#include "Kismet/GameplayStatics.h"

bool ULEGangDossierWidget::Initialize()
{
	const bool bOk = Super::Initialize();
	if (bOk && WidgetTree && !WidgetTree->RootWidget)
	{
		BuildLayout();
	}
	return bOk;
}

void ULEGangDossierWidget::NativeConstruct()
{
	Super::NativeConstruct();
	if (WidgetTree && !WidgetTree->RootWidget)
	{
		BuildLayout();
	}
}

void ULEGangDossierWidget::BuildLayout()
{
	RootCanvas = WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass(), TEXT("StreetRoot"));
	WidgetTree->RootWidget = RootCanvas;

	auto MakeText = [this](int32 Size) -> UTextBlock*
	{
		UTextBlock* T = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
		T->SetColorAndOpacity(FSlateColor(FLinearColor(0.12f, 0.1f, 0.08f)));
		FSlateFontInfo Font = T->GetFont();
		Font.Size = Size;
		T->SetFont(Font);
		T->SetAutoWrapText(true);
		return T;
	};

	auto MakeParchment = [this](UWidget* Child, const FVector2D& Pos, const FVector2D& Size) -> UBorder*
	{
		UBorder* Border = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());
		Border->SetBrushColor(FLinearColor(0.82f, 0.74f, 0.58f, 0.92f));
		Border->SetPadding(FMargin(12.f, 10.f));
		Border->SetContent(Child);
		UCanvasPanelSlot* Slot = RootCanvas->AddChildToCanvas(Border);
		Slot->SetAutoSize(false);
		Slot->SetPosition(Pos);
		Slot->SetSize(Size);
		Slot->SetZOrder(20);
		return Border;
	};

	CornerText = MakeText(15);
	CornerText->SetText(FText::FromString(TEXT("SAINT LORNE")));
	MakeParchment(CornerText, FVector2D(220.f, 12.f), FVector2D(720.f, 36.f));

	// Concept sheets stay in Art/Refs — not pasted into HUD until cropped portraits exist
	PortraitImage = nullptr;
	WeaponImage = nullptr;

	DossierText = MakeText(14);
	MakeParchment(DossierText, FVector2D(16.f, 56.f), FVector2D(280.f, 360.f));

	MissionText = MakeText(13);
	MakeParchment(MissionText, FVector2D(16.f, 430.f), FVector2D(320.f, 200.f));
}

void ULEGangDossierWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);
	Refresh();
}

void ULEGangDossierWidget::Refresh()
{
	const ALEStreetDirector* Street = Cast<ALEStreetDirector>(
		UGameplayStatics::GetActorOfClass(GetWorld(), ALEStreetDirector::StaticClass()));
	if (!Street)
	{
		return;
	}

	if (CornerText)
	{
		CornerText->SetText(FText::FromString(Street->CornerLabel));
	}

	const FString Dos = Street->GetDossierBlock().ToString();
	if (DossierText && Dos != LastDossier)
	{
		LastDossier = Dos;
		DossierText->SetText(FText::FromString(Dos));
	}

	const FString Mis = Street->GetMissionBlock().ToString();
	if (MissionText && Mis != LastMission)
	{
		LastMission = Mis;
		MissionText->SetText(FText::FromString(Mis));
	}

}

void ULEGangDossierWidget::SetPortraitFromPath(const FString& SoftTexturePath)
{
	if (!PortraitImage)
	{
		return;
	}
	if (SoftTexturePath.IsEmpty())
	{
		PortraitImage->SetOpacity(0.35f);
		return;
	}
	if (UTexture2D* Tex = LoadObject<UTexture2D>(nullptr, *SoftTexturePath))
	{
		PortraitImage->SetBrushFromTexture(Tex, true);
		PortraitImage->SetOpacity(1.f);
	}
}
