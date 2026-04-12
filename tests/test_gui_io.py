from __future__ import annotations

import sys
import unittest
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from netSim.gui.io import build_network_case_from_scene, build_solver_from_scene, load_scene_from_file


class GuiIoTests(unittest.TestCase):
    @staticmethod
    def _pipe_only_case_path() -> Path:
        return (
            Path(__file__).resolve().parents[1]
            / "tutorials"
            / "steady_isothermal_incompressible"
            / "01_pipe_only"
            / "pipe_only.gui.json"
        )

    def test_load_pipe_only_tutorial_scene(self) -> None:
        scene = load_scene_from_file(self._pipe_only_case_path())

        self.assertEqual(len(scene.nodes), 6)
        self.assertEqual(len(scene.links), 6)
        self.assertEqual(scene.get_node(1).properties["pressure"], "251300.0")
        self.assertEqual(scene.get_link(1).components[0].component_type, "pipe")

    def test_pipe_only_tutorial_scene_builds_and_converges(self) -> None:
        scene = load_scene_from_file(self._pipe_only_case_path())
        case = build_network_case_from_scene(scene)
        result = build_solver_from_scene(scene).solve(case)

        self.assertEqual(case.name, "GUI scene")
        self.assertEqual(len(case.components), 6)
        self.assertTrue(result.converged)

    def test_all_gui_tutorial_scenes_build_and_converge(self) -> None:
        tutorial_root = (
            Path(__file__).resolve().parents[1]
            / "tutorials"
            / "steady_isothermal_incompressible"
        )
        gui_paths = sorted(tutorial_root.glob("*/*.gui.json"))

        self.assertGreaterEqual(len(gui_paths), 6)

        for gui_path in gui_paths:
            with self.subTest(gui_path=gui_path.name):
                scene = load_scene_from_file(gui_path)
                case = build_network_case_from_scene(scene)
                result = build_solver_from_scene(scene).solve(case)
                self.assertTrue(result.converged, msg=f"{gui_path} did not converge")
