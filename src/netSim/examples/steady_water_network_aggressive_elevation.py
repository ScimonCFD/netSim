from __future__ import annotations

from netSim.cases import build_steady_water_network_aggressive_elevation_case
from netSim.io.reporting import print_solve_result
from netSim.main import build_default_solver


def main() -> None:
    case = build_steady_water_network_aggressive_elevation_case()
    solver = build_default_solver()
    result = solver.solve(case)
    print_solve_result(result)


if __name__ == "__main__":
    main()
