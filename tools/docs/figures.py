#******************************************************************************
# Stepper-C System Manual
#
# Description: Generates the data figures of the manual (docs/assets/figures/*.svg)
#              by running the Python twins of sfs-stepper-sim and reading the export
#              of sfs-stepper-power-spice. Run after a model change:
#                  python tools/docs/figures.py [--sim DIR] [--spice DIR]
#              (defaults: ../sfs-stepper-sim and ../sfs-stepper-power-spice)
#
# Author:      Anton Vynohradov
# Email:       avynohradov@systemfromscratch.com
# License:     Apache License 2.0
# Copyright (c) 2026 Anton Vynohradov
#
# SPDX-License-Identifier: Apache-2.0
#*****************************************************************************

"""Data figures of the Stepper-C system manual. Every number in a figure comes from a
model run here; the same values are printed by the tests of sfs-stepper-sim."""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
OUT = os.path.join(ROOT, "docs", "assets", "figures")

# documentation palette (tools/docs/svgkit.py)
NAVY, BLUE, TEAL, ORANGE = "#0B2545", "#1E5AA8", "#0F8B9A", "#E07A00"
GREEN, RED, GREY, LINE = "#2E7D32", "#C62828", "#5A6472", "#C9D3E0"

plt.rcParams.update({
    "svg.fonttype": "none",
    "font.family": ["Inter", "DejaVu Sans"],
    "font.size": 9.5,
    "axes.edgecolor": LINE,
    "axes.labelcolor": NAVY,
    "axes.titlesize": 10,
    "axes.titleweight": "bold",
    "axes.titlecolor": NAVY,
    "axes.grid": True,
    "grid.color": "#E6EBF2",
    "grid.linewidth": 0.8,
    "xtick.color": GREY,
    "ytick.color": GREY,
    "legend.frameon": False,
    "lines.linewidth": 1.6,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
})


def save(fig, name):
    os.makedirs(OUT, exist_ok=True)
    fig.tight_layout()
    path = os.path.join(OUT, name)
    fig.savefig(path)
    plt.close(fig)
    print("wrote", os.path.relpath(path, ROOT))


# ------------------------------------------------------------------------------

def fig_current_step(rc, rx):
    m, c, brd = rc.MOTOR, rc.CTRL, dict(rc.BOARD, topology="shared")
    step = lambda t: ((2.0 if t >= 1e-3 else 0.0), 0.0, 0.0, 0.0)  # noqa: E731
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.4, 2.8), sharey=True)
    log = rc.sim_closed_loop(m, brd, c, step, 4e-3, locked=True)
    t = (log[:, 0] - 1e-3) * 1e3
    a1.step(t, log[:, 5], where="post", color=GREY, ls="--", lw=1.2, label="reference")
    a1.plot(t, log[:, 1], color=BLUE, label="i_A (sampled)")
    a1.set_title("Nominal motor (T04)")
    a1.set_xlabel("time after the step [ms]")
    a1.set_ylabel("phase current [A]")
    a1.legend(loc="lower right")
    colors = [BLUE, TEAL, ORANGE, RED]
    for (fr, fl), col in zip(rx.T08_CURRENT, colors):
        plant = dict(m, R=m["R"] * fr, L=m["L"] * fl)
        log = rc.sim_closed_loop(plant, brd, c, step, 4e-3, locked=True, m_ctrl=m)
        a2.plot(t, log[:, 1], color=col, label=f"R ×{fr}, L ×{fl}")
    a2.set_title("Plant ≠ controller model (T08)")
    a2.set_xlabel("time after the step [ms]")
    a2.legend(loc="lower right", fontsize=8.5)
    for a in (a1, a2):
        a.set_xlim(-0.2, 3.0)
    save(fig, "current-step.svg")


