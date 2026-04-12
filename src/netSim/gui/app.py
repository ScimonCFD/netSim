from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .io import load_scene_from_file
from .model import CanvasLink, CanvasLinkComponent, CanvasNode, CanvasScene


class ToolTip:
    def __init__(self, widget: tk.Widget, text: str) -> None:
        self.widget = widget
        self.text = text
        self.tip_window: tk.Toplevel | None = None

        self.widget.bind("<Enter>", self._show)
        self.widget.bind("<Leave>", self._hide)

    def _show(self, _event: tk.Event) -> None:
        if self.tip_window is not None:
            return

        x = self.widget.winfo_rootx() + self.widget.winfo_width() + 8
        y = self.widget.winfo_rooty() + 4

        self.tip_window = tk.Toplevel(self.widget)
        self.tip_window.wm_overrideredirect(True)
        self.tip_window.wm_geometry(f"+{x}+{y}")

        label = tk.Label(
            self.tip_window,
            text=self.text,
            background="#fff8dc",
            relief="solid",
            borderwidth=1,
            padx=6,
            pady=3,
        )
        label.pack()

    def _hide(self, _event: tk.Event) -> None:
        if self.tip_window is not None:
            self.tip_window.destroy()
            self.tip_window = None


class NetSimGui:
    def __init__(self) -> None:
        self.scene = CanvasScene()
        self.drag_source_node_id: int | None = None
        self.drag_line_id: int | None = None
        self.moving_node_id: int | None = None
        self.root = tk.Tk()
        self.root.title("netSim GUI Prototype")
        self.root.geometry("1100x700")
        self.root.minsize(900, 600)

        self.status_var = tk.StringVar(value="Select a node type from the palette.")
        self.tool_var = tk.StringVar(value="No tool selected")

        self._build_menu()
        self._build_layout()

    def _build_menu(self) -> None:
        menu_bar = tk.Menu(self.root)
        file_menu = tk.Menu(menu_bar, tearoff=False)
        file_menu.add_command(label="New", command=self._new_scene)
        file_menu.add_command(label="Open", command=self._open_scene)
        file_menu.add_separator()
        file_menu.add_command(label="Close", command=self.root.destroy)
        menu_bar.add_cascade(label="File", menu=file_menu)
        self.root.config(menu=menu_bar)

    def _build_layout(self) -> None:
        container = ttk.Frame(self.root, padding=8)
        container.pack(fill="both", expand=True)

        palette = ttk.Frame(container, padding=(8, 8, 12, 8))
        palette.pack(side="left", fill="y")

        palette_title = ttk.Label(palette, text="Node Palette")
        palette_title.pack(anchor="w", pady=(0, 8))

        source_button = ttk.Button(
            palette,
            text="▲",
            command=lambda: self._select_tool("source"),
            width=4,
        )
        source_button.pack(anchor="w", pady=4)
        ToolTip(source_button, "Source")

        sink_button = ttk.Button(
            palette,
            text="▼",
            command=lambda: self._select_tool("sink"),
            width=4,
        )
        sink_button.pack(anchor="w", pady=4)
        ToolTip(sink_button, "Sink")

        junction_button = ttk.Button(
            palette,
            text="○",
            command=lambda: self._select_tool("junction"),
            width=4,
        )
        junction_button.pack(anchor="w", pady=4)
        ToolTip(junction_button, "Junction")

        ttk.Separator(palette, orient="horizontal").pack(fill="x", pady=10)

        ttk.Label(palette, text="Active Tool").pack(anchor="w")
        ttk.Label(
            palette,
            textvariable=self.tool_var,
            width=20,
            relief="groove",
            padding=6,
        ).pack(anchor="w", pady=(4, 0))

        canvas_frame = ttk.Frame(container)
        canvas_frame.pack(side="left", fill="both", expand=True)

        self.canvas = tk.Canvas(
            canvas_frame,
            background="#fbfaf4",
            highlightthickness=1,
            highlightbackground="#b8b2a7",
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<ButtonPress-1>", self._on_canvas_press)
        self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release)
        self.canvas.bind("<Shift-ButtonPress-1>", self._on_canvas_shift_press)
        self.canvas.bind("<Shift-B1-Motion>", self._on_canvas_shift_drag)
        self.canvas.bind("<Shift-ButtonRelease-1>", self._on_canvas_shift_release)
        self.canvas.bind("<ButtonPress-3>", self._on_canvas_right_press)
        self.canvas.bind("<B3-Motion>", self._on_canvas_right_drag)
        self.canvas.bind("<ButtonRelease-3>", self._on_canvas_right_release)
        self.canvas.bind("<Double-Button-1>", self._on_canvas_double_click)

        status = ttk.Label(
            self.root,
            textvariable=self.status_var,
            relief="sunken",
            anchor="w",
            padding=(8, 4),
        )
        status.pack(fill="x", side="bottom")

    def _select_tool(self, tool: str) -> None:
        self.scene.set_active_tool(tool)
        self.tool_var.set(tool.capitalize())
        self.status_var.set(f"{tool.capitalize()} selected. Click on the canvas to place it.")

    def _new_scene(self) -> None:
        self.scene.clear()
        self.canvas.delete("all")
        self.drag_source_node_id = None
        self.drag_line_id = None
        self.moving_node_id = None
        self.tool_var.set("No tool selected")
        self.status_var.set("New scene created. Select a node type from the palette.")

    def _open_scene(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Open netSim GUI case",
            filetypes=(
                ("netSim GUI case", "*.gui.json"),
                ("JSON files", "*.json"),
                ("All files", "*.*"),
            ),
        )
        if not file_path:
            return

        try:
            self.scene = load_scene_from_file(file_path)
        except Exception as exc:  # pragma: no cover - UI feedback path
            messagebox.showerror("Open failed", f"Could not open case:\n{exc}")
            return

        self.canvas.delete("all")
        self.drag_source_node_id = None
        self.drag_line_id = None
        self.moving_node_id = None
        self.tool_var.set("No tool selected")
        self._redraw_scene()
        self.status_var.set(f"Opened GUI case: {file_path}")

    def _on_canvas_press(self, event: tk.Event) -> None:
        node_id = self._node_id_at(event.x, event.y)

        if self.scene.active_tool is not None:
            return

        if node_id is None:
            return

        node = self.scene.get_node(node_id)
        if node is None:
            return

        self.moving_node_id = node_id
        self.status_var.set(
            f"Moving {node.node_type} #{node.node_id}. Drag with left mouse button."
        )

    def _on_canvas_right_press(self, event: tk.Event) -> None:
        if self.scene.active_tool is not None:
            return

        node_id = self._node_id_at(event.x, event.y)
        if node_id is None:
            return

        node = self.scene.get_node(node_id)
        if node is None:
            return

        self.drag_source_node_id = node_id
        self.drag_line_id = self.canvas.create_line(
            node.x,
            node.y,
            event.x,
            event.y,
            fill="#6c757d",
            width=2,
            dash=(5, 3),
        )
        self.status_var.set(
            f"Connecting from {node.node_type} #{node.node_id}. Drag with right mouse button."
        )

    def _on_canvas_shift_press(self, event: tk.Event) -> None:
        self._on_canvas_right_press(event)

    def _on_canvas_drag(self, event: tk.Event) -> None:
        if self.moving_node_id is None:
            return

        updated_node = self.scene.move_node(self.moving_node_id, event.x, event.y)
        self._redraw_scene()
        self.status_var.set(
            f"Moving {updated_node.node_type} #{updated_node.node_id} to "
            f"({int(updated_node.x)}, {int(updated_node.y)})."
        )

    def _on_canvas_right_drag(self, event: tk.Event) -> None:
        if self.drag_line_id is None or self.drag_source_node_id is None:
            return

        source = self.scene.get_node(self.drag_source_node_id)
        if source is None:
            return

        self.canvas.coords(self.drag_line_id, source.x, source.y, event.x, event.y)

    def _on_canvas_shift_drag(self, event: tk.Event) -> None:
        self._on_canvas_right_drag(event)

    def _on_canvas_release(self, event: tk.Event) -> None:
        if self.moving_node_id is not None:
            moved_node = self.scene.get_node(self.moving_node_id)
            self.moving_node_id = None
            if moved_node is not None:
                self.status_var.set(
                    f"Moved {moved_node.node_type} #{moved_node.node_id} to "
                    f"({int(moved_node.x)}, {int(moved_node.y)})."
                )
            return

        if self.scene.active_tool is None:
            self.status_var.set("Select Source, Sink, or Junction before placing a node.")
            return

        if self._node_id_at(event.x, event.y) is not None:
            self.status_var.set("Release on empty canvas space to place a new node.")
            return

        node = self.scene.add_node(event.x, event.y)
        self._draw_node(node)
        placed_tool = node.node_type
        self.scene.set_active_tool(None)
        self.tool_var.set("No tool selected")
        self.status_var.set(
            f"Placed {placed_tool} #{node.node_id} at ({int(node.x)}, {int(node.y)}). "
            "Select a node type to place another."
        )

    def _on_canvas_right_release(self, event: tk.Event) -> None:
        if self.drag_source_node_id is not None:
            self._finish_connection(event)

    def _on_canvas_shift_release(self, event: tk.Event) -> None:
        self._on_canvas_right_release(event)

    def _on_canvas_double_click(self, event: tk.Event) -> None:
        node_id = self._node_id_at(event.x, event.y)
        if node_id is not None:
            node = self.scene.get_node(node_id)
            if node is None:
                return

            self._open_node_properties_dialog(node)
            return

        link_id = self._link_id_at(event.x, event.y)
        if link_id is None:
            return

        link = self.scene.get_link(link_id)
        if link is None:
            return

        self._open_link_properties_dialog(link)

    def _finish_connection(self, event: tk.Event) -> None:
        source_node_id = self.drag_source_node_id
        target_node_id = self._node_id_at(event.x, event.y)
        self._clear_drag_line()

        if source_node_id is None:
            return
        if target_node_id is None:
            self.status_var.set("Connection cancelled. Release over another node to connect.")
            return
        if target_node_id == source_node_id:
            self.status_var.set("Connection cancelled. Choose a different target node.")
            return

        try:
            link = self.scene.add_link(source_node_id, target_node_id)
        except ValueError as exc:
            self.status_var.set(str(exc))
            return

        self._draw_link(link)
        source = self.scene.get_node(source_node_id)
        target = self.scene.get_node(target_node_id)
        if source is not None and target is not None:
            self.status_var.set(
                f"Connected {source.node_type} #{source.node_id} to "
                f"{target.node_type} #{target.node_id}."
            )

    def _draw_node(self, node: CanvasNode) -> None:
        radius = 24
        x0 = node.x - radius
        y0 = node.y - radius
        x1 = node.x + radius
        y1 = node.y + radius

        fill_color = self._node_fill(node.node_type)
        label = self._node_label(node)

        node_tag = f"node_{node.node_id}"

        self.canvas.create_oval(
            x0,
            y0,
            x1,
            y1,
            fill=fill_color,
            outline="#2e2a24",
            width=2,
            tags=(node_tag, "node"),
        )
        self.canvas.create_text(
            node.x,
            node.y - 2,
            text=label,
            font=("TkDefaultFont", 9, "bold"),
            tags=(node_tag, "node"),
        )
        self.canvas.create_text(
            node.x,
            node.y + 12,
            text=str(node.node_id),
            font=("TkDefaultFont", 8),
            tags=(node_tag, "node"),
        )

    def _draw_link(self, link: CanvasLink) -> None:
        start = self.scene.get_node(link.start_node_id)
        end = self.scene.get_node(link.end_node_id)
        if start is None or end is None:
            return

        self.canvas.create_line(
            start.x,
            start.y,
            end.x,
            end.y,
            fill="#4f5d75",
            width=3,
            tags=("link", f"link_{link.link_id}"),
        )
        self.canvas.tag_lower("link")

    def _redraw_scene(self) -> None:
        self.canvas.delete("all")
        for link in self.scene.links:
            self._draw_link(link)
        for node in self.scene.nodes:
            self._draw_node(node)

    def _node_id_at(self, x: float, y: float) -> int | None:
        overlapping = self.canvas.find_overlapping(x - 1, y - 1, x + 1, y + 1)
        for item_id in reversed(overlapping):
            for tag in self.canvas.gettags(item_id):
                if tag.startswith("node_"):
                    return int(tag.split("_", 1)[1])
        return None

    def _link_id_at(self, x: float, y: float) -> int | None:
        overlapping = self.canvas.find_overlapping(x - 3, y - 3, x + 3, y + 3)
        for item_id in reversed(overlapping):
            for tag in self.canvas.gettags(item_id):
                if tag.startswith("link_"):
                    return int(tag.split("_", 1)[1])
        return None

    def _clear_drag_line(self) -> None:
        if self.drag_line_id is not None:
            self.canvas.delete(self.drag_line_id)
        self.drag_line_id = None
        self.drag_source_node_id = None

    def _open_node_properties_dialog(self, node: CanvasNode) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title(f"{node.node_type.capitalize()} #{node.node_id}")
        dialog.transient(self.root)
        dialog.resizable(False, False)

        container = ttk.Frame(dialog, padding=12)
        container.pack(fill="both", expand=True)
        container.columnconfigure(1, weight=1)

        entries: dict[str, tk.StringVar] = {}

        if node.node_type in {"source", "sink"}:
            ttk.Label(container, text="Boundary Type").grid(row=0, column=0, sticky="w", pady=4)
            condition_var = tk.StringVar(value=node.properties.get("condition_type", "pressure"))
            entries["condition_type"] = condition_var

            condition_frame = ttk.Frame(container)
            condition_frame.grid(row=0, column=1, sticky="w", pady=4)

            ttk.Radiobutton(
                condition_frame,
                text="Pressure",
                value="pressure",
                variable=condition_var,
            ).pack(side="left", padx=(0, 8))
            ttk.Radiobutton(
                condition_frame,
                text="Flow",
                value="flow",
                variable=condition_var,
            ).pack(side="left")

            ttk.Label(container, text="Pressure").grid(row=1, column=0, sticky="w", pady=4)
            pressure_var = tk.StringVar(value=node.properties.get("pressure", ""))
            pressure_entry = ttk.Entry(container, textvariable=pressure_var, width=20)
            pressure_entry.grid(row=1, column=1, sticky="ew", pady=4)
            entries["pressure"] = pressure_var

            ttk.Label(container, text="Flow").grid(row=2, column=0, sticky="w", pady=4)
            flow_var = tk.StringVar(value=node.properties.get("flow", ""))
            flow_entry = ttk.Entry(container, textvariable=flow_var, width=20)
            flow_entry.grid(row=2, column=1, sticky="ew", pady=4)
            entries["flow"] = flow_var

            self._sync_boundary_entries(
                condition_var,
                pressure_entry,
                flow_entry,
            )
            condition_var.trace_add(
                "write",
                lambda *_args: self._sync_boundary_entries(
                    condition_var,
                    pressure_entry,
                    flow_entry,
                ),
            )
        else:
            ttk.Label(container, text="Label").grid(row=0, column=0, sticky="w", pady=4)
            label_var = tk.StringVar(value=node.properties.get("label", ""))
            ttk.Entry(container, textvariable=label_var, width=20).grid(
                row=0, column=1, sticky="ew", pady=4
            )
            entries["label"] = label_var

        button_row = ttk.Frame(container)
        button_row.grid(row=10, column=0, columnspan=2, sticky="e", pady=(10, 0))

        ttk.Button(button_row, text="Cancel", command=dialog.destroy).pack(side="right", padx=(8, 0))
        ttk.Button(
            button_row,
            text="Save",
            command=lambda: self._save_node_properties(node.node_id, entries, dialog),
        ).pack(side="right")

        dialog.update_idletasks()
        dialog.grab_set()
        dialog.focus_set()

    def _open_link_properties_dialog(self, link: CanvasLink) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Connection #{link.link_id}")
        dialog.transient(self.root)
        dialog.resizable(False, False)

        container = ttk.Frame(dialog, padding=12)
        container.pack(fill="both", expand=True)
        container.columnconfigure(1, weight=1)
        container.columnconfigure(2, weight=1)

        ttk.Label(container, text="Component Palette").grid(
            row=0, column=0, sticky="w", padx=(0, 12), pady=(0, 8)
        )
        ttk.Label(container, text="Added Components").grid(
            row=0, column=1, sticky="w", pady=(0, 8)
        )
        ttk.Label(container, text="Component Properties").grid(
            row=0, column=2, sticky="w", padx=(12, 0), pady=(0, 8)
        )

        palette = ttk.Frame(container)
        palette.grid(row=1, column=0, sticky="ns")

        components_list = tk.Listbox(container, width=28, height=8)
        components_list.grid(row=1, column=1, sticky="nsew")
        properties_frame = ttk.LabelFrame(container, text="Selected Component", padding=10)
        properties_frame.grid(row=1, column=2, sticky="nsew", padx=(12, 0))

        for component in link.components:
            components_list.insert("end", self._component_list_label(component))

        ttk.Button(
            palette,
            text="Pipe",
            command=lambda: self._add_component_to_link(
                link.link_id,
                "pipe",
                components_list,
                properties_frame,
            ),
            width=12,
        ).pack(anchor="w", pady=4)
        ttk.Button(
            palette,
            text="Fitting",
            command=lambda: self._add_component_to_link(
                link.link_id,
                "fitting",
                components_list,
                properties_frame,
            ),
            width=12,
        ).pack(anchor="w", pady=4)

        components_list.bind(
            "<<ListboxSelect>>",
            lambda _event: self._render_link_component_properties(
                link.link_id,
                components_list,
                properties_frame,
            ),
        )

        button_row = ttk.Frame(container)
        button_row.grid(row=2, column=0, columnspan=3, sticky="e", pady=(12, 0))
        ttk.Button(button_row, text="Close", command=dialog.destroy).pack(side="right")

        dialog.update_idletasks()
        dialog.grab_set()
        dialog.focus_set()

    def _add_component_to_link(
        self,
        link_id: int,
        component_type: str,
        components_list: tk.Listbox,
        properties_frame: ttk.LabelFrame,
    ) -> None:
        updated_link = self.scene.add_link_component(link_id, component_type)
        components_list.delete(0, "end")
        for component in updated_link.components:
            components_list.insert("end", self._component_list_label(component))
        components_list.selection_clear(0, "end")
        components_list.selection_set("end")
        self._render_link_component_properties(link_id, components_list, properties_frame)
        self.status_var.set(
            f"Added {component_type} to connection #{updated_link.link_id}."
        )

    def _render_link_component_properties(
        self,
        link_id: int,
        components_list: tk.Listbox,
        properties_frame: ttk.LabelFrame,
    ) -> None:
        for child in properties_frame.winfo_children():
            child.destroy()

        selected = components_list.curselection()
        if not selected:
            ttk.Label(properties_frame, text="Select a component to edit its data.").pack(
                anchor="w"
            )
            return

        link = self.scene.get_link(link_id)
        if link is None:
            return

        component = link.components[selected[0]]
        entries: dict[str, tk.StringVar] = {}

        ttk.Label(
            properties_frame,
            text=f"{component.component_type.capitalize()} #{component.component_id}",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        row = 1
        for key, value in component.properties.items():
            ttk.Label(properties_frame, text=self._pretty_field_name(key)).grid(
                row=row, column=0, sticky="w", pady=4
            )
            var = tk.StringVar(value=value)
            ttk.Entry(properties_frame, textvariable=var, width=18).grid(
                row=row, column=1, sticky="ew", pady=4
            )
            entries[key] = var
            row += 1

        button_row = ttk.Frame(properties_frame)
        button_row.grid(row=row, column=0, columnspan=2, sticky="e", pady=(10, 0))
        ttk.Button(
            button_row,
            text="Save",
            command=lambda: self._save_link_component_properties(
                link_id,
                component.component_id,
                entries,
                components_list,
                properties_frame,
            ),
        ).pack(side="right")

    def _save_link_component_properties(
        self,
        link_id: int,
        component_id: int,
        entries: dict[str, tk.StringVar],
        components_list: tk.Listbox,
        properties_frame: ttk.LabelFrame,
    ) -> None:
        properties = {key: value.get().strip() for key, value in entries.items()}
        updated_link = self.scene.update_link_component_properties(
            link_id,
            component_id,
            properties,
        )
        selection = components_list.curselection()
        components_list.delete(0, "end")
        for component in updated_link.components:
            components_list.insert("end", self._component_list_label(component))
        if selection:
            components_list.selection_set(selection[0])
        self._render_link_component_properties(link_id, components_list, properties_frame)
        self.status_var.set(f"Updated component #{component_id} in connection #{link_id}.")

    @staticmethod
    def _sync_boundary_entries(
        condition_var: tk.StringVar,
        pressure_entry: ttk.Entry,
        flow_entry: ttk.Entry,
    ) -> None:
        if condition_var.get() == "pressure":
            pressure_entry.state(["!disabled"])
            flow_entry.state(["disabled"])
        else:
            pressure_entry.state(["disabled"])
            flow_entry.state(["!disabled"])

    def _save_node_properties(
        self,
        node_id: int,
        entries: dict[str, tk.StringVar],
        dialog: tk.Toplevel,
    ) -> None:
        properties = {key: value.get().strip() for key, value in entries.items()}
        updated_node = self.scene.update_node_properties(node_id, properties)
        self.status_var.set(
            f"Updated properties for {updated_node.node_type} #{updated_node.node_id}."
        )
        dialog.destroy()

    @staticmethod
    def _node_fill(node_type: str) -> str:
        colors = {
            "source": "#8ecae6",
            "sink": "#f28482",
            "junction": "#d9d9d9",
        }
        return colors[node_type]

    @staticmethod
    def _node_label(node: CanvasNode) -> str:
        labels = {
            "source": "S",
            "sink": "K",
            "junction": "J",
        }
        return labels[node.node_type]

    @staticmethod
    def _component_list_label(component: CanvasLinkComponent) -> str:
        return f"{component.component_type.capitalize()} #{component.component_id}"

    @staticmethod
    def _pretty_field_name(field_name: str) -> str:
        return field_name.replace("_", " ").replace(" m", " (m)").capitalize()

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    app = NetSimGui()
    app.run()


if __name__ == "__main__":
    main()
