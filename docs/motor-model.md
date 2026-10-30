# Motor Model

The motor model is a two-phase hybrid stepper with sinusoidal back-EMF, a detent torque
term, viscous and dry friction and a rigid load. It is written once
(`model/stepper_motor_f.sci`) and used by the prototype, the Xcos plant block (in C) and
the Python twins. This chapter gives the equations, the sign conventions, the parameters
of the 17HS19-2004S1 and the limits of the model.

## State equations

The state is $x = [\,i_A,\ i_B,\ \omega,\ \theta\,]$: the two phase currents (A), the
mechanical speed (rad/s) and the mechanical rotor angle (rad). With $p = N_s / 4$
electrical periods per mechanical turn (50 for a 200-step motor):

**Electrical part**

$$
\begin{aligned}
L\,\frac{di_A}{dt} &= v_A - R\,i_A - e_A, \qquad e_A = -K_t\,\omega\,\sin(p\theta) \\
L\,\frac{di_B}{dt} &= v_B - R\,i_B - e_B, \qquad e_B = K_t\,\omega\,\cos(p\theta)
\end{aligned}
$$

**Mechanical part**

$$
\begin{aligned}
J\,\frac{d\omega}{dt} &= T_e - T_L - T_f \\
\frac{d\theta}{dt} &= \omega
\end{aligned}
$$

**Torques**

$$
\begin{aligned}
T_e &= K_t\,\left(-i_A \sin(p\theta) + i_B \cos(p\theta)\right) - T_d \sin(4p\theta) \\
T_f &= B\,\omega + T_c \tanh\left(\frac{\omega}{\omega_c}\right)
\end{aligned}
$$

| Symbol | Meaning | Unit |
| --- | --- | --- |
| $v_A$, $v_B$ | phase voltages applied by the power stage | V |
| $R$, $L$ | phase resistance and inductance (no mutual inductance between phases) | Ω, H |
| $K_t$ | torque constant = back-EMF constant | N·m/A = V·s/rad |
| $T_d$ | detent torque amplitude (period: one full step) | N·m |
| $T_L$ | load torque | N·m |
| $B$ | viscous friction | N·m·s/rad |
| $T_c$, $\omega_c$ | dry (Coulomb) friction and its smoothing speed | N·m, rad/s |
| $J$ | rotor + load inertia | kg·m² |

The back-EMF and the torque come from the same flux linkage, so the electrical power
$e_A i_A + e_B i_B$ equals the mechanical power $T_e\,\omega$ (without the detent term, which
does no net work over a step). Test **T00** checks this balance on 1000 random states
(largest error 1.1·10⁻¹³ W).

## Sign convention

With the current vector

$$
i_A = I \cos\varphi, \qquad i_B = I \sin\varphi
$$

the torque is $T_e = K_t\,I \sin(\varphi - p\theta)$: it is zero and restoring at
$p\theta = \varphi$. The rotor therefore **settles at $p\theta = \varphi$**, increasing
$\varphi$ turns it forward, and phase A leads phase B by 90°. The electrical angle between
the field and the rotor, the **load angle** (electrical degrees),

$$
\delta = \varphi - p\theta
$$

is the most useful quantity in every test: with a load $T_L$ the rotor lags by
$\delta = \arcsin\left(T_L / (K_t I)\right)$, the largest static torque is $K_t I$ at
$\delta = 90^\circ$, and beyond $\delta \approx 180^\circ$ the rotor falls into the next pole — the
motor has lost steps.

!!! note
    An early project note used $i_A = I \sin\varphi$, $i_B = I \cos\varphi$. With the torque equation
    above that turns the rotor backwards; the library, the prototype and this manual all
    use the cosine/sine form.

## Parameters of the 17HS19-2004S1

