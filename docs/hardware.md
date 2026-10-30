# Hardware Bring-up

The next step of the project (P3) ports Stepper-C to the B-G431B-ESC1 and runs the
17HS19-2004S1. This chapter is the plan and the checklist for that step: how to connect
the motor, what to measure first and how to compare the hardware with the models. It
describes work that has not been done yet; results will be added in the next edition.

!!! danger "Safety"
    A two-phase motor on a three-phase board is a non-standard connection; a wrong
    firmware setting can short a leg. Use a laboratory supply with a current limit
    (start at 1 A), keep a hand on its output switch, and never connect a battery before
    the current loop is verified.

## Connection

| ESC1 output | Motor wire | Phase |
| --- | --- | --- |
| U | A+ | phase A between U and W |
| V | B+ | phase B between V and W |
| W | A− and B− joined | common leg |

Identify the two coils of the motor with an ohmmeter (1.6 Ω within a pair, open between
pairs). The polarity of a coil only changes the direction of rotation; swapping the
phases A and B reverses it too.

The common wire W carries `−(i_A + i_B)`, up to √2 times the phase current amplitude
(2.83 A at 2 A); the ESC1 leg and its shunt handle it easily.

## Measurements before the first run

| Quantity | Method | Enters |
| --- | --- | --- |
| Phase resistance R | 4-wire measurement, or a DC current from the supply and a voltmeter, at room temperature | `r_mohm`, `mot.R` |
| Phase inductance L | LCR meter at 1 kHz; or the current rise time `L/R` with a voltage step | `l_uh`, `mot.L` |
| Back-EMF constant K_t | spin the unpowered shaft with a drill, measure the open-circuit phase voltage amplitude and the speed: `K_t = E/ω` | `ke_uv_s_per_rad`, `mot.Kt` |
| Detent torque | torque gauge or a lever and a scale on the unpowered shaft | `mot.Td` |
| Current sense | outputs off: ADC zero of both phases; known DC current: counts per ampere | `adc_i_zero`, `adc_i_span`, `i_full_scale_ma` |
| Bus voltage sense | ADC reading at a known supply voltage | `adc_vbus_mv_full` |
| Timer dead time | the value programmed in the timer break/dead-time register | ngspice `BOARD["dead_ns"]` |
| Gate resistors, shunt value | schematic MB1419 | ngspice `BOARD` |

Enter the measured values into the simulation first and rerun T01–T05: the SIL diagram
then predicts what the hardware should do.

## Firmware configuration (STM32G431)

| Item | Setting |
| --- | --- |
| PWM | advanced timer, centre-aligned, 20 kHz: with a 170 MHz timer clock the auto-reload is 4250 (`pwm_period_ticks`) |
| Dead time | the timer's dead-time generator (start with 500 ns, the value of the models) |
| Outputs | complementary outputs of the three legs; break input for a hardware trip |
| ADC | injected conversions of the two phase shunts used by A and B and of the bus voltage, triggered at the counter peak (all low sides on) |
| Interrupt | ADC end of injected conversion → `sstep_fast_loop()` |
| Slow loop | 1 kHz timer or SysTick → `sstep_slow_loop()` |
| Backend | `SSTEP_CFG_MATH_BACKEND_FLOAT` (the Cortex-M4F has an FPU), shared leg only |

Phase A is measured on the U shunt and phase B on the V shunt; the W shunt (common leg)
can be used as a plausibility check: `i_W = −(i_A + i_B)`.

## First power-up sequence

1. Outputs disabled: check the ADC zero readings and the bus voltage reading.
2. `sstep_enable()` with `i_run_ma` = 500, locked shaft: the rotor snaps to a full step
   and holds. Measure the phase currents with a current probe; they must match the
   reference within the current sense resolution.
3. Current step test as in T04 (enable, move by one microstep): compare overshoot and
   settling with the SIL run of the same configuration.
4. Slow move (0.5 rev/s): the rotor follows; listen for the low-speed resonance around
   1.2 rev/s.
5. Raise the speed in steps up to 6 rev/s; log the current amplitude and compare with
   [Results](results.md#voltage-limit-and-speed).
6. Measure the execution time of `sstep_fast_loop()` (GPIO toggle or cycle counter).

## What to compare with the models

| Hardware measurement | Model counterpart | Test |
| --- | --- | --- |
| Current step response | prototype / SIL | T04, S01 |
| Current amplitude vs. speed | prototype | T09, [voltage limit table](results.md#voltage-limit-and-speed) |
| Resonant speed | detent resonance | T11b |
| Switch node edges, gate voltages | ngspice | SP02 |
| Phase voltage error near the zero crossing | switching stage | T10 |

Differences beyond the tolerances point to a wrong parameter (most often `K_t`, the ADC
scaling or the dead time) and are fed back into the models.
