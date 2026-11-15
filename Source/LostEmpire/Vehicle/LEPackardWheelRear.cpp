#include "LEPackardWheelRear.h"

ULEPackardWheelRear::ULEPackardWheelRear()
{
	WheelRadius = 36.f;
	WheelWidth = 24.f;
	FrictionForceMultiplier = 2.6f;
	CorneringStiffness = 450.f;
	SideSlipModifier = 0.75f;
	SlipThreshold = 25.f;
	SkidThreshold = 18.f;
	MaxSteerAngle = 0.f;
	AxleType = EAxleType::Rear;
	bAffectedBySteering = false;
	bAffectedByEngine = true;
	bAffectedByBrake = true;
	bAffectedByHandbrake = true;
	MaxBrakeTorque = 3200.f;
	MaxHandBrakeTorque = 4500.f;
}