def fig_move(rc, rm):
    m, c, brd, mp = rc.MOTOR, rc.CTRL, rc.BOARD, rm.MOTION
    log, mo = rm.run(m, brd, c, mp, [(0.0, rm.MOVE, 6400.0)], 0.7)
    h = np.array(mo.hist)
    t = log[:, 0] * 1e3
    fig, (a1, a2, a3) = plt.subplots(3, 1, figsize=(7.4, 5.4), sharex=True)
    a1.step(h[:, 0] * 1e3, h[:, 2] / (mp["M"] * m["Ns"]), where="post", color=GREY, ls="--",
            lw=1.2, label="commanded")
    a1.plot(t, log[:, 3] / (2 * math.pi), color=BLUE, lw=1.2, label="rotor")
    a1.set_ylabel("speed [rev/s]")
    a1.set_title("Move of 2 revolutions: 5 rev/s, 50 rev/s², shared leg, 24 V (T05)")
    a1.legend(loc="upper right")
    amp = np.hypot(log[:, 1], log[:, 2])
    a2.plot(t, amp, color=TEAL, lw=1.2)
    a2.plot(t, log[:, 10], color=GREY, ls="--", lw=1.2)
    a2.set_ylabel("current [A]")
    a2.set_ylim(0, 2.4)
    a2.annotate("run current 2 A", (420, 2.05), color=GREY, fontsize=8.5)
    a2.annotate("hold current 1 A after 100 ms", (560, 0.75), color=GREY, fontsize=8.5,
                ha="center")
    a3.plot(t, rm.load_angle(log, m), color=ORANGE, lw=1.2)
    a3.set_ylabel("load angle [° el.]")
    a3.set_xlabel("time [ms]")
    save(fig, "move.svg")


def fig_voltage_limit(rc, rx):
    m, c = rc.MOTOR, rc.CTRL
    speeds = np.arange(1, 13, 1.0)
    fig, ax = plt.subplots(figsize=(7.4, 2.9))
    for topo, col, label in (("full", BLUE, "two H-bridges"),
                             ("shared", TEAL, "shared leg (B-G431B-ESC1)")):
        brd = dict(rc.BOARD, topology=topo)
        amps = []
        for v in speeds:
            log = rc.sim_closed_loop(m, brd, c, rx.ref_speed(2.0, v, m, 0.2), 0.4)
            sel = log[:, 0] >= 0.3
            amps.append(np.mean(np.hypot(log[sel, 1], log[sel, 2])))
        ax.plot(speeds, amps, "o-", color=col, label=label, ms=4)
    ax.axhline(2.0, color=GREY, ls="--", lw=1)
    ax.axvspan(9.5, 12.5, color="#FDECEC", lw=0)
    ax.annotate("shared leg: limit cycle (T11),\nmean of an oscillating current", (9.65, 0.25),
                color=RED, fontsize=8.5)
    ax.set_xlim(0.5, 12.5)
    ax.set_xlabel("speed [rev/s]")
    ax.set_ylabel("current amplitude [A]")
    ax.set_title("Current at constant speed, 24 V, reference 2 A")
    ax.set_ylim(0, 2.2)
    ax.legend(loc="lower left")
    save(fig, "voltage-limit.svg")


def fig_switching(rs, spice_json):
    """Current within three PWM periods (shared leg, locked, 2 A) and the dead time
    error against the phase current (ngspice and the sim step model)."""
    m = rs.MOTOR
    sg = dict(rs.STAGE)
    brd = dict(rs.BOARD, topology="shared", stage="switching", sw=sg)
    log, ext = rs.sim_closed_loop(m, brd, rs.CTRL, lambda t: (2.0, 0.6, 0.0, 0.0), 0.02,
                                  locked=True)
    # replay the last three periods with a fine trace
    Ts = 1.0 / brd["fs"]
    x = np.array(log[-3, 1:5])
    duty_hist = []
    for k in (-3, -2, -1):
        vref = (log[k, 7], log[k, 8])
        _, duty, _ = rs.bridge_avg(vref, brd["vbus"], "shared")
        duty_hist.append(duty)
    tt, ia, ib = [], [], []
    t0 = 0.0
    for duty in duty_hist:
        td = sg["dead_ns"] * 1e-9
        evs = [rs.leg_events(d, Ts, td) for d in duty]
        bps = sorted(set([0.0, Ts] + [te for ev in evs for te, _ in ev if 0.0 < te < Ts]))
        for j in range(len(bps) - 1):
            ta, tb = bps[j], bps[j + 1]
            states = [rs.leg_state(ev, ta) for ev in evs]
            n = max(2, int(math.ceil((tb - ta) / (Ts / 200))))
            h = (tb - ta) / n
            for i in range(n):
                vA, vB = rs.phase_voltages(states, x, brd["vbus"], "shared", sg)
                x = rs.rk4(x, (vA, vB, 0.0), m, h, True)
                tt.append(t0 + ta + (i + 1) * h)
                ia.append(x[0])
                ib.append(x[1])
        t0 += Ts
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.4, 2.9))
    tt = np.array(tt) * 1e6
    a1.plot(tt, (np.array(ia) - np.mean(ia)) * 1e3, color=BLUE, label="i_A − mean")
    a1.plot(tt, (np.array(ib) - np.mean(ib)) * 1e3, color=TEAL, label="i_B − mean")
    for k in range(4):
        a1.axvline(k * Ts * 1e6, color=GREEN, ls=":", lw=1)
    a1.set_xlabel("time [µs]; dotted: ADC sampling instants")
    a1.set_ylabel("ripple [mA]")
    a1.set_title("Current ripple, 20 kHz, locked rotor")
    a1.legend(loc="upper center", bbox_to_anchor=(0.5, -0.24), fontsize=8.5, ncol=2)
    if spice_json and os.path.isfile(spice_json):
        with open(spice_json) as f:
            st = json.load(f)
        tab = np.array(st["leg_error_table"])
        a2.plot(tab[:, 0], tab[:, 1] * 1e3, "o", color=ORANGE, ms=5, label="ngspice")
        i = np.linspace(-3, 3, 601)
        k = (24.0 + 2 * st["vd"]) * st["dead_eff_ns"] * 1e-9 * 20000.0
        model = (-np.sign(i) * k - i * st["r_leg"]) * 1e3
        a2.plot(i, model, color=BLUE, lw=1.4, label="sim model (td_eff)")
        a2.legend(loc="upper right", fontsize=8.5)
    a2.axhline(0, color=LINE, lw=1)
    a2.set_xlabel("phase current [A]")
    a2.set_ylabel("leg voltage error [mV]")
    a2.set_title("Dead time error of one leg (24 V)")
    save(fig, "switching.svg")