| Parameter | Value | Source |
| --- | --- | --- |
| $R$ | 1.60 Ω | datasheet (±10 %, 25 °C); older listings state 1.4 Ω — **measure** |
| $L$ | 3.0 mH | datasheet at 1 kHz (±20 %) |
| $I_{\mathrm{rated}}$ | 2.0 A | datasheet |
| $K_t$ | 0.2086 N·m/A | derived: holding torque 0.59 N·m with both phases at 2 A, $K_t = 0.59 / (\sqrt{2} \cdot 2)$ — **measure the back-EMF** |
| $N_s$ | 200 (1.8°) | datasheet |
| $J$ | 82 g·cm² = 8.2·10⁻⁶ kg·m² | datasheet, rotor only |
| $B$ | 1·10⁻⁵ N·m·s/rad | assumption |
| $T_d$ | 0 (tests: 0.02 N·m) | not in the datasheet; 0.02 N·m ≈ 3 % of the holding torque is an assumption |
| $T_c$ | 0 (tests: 0.01 N·m) | assumption |
| $\omega_c$ | 0.05 rad/s | numerical smoothing of the dry friction |

The parameters are a Scilab structure returned by `motor_17hs19_2004s1()`
(`params/motor_17hs19_2004s1.sci`); a test or a scenario changes a field
(`mot.Td = 0.02;`) without touching the equations.

!!! tip "Measuring K_t"
    Spin the unpowered shaft (a drill), measure the open-circuit phase voltage amplitude
    $E$ and the speed $\omega$: $K_t = E / \omega$. If the datasheet holding torque is meant for
    one phase only, `K_t` would be 0.295 N·m/A — 41 % more, which changes every speed
    limit in this manual.

## Characteristic values

| Quantity | Formula | 17HS19-2004S1 |
| --- | --- | --- |
| Electrical time constant | $\tau = L / R$ | 1.875 ms |
| Steady current at 3.2 V | $V / R$ | 2.0 A (T01) |
| Rotor natural frequency at current $I$ | $f_n = \frac{1}{2\pi}\sqrt{p K_t I / J}$ | 254 Hz at 2 A, no load |
| Back-EMF amplitude | $K_t\,\omega$ | 1.31 V per rev/s |
| Holding torque | $\sqrt{2}\,K_t I$ (both phases) | 0.59 N·m at 2 A |
| Static torque of the current vector | $K_t I$ | 0.417 N·m at 2 A |

The natural frequency is the stiffness of the "magnetic spring" $p K_t I$ against the
inertia; it decides the low-speed resonance ([Results](results.md#rotor-resonance)).

## Numerical solution

| Use | Solver |
| --- | --- |
| Open-loop studies (`stepper_simulate`) | Scilab `ode` (lsoda), rtol 10⁻⁸, atol 10⁻¹⁰ |
| Closed loop, averaged power stage | fixed-step RK4, 4 steps per PWM period (12.5 µs) |
| Closed loop, switching power stage | RK4 between the switching instants, at least 16 steps per period |
| Python twin of the open-loop model | scipy `solve_ivp` (Radau), rtol 10⁻¹⁰ |

The dry friction $T_c \tanh(\omega/\omega_c)$ is stiff near zero speed (time constant
$J\omega_c / T_c$). RK4 stays stable while $h\,T_c / (J\omega_c) < 2.8$: with
$\omega_c$ = 0.05 rad/s and the 12.5 µs step of the closed loop that is $T_c$ up to about
0.09 N·m. Increase $\omega_c$ for larger friction values.

## Limits of the model

The model is meant for designing and testing the controller. It does **not** include:

- magnetic saturation (inductance and `K_t` drop at high current);
- harmonics of the back-EMF and of the torque other than the detent term;
- mutual inductance between the phases;
- temperature (R rises about 0.4 %/K in copper);
- stiction (the dry friction is smoothed);
- elasticity of the coupling and the load (one rigid inertia).

Effects that depend on these — the exact speed of the mid-band instability, the noise
spectrum, the current at full saturation — must be checked on the hardware.
