#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "LEEmpireOrganizerWidget.generated.h"

class UBorder;
class UTextBlock;
class UVerticalBox;
class UHorizontalBox;
class UCanvasPanel;
class ALEWeekDirector;

/** Gangsters-style parchment organizer — UMG replacement for Canvas DrawHUD. */
UCLASS()
class LOSTEMPIRE_API ULEEmpireOrganizerWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual bool Initialize() override;
	virtual void NativeConstruct() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

protected:
	void BuildLayout();
	void RefreshFromWorld();
	UBorder* MakeParchment(UWidget* Child, FLinearColor Fill, FMargin InPadding);
	UTextBlock* MakeText(const FString& InText, FLinearColor Color, float Size);

	UPROPERTY()
	TObjectPtr<UCanvasPanel> RootCanvas;

	UPROPERTY()
	TObjectPtr<UTextBlock> HeaderText;

	UPROPERTY()
	TObjectPtr<UTextBlock> WeekText;

	UPROPERTY()
	TObjectPtr<UTextBlock> LedgerTitle;

	UPROPERTY()
	TObjectPtr<UTextBlock> LedgerBody;

	UPROPERTY()
	TObjectPtr<UTextBlock> RosterTitle;

	UPROPERTY()
	TObjectPtr<UHorizontalBox> RosterRow;

	UPROPERTY()
	TObjectPtr<UTextBlock> ClockTitle;

	UPROPERTY()
	TObjectPtr<UTextBlock> ClockBody;

	UPROPERTY()
	TObjectPtr<UTextBlock> HintText;

	UPROPERTY()
	TObjectPtr<UBorder> ResultsSheet;

	UPROPERTY()
	TObjectPtr<UTextBlock> ResultsTitle;

	UPROPERTY()
	TObjectPtr<UTextBlock> ResultsBody;

	UPROPERTY()
	TObjectPtr<UBorder> DimOverlay;

	FString LastRosterSignature;
	FString LastLedgerText;
	FString LastHeaderText;
};
