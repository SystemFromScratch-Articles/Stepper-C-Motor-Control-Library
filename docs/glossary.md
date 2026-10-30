# Glossary

Anti-windup (back-calculation)
:   Feedback of the difference between the applied and the requested voltage into the PI
    integrator while the power stage limits the voltage, so the integrator does not grow
    without bound.

Back-EMF
:   The voltage induced in a phase by the moving rotor, `K_t ω` in amplitude.

Bootstrap
:   The supply of the high-side gate driver: a capacitor charged from VCC through a
    diode (in the L6387E a DMOS) while the low side conducts.

Centre-aligned PWM
:   PWM whose counter counts up and down; the pulses of all legs are centred in the
    period, and the counter peak is a common instant at which all low sides conduct.

Dead time
:   The interval in which both transistors of a leg are off, inserted to prevent a
    short circuit. The *timer* dead time is programmed; the *effective* dead time is its
    net effect on the phase voltage after the driver and transistor delays.

Detent torque
:   The torque of the permanent magnet on the unpowered motor, periodic with one full
    step.

Electrical angle
:   `p θ`: one electrical turn equals four full steps.

Feed-forward
:   A control signal computed from a model (here the back-EMF from the commanded speed)
    and added to the controller output.

Hold current
:   The reduced phase current applied after a standstill time, to limit heating.

Leg
:   A half-bridge: two transistors in series between the bus and ground, with the output
    between them.

Load angle
:   `δ = φ − p θ`, the electrical angle between the current vector and the rotor.

Mid-band instability
:   A rotor oscillation that appears at medium speeds when the drive cannot control the
    current any more (voltage limit) and the back-EMF coupling undamps the rotor.

Miller plateau
:   The gate voltage at which a MOSFET switches; the gate current then only charges the
    gate-drain capacitance while the drain voltage changes.

Per unit (pu)
:   A quantity divided by its base value (current: ADC full scale; voltage: nominal bus
    voltage).

Pole-zero cancellation
:   Choosing the PI zero at the pole of the R-L phase (`Ki / Kp = R / L`), so the closed
    loop is first order.

Q15, Q27
:   Fixed point formats with 15 or 27 fractional bits.

Shoot-through
:   Both transistors of a leg conducting at the same time; a short circuit of the bus.

SIL
:   Software in the loop: the target code running in a simulation.

Slow loop, fast loop
:   The two periodic functions of the library: motion at 1 kHz, current control at the
    PWM rate.

Synchronism
:   The rotor following the rotating field; lost when the load angle exceeds about 180°.

Twin
:   An independent implementation of the same algorithm used for cross-checking.

VDMOS
:   The ngspice model of a vertical power MOSFET with body diode and non-linear
    capacitances.
