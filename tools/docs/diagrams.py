#******************************************************************************
# Stepper-C System Manual
#
# Description: Generates the SVG diagrams of the manual (docs/assets/images/*.svg).
#              Run after changing a diagram:
#                  python tools/docs/diagrams.py
#
# Author:      Anton Vynohradov
# Email:       avynohradov@systemfromscratch.com
# License:     Apache License 2.0
# Copyright (c) 2026 Anton Vynohradov
#
# SPDX-License-Identifier: Apache-2.0
#*****************************************************************************

"""Documentation diagrams of the Stepper-C system, built with svgkit. Preview every
diagram (headless Chrome --screenshot) and check its labels against the code after a
change."""

from __future__ import annotations

import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from svgkit import (BLUE, GREEN, GREY, HERO_DEFS, HERO_STYLE, LIGHT, LINE, NAVY,  # noqa: E402
                    ORANGE, RED, TEAL, WHITE, Iso, Svg, _write)

OUT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..",
                                    "docs", "assets", "images"))

PALE_BLUE = "#EAF2FC"
PALE_TEAL = "#E6F4F5"
PALE_ORANGE = "#FFF4E5"
PALE_GREEN = "#EEF7EF"
PALE_RED = "#FDECEC"


def box(s, x, y, w, h, title, lines=(), color=BLUE, fill=None, title_size=14.5, size=12.5):
    """A titled box: bold title and grey detail lines, vertically centred."""
    s.rect(x, y, w, h, fill=fill or LIGHT, stroke=color, rx=10)
    n = len(lines)
    top = y + h / 2 - (n * 17) / 2 + 5
    s.text(x + w / 2, top, title, size=title_size, weight="bold", fill=NAVY)
    for i, value in enumerate(lines):
        s.text(x + w / 2, top + 19 + i * 17, value, size=size, fill=GREY)


def arrow(s, x1, y1, x2, y2, label="", color=GREY, kind="end", dx=0, dy=-7, anchor="middle",
          size=12, dash=False):
    s.line(x1, y1, x2, y2, color=color, arrow=kind, dash=dash)
    if label:
        s.text((x1 + x2) / 2 + dx, (y1 + y2) / 2 + dy, label, size=size, fill=color,
               anchor=anchor)


# ==============================================================================
# HERO (landing page, README banner, PDF cover)
# ==============================================================================

# ------------------------------------------------------------------------------
# small mesh renderer on top of svgkit.Iso: flat-shaded polygons with back-face
# culling (view direction (1, 1, 1)) and painter's order inside an object
# ------------------------------------------------------------------------------

LIGHT_DIR = (-0.25, 0.35, 0.90)


def _norm(v):
    n = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / n for c in v)


