#include "LESiteActor.h"

#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "UObject/ConstructorHelpers.h"

ALESiteActor::ALESiteActor()
{
	Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	RootComponent = Root;

	Marker = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Marker"));
	Marker->SetupAttachment(Root);
	Marker->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	Marker->SetCollisionResponseToAllChannels(ECR_Ignore);
	Marker->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
	// Small curb marker — large dark slabs read as broken building bases.
	Marker->SetRelativeScale3D(FVector(1.1f, 1.1f, 0.35f));
	Marker->SetRelativeLocation(FVector(0.f, 0.f, 12.f));
	Marker->SetCastShadow(false);

	static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeFinder(TEXT("/Engine/BasicShapes/Cube.Cube"));
	if (CubeFinder.Succeeded())
	{
		Marker->SetStaticMesh(CubeFinder.Object);
	}

	Label = CreateDefaultSubobject<UTextRenderComponent>(TEXT("Label"));
	Label->SetupAttachment(Root);
	Label->SetRelativeLocation(FVector(0.f, 0.f, 140.f));
	Label->SetHorizontalAlignment(EHTA_Center);
	Label->SetWorldSize(55.f);
	Label->SetTextRenderColor(FColor(25, 22, 16));
}

void ALESiteActor::BeginPlay()
{
	Super::BeginPlay();
	RefreshColor();
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

void ALESiteActor::SetSelected(bool bInSelected)
{
	bSelected = bInSelected;
	RefreshColor();
}

void ALESiteActor::RefreshColor()
{
	if (Label)
	{
		const FString Pay = CollectPayout > 0 ? FString::Printf(TEXT("  $%d"), CollectPayout) : FString();
		Label->SetText(FText::FromString(
			FString::Printf(TEXT("%s%s"), *DisplayName.ToString(), *Pay)));
	}

	if (!Marker)
	{
		return;
	}

	FLinearColor Color(0.55f, 0.55f, 0.52f);
	switch (OwnerFaction)
	{
	case ELEOwner::Player:
		Color = FLinearColor(0.2f, 0.5f, 0.95f);
		break;
	case ELEOwner::Rival:
		Color = FLinearColor(0.9f, 0.22f, 0.16f);
		break;
	case ELEOwner::Contested:
		Color = FLinearColor(0.95f, 0.75f, 0.18f);
		break;
	default:
		break;
	}

	if (bSelected)
	{
		Color = Color * 1.25f;
		Marker->SetRelativeScale3D(FVector(1.4f, 1.4f, 0.4f));
	}
	else
	{
		Marker->SetRelativeScale3D(FVector(1.1f, 1.1f, 0.35f));
	}

	UMaterialInterface* BaseMat = Marker->GetMaterial(0);
	if (BaseMat)
	{
		UMaterialInstanceDynamic* Mid = Marker->CreateAndSetMaterialInstanceDynamic(0);
		if (Mid)
		{
			Mid->SetVectorParameterValue(TEXT("Color"), Color);
			Mid->SetVectorParameterValue(TEXT("BaseColor"), Color);
		}
	}
}
