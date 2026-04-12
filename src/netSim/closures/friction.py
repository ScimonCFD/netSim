from __future__ import annotations

import math

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
    ) -> float:
        if tolerance is None:
            raise ValueError("ColebrookPipeCorrelation requires a tolerance value.")

        if abs(pipe_state.velocity_m_per_s) < 1e-12:
            pipe_state.velocity_m_per_s = 1e-6

        pipe_state.friction_factor = max(64.0 / max(pipe_state.reynolds, 1e-12), 1e-6)
        residual = 1.0
        while residual >= tolerance:
            pipe_state.friction_factor = self.solve_colebrook(pipe_state, pipe_state.friction_factor, tolerance)
            driving_term = delta_p - elevation_pressure_term(density, pipe_state.component.height_change_m)
            new_velocity = (
                2.0
                * pipe_state.component.diameter_m
                * driving_term
                / (
                    density
                    * pipe_state.friction_factor
                    * pipe_state.component.length_m
                    * abs(pipe_state.velocity_m_per_s)
                )
            )
            denominator = max(abs(new_velocity), 1e-12)
            residual = abs(new_velocity - pipe_state.velocity_m_per_s) / denominator
            pipe_state.velocity_m_per_s = new_velocity
            pipe_state.reynolds = density * abs(pipe_state.velocity_m_per_s) * pipe_state.component.diameter_m / viscosity

        return pipe_state.velocity_m_per_s

    def calculate_coupling(self, pipe_state, density: float, viscosity: float) -> float:
        return (
            -2.0
            * pipe_state.area_m2
            * pipe_state.component.diameter_m
            / (
                pipe_state.friction_factor
                * pipe_state.velocity_m_per_s
                * pipe_state.component.length_m
            )
        )

    def solve_colebrook(self, pipe_state, initial_guess: float, tolerance: float) -> float:
        friction_factor = initial_guess
        residual = 1.0
        while residual >= tolerance:
            base_value = self.evaluate_colebrook(pipe_state, friction_factor)
            delta_f = 1e-7
            shifted_value = self.evaluate_colebrook(pipe_state, friction_factor + delta_f)
            derivative = (shifted_value - base_value) / delta_f
            friction_factor = abs(friction_factor - base_value / derivative)
            residual = abs(shifted_value)
        return max(friction_factor, 1e-8)

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
