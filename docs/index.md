---
title: Stepper-C — stepper motor control from model to metal
description: User manual of the Stepper-C system — control library, simulation and power stage model.
template: home.html
hide:
  - navigation
  - toc
---

<span class="sfs-eyebrow">Quick start</span>

## A driver instance, two loops, four callbacks

Stepper-C needs two functions from your board — one that writes the PWM compare values
and one that switches the gate drivers on or off — and two periodic calls: the fast loop
in the PWM/ADC interrupt and the slow loop at 1 kHz.

```c
#include "sstep.h"

/* Board functions (your HAL) */
extern void board_pwm_set(const uint16_t compare[SSTEP_LEGS_MAX]);
extern void board_gate_enable(bool on);

static int pwm_write(void* ctx, const uint16_t cmp[SSTEP_LEGS_MAX])
{
    (void)ctx;
    board_pwm_set(cmp);
    return 0;
}

static int output_enable(void* ctx, bool on)
{
    (void)ctx;
    board_gate_enable(on);
    return 0;
}

static struct sstep motor;

void app_start(const struct sstep_config* cfg)   /* cfg.hal uses the two functions */
{
    (void)sstep_init(&motor, cfg);
    (void)sstep_enable(&motor);
    (void)sstep_move_to(&motor, 3200);           /* one revolution at 1/16 */
}

void adc_isr(uint16_t ia, uint16_t ib, uint16_t vbus)   /* 20 kHz */
{
    const struct sstep_sample s = { ia, ib, vbus };
    (void)sstep_fast_loop(&motor, &s);
}

void tick_1khz(void)
{
    (void)sstep_slow_loop(&motor);
}
```

A complete configuration for the 17HS19-2004S1 motor on the B-G431B-ESC1 board is in
[Using the library](library.md#configuring-a-driver). Before the first motor turns on
the bench, run the same code in the [software-in-the-loop diagram](sil.md).

## Find your way

| If you want to… | Read |
| --- | --- |
| Understand what the system is and what it is not | [Introduction](overview.md) |
| See how the three repositories work together | [System Architecture](system.md) |
| Install Scilab, the compiler, Python and ngspice and run everything | [Getting Started](getting-started.md) |
| Understand the motor equations and the conventions | [Motor Model](motor-model.md) |
| Understand the current loop, the power stage mapping and the motion generator | [Control Algorithms](control.md) |
| Add the library to a firmware project | [Stepper-C Library](library.md) |
| Look up a function, structure or return code | [API Reference](api.md) |
| Simulate a scenario or change the model | [Simulation](simulation.md) |
| Run the real C code against the motor model in Xcos | [Software in the Loop](sil.md) |
| See what the power stage does in the dead time | [Power Stage Model](power-stage.md) |
| Find a test and its pass criteria | [Test Catalogue](tests.md) |
| Know the speed, resonance and dead time limits | [Results and Design Guidance](results.md) |
| Read everything offline or print it | [PDF manual](https://systemfromscratch-articles.github.io/Stepper-C-Motor-Control-Library/downloads/Stepper-C_System_Manual.pdf) |
