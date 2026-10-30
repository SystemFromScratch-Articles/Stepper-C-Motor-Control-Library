# Introduction

This manual describes the **Stepper-C system**: a control library for two-phase hybrid
stepper motors written in C11, the Scilab/Xcos model it is developed and verified
against, and the ngspice model of the power stage it will drive first. It is written for
embedded engineers who want to use the library, check its behaviour in simulation, or
extend the models. Every number in it was measured with the models and tests of the
versions listed below.

## What the system is

Stepper-C replaces the closed "step/direction" driver chip with software: the
microcontroller measures the two phase currents, runs a current controller per phase and
writes the PWM of the power stage itself. The library computes everything between a
motion command (*move to position 3200*) and the PWM compare values; the board code only
reads the ADC and writes the timer.

Three repositories make up the system:

| Repository | Local folder | Content | Language / tool |
| --- | --- | --- | --- |
| [Stepper-C](https://github.com/AntonVynohradov/Stepper-C) | `sfs-stepper-ctrl` | **Stepper-C**, the control library | C11, CMake, GoogleTest |
| [sfs-stepper-sim](https://github.com/AntonVynohradov/sfs-stepper-sim) | `sfs-stepper-sim` | Motor model, prototype of the control algorithms, software in the loop | Scilab 2027, Xcos, Python twins |
| [sfs-stepper-power-spice](https://github.com/AntonVynohradov/sfs-stepper-power-spice) | `sfs-stepper-power-spice` | Transistor-level model of one leg of the B-G431B-ESC1 power stage | ngspice, Python |

The library repository is published as **Stepper-C**; it is cloned into the folder
`sfs-stepper-ctrl`, the name the simulation looks for.

The library is the product; the two models exist to find its limits before hardware
does. The chain is closed in both directions: the C code runs unchanged inside Xcos, and
the parameters the ngspice model extracts (effective dead time, leg resistance, diode
drop) are written into the simulation.

## What it does and does not do

| Stepper-C does | Why |
| --- | --- |
| Closed-loop current control of both phases (PI with back-calculation anti-windup, back-EMF feed-forward) | Microstepping torque follows the current, not the voltage; at speed only a current loop keeps the amplitude |
| Microstepping 1 … 256 per full step from a 32-bit electrical angle | Smooth motion, low noise; resolution independent of the step rate |
| Trapezoidal motion profile with exact integer braking | No overshoot, exact stop on the target, no velocity step when a move is replaced |
| Two power stage topologies: two H-bridges, or three legs with a shared leg | The shared-leg layout lets three-phase BLDC boards (B-G431B-ESC1) drive a stepper |
| Bus voltage compensation and voltage vector limiting with the direction kept | Torque direction is preserved when the bridge runs out of voltage |
| Overcurrent, over- and undervoltage trips; external faults | Protects the board in the fast loop, within one PWM period |
| Fixed point (Q15/Q31) or float arithmetic, chosen at build time | Runs on MCUs with and without FPU |

| Stepper-C does not | Why / what to use instead |
| --- | --- |
| Generate step/direction pulses for an external driver chip | It *is* the driver; use the chip's own interface for that case |
| Read the clock, sleep or allocate memory | Time comes from the configured loop rates; the instance is allocated by the application |
| Configure timers, ADC or GPIO | Board-specific; done by the application through the callbacks |
| Close a position loop on an encoder (yet) | Open-loop microstepping; the load angle is visible in simulation (planned extension) |
| Compensate the dead time (yet) | The configuration field exists; the ngspice results define the value (planned) |

## Who it is for

- **Firmware engineers** integrating stepper control on an STM32, a Cortex-M0 or any MCU
  with two ADC channels and a PWM timer: read [Stepper-C Library](library.md) and the
  [API Reference](api.md).
- **Control and system engineers** who want to know where the drive loses steps,
  resonates or saturates: read [Motor Model](motor-model.md),
  [Control Algorithms](control.md) and [Results](results.md).
- **Hardware engineers** choosing dead time, gate resistors and shunt sampling: read
  [Power Stage Model](power-stage.md).
- **Students** who want to open one file, press Start and see a stepper motor being
  controlled by real embedded C code: read [Software in the Loop](sil.md).

## Key properties

| Property | Value |
| --- | --- |
| Language | C11 (library), Scilab 2027 (model), Python 3.9+ (twins, tools), ngspice 42+ |
| Dependencies of the library | None (`<stdint.h>`, `<stdbool.h>`, `<stddef.h>` only; no `<string.h>`) |
| Memory | One `struct sstep` per motor, allocated by the application; no heap, no global state |
| Code size | 8.2 kB Cortex-M4F fixed point, 9.0 kB Cortex-M4F float, 8.5 kB Cortex-M0+ (clang `-Os`, both topologies, sine table included) |
| Execution model | `sstep_fast_loop()` in the PWM interrupt (20 kHz), `sstep_slow_loop()` at 1 kHz |
| Unit tests | 76 (fixed point), 75 (float); 100 % line and branch coverage of `src/`; clean under ASan/UBSan |
| Model tests | T00–T12, B01, X01–X04 (prototype), S01–S04 (software in the loop), SP01–SP03 (ngspice) |
| Coding rules | MISRA C:2012 followed in the code; the Cppcheck MISRA target is configured, a full report is pending |
| License | Apache License 2.0 |

## Versions covered

| Component | Version | State |
| --- | --- | --- |
| [Stepper-C](https://github.com/AntonVynohradov/Stepper-C) (`sfs-stepper-ctrl`) | 0.1.0 (unreleased) | control loops complete, tested on models |
| Simulation ([sfs-stepper-sim](https://github.com/AntonVynohradov/sfs-stepper-sim)) | 0.1.0 (unreleased) | prototype, switching stage, SIL, resonance and robustness tests |
| Power stage ([sfs-stepper-power-spice](https://github.com/AntonVynohradov/sfs-stepper-power-spice)) | 0.1.0 (unreleased) | ESC1 leg model, export to the simulation |
| Hardware port (B-G431B-ESC1) | — | next step (P3), see [Hardware Bring-up](hardware.md) |

!!! warning "Models are not hardware"
    The results in this manual come from models with datasheet parameters and several
    stated assumptions (detent torque, dry friction, gate resistors, dead time). They
    show *where* to look and *what* to expect. Check every limit on the real motor and
    board before relying on it, and start with a current-limited supply.

## Conventions

| Item | Convention |
| --- | --- |
| Phase currents | `i_A = I cos φ`, `i_B = I sin φ`; the rotor settles at `p θ = φ` |
| Electrical angle | 32-bit unsigned, one turn = 2³², wraps naturally |
| Positions | microsteps (API), 1/65536 microstep inside the motion generator |
| Load angle | `φ − p θ` in electrical degrees; positive = rotor behind the field; loss of synchronism above 90° … 180° |
| Per unit | current base = ADC full scale current, voltage base = nominal bus voltage |
| Configuration | integer engineering units: mΩ, µH, mA, mV, Hz, ns |
| Code | function names with `()`, values with units, hex as `0x0010` |
| Tests | `T` prototype tests, `X` cross-checks with the Python twins, `B` bridge, `S` software in the loop, `SP` ngspice |

## Terminology

Full step
:   1.8° for a 200-step motor: one quarter of an electrical period.

Microstep
:   A fraction 1/M of a full step; M = 16 gives 3200 positions per revolution.

Fast loop
:   The code that runs every PWM period: current measurement, PI controllers, voltage
    limit, PWM write.

Slow loop
:   The code that runs at 1 kHz: motion profile, current amplitude, events.

Shared leg
:   A power stage with three half-bridges where phase A is connected between legs U and
    W and phase B between V and W; W is common to both phases.

Software in the loop (SIL)
:   The real library code, compiled for the PC, running inside the Xcos simulation
    against the motor model.

Twin
:   A second implementation of the same algorithm in another language (Scilab ↔ Python,
    Scilab ↔ C) used to cross-check results sample by sample.