def fig_resonance(rc, rx):
    m, c, brd = rc.MOTOR, rc.CTRL, dict(rc.BOARD, topology="shared")
    p = m["Ns"] / 4
    fn = math.sqrt(p * m["Kt"] * 2.0 / m["J"]) / (2 * math.pi)
    md = dict(m, Td=rx.TD_T11)
    speeds = np.round(np.arange(0.6, 2.01, 0.05), 2)
    amp = []
    for v in speeds:
        log = rc.sim_closed_loop(md, brd, c, rx.ref_speed(2.0, v, m, 0.1), 0.3)
        sel = log[:, 0] >= 0.2
        a = rx.load_angle(log[sel], m)
        amp.append((a.max() - a.min()) / 2)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.4, 2.9))
    a1.plot(speeds, amp, "o-", color=BLUE, ms=3.5)
    a1.axvline(fn / (4 * p), color=ORANGE, ls="--", lw=1.2)
    a1.annotate("4 p n = f_n", (fn / (4 * p) + 0.03, max(amp) * 0.92), color=ORANGE, fontsize=8.5)
    a1.set_xlabel("speed [rev/s]")
    a1.set_ylabel("rotor oscillation [± ° el.]")
    a1.set_title(f"Detent {rx.TD_T11} N·m: low-speed resonance")
    for v, col in ((5, BLUE), (8, TEAL), (11, RED)):
        log = rc.sim_closed_loop(m, brd, c, rx.ref_speed(2.0, v, m, 0.2), 0.5)
        sel = log[:, 0] >= 0.35
        a2.plot((log[sel, 0] - 0.35) * 1e3, rx.load_angle(log[sel], m), color=col, lw=1.1,
                label=f"{v} rev/s")
    a2.set_xlabel("time [ms]")
    a2.set_ylabel("load angle [° el.]")
    a2.set_title("Mid-band instability beyond the voltage limit")
    a2.legend(loc="upper center", bbox_to_anchor=(0.5, -0.24), fontsize=8.5, ncol=3)
    save(fig, "resonance.svg")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sim", default=os.path.join(os.path.dirname(ROOT), "sfs-stepper-sim"))
    ap.add_argument("--spice", default=os.path.join(os.path.dirname(ROOT),
                                                    "sfs-stepper-power-spice"))
    args = ap.parse_args()
    sys.path.insert(0, os.path.join(args.sim, "tools"))
    import ref_ctrl as rc
    import ref_ext as rx
    import ref_motion as rm
    import ref_switching as rs

    fig_current_step(rc, rx)
    fig_move(rc, rm)
    fig_voltage_limit(rc, rx)
    fig_switching(rs, os.path.join(args.spice, "export", "stage_esc1.json"))
    fig_resonance(rc, rx)
    edges = os.path.join(args.spice, "docs", "leg_edges.png")
    if os.path.isfile(edges):
        shutil.copyfile(edges, os.path.join(OUT, "leg-edges.png"))
        print("copied docs/leg_edges.png from", args.spice)


if __name__ == "__main__":
    main()
