#include "LESiteActor.h"

#include "Components/StaticMeshComponent.h"
#include "UObject/ConstructorHelpers.h"

ALESiteActor::ALESiteActor()
{
	Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	RootComponent = Root;

	Marker = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Marker"));
	Marker->SetupAttachment(Root);
	Marker->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Marker->SetRelativeScale3D(FVector(2.5f, 2.5f, 0.4f));

	static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeFinder(TEXT("/Engine/BasicShapes/Cube.Cube"));
	if (CubeFinder.Succeeded())
	{
		Marker->SetStaticMesh(CubeFinder.Object);
	}
}

void ALESiteActor::Configure(FName InSiteId, FText InDisplayName, uint8 InKind, uint8 InOwner, FName InBlockId, int32 InPayout, int32 InHeat)
{
	SiteId = InSiteId;
	DisplayName = InDisplayName;
	Kind = static_cast<ELESiteKind>(InKind);
	OwnerFaction = static_cast<ELEOwner>(InOwner);
	BlockId = InBlockId;
	CollectPayout = InPayout;
	CollectHeat = InHeat;
	RefreshColor();
}

void ALESiteActor::RefreshColor()
{
	if (!Marker)
	{
		return;
	}

	FLinearColor Color(0.5f, 0.5f, 0.5f);
	switch (OwnerFaction)
	{
	case ELEOwner::Player:
		Color = FLinearColor(0.15f, 0.45f, 0.85f);
		break;
	case ELEOwner::Rival:
		Color = FLinearColor(0.85f, 0.2f, 0.15f);
		break;
	case ELEOwner::Contested:
		Color = FLinearColor(0.9f, 0.7f, 0.15f);
		break;
	default:
		break;
	}

	Marker->SetVectorParameterValueOnMaterials(TEXT("Color"), FVector(Color.R, Color.G, Color.B));
}