def _sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _shade(color, n, lo=0.42, hi=1.0):
    k = lo + (hi - lo) * max(0.0, _dot(_norm(n), _norm(LIGHT_DIR)))
    r, g, b = (int(color[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % tuple(min(255, int(c * k)) for c in (r, g, b))


class Mesh:
    """Faces of one object; draw() culls and sorts them."""

    def __init__(self):
        self.faces = []      # (points3d, color, stroke, extra)

    def face(self, pts, color, stroke="none", extra=""):
        self.faces.append((pts, color, stroke, extra))

    def prism(self, poly, z0, z1, side, top, bottom=None, stroke="none"):
        """Vertical prism over a 2D polygon (counter-clockwise)."""
        n = len(poly)
        for i in range(n):
            (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
            self.face([(x0, y0, z0), (x1, y1, z0), (x1, y1, z1), (x0, y0, z1)], side, stroke)
        self.face([(x, y, z1) for x, y in poly], top, stroke)
        if bottom:
            self.face([(x, y, z0) for x, y in reversed(poly)], bottom, stroke)

    def cylinder(self, p0, p1, r, color, cap=None, n=40, stroke="none"):
        axis = _norm(_sub(p1, p0))
        ref = (0, 0, 1) if abs(axis[2]) < 0.9 else (1, 0, 0)
        u = _norm(_cross(axis, ref))
        v = _cross(axis, u)
        ring = [(math.cos(2 * math.pi * k / n), math.sin(2 * math.pi * k / n)) for k in range(n)]
        a = [tuple(p0[i] + r * (c * u[i] + s_ * v[i]) for i in range(3)) for c, s_ in ring]
        b = [tuple(p1[i] + r * (c * u[i] + s_ * v[i]) for i in range(3)) for c, s_ in ring]
        for k in range(n):
            self.face([a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]], color, stroke, "#side")
        self.face(list(b), cap or color, stroke)
        self.face(list(reversed(a)), cap or color, stroke)

    def obox(self, c, u, v, w, color, stroke="none"):
        """Oriented box: centre c, half axes u, v, w (right-handed)."""
        pts = {}
        for i in (-1, 1):
            for j in (-1, 1):
                for k in (-1, 1):
                    pts[(i, j, k)] = tuple(c[m] + i * u[m] + j * v[m] + k * w[m] for m in range(3))
        quads = [((1, -1, -1), (1, 1, -1), (1, 1, 1), (1, -1, 1)),
                 ((-1, -1, -1), (-1, -1, 1), (-1, 1, 1), (-1, 1, -1)),
                 ((-1, 1, -1), (-1, 1, 1), (1, 1, 1), (1, 1, -1)),
                 ((-1, -1, -1), (1, -1, -1), (1, -1, 1), (-1, -1, 1)),
                 ((-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)),
                 ((-1, -1, -1), (-1, 1, -1), (1, 1, -1), (1, -1, -1))]
        for q in quads:
            self.face([pts[t] for t in q], color, stroke)

    def extrude(self, base, vec, side, cap, stroke="none"):
        """Prism from a planar polygon `base` (3D points) along `vec`; faces are
        oriented outwards automatically."""
        top = [tuple(q[i] + vec[i] for i in range(3)) for q in base]
        pts = base + top
        ctr = tuple(sum(q[i] for q in pts) / len(pts) for i in range(3))
        n = len(base)
        mark = "#side" if n > 12 else ""     # round bodies: no facet lines in x-ray
        faces = [([base[k], base[(k + 1) % n], top[(k + 1) % n], top[k]], side, mark)
                 for k in range(n)]
        faces += [(list(top), cap, ""), (list(base), cap, "")]
        for f, col, ex in faces:
            nrm = _cross(_sub(f[1], f[0]), _sub(f[2], f[0]))
            fc = tuple(sum(q[i] for q in f) / len(f) for i in range(3))
            if _dot(nrm, _sub(fc, ctr)) < 0:
                f = list(reversed(f))
            self.face(f, col, stroke, ex)

    def draw(self, iso, group="", xray=None):
        """Flat-shaded solid; xray=(stroke, fill, fill_opacity, stroke_opacity) draws
        every face transparent instead (hidden edges visible)."""
        view = (1.0, 1.0, 1.0)
        items = []
        for pts, color, stroke, extra in self.faces:
            nrm = _cross(_sub(pts[1], pts[0]), _sub(pts[2], pts[0]))
            if _dot(nrm, nrm) < 1e-12 and len(pts) > 3:
                nrm = _cross(_sub(pts[2], pts[0]), _sub(pts[3], pts[0]))
            front = _dot(nrm, view) > 1e-9
            if not front and xray is None:
                continue
            depth = sum(x + y + z for x, y, z in pts) / len(pts)
            items.append((depth, pts, _shade(color, nrm), stroke, extra, front))
        items.sort(key=lambda t: t[0])
        out = []
        for _, pts, fill, stroke, extra, front in items:
            d = " ".join("%.1f,%.1f" % iso.p(*q) for q in pts)
            if xray is None:
                ex = "" if extra == "#side" else extra
                out.append(f'<polygon points="{d}" fill="{fill}" stroke="{stroke if stroke != "none" else fill}" '
                           f'stroke-width="0.6" stroke-linejoin="round"{ex}/>')
            else:
                sc, fc, fo, so = xray
                if extra == "#side":
                    so = 0.0                 # cylinder mantle: no facet lines
                out.append(f'<polygon points="{d}" fill="{fc}" fill-opacity="{fo if front else fo * 0.4}" '
                           f'stroke="{sc}" stroke-opacity="{so if front else so * 0.35}" '
                           f'stroke-width="0.7" stroke-linejoin="round"/>')
        if group:
            iso.parts.append(f"<g {group}>" + "".join(out) + "</g>")
        else:
            iso.parts.extend(out)


def octagon(x0, x1, y0, y1, c):
    return [(x0 + c, y0), (x1 - c, y0), (x1, y0 + c), (x1, y1 - c), (x1 - c, y1), (x0 + c, y1),
            (x0, y1 - c), (x0, y0 + c)]


def circle(cx, cy, r, n=48):
    return [(cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n))
            for k in range(n)]


XRAY = ("#5ea6ff", "#2f8cff", 0.05, 0.55)


def _basis(axis):
    axis = _norm(axis)
    ref = (0, 0, 1) if abs(axis[2]) < 0.9 else (1, 0, 0)
    u = _norm(_cross(axis, ref))
    return u, _cross(axis, u)


def _ring3(c, axis, r, a0=0.0, a1=2 * math.pi, n=60):
    u, v = _basis(axis)
    return [tuple(c[i] + r * (math.cos(t) * u[i] + math.sin(t) * v[i]) for i in range(3))
            for t in (a0 + (a1 - a0) * k / n for k in range(n + 1))]


def gear_outline(iso, c, axis, r, teeth=18, color="#9cc8ff", op=0.7):
    """Spur gear outline (tooth tips and roots) plus hub, in the plane normal to axis."""
    u, v = _basis(axis)
    pts = []
    for k in range(teeth * 4):
        t = 2 * math.pi * k / (teeth * 4)
        rr = r if (k % 4) in (1, 2) else r * 0.86
        pts.append(iso.p(*(c[i] + rr * (math.cos(t) * u[i] + math.sin(t) * v[i]) for i in range(3))))
    d = "M" + " L".join("%.1f,%.1f" % q for q in pts) + " Z"
    iso.parts.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="0.8" '
                     f'stroke-opacity="{op}"/>')
    for rr in (0.55 * r, 0.22 * r):
        ring = [iso.p(*q) for q in _ring3(c, axis, rr)]
        iso.path(ring, color, 0.7, f' opacity="{op * 0.8}"')


def rotation_arc(iso, c, axis, r, number, color="#2f8cff"):
    """Rotation arrow around an axis and a numbered badge (like an axis plan)."""
    arc = _ring3(c, axis, r, 0.3, 0.3 + 1.6 * math.pi, 48)
    pts = [iso.p(*q) for q in arc]
    iso.path(pts, color, 1.8, ' opacity="0.85" class="axis-arc"')
    (x1, y1), (x2, y2) = pts[-2], pts[-1]
    ang = math.atan2(y2 - y1, x2 - x1)
    hx, hy = x2 + 6 * math.cos(ang), y2 + 6 * math.sin(ang)
    l1 = (x2 + 7 * math.cos(ang + 2.5), y2 + 7 * math.sin(ang + 2.5))
    l2 = (x2 + 7 * math.cos(ang - 2.5), y2 + 7 * math.sin(ang - 2.5))
    iso.parts.append(f'<path d="M{hx:.1f},{hy:.1f} L{l1[0]:.1f},{l1[1]:.1f} '
                     f'L{l2[0]:.1f},{l2[1]:.1f} z" fill="{color}" opacity="0.9"/>')
    bx, by = pts[len(pts) // 2]
    iso.parts.append(f'<circle cx="{bx:.1f}" cy="{by:.1f}" r="8.5" fill="#0b2545" '
                     f'stroke="{color}" stroke-width="1.4"/>'
                     f'<text x="{bx:.1f}" y="{by + 3.8:.1f}" font-family="Inter, Arial, sans-serif" '
                     f'font-size="10.5" font-weight="800" fill="#e6edf7" '
                     f'text-anchor="middle">{number}</text>')


def robot_arm(iso, bx, by, heading_deg, scale=1.0) -> None:
    """Six-axis industrial arm drawn as a transparent technical plan in the background:
    glass-like bodies with visible edges, spur gears in the joints, rotation arrows and
    numbered axes."""
    h = math.radians(heading_deg)
    d = (math.cos(h), math.sin(h), 0.0)
    side = (-math.sin(h), math.cos(h), 0.0)
    S = scale

    def at(r, z):
        return (bx + r * d[0], by + r * d[1], z)

    iso.parts.append('<g class="arm-plan">')
    m = Mesh()
    m.extrude([(x, y, -0.4) for x, y in octagon(bx - 2.4 * S, bx + 2.4 * S, by - 2.4 * S,
                                                    by + 2.4 * S, 0.8 * S)], (0, 0, 1.0 * S),
              "#2f8cff", "#2f8cff")
    m.extrude([(x, y, 0.6 * S) for x, y in circle(bx, by, 1.9 * S, 36)], (0, 0, 0.5 * S),
              "#2f8cff", "#2f8cff")
    m.extrude([(x, y, 1.1 * S) for x, y in circle(bx, by, 1.45 * S, 36)], (0, 0, 2.2 * S),
              "#2f8cff", "#2f8cff")
    m.draw(iso, xray=XRAY)
    gear_outline(iso, (bx, by, 1.12 * S), (0, 0, 1), 1.75 * S, 30)
    sh = at(0.3 * S, 4.1 * S)
    a1, a2, a3 = math.radians(74), math.radians(-12), math.radians(-58)
    r_el = 0.3 * S + 6.4 * S * math.cos(a1)
    el = at(r_el, sh[2] + 6.4 * S * math.sin(a1))
    r_wr = r_el + 6.0 * S * math.cos(a2)
    wr = at(r_wr, el[2] + 6.0 * S * math.sin(a2))
    tool = at(r_wr + 2.0 * S * math.cos(a3), wr[2] + 2.0 * S * math.sin(a3))

    def link(p0, p1, half_w, half_t):
        c = tuple((u + v) / 2 for u, v in zip(p0, p1))
        dd = _sub(p1, p0)
        ln = math.sqrt(_dot(dd, dd)) / 2
        ax = _norm(dd)
        nrm = _cross(ax, side)
        m2 = Mesh()
        m2.obox(c, tuple(ln * x for x in ax), tuple(half_w * x for x in side),
                tuple(half_t * x for x in nrm), "#2f8cff")
        m2.draw(iso, xray=XRAY)

    def joint(pt, r, half_len, teeth):
        p0 = tuple(pt[i] - half_len * side[i] for i in range(3))
        m2 = Mesh()
        p1 = tuple(pt[i] + half_len * side[i] for i in range(3))
        m2.cylinder(p0, p1, r, "#2f8cff", n=32)
        m2.draw(iso, xray=XRAY)
        for q in (p0, p1):
            ring = [iso.p(*w) for w in _ring3(q, side, r)]
            iso.path(ring, "#5ea6ff", 0.9, ' opacity="0.6"')
        face = tuple(pt[i] + half_len * side[i] for i in range(3))
        gear_outline(iso, face, side, 0.8 * r, teeth)

    link(at(0.15 * S, 3.0 * S), sh, 0.9 * S, 0.8 * S)
    joint(sh, 1.15 * S, 1.0 * S, 24)
    link(sh, el, 0.8 * S, 0.66 * S)
    joint(el, 0.95 * S, 0.9 * S, 20)
    link(el, wr, 0.62 * S, 0.52 * S)
    joint(wr, 0.68 * S, 0.7 * S, 16)
    link(wr, tool, 0.42 * S, 0.42 * S)
    ax = _norm(_sub(tool, wr))
    fl = Mesh()
    fl.cylinder(tool, tuple(tool[i] + 0.35 * S * ax[i] for i in range(3)), 0.55 * S, "#2f8cff",
                n=28)
    fl.draw(iso, xray=XRAY)
    gear_outline(iso, tool, ax, 0.45 * S, 12)
    # rotation axes 1-6
    rotation_arc(iso, (bx, by, 0.85 * S), (0, 0, 1), 2.7 * S, 1)
    rotation_arc(iso, tuple(sh[i] + 1.15 * S * side[i] for i in range(3)), side, 1.6 * S, 2)
    rotation_arc(iso, tuple(el[i] + 1.0 * S * side[i] for i in range(3)), side, 1.35 * S, 3)
    mid = tuple((el[i] + wr[i]) / 2 for i in range(3))
    rotation_arc(iso, mid, _sub(wr, el), 0.95 * S, 4)
    rotation_arc(iso, tuple(wr[i] + 0.8 * S * side[i] for i in range(3)), side, 1.0 * S, 5)
    rotation_arc(iso, tuple(tool[i] + 0.45 * S * ax[i] for i in range(3)), ax, 0.85 * S, 6)
    iso.parts.append("</g>")


def nema17(iso, x0, y0, z0=0.0) -> tuple:
    """NEMA 17 stepper (42.3 x 42.3 x 48 mm, 1 unit = 10 mm) lying on its side, shaft
    along +x. Returns the shaft tip."""
    s, c, L = 4.23, 0.45, 4.8
    y1, z1 = y0 + s, z0 + s
    cap, stack = "#20242b", "#aeb7c4"
    sec = [(x0, y, z) for y, z in octagon(y0, y1, z0, z1, c)]
    sec_in = [(x0, y, z) for y, z in octagon(y0 + 0.06, y1 - 0.06, z0 + 0.06, z1 - 0.06, c)]
    m = Mesh()
    m.extrude(sec, (0.85, 0, 0), cap, "#2b3038")
    m.draw(iso)
    m = Mesh()
    m.extrude([(x0 + 0.85, y, z) for _, y, z in sec_in], (3.1, 0, 0), stack, stack)
    m.draw(iso)
    m = Mesh()
    m.extrude([(x0 + 3.95, y, z) for _, y, z in sec], (0.85, 0, 0), cap, "#2b3038")
    m.draw(iso)
    # lamination ridges across the visible top (+z) and side (+y) faces of the stack
    for k in range(1, 15):
        x = x0 + 0.85 + k * 3.1 / 15
        for pts in ([(x, y0 + c, z1 - 0.06), (x, y1 - c, z1 - 0.06)],
                    [(x, y1 - 0.06, z0 + c), (x, y1 - 0.06, z1 - c)],
                    [(x, y1 - c, z1 - 0.06), (x, y1 - 0.06, z1 - c)]):
            iso.path([iso.p(*q) for q in pts], "#7d8796", 0.7, ' opacity="0.85"')
    # label on the side (+y) face, written along the axis
    iso.text(x0 + L / 2, y1 - 0.04, z0 + 2.45, "17HS19-2004S1", 0.34, "#20242b", 800, face="y")
    iso.text(x0 + L / 2, y1 - 0.04, z0 + 1.95, "NEMA 17 · 1.8° · 2.0 A", 0.24, "#3a4250", 600,
             face="y")
    # front face (+x): mounting holes, pilot boss, shaft
    xf = x0 + L
    cy, cz = (y0 + y1) / 2, (z0 + z1) / 2
    for hy, hz in ((y0 + 0.56, z0 + 0.56), (y1 - 0.56, z0 + 0.56), (y0 + 0.56, z1 - 0.56),
                   (y1 - 0.56, z1 - 0.56)):
        ring = [iso.p(*q) for q in _ring3((xf + 0.001, hy, hz), (1, 0, 0), 0.16, n=20)]
        iso.parts.append('<polygon points="' + " ".join("%.1f,%.1f" % q for q in ring) +
                         '" fill="#05070a"/>')
    b = Mesh()
    b.cylinder((xf, cy, cz), (xf + 0.2, cy, cz), 1.1, "#c3ccd8", cap="#d6dde7", n=48)
    b.draw(iso)
    sh = Mesh()
    sh.cylinder((xf + 0.2, cy, cz), (xf + 2.4, cy, cz), 0.25, "#cfd7e2", cap="#e6ebf2", n=28)
    sh.draw(iso)
    return xf + 2.4, cy, cz


ARM = (21.1, -3.3, 150.0, 1.35)       # PDF cover (cover-3d.svg)
ARM_WEB = (25.45, -2.25, 150.0, 1.35)    # website hero and README banner (hero-3d.svg):
#                                        board and motor higher and further left   # base x, y, heading, scale: 1.5x, on the right


def hero(filename: str = "hero-3d.svg", arm=ARM) -> None:
    """Isometric scene: a robotic arm in the background; the Stepper-C chip on a board
    drives three half-bridge legs (U, V, W); the phase wires carry the current to a
    NEMA 17 stepper whose shaft turns. `arm` places the arm relative to the board."""
    iso = Iso()
    p = iso.p
    robot_arm(iso, arm[0], arm[1], arm[2], arm[3])
    # board
    iso.box(0, 10.5, 0, 7.6, -0.4, 0, "url(#boardTop)", "#0a1628", "#071122", "#1e3a66", 1.2)
    traces = []
    for i in range(6):
        y = 2.3 + i * 0.55
        traces.append([p(2.0, y), p(1.1, y), p(0.7, y - 0.4), p(0.25, y - 0.4)])
        x = 2.3 + i * 0.55
        traces.append([p(x, 2.0), p(x, 1.1), p(x + 0.35, 0.75), p(x + 0.35, 0.25)])
    for trace in traces:
        iso.path(trace, "#1d5fbf", 1.3, ' opacity="0.7"')
    for k in range(3):
        y = 1.6 + k * 2.0
        trace = [p(5.2, 3.6), p(5.9, 3.6), p(6.4, y + 0.6), p(7.0, y + 0.6)]
        iso.path(trace, "#1d5fbf", 1.6)
        iso.path(trace, "#5ea6ff", 1.6, ' class="flow"')
    iso.box(2.0, 5.2, 2.0, 5.2, 0, 0.75, "url(#chipTop)", "#0a1322", "#060d18", "#2f8cff", 1.0)
    iso.text(3.6, 3.55, 0.76, "STEPPER-C", 0.42, "#e6edf7", 800, 0.03)
    iso.text(3.6, 4.25, 0.76, "CURRENT · MOTION", 0.22, "#5ea6ff", 600, 0.06)
    iso.led(2.45, 2.45, 0.76)
    for k, name in enumerate(("U", "V", "W")):
        y0 = 1.3 + k * 2.0
        for j in range(2):
            x0 = 7.0 + j * 1.25
            iso.box(x0, x0 + 1.0, y0, y0 + 1.2, 0, 0.4, "#14243c", "#0c182b", "#09121f", "#2a4870")
        iso.text(6.45, y0 + 0.75, 0.01, name, 0.42, "#9aabc4", 800)
        iso.led(8.95, y0 + 0.2, 0.42, "led", "#5ea6ff", 2.2)
    iso.box(9.8, 10.5, 2.0, 5.8, 0, 0.55, "#c9d6ea", "#8aa0bf", "#6f86a6")
    # four motor wires (A+ A- B+ B-) from the connector into the rear cap of the motor
    mx0, my0 = 13.4, 1.7
    for k, color in enumerate(("#e5484d", "#2f8cff", "#3fcf8e", "#9aabc4")):
        y = 2.7 + k * 0.42
        wire = [p(10.5, y, 0.3), p(11.4, y, 0.3), p(12.4, 3.2 + k * 0.3, 1.2),
                p(13.5, 3.2 + k * 0.3, 1.2)]
        iso.path(wire, "#0e1726", 4.2)
        iso.path(wire, color, 1.8)
    tip = nema17(iso, mx0, my0)
    # rotation of the shaft
    ring = [p(*q) for q in _ring3((tip[0] - 0.6, tip[1], tip[2]), (1, 0, 0), 0.62,
                                   0.0, 1.7 * math.pi, 40)]
    iso.path(ring, "#2f8cff", 2.0, ' class="flow"')
    (x1, y1), (x2, y2) = ring[-2], ring[-1]
    ang = math.atan2(y2 - y1, x2 - x1)
    iso.parts.append(
        f'<path d="M{x2 + 6 * math.cos(ang):.1f},{y2 + 6 * math.sin(ang):.1f} '
        f'L{x2 + 6 * math.cos(ang + 2.5):.1f},{y2 + 6 * math.sin(ang + 2.5):.1f} '
        f'L{x2 + 6 * math.cos(ang - 2.5):.1f},{y2 + 6 * math.sin(ang - 2.5):.1f} z" '
        f'fill="#2f8cff"/>')
    style = HERO_STYLE.replace(
        "@media (prefers-reduced-motion:reduce){",
        ".wave{stroke-dasharray:3 6;animation:flow 1.2s linear infinite}"
        ".axis-arc{stroke-dasharray:6 5;animation:flow 3s linear infinite}"
        "@media (prefers-reduced-motion:reduce){.wave,.axis-arc,")
    svg = iso.svg("Stepper-C drives a NEMA 17 stepper motor through three half-bridges; "
                  "a robotic arm in the background", HERO_DEFS, style, glow_at=(9, 1))
    _write(os.path.join(OUT, filename), _glow_inside(svg))


def _glow_inside(svg: str) -> str:
    """Shrink the floor glow ellipse so it fades out inside the view box (a glow larger
    than the box is cut off with a visible straight edge on a dark page)."""
    vx, vy, vw, vh = map(float, re.search(r'viewBox="([^"]+)"', svg).group(1).split())
    m = re.search(r'<ellipse cx="([-\d.]+)" cy="([-\d.]+)" rx="[\d.]+" ry="[\d.]+" '
                  r'fill="url\(#floorGlow\)"/>', svg)
    gx, gy = float(m.group(1)), float(m.group(2))
    rx = 0.98 * min(gx - vx, vx + vw - gx)
    ry = 0.98 * min(gy - vy, vy + vh - gy)
    return svg.replace(m.group(0), f'<ellipse cx="{gx:.1f}" cy="{gy:.1f}" rx="{rx:.0f}" '
                                   f'ry="{ry:.0f}" fill="url(#floorGlow)"/>')


def readme_banner() -> None:
    w, h = 1280, 520
    font = "Inter, 'Segoe UI', Helvetica, Arial, sans-serif"
    with open(os.path.join(OUT, "hero-3d.svg"), encoding="utf-8") as f:
        scene = f.read()
    size = re.search(r'width="(\d+)" height="(\d+)"', scene)
    box_x, box_y, box_w, box_h = 600, 30, 660, 460
    scale = min(box_w / int(size.group(1)), box_h / int(size.group(2)))
    hw, hh = int(size.group(1)) * scale, int(size.group(2)) * scale
    scene = scene.replace(size.group(0), f'x="{box_x + (box_w - hw) / 2:.0f}" '
                          f'y="{box_y + (box_h - hh) / 2:.0f}" width="{hw:.0f}" '
                          f'height="{hh:.0f}"', 1)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" '
        f'height="{h}" role="img" aria-label="Stepper-C: stepper motor control from model to metal">',
        "<title>Stepper-C: stepper motor control from model to metal</title>",
        '<defs><radialGradient id="bannerGlow" cx="72%" cy="62%" r="55%">'
        '<stop offset="0" stop-color="#1a6fe0" stop-opacity="0.32"/>'
        '<stop offset="1" stop-color="#1a6fe0" stop-opacity="0"/></radialGradient>'
        '<linearGradient id="bannerBg" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#050b16"/><stop offset="1" stop-color="#071122"/>'
        '</linearGradient></defs>',
        f'<rect width="{w}" height="{h}" rx="18" fill="url(#bannerBg)"/>',
        f'<rect width="{w}" height="{h}" rx="18" fill="url(#bannerGlow)"/>',
        f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="18" fill="none" '
        f'stroke="#15294a"/>',
        f'<text x="64" y="118" font-family="{font}" font-size="17" font-weight="700" '
        f'letter-spacing="3" fill="#2f8cff">OPEN-SOURCE MOTOR CONTROL SYSTEM</text>',
    ]
    for y, line, color in ((196, "STEPPER MOTOR", "#e6edf7"), (264, "CONTROL FROM", "#e6edf7"),
                           (332, "MODEL TO METAL", "#2f8cff")):
        parts.append(f'<text x="60" y="{y}" font-family="{font}" font-size="54" '
                     f'font-weight="800" fill="{color}">{line}</text>')
    parts += [
        '<rect x="64" y="368" width="150" height="3" rx="1.5" fill="#2f8cff" opacity="0.5"/>',
        '<circle cx="128" cy="369.5" r="5" fill="#2f8cff"/>',
        f'<text x="64" y="420" font-family="{font}" font-size="19" fill="#9aabc4">'
        "C11 library · Scilab/Xcos SIL · ngspice power stage</text>",
        scene,
        "</svg>",
    ]
    _write(os.path.join(OUT, "readme-banner.svg"), "\n".join(parts) + "\n")


# ==============================================================================
# SYSTEM
# ==============================================================================

def system_architecture() -> None:
    s = Svg(980, 520, "Stepper-C system: three repositories and the hardware")
    # library in the middle
    s.rect(330, 40, 320, 190, fill=NAVY, stroke=NAVY, rx=14)
    s.text(490, 72, "sfs-stepper-ctrl", size=13, fill="#9cc8ff", mono=True)
    s.text(490, 100, "Stepper-C library (C11)", size=18, weight="bold", fill=WHITE)
    for i, value in enumerate(("current control · PI + anti-windup",
                               "motion generator · exact braking",
                               "power stage mapping · 2 topologies",
                               "fixed point Q15/Q31 or float")):
        s.text(490, 130 + i * 22, value, size=13, fill="#C9D6EA")
    # simulation
    s.rect(30, 300, 400, 190, fill=PALE_TEAL, stroke=TEAL, rx=14)
    s.text(230, 328, "sfs-stepper-sim", size=13, fill=TEAL, mono=True)
    s.text(230, 354, "Simulation (Scilab / Xcos)", size=17, weight="bold")
    for i, value in enumerate(("motor model: back-EMF, detent, friction",
                               "prototype of the control algorithms",
                               "averaged and switching power stage",
                               "software in the loop: the C code in Xcos",
                               "Python twins, tests T00–T12, S01–S04")):
        s.text(230, 380 + i * 21, value, size=12.5, fill=GREY)
    # spice
    s.rect(550, 300, 400, 190, fill=PALE_ORANGE, stroke=ORANGE, rx=14)
    s.text(750, 328, "sfs-stepper-power-spice", size=13, fill=ORANGE, mono=True)
    s.text(750, 354, "Power stage model (ngspice)", size=17, weight="bold")
    for i, value in enumerate(("STL180N6F7 fitted to the datasheet",
                               "L6387E behavioural gate driver",
                               "one B-G431B-ESC1 leg with shunt",
                               "dead time, diodes, shunt settling",
                               "tests SP01–SP03, parameter export")):
        s.text(750, 380 + i * 21, value, size=12.5, fill=GREY)
    # hardware
    s.rect(730, 60, 220, 150, fill=PALE_GREEN, stroke=GREEN, rx=14)
    s.text(840, 92, "Hardware", size=17, weight="bold")
    s.text(840, 118, "B-G431B-ESC1", size=13, fill=GREY)
    s.text(840, 138, "(STM32G431, 3 legs)", size=12, fill=GREY)
    s.text(840, 162, "17HS19-2004S1", size=13, fill=GREY)
    s.text(840, 182, "NEMA 17, 2 A", size=12, fill=GREY)
    s.rect(30, 60, 220, 150, fill=LIGHT, stroke=BLUE, rx=14)
    s.text(140, 92, "Application", size=17, weight="bold")
    s.text(140, 118, "move_to, run, stop", size=13, fill=GREY)
    s.text(140, 138, "callbacks: PWM, enable", size=12, fill=GREY)
    s.text(140, 162, "ISR: sstep_fast_loop()", size=12, fill=GREY, mono=True)
    s.text(140, 182, "task: sstep_slow_loop()", size=12, fill=GREY, mono=True)
    arrow(s, 250, 135, 328, 135, "", BLUE)
    arrow(s, 652, 135, 728, 135, "PWM (P3)", GREEN, kind="green")
    # library compiled into Xcos
    s.path("M420,232 L420,298", color=TEAL, arrow="teal", width=2)
    s.text(428, 270, "same C sources compiled", size=12, fill=TEAL, anchor="start")
    s.text(428, 285, "into Xcos blocks (SIL)", size=12, fill=TEAL, anchor="start")
    # prototype twin
    s.path("M300,300 L300,250 L330,250", color=TEAL, arrow="teal", width=1.6, )
    s.text(290, 266, "algorithm twin", size=12, fill=TEAL, anchor="end")
    # spice -> sim export
    s.line(548, 420, 432, 420, color=ORANGE, arrow="orange", width=2)
    s.text(490, 410, "stage_esc1_spice", size=12, fill=ORANGE, mono=True)
    s.text(490, 440, "dead time, Rds, Vd", size=12, fill=ORANGE)
    s.save(os.path.join(OUT, "system-architecture.svg"))


def workflow() -> None:
    s = Svg(980, 250, "Development workflow")
    steps = [
        ("1  Model", ["motor equations", "Python twin"], TEAL, PALE_TEAL),
        ("2  Prototype", ["control in Scilab", "tests T00–T12"], TEAL, PALE_TEAL),
        ("3  Library", ["Stepper-C in C11", "unit tests, 100 %"], BLUE, PALE_BLUE),
        ("4  SIL", ["C code in Xcos", "S01–S04 vs prototype"], BLUE, PALE_BLUE),
        ("5  Power stage", ["ngspice leg model", "SP01–SP03, export"], ORANGE, PALE_ORANGE),
        ("6  Hardware", ["B-G431B-ESC1 port", "measure, compare"], GREEN, PALE_GREEN),
    ]
    w, gap = 136, 22
    for i, (title, lines, color, fill) in enumerate(steps):
        x = 24 + i * (w + gap)
        box(s, x, 70, w, 100, title, lines, color, fill, title_size=14, size=11.5)
        if i < len(steps) - 1:
            arrow(s, x + w + 2, 120, x + w + gap - 2, 120)
    s.text(490, 40, "Each step is checked against the previous one; a change in the library is "
           "ported to the prototype in the same step.", size=13, fill=GREY)
    s.path("M 884,172 L 884,210 L 92,210 L 92,174", color=GREY, arrow="end", width=1.4)
    s.text(464, 228, "measured parameters (R, L, Kt, dead time) flow back into the models",
           size=12, fill=GREY)
    s.save(os.path.join(OUT, "workflow.svg"))


# ==============================================================================
# CONTROL
# ==============================================================================

def control_structure() -> None:
    s = Svg(980, 470, "Control structure of Stepper-C")
    s.rect(20, 20, 300, 430, fill="#F7FAFE", stroke=LINE, rx=14, dash=True)
    s.text(170, 44, "slow loop · 1 kHz · sstep_slow_loop()", size=12.5, fill=BLUE, weight="bold")
    s.rect(340, 20, 620, 430, fill="#F7FAFE", stroke=LINE, rx=14, dash=True)
    s.text(650, 44, "fast loop · 20 kHz · sstep_fast_loop() (PWM / ADC interrupt)", size=12.5,
           fill=BLUE, weight="bold")
    box(s, 40, 70, 260, 70, "Commands", ["move_to · move_by · run · stop"], GREY)
    box(s, 40, 170, 260, 90, "Motion generator", ["trapezoid, exact braking", "Q16 position, velocity"], BLUE, PALE_BLUE)
    box(s, 40, 290, 260, 70, "Hold current", ["i_run moving · i_hold at rest"], BLUE, PALE_BLUE)
    box(s, 40, 380, 260, 56, "Setpoint (double buffer)", [], NAVY, WHITE, title_size=13.5)
    arrow(s, 170, 140, 170, 168)
    arrow(s, 170, 260, 170, 288)
    arrow(s, 170, 360, 170, 378)
    # fast loop chain
    box(s, 360, 380, 150, 56, "angle + Δ / tick", [], BLUE, PALE_BLUE, title_size=13)
    arrow(s, 300, 408, 358, 408)
    box(s, 360, 270, 150, 80, "sin / cos table", ["i_A* = I cos φ", "i_B* = I sin φ"], BLUE, PALE_BLUE, size=11.5)
    arrow(s, 435, 380, 435, 352)
    box(s, 575, 270, 140, 80, "PI per phase", ["Kp = L ωc", "Ki = R ωc"], BLUE, PALE_BLUE, size=11.5)
    s.parts.append(f'<circle cx="540" cy="310" r="11" fill="{WHITE}" stroke="{GREY}" stroke-width="1.5"/>')
    s.text(540, 315, "−", size=14, weight="bold", fill=GREY)
    arrow(s, 510, 310, 528, 310)
    arrow(s, 551, 310, 573, 310)
    box(s, 575, 160, 140, 70, "+ back-EMF FF", ["Kt ω (−sin, cos)"], BLUE, PALE_BLUE, size=11.5)
    arrow(s, 645, 230, 645, 268)
    box(s, 760, 270, 180, 80, "Voltage limit + map", ["÷ Vbus, keep direction", "legs: 4 or 3"], BLUE, PALE_BLUE, size=11.5)
    arrow(s, 715, 310, 758, 310, "v", dy=-6)
    box(s, 760, 380, 180, 56, "pwm_write()", ["compare[4]"], GREEN, PALE_GREEN, title_size=13, size=11.5)
    arrow(s, 880, 350, 880, 378)
    box(s, 760, 70, 180, 70, "ADC sample", ["i_a, i_b, vbus (counts)"], GREEN, PALE_GREEN, size=11.5)
    s.path("M760,105 L540,105 L540,297", color=GREY, arrow="end")
    s.text(650, 98, "measured currents, trips", size=12, fill=GREY)
    s.line(880, 140, 880, 268, color=GREY, arrow="end", dash=True)
    s.text(888, 210, "Vbus", size=12, fill=GREY, anchor="start")
    s.path("M800,352 L800,368 L645,368 L645,354", color=ORANGE, arrow="orange")
    s.text(722, 386, "anti-windup", size=11.5, fill=ORANGE)
    s.save(os.path.join(OUT, "control-structure.svg"))


def loop_timing() -> None:
    s = Svg(980, 300, "Fast and slow loop timing")
    x0, x1, y = 60, 940, 130
    n = 40
    tick = (x1 - x0) / n
    s.line(x0, y, x1, y, color=NAVY, width=2)
    s.text(x0 - 10, y + 5, "fast", size=12.5, fill=NAVY, anchor="end")
    for i in range(n + 1):
        s.line(x0 + i * tick, y - 9, x0 + i * tick, y + 9, color=BLUE, width=1.4)
    s.rect(x0, y - 34, tick, 16, fill=PALE_BLUE, stroke=BLUE, rx=3)
    s.text(x0 + tick + 8, y - 22, "50 µs (20 kHz): sample → PI → PWM, angle += Δ", size=12.5,
           fill=BLUE, anchor="start")
    y2 = 210
    s.line(x0, y2, x1, y2, color=NAVY, width=2)
    s.text(x0 - 10, y2 + 5, "slow", size=12.5, fill=NAVY, anchor="end")
    for k in range(2):
        xs = x0 + k * 20 * tick
        s.rect(xs + 4, y2 - 18, 120, 36, fill=PALE_BLUE, stroke=BLUE, rx=6)
        s.text(xs + 64, y2 + 5, "slow loop", size=12.5, weight="bold")
        s.line(xs + 124, y2 - 18, xs + 124, y + 14, color=TEAL, arrow="teal", dash=True)
        s.text(xs + 130, (y + y2) / 2 + 6, "publish setpoint", size=11.5, fill=TEAL,
               anchor="start")
    s.bracket(x0, x0 + 20 * tick, 262, "1 ms = 20 fast periods (ratio)", NAVY)
    s.text(490, 34, "The fast loop takes the new setpoint at its next tick; between hand-offs "
           "it advances the angle by a constant increment.", size=12.5, fill=GREY)
    s.save(os.path.join(OUT, "loop-timing.svg"))


def topologies() -> None:
    s = Svg(980, 380, "Power stage topologies")

    def leg(x, y, label):
        s.text(x + 35, y - 10, label, size=13, weight="bold")
        s.rect(x, y, 70, 140, fill=WHITE, stroke=NAVY, rx=8)
        s.rect(x + 15, y + 12, 40, 40, fill=PALE_BLUE, stroke=BLUE, rx=5)
        s.rect(x + 15, y + 88, 40, 40, fill=PALE_BLUE, stroke=BLUE, rx=5)
        s.text(x + 35, y + 37, "H", size=13, weight="bold", fill=BLUE)
        s.text(x + 35, y + 113, "L", size=13, weight="bold", fill=BLUE)
        return x + 35, y + 140

    def coil(xa, xb, ya, yb, y, color, label, label_y):
        s.path(f"M{xa},{ya} L{xa},{y} L{xb},{y} L{xb},{yb}", color=color, width=2)
        mid = (xa + xb) / 2
        s.rect(mid - 28, y - 10, 56, 20, fill=WHITE, stroke=color, rx=10, sw=2)
        s.text(mid, label_y, label, size=12.5, fill=color, weight="bold")

    s.text(250, 34, "Two full H-bridges (4 legs)", size=16, weight="bold")
    s.text(250, 54, "|v_A|, |v_B| ≤ Vbus", size=12.5, fill=GREY, mono=True)
    pts = [leg(30 + i * 100, 95, name) for i, name in enumerate(("A+", "A−", "B+", "B−"))]
    coil(pts[0][0], pts[1][0], pts[0][1], pts[1][1], 285, BLUE, "phase A", 315)
    coil(pts[2][0], pts[3][0], pts[2][1], pts[3][1], 285, TEAL, "phase B", 315)
    s.text(250, 352, "duties 0.5 ± a/2, 0.5 ± b/2  (a = v_A/Vbus, b = v_B/Vbus)", size=12.5,
           fill=GREY, mono=True)

    s.line(490, 20, 490, 360, color=LINE)
    s.text(735, 34, "Three legs with a shared leg (B-G431B-ESC1)", size=16, weight="bold")
    s.text(735, 54, "max(a, b, 0) − min(a, b, 0) ≤ 1  →  circle Vbus/√2", size=12.5, fill=GREY,
           mono=True)
    (xu, yu), (xv, yv), (xw, yw) = [leg(560 + i * 120, 95, name)
                                    for i, name in enumerate(("U", "V", "W"))]
    coil(xu, xw, yu, yw, 300, BLUE, "A = U − W", 330)
    coil(xv, xw, yv, yw, 265, TEAL, "B = V − W", 250)
    for y in (265, 300):
        s.parts.append(f'<circle cx="{xw}" cy="{y}" r="3.5" fill="{TEAL if y == 265 else BLUE}"/>')
    s.text(735, 362, "common leg centred: w = 0.5 − (max + min)/2", size=12.5, fill=GREY, mono=True)
    s.save(os.path.join(OUT, "topologies.svg"))


def pwm_period() -> None:
    s = Svg(980, 330, "Centre-aligned PWM period with dead time")
    x0, x1 = 120, 900
    T = x1 - x0

    def X(f):
        return x0 + f * T

    d, td = 0.5, 0.06
    t1, t2 = (1 - d) / 2, (1 + d) / 2
    s.text(490, 28, "One period, from counter peak to counter peak (the current sampling "
           "instants); leg duty d = 0.5", size=13, fill=GREY)
    # counter triangle
    s.path(f"M{X(0)},70 L{X(0.5)},130 L{X(1)},70", color=GREY, width=1.4)
    s.text(x0 - 12, 104, "counter", size=12, fill=GREY, anchor="end")
    # high side
    yh, yl = 175, 245
    s.text(x0 - 12, yh + 5, "high side", size=12.5, fill=NAVY, anchor="end")
    s.text(x0 - 12, yl + 5, "low side", size=12.5, fill=NAVY, anchor="end")
    for a in (t1, t2):
        s.rect(X(a), 150, td * T, 120, fill="#FDECEC", stroke=RED, rx=2, sw=1)
    s.path(f"M{X(0)},{yh + 15} L{X(t1 + td)},{yh + 15} L{X(t1 + td)},{yh - 15} L{X(t2)},{yh - 15} "
           f"L{X(t2)},{yh + 15} L{X(1)},{yh + 15}", color=BLUE, width=2.2)
    s.path(f"M{X(0)},{yl - 15} L{X(t1)},{yl - 15} L{X(t1)},{yl + 15} L{X(t2 + td)},{yl + 15} "
           f"L{X(t2 + td)},{yl - 15} L{X(1)},{yl - 15}", color=TEAL, width=2.2)
    s.text(X(t1 + td / 2), 290, "dead", size=12, fill=RED)
    s.text(X(t2 + td / 2), 290, "dead", size=12, fill=RED)
    for f in (0, 1):
        s.line(X(f), 60, X(f), 300, color=GREEN, dash=True)
        s.text(X(f), 316, "ADC sample", size=12, fill=GREEN, weight="bold")
    s.bracket(X(t1), X(t2), 148 - 2, "", BLUE)
    s.text(X(0.5), 142, "d · Ts (commanded high time)", size=12, fill=BLUE)
    s.text(X(0.5), 316, "body diode conducts in the dead time: leg at −Vd (i > 0) or Vbus + Vd (i < 0)",
           size=12, fill=GREY)
    s.save(os.path.join(OUT, "pwm-period.svg"))


def state_machine() -> None:
    s = Svg(980, 300, "Driver states")
    box(s, 40, 70, 200, 70, "DISABLED", ["outputs off"], NAVY, LIGHT)
    box(s, 390, 70, 200, 70, "HOLDING", ["position held"], NAVY, PALE_BLUE)
    box(s, 740, 70, 200, 70, "MOVING", ["command running"], BLUE, PALE_BLUE)
    box(s, 565, 205, 200, 70, "FAULT", ["outputs off, flags"], RED, PALE_RED)
    arrow(s, 240, 95, 388, 95, "sstep_enable()", BLUE, dy=-8)
    arrow(s, 388, 118, 242, 118, "sstep_disable()", GREY, dy=18)
    arrow(s, 590, 95, 738, 95, "move / run", BLUE, dy=-8)
    arrow(s, 738, 118, 592, 118, "done / stopped", GREY, dy=18)
    s.path("M490,140 L490,175 L610,175 L610,203", color=RED, arrow="end")
    s.path("M840,140 L840,175 L720,175 L720,203", color=RED, arrow="end")
    s.text(780, 230, "overcurrent, Vbus trip,", size=12, fill=RED, anchor="start")
    s.text(780, 246, "HAL error,", size=12, fill=RED, anchor="start")
    s.text(780, 262, "sstep_report_fault()", size=12, fill=RED, anchor="start", mono=True)
    s.path("M565,250 L140,250 L140,142", color=GREY, arrow="end")
    s.text(350, 270, "sstep_clear_faults()  →  DISABLED", size=12.5, fill=GREY, mono=True)
    s.text(490, 36, "HOLDING and MOVING are set by the slow loop from the motion mode.",
           size=12.5, fill=GREY)
    s.save(os.path.join(OUT, "state-machine.svg"))


def motion_profile() -> None:
    s = Svg(980, 300, "Trapezoidal profile with exact discrete braking")
    x0, y0, w, h = 80, 250, 690, 190
    s.line(x0, y0, x0 + w + 20, y0, color=NAVY, arrow="end")
    s.line(x0, y0, x0, y0 - h - 20, color=NAVY, arrow="end")
    s.text(x0 + w + 20, y0 + 22, "time (slow loop periods)", size=12, fill=GREY, anchor="end")
    s.text(x0 - 10, y0 - h - 10, "v", size=13, fill=NAVY, anchor="end", weight="bold")
    # staircase velocity: accelerate, cruise, brake
    steps = []
    v, vmax, acc = 0, 9, 1
    for k in range(9):
        v = min(vmax, v + acc)
        steps.append(v)
    steps += [vmax] * 8
    vb = vmax
    while vb > 0:
        vb -= 1
        steps.append(max(vb, 0))
    dx = w / len(steps)
    d = f"M{x0},{y0}"
    for i, vv in enumerate(steps):
        y = y0 - vv * (h / (vmax + 1))
        d += f" L{x0 + i * dx:.1f},{y:.1f} L{x0 + (i + 1) * dx:.1f},{y:.1f}"
    s.path(d, color=BLUE, width=2.2)
    s.text(x0 + 5 * dx, y0 - h + 20, "|Δv| ≤ acc per period", size=12.5, fill=BLUE, anchor="middle")
    s.text(x0 + 13 * dx, y0 - h - 2, "v_max", size=12.5, fill=BLUE)
    s.text(x0 + w + 10, y0 - h + 30, "braking: largest v_new whose", size=12.5, fill=TEAL, anchor="start")
    s.text(x0 + w + 10, y0 - h + 47, "braking distance fits the", size=12.5, fill=TEAL, anchor="start")
    s.text(x0 + w + 10, y0 - h + 64, "distance left: no overshoot", size=12.5, fill=TEAL, anchor="start")
    xe = x0 + len(steps) * dx
    s.line(xe, y0 - 4, xe, y0 - 110, color=GREEN, dash=True)
    s.text(xe + 8, y0 - 100, "stops exactly", size=12, fill=GREEN, anchor="start")
    s.text(xe + 8, y0 - 84, "on the target", size=12, fill=GREEN, anchor="start")
    s.save(os.path.join(OUT, "motion-profile.svg"))


# ==============================================================================
# SIMULATION AND POWER STAGE
# ==============================================================================

def sil_diagram() -> None:
    s = Svg(980, 340, "Software in the loop diagram in Xcos")
    box(s, 20, 30, 120, 60, "SampleCLK", ["Ts = 1/fs"], GREY, LIGHT, title_size=13, size=11.5)
    box(s, 150, 160, 210, 110, "STEPPER_CTRL", ["Stepper-C (C library)", "fast + slow loop", "commands from cmds"], BLUE, PALE_BLUE, title_size=13.5, size=11.5)
    box(s, 480, 160, 210, 110, "STEPPER_PLANT", ["power stage (avg / switching)", "motor RK4, loads", "ADC model"], TEAL, PALE_TEAL, title_size=13.5, size=11.5)
    box(s, 760, 30, 190, 70, "STEPPER_MONITOR", ["rpm, load angle, µsteps"], GREY, LIGHT, title_size=13, size=11.5)
    box(s, 760, 150, 190, 60, "CMSCOPE", ["4 plots"], GREEN, PALE_GREEN, title_size=13, size=11.5)
    box(s, 760, 235, 190, 60, "TOWS_c → sil", ["workspace variable"], GREEN, PALE_GREEN, title_size=13, size=11.5)
    s.path("M80,90 L80,215 L148,215", color=RED, arrow="end")
    s.path("M80,135 L585,135 L585,158", color=RED, arrow="end")
    s.text(90, 128, "event: one fast period", size=11.5, fill=RED, anchor="start")
    arrow(s, 360, 195, 478, 195)
    s.text(420, 182, "compare[4],", size=11.5, fill=BLUE)
    s.text(420, 214, "enabled", size=11.5, fill=BLUE)
    s.path("M480,245 L362,245", color=TEAL, arrow="teal")
    s.text(420, 263, "ADC i_a, i_b, vbus", size=11.5, fill=TEAL)
    s.path("M690,215 L725,215 L725,65 L758,65", color=GREY, arrow="end")
    s.path("M255,160 L255,112 L725,112", color=GREY)
    s.text(500, 106, "controller monitor (angle, references)", size=11.5, fill=GREY)
    s.path("M855,100 L855,148", color=GREY, arrow="end")
    s.path("M950,65 L966,65 L966,265 L952,265", color=GREY, arrow="end")
    s.text(470, 322, "Scenario (motor, board, commands, loads, T_end) in Simulation → Set Context; "
           "END_c stops the run at T_end.", size=12.5, fill=GREY)
    s.save(os.path.join(OUT, "sil-diagram.svg"))


def esc1_leg() -> None:
    s = Svg(980, 400, "One B-G431B-ESC1 leg in ngspice")
    box(s, 40, 140, 180, 120, "L6387E", ["interlock, 107 ns", "30 Ω / 18 Ω out", "bootstrap 125 Ω"], BLUE, PALE_BLUE, size=11.5)
    s.text(130, 290, "HIN / LIN from the timer", size=12, fill=GREY)
    s.text(130, 306, "(dead time 500 ns)", size=12, fill=GREY)
    # bus
    s.line(380, 40, 940, 40, color=RED, width=2)
    s.text(940, 32, "Vbus 24 V", size=12.5, fill=RED, anchor="end")
    # high MOSFET
    box(s, 420, 80, 160, 70, "Q_H  STL180N6F7", ["VDMOS fit"], NAVY, WHITE, title_size=12.5, size=11.5)
    box(s, 420, 230, 160, 70, "Q_L  STL180N6F7", ["VDMOS fit"], NAVY, WHITE, title_size=12.5, size=11.5)
    s.line(500, 40, 500, 78, color=NAVY, width=2)
    s.text(510, 64, "L_loop/2", size=11.5, fill=GREY, anchor="start")
    s.line(500, 150, 500, 228, color=NAVY, width=2)
    s.line(500, 190, 700, 190, color=NAVY, width=2)
    s.parts.append(f'<circle cx="500" cy="190" r="4" fill="{NAVY}"/>')
    box(s, 700, 160, 200, 60, "phase current", ["source ±0.25 … ±3 A"], TEAL, PALE_TEAL, title_size=13, size=11.5)
    s.text(600, 182, "switch node", size=12, fill=NAVY)
    s.line(500, 300, 500, 330, color=NAVY, width=2)
    s.rect(470, 330, 60, 24, fill=PALE_ORANGE, stroke=ORANGE, rx=4)
    s.text(500, 347, "3 mΩ", size=11.5, fill=ORANGE, weight="bold")
    s.text(540, 347, "shunt (sampled)", size=12, fill=ORANGE, anchor="start")
    s.line(500, 354, 500, 380, color=NAVY, width=2)
    s.line(470, 380, 530, 380, color=NAVY, width=2)
    s.path("M220,170 L320,170 L320,115 L418,115", color=BLUE, arrow="end")
    s.text(330, 108, "Rg 10 Ω", size=11.5, fill=BLUE, anchor="start")
    s.path("M220,230 L320,230 L320,265 L418,265", color=BLUE, arrow="end")
    s.text(330, 284, "Rg 10 Ω", size=11.5, fill=BLUE, anchor="start")
    s.rect(60, 92, 140, 26, fill=WHITE, stroke=GREY, rx=4)
    s.text(130, 110, "C_boot 1 µF", size=11.5, fill=GREY)
    s.line(130, 118, 130, 138, color=GREY)
    s.save(os.path.join(OUT, "esc1-leg.svg"))


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    hero("cover-3d.svg", ARM)
    hero("hero-3d.svg", ARM_WEB)
    readme_banner()
    system_architecture()
    workflow()
    control_structure()
    loop_timing()
    topologies()
    pwm_period()
    state_machine()
    motion_profile()
    sil_diagram()
    esc1_leg()


if __name__ == "__main__":
    main()
