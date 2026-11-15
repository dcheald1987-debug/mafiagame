#include "LEPackardWheelFront.h"

ULEPackardWheelFront::ULEPackardWheelFront()
{
	WheelRadius = 36.f;
	WheelWidth = 22.f;
	FrictionForceMultiplier = 2.4f;
	CorneringStiffness = 500.f;
	SideSlipModifier = 0.8f;
	SlipThreshold = 30.f;
	SkidThreshold = 20.f;
	MaxSteerAngle = 32.f;
	AxleType = EAxleType::Front;
	bAffectedBySteering = true;
	bAffectedByEngine = false;
	bAffectedByBrake = true;
	bAffectedByHandbrake = false;
	MaxBrakeTorque = 2800.f;
	MaxHandBrakeTorque = 0.f;
}
