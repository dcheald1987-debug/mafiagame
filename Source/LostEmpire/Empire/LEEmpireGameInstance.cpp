#include "LEEmpireGameInstance.h"

FName ULEEmpireGameInstance::DistrictToMapName(ELEDistrictId District)
{
	switch (District)
	{
	case ELEDistrictId::Brickyard:
		return TEXT("Brickyard_Greybox");
	case ELEDistrictId::HaldenRow:
		return TEXT("HaldenRow_Greybox");
	case ELEDistrictId::AmesHill:
		return TEXT("AmesHill_Greybox");
	default:
		return TEXT("Levee_Greybox");
	}
}

FText ULEEmpireGameInstance::DistrictDisplayName(ELEDistrictId District)
{
	switch (District)
	{
	case ELEDistrictId::Brickyard:
		return FText::FromString(TEXT("The Brickyard"));
	case ELEDistrictId::HaldenRow:
		return FText::FromString(TEXT("Halden Row"));
	case ELEDistrictId::AmesHill:
		return FText::FromString(TEXT("Ames Hill"));
	default:
		return FText::FromString(TEXT("The Levee"));
	}
}

bool ULEEmpireGameInstance::IsDistrictUnlocked(ELEDistrictId District) const
{
	switch (District)
	{
	case ELEDistrictId::Levee:
		return true;
	case ELEDistrictId::Brickyard:
		return bBrickyardUnlocked;
	case ELEDistrictId::HaldenRow:
		return bHaldenRowUnlocked;
	case ELEDistrictId::AmesHill:
		return bAmesHillUnlocked;
	default:
		return false;
	}
}
