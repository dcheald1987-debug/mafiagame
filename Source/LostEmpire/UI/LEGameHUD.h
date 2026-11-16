#pragma once

#include "CoreMinimal.h"
#include "GameFramework/HUD.h"
#include "LEGameHUD.generated.h"

class ULEEmpireOrganizerWidget;
class ULEGangDossierWidget;

/** Empire HUD — Gangsters dossier + light organizer; Canvas only for C01 legacy maps. */
UCLASS()
class LOSTEMPIRE_API ALEGameHUD : public AHUD
{
	GENERATED_BODY()

public:
	virtual void BeginPlay() override;
	virtual void DrawHUD() override;

protected:
	UPROPERTY()
	TObjectPtr<ULEEmpireOrganizerWidget> OrganizerWidget;

	UPROPERTY()
	TObjectPtr<ULEGangDossierWidget> DossierWidget;
};
