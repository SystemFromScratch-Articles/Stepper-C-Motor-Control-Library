# API Reference

The public API of Stepper-C 0.1.0 is declared in `inc/sstep_ctrl.h` and included through
`sstep.h`. All functions return an `int` status code, never block and never allocate.
Types and members marked *private* may change in any release.

## Headers

| Header | Content |
| --- | --- |
| `sstep.h` | umbrella header and version (`SSTEP_VERSION`, fallback `"0.1.0"`) |
| `inc/sstep_config.h` | build-time macros (see [Build-time configuration](library.md#build-time-configuration)) |
| `inc/sstep_defs.h` | status codes, `enum sstep_topology`, fault flags, `enum sstep_state` |
| `inc/sstep_math.h` | numeric types (`sstep_real_t`, `sstep_acc_t`, `sstep_angle_t`, `struct sstep_gain`) |
| `inc/sstep_ctrl.h` | configuration, callbacks, loops, commands |

## Status codes

| Code | Value | Meaning |
| --- | --- | --- |
| `SSTEP_OK` | 0 | success |
| `SSTEP_ERR_PARAM` | −1 | NULL pointer, missing required callback, value out of range |
| `SSTEP_ERR_CONFIG` | −2 | values that are valid alone but inconsistent together |
| `SSTEP_ERR_STATE` | −3 | command not allowed in the current state (disabled, faulted, moving) |
| `SSTEP_ERR_UNSUPPORTED` | −4 | topology not compiled in |

## Enumerations and flags

| Name | Values |
| --- | --- |
| `enum sstep_topology` | `SSTEP_TOPOLOGY_FULL_BRIDGE` = 0 (4 legs), `SSTEP_TOPOLOGY_SHARED_LEG` = 1 (3 legs); `SSTEP_LEGS_MAX` = 4 |
| `enum sstep_drive_mode` | `SSTEP_DRIVE_CURRENT` = 0 (PI current control), `SSTEP_DRIVE_VOLTAGE` = 1 (open loop `R·I + ff`) |
| `enum sstep_state` | `SSTEP_STATE_DISABLED` = 0, `SSTEP_STATE_HOLDING` = 1, `SSTEP_STATE_MOVING` = 2, `SSTEP_STATE_FAULT` = 3 |
| `enum sstep_event` | `SSTEP_EVENT_MOVE_DONE` = 0, `SSTEP_EVENT_HOLD_CURRENT` = 1 |
| Fault flags (`uint16_t`) | `SSTEP_FAULT_NONE` 0x0000, `…_OVERCURRENT` 0x0001, `…_OVERVOLTAGE` 0x0002, `…_UNDERVOLTAGE` 0x0004, `…_HAL` 0x0008, `…_EXTERNAL` 0x0010 |

## Callbacks

```c
typedef int  (*sstep_pwm_write_fn)(void* context, const uint16_t compare[SSTEP_LEGS_MAX]);
typedef int  (*sstep_output_enable_fn)(void* context, bool enable);
typedef void (*sstep_fault_fn)(void* context, uint16_t faults);
typedef void (*sstep_event_fn)(void* context, enum sstep_event event);
```

| Callback | Required | Called from | Contract |
| --- | --- | --- | --- |
| `pwm_write` | yes | fast loop (interrupt) | write one compare value per leg (0 … `pwm_period_ticks`; 0 = low side on); the array is valid only during the call; return < 0 on error (raises `SSTEP_FAULT_HAL`) |
| `output_enable` | yes | enable, disable, any fault | `true` enables the gate drivers, `false` switches every leg off (high impedance); return < 0 on error |
| `on_fault` | no | the context that detected the fault (may be the interrupt) | newly raised flags |
| `on_event` | no | slow loop | move done, hold current applied |

## Configuration structures

### `struct sstep_motor_cfg`

| Member | Type | Unit | Range | Meaning |
| --- | --- | --- | --- | --- |
| `r_mohm` | `uint32_t` | mΩ | 1 … 10⁷ | phase resistance at 25 °C |
| `l_uh` | `uint32_t` | µH | 1 … 10⁷ | phase inductance |
| `i_rated_ma` | `uint32_t` | mA | 1 … 10⁷ | rated phase current (upper limit of `i_run_ma`) |
| `ke_uv_s_per_rad` | `uint32_t` | µV·s/rad | 0 … 10⁷ | back-EMF constant = `K_t` in µN·m/A; 0 disables the feed-forward |
| `full_steps_per_rev` | `uint16_t` | — | ≥ 1 | 200 for 1.8° |

### `struct sstep_stage_cfg`

| Member | Type | Unit | Meaning |
| --- | --- | --- | --- |
| `topology` | `enum sstep_topology` | — | power stage topology |
| `vbus_nominal_mv` | `uint32_t` | mV | nominal bus voltage, base of the per-unit voltage |
| `vbus_min_mv` | `uint32_t` | mV | undervoltage trip, below nominal; 0 = disabled |
| `vbus_max_mv` | `uint32_t` | mV | overvoltage trip, above nominal; 0 = disabled |
| `i_full_scale_ma` | `uint32_t` | mA | phase current at ADC full scale, base of the per-unit current |
| `i_trip_ma` | `uint32_t` | mA | overcurrent trip, ≤ `i_full_scale_ma` |
| `pwm_period_ticks` | `uint16_t` | ticks | compare value for 100 % duty (≥ 2) |
| `pwm_freq_hz` | `uint32_t` | Hz | PWM frequency |
| `dead_time_ns` | `uint32_t` | ns | dead time for compensation (stored; compensation planned) |
| `adc_i_zero` | `uint16_t` | counts | current ADC reading at 0 A (≤ `adc_full`) |
| `adc_i_span` | `int32_t` | counts | counts from 0 A to +`i_full_scale_ma`; negative for an inverting amplifier; ±1 … ±65535 |
| `adc_vbus_mv_full` | `uint32_t` | mV | bus voltage at ADC reading `adc_full` |
| `adc_full` | `uint16_t` | counts | largest ADC reading (4095 for 12 bits) |

### `struct sstep_ctrl_cfg`

| Member | Type | Unit | Meaning |
| --- | --- | --- | --- |
| `drive_mode` | `enum sstep_drive_mode` | — | current or voltage drive |
| `fast_loop_hz` | `uint32_t` | Hz | rate of `sstep_fast_loop()`; integer multiple of `slow_loop_hz`, ratio ≤ 65535 |
| `slow_loop_hz` | `uint32_t` | Hz | rate of `sstep_slow_loop()` |
| `microsteps` | `uint16_t` | — | microsteps per full step, power of two ≤ `SSTEP_CFG_MICROSTEPS_MAX` |
| `current_bw_hz` | `uint32_t` | Hz | current loop bandwidth, ≤ `fast_loop_hz / 4` |
| `i_run_ma` | `uint32_t` | mA | peak phase current while moving, ≤ `i_trip_ma` and ≤ `i_rated_ma` |
| `i_hold_ma` | `uint32_t` | mA | peak phase current at standstill, ≤ `i_run_ma` |
| `hold_delay_ms` | `uint32_t` | ms | standstill time before the hold current |
| `v_max` | `uint32_t` | µsteps/s | maximum velocity |
| `accel` | `uint32_t` | µsteps/s² | acceleration |
| `decel` | `uint32_t` | µsteps/s² | deceleration; 0 = same as `accel` |

### `struct sstep_config`, `struct sstep_callbacks`

`struct sstep_config` groups `motor`, `stage`, `ctrl` and `hal`
(`struct sstep_callbacks`: `context`, `pwm_write`, `output_enable`, `on_fault`,
`on_event`). It is copied by `sstep_init()` and may be discarded afterwards.

### `struct sstep_sample`

| Member | Type | Meaning |
| --- | --- | --- |
| `i_a` | `uint16_t` | phase A current, ADC counts (ignored in voltage drive) |
| `i_b` | `uint16_t` | phase B current, ADC counts (ignored in voltage drive) |
| `vbus` | `uint16_t` | bus voltage, ADC counts |

### `struct sstep_status`

| Member | Type | Unit |
| --- | --- | --- |
| `state` | `enum sstep_state` | — |
| `faults` | `uint16_t` | active fault flags |
| `position` | `int32_t` | commanded position, µsteps |
| `target` | `int32_t` | target of the move, µsteps |
| `velocity` | `int32_t` | commanded velocity, µsteps/s |
| `i_a_ma`, `i_b_ma` | `int32_t` | last measured phase currents, mA |
| `vbus_mv` | `uint32_t` | last measured bus voltage, mV |

### `struct sstep` (private)

The driver instance, allocated by the application and initialised by `sstep_init()`. Its
members (configuration copy, derived gains, double-buffered setpoint, PI integrators,
motion state, faults, state) are private; use the functions only.

## Functions

### `sstep_init()`

```c
int sstep_init(struct sstep* m, const struct sstep_config* cfg);
```

Validates the configuration, copies it, derives the per-unit gains (`Kp = L ωc`,
`Ki = R ωc`, `Kb = Ts R / L`), the ADC scaling, the trip levels and the motion limits.
No floating point is used with the fixed point backend. The outputs stay disabled.

| Parameter | Meaning |
| --- | --- |
| `m` | driver instance |
| `cfg` | configuration; copied |

| Returns | When |
| --- | --- |
| `SSTEP_OK` | state `SSTEP_STATE_DISABLED` |
| `SSTEP_ERR_PARAM` | NULL pointer, missing `pwm_write`/`output_enable`, a field out of range |
| `SSTEP_ERR_CONFIG` | inconsistent fields (trip above full scale, run current above trip or rated, loop rates, bandwidth, bus thresholds, gains that do not fit) |
| `SSTEP_ERR_UNSUPPORTED` | topology not compiled in |

### `sstep_enable()`

```c
int sstep_enable(struct sstep* m);
```

Enables the outputs and holds the current position with the run current (the hold
current follows after `hold_delay_ms`). Resets the integrators. No effect when already
enabled.

| Returns | When |
| --- | --- |
| `SSTEP_OK` | state `SSTEP_STATE_HOLDING` |
| `SSTEP_ERR_PARAM` | `m` is NULL |
| `SSTEP_ERR_STATE` | faulted, or `output_enable()` failed (then `SSTEP_FAULT_HAL`) |

### `sstep_disable()`

```c
int sstep_disable(struct sstep* m);
```

Stops immediately and switches the outputs off: the motor coasts without holding torque.
A faulted driver stays faulted. Returns `SSTEP_OK` or `SSTEP_ERR_PARAM`.

### `sstep_fast_loop()`

```c
int sstep_fast_loop(struct sstep* m, const struct sstep_sample* sample);
```

Call once per PWM period from the PWM/ADC interrupt. Converts the sample, checks the
overcurrent and bus voltage trips (when the outputs are on), runs the current
controllers, limits and maps the voltage and calls `pwm_write()`. Bounded execution
time. With the outputs off it only stores the measurements.

| Returns | When |
| --- | --- |
| `SSTEP_OK` | always, except: |
| `SSTEP_ERR_PARAM` | NULL pointer (only with `SSTEP_CFG_ARG_CHECKS` = 1) |

### `sstep_slow_loop()`

```c
int sstep_slow_loop(struct sstep* m);
```

Call at `slow_loop_hz`. Advances the motion generator, selects run or hold current,
updates the bus voltage scale, publishes the setpoint for the fast loop, sets the state
(HOLDING/MOVING, or FAULT if the fast loop tripped meanwhile) and reports events.
Returns `SSTEP_OK` or `SSTEP_ERR_PARAM`.

### `sstep_move_to()`, `sstep_move_by()`

```c
int sstep_move_to(struct sstep* m, int32_t position);
int sstep_move_by(struct sstep* m, int32_t delta);
```

Start a move to an absolute position, or relative to the current *target*, with the
trapezoidal profile. A running command is replaced smoothly (no velocity step).

| Returns | When |
| --- | --- |
| `SSTEP_OK` | move started |
| `SSTEP_ERR_PARAM` | `m` is NULL; `move_by` target outside `int32_t` |
| `SSTEP_ERR_STATE` | disabled or faulted |

### `sstep_run()`

```c
int sstep_run(struct sstep* m, int32_t velocity);
```

Run at a constant signed velocity [µsteps/s] until another command, accelerating with
the configured limits. `|velocity|` ≤ `v_max`. Returns `SSTEP_OK`, `SSTEP_ERR_PARAM`
(NULL or velocity above `v_max`) or `SSTEP_ERR_STATE` (disabled or faulted).

### `sstep_stop()`

```c
int sstep_stop(struct sstep* m);
```

Decelerates to standstill with the deceleration limit, then holds. No effect when
nothing moves. Returns `SSTEP_OK` or `SSTEP_ERR_PARAM`.

### `sstep_set_position()`

```c
int sstep_set_position(struct sstep* m, int32_t position);
```

Redefines the current position (homing). The rotor does not move: the electrical angle
is kept and only the numbering changes. Returns `SSTEP_OK`, `SSTEP_ERR_PARAM` or
`SSTEP_ERR_STATE` (a command is running).

### `sstep_set_current()`

```c
int sstep_set_current(struct sstep* m, uint32_t run_ma, uint32_t hold_ma);
```

Changes the run and hold currents; used from the next slow loop period.

| Returns | When |
| --- | --- |
| `SSTEP_OK` | accepted |
| `SSTEP_ERR_PARAM` | NULL, `run_ma` = 0, a value above 10⁷ |
| `SSTEP_ERR_CONFIG` | `hold_ma` > `run_ma`, `run_ma` above `i_trip_ma` or `i_rated_ma` |

### `sstep_set_motion_limits()`

```c
int sstep_set_motion_limits(struct sstep* m, uint32_t v_max, uint32_t accel, uint32_t decel);
```

Changes the velocity [µsteps/s], acceleration and deceleration [µsteps/s²] limits
(`decel` = 0: same as `accel`). The motion generator uses them from the next slow loop
period, also for a running move. Returns `SSTEP_ERR_PARAM` for zero values or values
that become zero or too large in the internal units (for example an acceleration below
`slow_loop_hz² / 65536`).

### `sstep_report_fault()`

```c
int sstep_report_fault(struct sstep* m, uint16_t faults);
```

Raises application faults (a driver fault pin, over-temperature), typically
`SSTEP_FAULT_EXTERNAL`: the outputs switch off and the state becomes FAULT. May be called
from an interrupt. Returns `SSTEP_OK` or `SSTEP_ERR_PARAM`.

### `sstep_clear_faults()`

```c
int sstep_clear_faults(struct sstep* m);
```

Clears all faults; the driver goes to DISABLED and must be enabled again. Returns
`SSTEP_OK` or `SSTEP_ERR_PARAM`.

### `sstep_get_status()`

```c
int sstep_get_status(const struct sstep* m, struct sstep_status* status);
```

Fills a snapshot in engineering units (state, faults, position, target, velocity,
currents, bus voltage). Returns `SSTEP_OK` or `SSTEP_ERR_PARAM`.

## Calling contexts

| Function | Context |
| --- | --- |
| `sstep_fast_loop()` | PWM/ADC interrupt only |
| `sstep_report_fault()` | any (interrupt allowed) |
| all others | the slow loop context (one task), never concurrently with each other |
