using UnrealBuildTool;

public class LostEmpire : ModuleRules
{
	public LostEmpire(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(new string[]
		{
			"Core",
			"CoreUObject",
			"Engine",
			"InputCore",
			"EnhancedInput",
			"ChaosVehicles",
			"PhysicsCore",
			"AIModule",
			"NavigationSystem",
			"UMG"
		});

		PublicIncludePaths.AddRange(new string[]
		{
			"LostEmpire",
			"LostEmpire/Mission",
			"LostEmpire/Vehicle",
			"LostEmpire/UI",
			"LostEmpire/Empire"
		});
	}
}
