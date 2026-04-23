from __future__ import annotations

import math

from netSim.numerics import NonlinearProblem, build_nonlinear_solver

from .gravity import elevation_pressure_term
from .pressure_drop import PressureDropCorrelation


class LaminarPipeCorrelation(PressureDropCorrelation):
    def calculate_velocity(
        self,
        pipe_state,
        delta_p: float,
        density: float,
        viscosity: float,
        tolerance: float | None = None,
    ) -> float:
        driving_term = delta_p - elevation_pressure_term(density, pipe_state.component.height_change_m)
        return (
            pipe_state.component.diameter_m**2
            * driving_term
            / (32.0 * viscosity * pipe_state.component.length_m)
        )

    def calculate_coupling(self, pipe_state, density: float, viscosity: float) -> float:
        return (-density / (32.0 * viscosity)) * (
            pipe_state.area_m2 * pipe_state.component.diameter_m**2 / pipe_state.component.length_m
        )


class ColebrookPipeCorrelation(PressureDropCorrelation):
    def calculate_velocity(
        self,
        pipe_state,
        delta_p: float,
        density: float,
        viscosity: float,
        tolerance: float | None = None,
        friction_factor_method: str = "newton",
        velocity_loop_method: str = "fixed_point",
    ) -> float:
        if tolerance is None:
            raise ValueError("ColebrookPipeCorrelation requires a tolerance value.")

        initial_velocity = self._safe_velocity_guess(pipe_state.velocity_m_per_s)
        problem = NonlinearProblem(
            fixed_point_fn=lambda velocity: self._fixed_point_mapping(
                pipe_state,
                velocity,
                delta_p,
                density,
                viscosity,
                tolerance,
                friction_factor_method,
            ),
            residual_fn=lambda velocity: self._velocity_residual(
                pipe_state,
                velocity,
                delta_p,
                density,
                viscosity,
                tolerance,
                friction_factor_method,
            ),
        )
        solver = build_nonlinear_solver(velocity_loop_method)
        solved_velocity = solver.solve(problem, initial_velocity, tolerance)
        self._assign_pipe_state(
            pipe_state,
            solved_velocity,
            density,
            viscosity,
            tolerance,
            friction_factor_method,
        )
        return pipe_state.velocity_m_per_s

    def _fixed_point_mapping(
        self,
        pipe_state,
        velocity: float,
        delta_p: float,
        density: float,
        viscosity: float,
        tolerance: float,
        friction_factor_method: str,
    ) -> float:
        safe_velocity = self._safe_velocity_guess(velocity)
        friction_factor, _ = self._friction_factor_for_velocity(
            pipe_state,
            safe_velocity,
            density,
            viscosity,
            tolerance,
            friction_factor_method,
        )
        driving_term = delta_p - elevation_pressure_term(
            density,
            pipe_state.component.height_change_m,
        )
        return (
            2.0
            * pipe_state.component.diameter_m
            * driving_term
            / (
                density
                * friction_factor
                * pipe_state.component.length_m
                * max(abs(safe_velocity), 1e-12)
            )
        )

    def _velocity_residual(
        self,
        pipe_state,
        velocity: float,
        delta_p: float,
        density: float,
        viscosity: float,
        tolerance: float,
        friction_factor_method: str,
    ) -> float:
        safe_velocity = self._safe_velocity_guess(velocity)
        friction_factor, _ = self._friction_factor_for_velocity(
            pipe_state,
            safe_velocity,
            density,
            viscosity,
            tolerance,
            friction_factor_method,
        )

        driving_term = delta_p - elevation_pressure_term(
            density,
            pipe_state.component.height_change_m,
        )
        friction_term = (
            density
            * friction_factor
            * pipe_state.component.length_m
            * safe_velocity
            * abs(safe_velocity)
            / (2.0 * pipe_state.component.diameter_m)
        )
        return driving_term - friction_term

    def _friction_factor_for_velocity(
        self,
        pipe_state,
        velocity: float,
        density: float,
        viscosity: float,
        tolerance: float,
        friction_factor_method: str,
    ) -> tuple[float, float]:
        reynolds = density * abs(velocity) * pipe_state.component.diameter_m / viscosity
        pipe_state.reynolds = reynolds
        initial_guess = max(64.0 / max(reynolds, 1e-12), 1e-6)
        friction_factor = self.solve_colebrook(
            pipe_state,
            initial_guess,
            tolerance,
            friction_factor_method,
        )
        return friction_factor, reynolds

    def _assign_pipe_state(
        self,
        pipe_state,
        velocity: float,
        density: float,
        viscosity: float,
        tolerance: float,
        friction_factor_method: str,
    ) -> None:
        safe_velocity = self._safe_velocity_guess(velocity)
        friction_factor, reynolds = self._friction_factor_for_velocity(
            pipe_state,
            safe_velocity,
            density,
            viscosity,
            tolerance,
            friction_factor_method,
        )
        pipe_state.velocity_m_per_s = safe_velocity
        pipe_state.reynolds = reynolds
        pipe_state.friction_factor = friction_factor

    @staticmethod
    def _safe_velocity_guess(velocity: float) -> float:
        if abs(velocity) < 1e-6:
            return 1e-6 if velocity >= 0.0 else -1e-6
        return velocity

    def calculate_coupling(self, pipe_state, density: float, viscosity: float) -> float:
        return (
            -2.0
            * pipe_state.area_m2
            * pipe_state.component.diameter_m
            / (
                pipe_state.friction_factor
                * max(abs(pipe_state.velocity_m_per_s), 1e-12)
                * pipe_state.component.length_m
            )
        )

    def solve_colebrook(
        self,
        pipe_state,
        initial_guess: float,
        tolerance: float,
        friction_factor_method: str,
    ) -> float:
        problem = NonlinearProblem(
            residual_fn=lambda friction_factor: self.evaluate_colebrook(
                pipe_state,
                friction_factor,
            ),
            derivative_fn=lambda friction_factor: self._colebrook_derivative(
                pipe_state,
                friction_factor,
            ),
        )
        solver = build_nonlinear_solver(friction_factor_method)
        friction_factor = solver.solve(problem, initial_guess, tolerance)
        return max(abs(friction_factor), 1e-8)

    def _colebrook_derivative(self, pipe_state, friction_factor: float) -> float:
        delta_f = 1e-7
        base_value = self.evaluate_colebrook(pipe_state, friction_factor)
        shifted_value = self.evaluate_colebrook(pipe_state, friction_factor + delta_f)
        return (shifted_value - base_value) / delta_f

    def evaluate_colebrook(self, pipe_state, friction_factor: float) -> float:
        log_term = (
            (pipe_state.component.absolute_roughness_m / pipe_state.component.diameter_m) / 3.7
            + 2.51 / (max(pipe_state.reynolds, 1e-12) * math.sqrt(friction_factor))
        )
        return 1.0 / math.sqrt(friction_factor) + 2.0 * math.log10(log_term)


class DarcyWeisbachModel:
    def __init__(self) -> None:
        self.laminar_correlation = LaminarPipeCorrelation()
        self.turbulent_correlation = ColebrookPipeCorrelation()

    def laminar_velocity(self, pipe_state, delta_p: float, density: float, viscosity: float) -> float:
        return self.laminar_correlation.calculate_velocity(pipe_state, delta_p, density, viscosity)

    def turbulent_velocity(self, pipe_state, delta_p: float, density: float, viscosity: float, tolerance: float) -> float:
        return self.turbulent_correlation.calculate_velocity(
            pipe_state,
            delta_p,
            density,
            viscosity,
            tolerance,
        )

    def laminar_coupling(self, pipe_state, density: float, viscosity: float) -> float:
        return self.laminar_correlation.calculate_coupling(pipe_state, density, viscosity)

    def turbulent_coupling(self, pipe_state) -> float:
        return self.turbulent_correlation.calculate_coupling(pipe_state, 0.0, 0.0)
