from __future__ import annotations

import json
from pathlib import Path

from .model import CanvasLink, CanvasLinkComponent, CanvasNode, CanvasScene


def scene_from_dict(data: dict) -> CanvasScene:
    scene = CanvasScene()
    scene.nodes = [
        CanvasNode(
            node_id=int(node["node_id"]),
            node_type=str(node["node_type"]),
            x=float(node["x"]),
            y=float(node["y"]),
            properties=dict(node.get("properties", {})),
        )
        for node in data.get("nodes", [])
    ]
    scene.links = [
        CanvasLink(
            link_id=int(link["link_id"]),
            start_node_id=int(link["start_node_id"]),
            end_node_id=int(link["end_node_id"]),
            components=[
                CanvasLinkComponent(
                    component_id=int(component["component_id"]),
                    component_type=str(component["component_type"]),
                    properties=dict(component.get("properties", {})),
                )
                for component in link.get("components", [])
            ],
        )
        for link in data.get("links", [])
    ]

    scene._next_node_id = max((node.node_id for node in scene.nodes), default=0) + 1
    scene._next_link_id = max((link.link_id for link in scene.links), default=0) + 1
    scene._next_component_id = (
        max(
            (
                component.component_id
                for link in scene.links
                for component in link.components
            ),
            default=0,
        )
        + 1
    )
    scene.active_tool = None
    return scene


def load_scene_from_file(path: str | Path) -> CanvasScene:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return scene_from_dict(data)
