# netSim

`netSim` is a clean hydraulic-network solver project built from the recovered
core of an earlier thesis prototype.

The current version focuses on a deliberately narrow but useful scope:

- steady
- incompressible
- isothermal
- single-component
- pipes and fittings
- pressure and mass-flow boundary conditions

This folder is the master project for the new codebase. It is intended to be
worked on independently from the older thesis files outside `netSim/`.

## What It Does Today

The current solver can compute nodal pressures and component flow rates for
small steady pipe networks with:

- laminar and turbulent pipe flow
- fittings represented through local-loss coefficients
- optional elevation changes in pipes
- pressure boundaries
- inlet and outlet mass-flow boundaries

The present implementation uses:

- adaptive laminar initialisation
- a segregated pressure-correction workflow
- explicit pressure under-relaxation
- interchangeable pressure-drop models for pipes and fittings

## Repository Layout

The project is organised around a simple split between engine code,
tutorials, and technical notes:

- `src/netSim/`: solver engine
- `tutorials/`: runnable example cases grouped by solver family
- `docs/`: design and equation notes
- `tests/`: smoke tests for the validated tutorial suite

Inside `src/netSim/`, the main folders are:

- `core/`: network topology, components, state, settings, results
- `properties/`: fluid-property models
- `closures/`: pressure-drop and related closure models
- `numerics/`: assembly, convergence, and linear algebra helpers
- `solvers/`: solver implementations
- `cases/`: reusable case definitions
- `io/`: reporting helpers

## Quick Start

Run the default example:

```bash
PYTHONPATH=src python3 -m netSim.main
```

Launch the first GUI prototype:

```bash
PYTHONPATH=src python3 -m netSim.gui.app
```

Run the smoke-test suite:

```bash
python3 -m unittest discover -s tests
```

## Tutorials

The validated tutorial suite currently contains six cases:

For the current solver family, they live under:

- `tutorials/steady_isothermal_incompressible/`

The six validated cases are:

1. Pipe-only base case
   `python3 tutorials/steady_isothermal_incompressible/01_pipe_only/run.py`
2. Base case with fittings
   `python3 tutorials/steady_isothermal_incompressible/02_fittings_no_elevation/run.py`
3. Base case with fittings and elevation changes
   `python3 tutorials/steady_isothermal_incompressible/03_fittings_with_elevation/run.py`
4. Elevation case with an inlet mass-flow boundary
   `python3 tutorials/steady_isothermal_incompressible/04_inlet_flow/run.py`
5. Elevation case with an outlet mass-flow boundary
   `python3 tutorials/steady_isothermal_incompressible/05_outlet_flow/run.py`
6. Case with both inlet and outlet mass-flow boundaries
   `python3 tutorials/steady_isothermal_incompressible/06_inlet_and_outlet_flow/run.py`

These tutorials are intended both as examples for users and as a lightweight
validation suite for the current solver.

## Current Limits

This is still an early foundation, not yet a full industrial simulator.

Some important limits of the current branch are:

- no energy equation yet
- no transient solving yet
- no multicomponent or multiphase models yet
- only a very early GUI prototype
- explicit, not implicit, pressure relaxation

## Near-Term Direction

The current branch is meant to serve as the numerical base for future work,
including:

- non-isothermal solving through an energy equation
- richer property models
- additional pressure-drop correlations
- coupled versus segregated solver families
- a future GUI that writes inputs for the same calculation engine

## Additional Notes

The longer workflow and governing-equation note is available in:

- `docs/WORKFLOW_AND_EQUATIONS.md`
