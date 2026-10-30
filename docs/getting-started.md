# Getting Started

This chapter installs the tools, gets the three repositories and runs each part once: the
library tests, the simulation tests, the software-in-the-loop diagram and the ngspice
model. Each section can be done on its own; the order below is the one that needs the
fewest tools first.

## Requirements

| Tool | Version | Needed for | Notes |
| --- | --- | --- | --- |
| Git | any | all | |
| CMake | 3.21+ | library | presets need 3.21 |
| C compiler | GCC 11+, Clang 14+ or MSVC 2022 | library, SIL | the SIL build uses the compiler Scilab finds |
| Python | 3.9+ | twins, ngspice runner, docs | `numpy`, `scipy`, `matplotlib` |
| Scilab | 2027.0.0 (2025 and 2026 work) | simulation, SIL | includes Xcos |
| Visual Studio 2022 or Build Tools | "Desktop development with C++" | SIL on Windows | Scilab compiles the Xcos blocks with it |
| ngspice | 42+ (tested 45.2) | power stage model | console executable |
| GoogleTest, gcov | from the presets | library unit tests | fetched by CMake |

Get the repositories into one folder:

```bash
mkdir sfs-stepper && cd sfs-stepper
git clone https://github.com/AntonVynohradov/Stepper-C.git sfs-stepper-ctrl
git clone https://github.com/AntonVynohradov/sfs-stepper-sim.git
git clone https://github.com/AntonVynohradov/sfs-stepper-power-spice.git
```

The library repository [Stepper-C](https://github.com/AntonVynohradov/Stepper-C) is
cloned into the folder `sfs-stepper-ctrl`: the simulation looks for the library under
that name (or in `SSTEP_CTRL_DIR`).

## Library: build and test

The library uses CMake presets. The preset names carry the configuration in brackets:

| Preset | What it builds |
| --- | --- |
| `[Debug]Stepper Motor Control` | static library, debug |
| `[Release]Stepper Motor Control` | static library, optimised |
| `[UnitTests]Stepper Motor Control` | GoogleTest suite, fixed point backend, coverage |
| `[UnitTestsFloat]Stepper Motor Control` | GoogleTest suite, float backend |
| `[IntegrationTests]Stepper Motor Control` | pytest integration tests (placeholder) |
| `[Examples]Stepper Motor Control` | host examples (placeholder) |

```bash
cd sfs-stepper-ctrl
cmake --preset "[UnitTests]Stepper Motor Control"
cmake --build "build/[UnitTests]Stepper Motor Control"
ctest --test-dir "build/[UnitTests]Stepper Motor Control" --output-on-failure
```

Expected result: 76 tests pass (75 with the float preset). VS Code users find the same
steps as tasks (*Terminal → Run Task*).

## Simulation: run the tests

1. Open Scilab and change to the `sfs-stepper-sim` folder.
2. Run the test runner:

```scilab
exec("tests/run_all.sce", -1);
```

or from a terminal (exit status 1 on a failure, for CI):

```bash
scilab-cli -f tests/run_all.sce
```

Each test prints one line `PASS name: measured values` or `FAIL …`, and the runner ends
with the number of failures. The full run takes a few minutes; T10 (switching stage) and
T11 (resonance sweep) take the longest.

The Python twins run without Scilab:

```bash
cd sfs-stepper-sim
python -m pip install -r requirements-dev.txt
python tools/ref_model.py        # T00–T02, motor model
python tools/ref_ctrl.py         # B01, T03, T04, current loop
python tools/ref_motion.py       # T05–T07, T09, motion generator
python tools/ref_switching.py    # T10, switching stage
python tools/ref_ext.py          # T08, T11, T12
```

## Software in the loop: see the motor turn

1. Make sure `sfs-stepper-ctrl` is next to `sfs-stepper-sim` (or set `SSTEP_CTRL_DIR`).
2. Open `start_sil.sce` in Scilab and press **F5**. The first time, Scilab compiles the
   library and the Xcos blocks (a few seconds); later it only links them, and it
   rebuilds automatically when a source file changed.
3. Xcos opens `xcos/stepper_sil.zcos`. Press **Start** (▶).

The scope shows the phase currents with their references, the speed, the load angle and
the commanded and real rotor positions. The scenario is edited in
**Simulation → Set Context**; see [Software in the Loop](sil.md) for every variable.

!!! tip "After an update of the blocks"
    When the block interface changed (new outputs, parameters), set
    `sil_regenerate = %t` in `start_sil.sce` once, or delete `xcos/stepper_sil.zcos`; the
    diagram is generated again from `xcos/sil_diagram.sci`. Restart Scilab when the
    library was rebuilt, because Windows keeps the old DLL loaded.

## Power stage: run ngspice

1. Install ngspice. On Windows, download the 64-bit zip from
   <https://ngspice.sourceforge.io/download.html>, unpack it and point `NGSPICE` to
   `Spice64\bin\ngspice_con.exe` (or install `mingw-w64-ucrt-x86_64-ngspice` in MSYS2).
   On Linux, `apt install ngspice`.
2. Run the tests and export the parameters to the simulation:

```bash
cd sfs-stepper-power-spice
python -m pip install -r requirements-dev.txt
python tools/run_tests.py --export     # about 40 s
python tools/plot_leg.py               # docs/leg_edges.png
```

The runner prints SP01–SP03 and writes `export/stage_esc1.json` and, when
`../sfs-stepper-sim` exists, `params/stage_esc1_spice.sci` and `.json` there.

## This manual

The manual is built from Markdown with MkDocs Material (website) and WeasyPrint (PDF):

```bash
git clone https://github.com/SystemFromScratch-Articles/Stepper-C-Motor-Control-Library.git sfs-stepper-article
cd sfs-stepper-article
python -m pip install -r requirements-docs.txt
mkdocs serve                              # http://127.0.0.1:8000
python tools/docs/build_manual.py         # pdf/Stepper-C_System_Manual_v0.1.0.pdf (not committed)
python tools/docs/diagrams.py             # regenerate the diagrams
python tools/docs/figures.py              # regenerate the data figures (needs the sim twins)
```

WeasyPrint needs the Pango library: on Windows install `mingw-w64-x86_64-pango` in MSYS2
(the build script finds `C:\msys64\mingw64\bin` by itself), on Linux
`apt install libpango-1.0-0 libpangoft2-1.0-0`.
