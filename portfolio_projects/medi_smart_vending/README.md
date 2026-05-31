# Medi Smart Medical Vending System

Academic functional prototype for dispensing essential medical and hygiene items in public places such as colleges, hospitals, airports, malls, and stations.

## Architecture

- Raspberry Pi as the main controller
- Arduino as the motor controller
- USB serial communication between Raspberry Pi and Arduino
- Tkinter touchscreen UI
- Numeric keypad-style product selection
- Payment-verification step before dispensing
- Inventory and motor-turn tracking per slot
- 9-slot compartment model

## Files

- `raspberry_pi_ui.py` - touchscreen/keypad vending UI simulation with serial command output.
- `arduino_motor_controller.ino` - Arduino reference sketch for slot-based motor dispensing.

## Status

Reconstructed portfolio demo based on the completed academic prototype architecture and feature list.
