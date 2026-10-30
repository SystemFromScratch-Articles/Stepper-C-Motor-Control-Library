# Test Catalogue

Every claim in this manual is backed by a test that prints the measured value. This
chapter lists all tests of the three repositories with their stimulus, their pass
criterion and the last result. The **Status** column says where the result comes from:
*Scilab* (run in Scilab 2027), *Python* (run in the Python twin, the Scilab run of this
version is pending), *C* (GoogleTest), *ngspice*.

## Naming

| Prefix | Meaning | Where |
| --- | --- | --- |
| `T` | test of the model or of the prototype against theory or limits | `sfs-stepper-sim/tests/test_T*.sce`, twins in `tools/` |
| `X` | cross-check: Scilab equals its Python twin | `tests/test_X*.sce` + `tests/reference/*.csv` |
| `B` | power stage mapping | `tests/test_B01_bridge.sce` |
| `S` | software in the loop: the C library in Xcos equals the prototype | `tests/test_S01_sil.sce` |
| `SP` | ngspice power stage | `sfs-stepper-power-spice/tools/run_tests.py` |
| GoogleTest suites | library unit tests | `sfs-stepper-ctrl/tests/unit/` |

## Motor model

| Test | Stimulus | Pass criterion | Result | Status |
| --- | --- | --- | --- | --- |
| T00 | 1000 random states; current vector at φ = 0.7 | power balance `e·i = T·ω` within 10⁻⁹ W; zero and restoring torque at `p θ = φ` | 1.1·10⁻¹³ W; −1.0·10⁻⁵ N·m restoring | Scilab |
| T01 | 3.2 V on phase A, locked and free rotor | steady current `V/R` within 10⁻⁶; free rotor stays at θ = 0 | 2.000000 A, error 2·10⁻⁹ | Scilab |
| T02 | voltage step, locked rotor | `i(t) = V/R (1 − e^(−t/τ))`, t63 = L/R within 0.1 % | t63 = 1.8750 ms | Scilab |
| X01 | rotating voltage 5 Hz el., free rotor | Scilab (lsoda) equals Python (Radau) | 3.6·10⁻⁸ A, 8.8·10⁻⁷ rad/s | Scilab |

## Power stage and current loop

| Test | Stimulus | Pass criterion | Result | Status |
| --- | --- | --- | --- | --- |
| B01 | 20 000 random voltage requests, both topologies | duties 0 … 1, direction kept, exact when feasible; largest circle `Vbus` / `Vbus/√2` | direction error 2·10⁻¹⁶; 24.0000 V / 16.9706 V | Scilab |
| T03 | microstepping 2 A, 10 Hz el. | A leads B by 90° ± 0.5°, amplitude ± 10 mA, rotor follows | 90.000°, 2.0000 A, lag 0.57° | Scilab |
| T04 | current step 0 → 2 A, locked, both topologies | overshoot < 5 %, settling (2 %) < 1 ms, error < 0.1 % | 1.12 %, rise 0.35 ms, settling 0.40 ms | Scilab |
| X02 | current step, shared leg | Scilab equals Python | 5·10⁻¹³ A | Scilab |
| T08 | controller for the nominal motor; plant R ×0.9 … 1.3, L ×0.8 … 1.2 (current step) and R, L, J ×5, load 0.15 N·m (ramp to 4 rev/s) | step: overshoot < 10 %, settling < 2 ms, error < 1 %; ramp: load angle < 90° | worst settling 1.6 ms (R ×1.3, L ×0.8); worst load angle 46.3° | Python |
| T09 | 8 rev/s, both topologies | shared leg limited earlier than full bridge, both synchronous | 1.862 A / 1.557 A, load angle 24.5° / 39.3° | Scilab |
| T10 | switching stage: hold 2 A; ±2 A with dead time; 4 rev/s | ideal switches = averaged (< 1 mA); ripple = analytic ± 5 %; dead time error = formula ± 1 %; synchronous, peak < trip | 0.01 mA; 23.11 mA p-p (analytic 23.11); 0.07 mV deviation; peak 2.03 A | Python |
| X04 | switching stage, shared leg, 4 rev/s | Scilab equals Python (10⁻⁶ A) | — | pending |

## Motion

