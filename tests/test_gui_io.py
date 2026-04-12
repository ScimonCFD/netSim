from __future__ import annotations

import sys
import unittest
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from netSim.gui.io import load_scene_from_file


class GuiIoTests(unittest.TestCase):
    def test_load_pipe_only_tutorial_scene(self) -> None:
        case_path = (
            Path(__file__).resolve().parents[1]
            / "tutorials"
            / "steady_isothermal_incompressible"
            / "01_pipe_only"
            / "pipe_only.gui.json"
        )

        scene = load_scene_from_file(case_path)

        self.assertEqual(len(scene.nodes), 6)
        self.assertEqual(len(scene.links), 6)
        self.assertEqual(scene.get_node(1).properties["pressure"], "251300.0")
        self.assertEqual(scene.get_link(1).components[0].component_type, "pipe")
