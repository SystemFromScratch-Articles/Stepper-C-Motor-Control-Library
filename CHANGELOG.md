# Changelog

All notable changes to this manual are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- First edition (0.1.0) of the Stepper-C system user manual, covering Stepper-C 0.1.0,
  `sfs-stepper-sim` 0.1.0 and `sfs-stepper-power-spice` 0.1.0:
  introduction, system architecture, getting started, motor model, control algorithms,
  library guide, API reference, simulation, software in the loop, power stage model,
  test catalogue, results and design guidance, hardware bring-up plan, parameter
  reference, glossary.
- Website (MkDocs Material, SystemFromScratch® style) and print-ready A4 PDF
  (`tools/docs/build_manual.py`, WeasyPrint) from the same Markdown.
- Typeset formulas (LaTeX through `pymdownx.arithmatex`): MathJax on the website, SVG
  rendered with matplotlib mathtext in the PDF.
- Generated diagrams (`tools/docs/diagrams.py`) and data figures from the Python twins
  of the simulation (`tools/docs/figures.py`).
- GitHub Actions workflow: builds the PDF and deploys the website to GitHub Pages.