| Test | Stimulus | Pass criterion | Result | Status |
| --- | --- | --- | --- | --- |
| T05 | move 6400 µsteps (2 rev), 5 rev/s, 50 rev/s² | target exact, `|Δv|` ≤ acc, monotonic, load angle < 45° | 499 ms, load angle 15.24°, final 6400.00 µsteps | Scilab |
| T06 | load step 0.25 and 0.5 N·m at 1 rev/s | synchronous below `K_t I` with angle `asin(T/(K_t I))`; loss of synchronism detected above | 37.21° (theory 37.21°); slip at 151.9 ms | Scilab |
| T07 | reversal +4 → −4 rev/s | synchronous, deceleration limit kept, final speed | load angle 12.25°, −240.0 rpm | Scilab |
| X03 | move 160 µsteps | motion generator + loop equal the Python twin | 4.9·10⁻¹³ A | Scilab |

## Resonance and friction

| Test | Stimulus | Pass criterion | Result | Status |
| --- | --- | --- | --- | --- |
| T11a | angle step 0.1 rad at 2 A | natural frequency `√(p K_t I / J)/2π` ± 5 % | 248.1 Hz (theory 253.8 Hz) | Python |
| T11b | speed sweep 0.8 … 1.8 rev/s, detent 0.02 N·m | largest oscillation at `4 p n = f_n` ± 10 %, peak > 3× minimum | peak at 1.2 rev/s (theory 1.27), ±13.6° | Python |
| T11c | 5, 8, 11 rev/s, shared leg, 24 V | oscillation < 1° / < 5° below the voltage limit, > 20° beyond | 0.0° / 1.3° / 47.6° | Python |
| T12 | unpowered rotor without back-EMF, `T_c` 0.01 N·m, 50 rad/s | spin-down time `(J/B) ln((ω0 + T_c/B)/(ω + T_c/B))` ± 1 % | 39.60 ms (theory 39.60 ms) | Python |

## Software in the loop

| Test | Scenario | Pass criterion | Result | Status |
| --- | --- | --- | --- | --- |
| S01 | current step, locked rotor | currents < 5 mA from the prototype | — | pending re-run |
| S02 | move 640 µsteps | currents < 5 mA, commanded angle identical, rotor < 0.05 µstep | 1.05 mA, 0, 0.0075 µstep | Scilab |
| S03 | 8 rev/s, both topologies | amplitude as T09 ± 30 mA | 1.862 A / 1.557 A | Scilab |
| S04 | run 4 rev/s, switching stage | currents and peak < 5 mA from the prototype | — | pending |

## Library unit tests (GoogleTest)

| Suite | Tests | Covers |
| --- | --- | --- |
| `SstepMath` | 29 | saturating arithmetic, gains from ratios (brute force over 200 000 cases), sine/cosine accuracy, integrator, duty to ticks |
| `SstepBridge` | 5 | random requests, circular amplitude, bus voltage scaling, very large requests keep the direction, zero request centred |
| `SstepMotion` | 10 | integer square root, two-revolution move (499 ms), short and negative moves, random targets without velocity step, retarget and reversal, run and reverse, hold |
| `SstepApi` | 24 | configuration validation, NULL arguments, state rules, trips, faults, hardware errors, late slow loop, bus voltage corner cases, feed-forward saturation |
| `SstepLoop` | 8 | closed loop with a motor model: current step, move, load step, reversal and stop, voltage limit by topology, bus voltage compensation, voltage drive, other microstep settings |

Result: 76 tests pass with the fixed point backend, 75 with float (one test is
backend-specific); 100 % line and branch coverage of `src/`; no finding under ASan and
UBSan. Status: C.

## ngspice

| Test | Pass criterion | Result | Status |
| --- | --- | --- | --- |
| SP01 | device against the datasheet (Rds ±5 %, capacitances and Qg ±10 %, VSD ≤ 1.2 V) | all within | ngspice |
| SP02 | step model within 15 mV for 1–3 A; driven gates never overlap | 12.8 mV; 154 ns gap | ngspice |
| SP03 | shunt sample within 1 % | exact, settling 345 ns | ngspice |

## Running everything

| Repository | Command |
| --- | --- |
| [Stepper-C](https://github.com/AntonVynohradov/Stepper-C) | `ctest --test-dir "build/[UnitTests]Stepper Motor Control"` (and the Float preset) |
| [sfs-stepper-sim](https://github.com/AntonVynohradov/sfs-stepper-sim) | `scilab-cli -f tests/run_all.sce`; Python: `python tools/ref_*.py` |
| [sfs-stepper-power-spice](https://github.com/AntonVynohradov/sfs-stepper-power-spice) | `python tools/run_tests.py` |
