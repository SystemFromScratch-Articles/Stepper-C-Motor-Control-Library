# Parameter Reference

All parameters of the system in one place: the library configuration, the Scilab
parameter structures and the ngspice board values, with the reference values for the
17HS19-2004S1 on the B-G431B-ESC1 at 24 V.

## Stepper-C configuration

| Field | Reference value | Unit | Constraint |
| --- | --- | --- | --- |
| `motor.r_mohm` | 1600 | mΩ | 1 … 10⁷ |
| `motor.l_uh` | 3000 | µH | 1 … 10⁷ |
| `motor.i_rated_ma` | 2000 | mA | 1 … 10⁷ |
| `motor.ke_uv_s_per_rad` | 208600 | µV·s/rad | 0 … 10⁷ (0 = no feed-forward) |
| `motor.full_steps_per_rev` | 200 | — | ≥ 1 |
| `stage.topology` | `SSTEP_TOPOLOGY_SHARED_LEG` | — | compiled in |
| `stage.vbus_nominal_mv` | 24000 | mV | 1 … 10⁷ |
| `stage.vbus_min_mv` | 10000 | mV | 0 or < nominal |
| `stage.vbus_max_mv` | 30000 | mV | 0 or > nominal |
| `stage.i_full_scale_ma` | 4000 (placeholder) | mA | 1 … 10⁷ |
| `stage.i_trip_ma` | 3500 | mA | ≤ full scale |
| `stage.pwm_period_ticks` | 4250 | ticks | ≥ 2 |
| `stage.pwm_freq_hz` | 20000 | Hz | — |
| `stage.dead_time_ns` | 133 (effective) | ns | — |
| `stage.adc_i_zero` | 2048 | counts | ≤ `adc_full` |
| `stage.adc_i_span` | 2047 | counts | ±1 … ±65535 |
| `stage.adc_vbus_mv_full` | 34320 | mV | 1 … 10⁷ |
| `stage.adc_full` | 4095 | counts | ≥ 1 |
| `ctrl.drive_mode` | `SSTEP_DRIVE_CURRENT` | — | — |
| `ctrl.fast_loop_hz` | 20000 | Hz | multiple of the slow rate |
| `ctrl.slow_loop_hz` | 1000 | Hz | ratio ≤ 65535 |
| `ctrl.microsteps` | 16 | — | power of two ≤ `SSTEP_CFG_MICROSTEPS_MAX` |
| `ctrl.current_bw_hz` | 1000 | Hz | ≤ fast rate / 4 |
| `ctrl.i_run_ma` | 2000 | mA | ≤ trip, ≤ rated |
| `ctrl.i_hold_ma` | 1000 | mA | ≤ run |
| `ctrl.hold_delay_ms` | 100 | ms | — |
| `ctrl.v_max` | 16000 | µsteps/s | > 0 |
| `ctrl.accel` | 160000 | µsteps/s² | > 0 |
| `ctrl.decel` | 0 (= accel) | µsteps/s² | — |

## Simulation parameters

| Structure.field | Value | Unit | Source |
| --- | --- | --- | --- |
| `mot.R`, `mot.L`, `mot.I_rated` | 1.60, 3.0·10⁻³, 2.0 | Ω, H, A | datasheet |
| `mot.Kt`, `mot.Ns` | 0.2086, 200 | N·m/A, — | derived, datasheet |
| `mot.J`, `mot.B` | 8.2·10⁻⁶, 1·10⁻⁵ | kg·m², N·m·s/rad | datasheet, assumption |
| `mot.Td`, `mot.Tc`, `mot.w_c` | 0, 0, 0.05 | N·m, N·m, rad/s | not in datasheet (tests: 0.02, 0.01) |
| `brd.vbus`, `brd.topology`, `brd.fs` | 24, `"shared"`, 20000 | V, —, Hz | laboratory supply, ESC1 |
| `brd.vbus_min`, `brd.vbus_max` | 10, 30 | V | trips |
| `brd.i_full`, `brd.i_trip` | 4.0, 3.5 | A | ADC model |
| `brd.period`, `brd.adc_zero`, `brd.adc_span` | 4250, 2048, 2047 | ticks, counts | ADC model |
| `brd.adc_vbus_full`, `brd.adc_full` | 34.32, 4095 | V, counts | ADC model |
| `brd.stage`, `brd.sw_nstep` | `"avg"`, 16 | —, steps | power stage model |
| `brd.dead_ns`, `brd.dead_timer_ns` | 132.6, 500 | ns | ngspice export |
| `brd.rds_on`, `brd.vd` | 3.40·10⁻³, 0.727 | Ω, V | ngspice export |
| `ctl.bw_hz`, `ctl.delay`, `ctl.ff`, `ctl.nsub` | 1000, 1, 1, 4 | Hz, periods, —, steps | controller |
| `mp.M`, `mp.f_slow` | 16, 1000 | —, Hz | motion |
| `mp.v_max`, `mp.acc`, `mp.dec` | 16000, 160000, 160000 | µsteps/s, µsteps/s² | motion |
| `mp.i_run`, `mp.i_hold`, `mp.hold_delay` | 2.0, 1.0, 0.1 | A, A, s | motion |

## ngspice board values

| Key | Value | Unit | Status |
| --- | --- | --- | --- |
| `vbus` | 24 | V | operating point |
| `fs` | 20000 | Hz | operating point |
| `dead_ns` | 500 | ns | assumption (firmware) |
| `vcc` | 12 | V | assumption |
| `rg` | 10 | Ω | assumption |
| `cboot` | 1 | µF | assumption |
| `rsh`, `lsh` | 3, 1 | mΩ, nH | assumption |
| `lloop` | 3 | nH | assumption |
| `tj` | 25 | °C | operating point |

## Derived values

| Quantity | Formula | Value |
| --- | --- | --- |
| `Kp` | `L · 2π · bw` | 18.85 V/A |
| `Ki` | `R · 2π · bw` | 10 053 V/(A·s) |
| `Kb` | `Ts · R / L` | 0.0267 |
| Electrical time constant | `L / R` | 1.875 ms |
| Natural frequency at 2 A | `√(p K_t I / J) / 2π` | 254 Hz |
| Microsteps per revolution | `N_s · M` | 3200 |
| Largest phase voltage, shared leg | `Vbus / √2` | 16.97 V |
| ADC current resolution (placeholder scaling) | `i_full / span` | 1.95 mA/count |
