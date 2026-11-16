#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "LEGangDossierWidget.generated.h"

class UBorder;
class UTextBlock;
class UCanvasPanel;
class UImage;
class ALEStreetDirector;

/** Gangsters left dossier + top corner/mission strip — 1930s parchment. */
UCLASS()
class LOSTEMPIRE_API ULEGangDossierWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual bool Initialize() override;
	virtual void NativeConstruct() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

protected:
	void BuildLayout();
	void Refresh();
	void SetPortraitFromPath(const FString& SoftTexturePath);

	UPROPERTY()
	TObjectPtr<UCanvasPanel> RootCanvas;

	UPROPERTY()
	TObjectPtr<UTextBlock> CornerText;

	UPROPERTY()
	TObjectPtr<UTextBlock> DossierText;

	UPROPERTY()
	TObjectPtr<UTextBlock> MissionText;

	UPROPERTY()
	TObjectPtr<UImage> PortraitImage;

	UPROPERTY()
	TObjectPtr<UImage> WeaponImage;

	FString LastDossier;
	FString LastMission;
	FString LastPortraitPath;
};
