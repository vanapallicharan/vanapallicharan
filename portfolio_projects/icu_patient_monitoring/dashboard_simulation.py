import random
import time
from dataclasses import dataclass


@dataclass
class Vitals:
    patient_id: str
    heart_rate: int
    spo2: int
    systolic_bp: int
    diastolic_bp: int
    temperature_c: float
    respiration_rate: int
    motion_detected: bool


def classify(vitals: Vitals):
    alerts = []
    if vitals.heart_rate < 50 or vitals.heart_rate > 120:
        alerts.append("heart-rate")
    if vitals.spo2 < 92:
        alerts.append("low-spo2")
    if vitals.systolic_bp > 150 or vitals.systolic_bp < 85:
        alerts.append("blood-pressure")
    if vitals.temperature_c > 38.5 or vitals.temperature_c < 35.0:
        alerts.append("temperature")
    if vitals.respiration_rate < 10 or vitals.respiration_rate > 28:
        alerts.append("respiration")
    return alerts


def read_sensor_packet(patient_id):
    return Vitals(
        patient_id=patient_id,
        heart_rate=random.randint(45, 135),
        spo2=random.randint(88, 100),
        systolic_bp=random.randint(80, 165),
        diastolic_bp=random.randint(50, 100),
        temperature_c=round(random.uniform(34.5, 39.5), 1),
        respiration_rate=random.randint(8, 32),
        motion_detected=random.choice([True, False]),
    )


def main():
    print("ICU Patient Monitoring Simulation")
    for _ in range(10):
        vitals = read_sensor_packet("ICU-BED-01")
        alerts = classify(vitals)
        status = "CRITICAL: " + ", ".join(alerts) if alerts else "stable"
        print(f"{vitals} -> {status}")
        time.sleep(1)


if __name__ == "__main__":
    main()
