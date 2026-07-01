import io
import json
import math
import tkinter as tk
import tkinter.colorchooser as tkcolorchooser
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk


class GaramiEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Garami — Editor Gráfico Moderno")
        self.geometry("1360x820")
        self.minsize(1080, 720)
        self.configure(bg="#0f172a")

        self.current_tool = tk.StringVar(value="pen")
        self.current_color = tk.StringVar(value="#2563eb")
        self.current_fill_color = tk.StringVar(value="#f8fafc")
        self.brush_width = tk.IntVar(value=3)
        self.font_size = tk.IntVar(value=18)
        self.zoom_level = 1.0
        self.undo_stack = []
        self.selected_items = []
        self.clipboard_items = []
        self.drag_items = []
        self.last_drag_x = 0
        self.last_drag_y = 0
        self.preview_id = None
        self.background_image = None
        self.group_counter = 0
        self.groups = {}
        self.selection_box_id = None
        self.selection_handles = []
        self.active_resize_handle = None
        self.active_resize_anchor = None
        self.resize_start_bbox = None
        self.resize_start_state = {}
        self.grid_enabled = True
        self.snap_to_grid = True
        self.grid_size = 20
        self.opacity_value = tk.DoubleVar(value=1.0)
        self.layer_order_ids = []
        self.layer_visibility = {}
        self.layer_locked = {}
        self.layer_names = {}

        self._build_ui()

    def _build_ui(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("TFrame", background="#0f172a")
        style.configure("Card.TFrame", background="#111827")
        style.configure("TLabel", background="#0f172a", foreground="#e5e7eb")
        style.configure("Tool.TButton", padding=8, borderwidth=0)
        style.configure("Accent.TButton", padding=8, borderwidth=0)
        style.configure("TScale", background="#0f172a")

        self.menu_bar = tk.Menu(
            self, bg="#111827", fg="#e5e7eb", activebackground="#1f2937")
        file_menu = tk.Menu(self.menu_bar, tearoff=0,
                            bg="#111827", fg="#e5e7eb")
        file_menu.add_command(label="Novo", command=self.new_canvas)
        file_menu.add_command(label="Abrir...", command=self.load_file)
        file_menu.add_command(label="Salvar...", command=self.save_file)
        file_menu.add_command(label="Exportar imagem",
                              command=self.export_image)
        file_menu.add_separator()
        file_menu.add_command(label="Sair", command=self.destroy)
        self.menu_bar.add_cascade(label="Arquivo", menu=file_menu)

        edit_menu = tk.Menu(self.menu_bar, tearoff=0,
                            bg="#111827", fg="#e5e7eb")
        edit_menu.add_command(label="Copiar", command=self.copy_selection)
        edit_menu.add_command(label="Colar", command=self.paste_selection)
        edit_menu.add_command(label="Recortar", command=self.cut_selection)
        edit_menu.add_command(label="Excluir", command=self.delete_selection)
        edit_menu.add_command(label="Agrupar", command=self.group_selection)
        edit_menu.add_command(label="Desagrupar",
                              command=self.ungroup_selection)
        edit_menu.add_command(label="Adicionar imagem de fundo",
                              command=self.add_background_image)
        self.menu_bar.add_cascade(label="Editar", menu=edit_menu)
        self.config(menu=self.menu_bar)

        top_bar = ttk.Frame(self, style="Card.TFrame", padding=12)
        top_bar.pack(fill="x")

        ttk.Label(top_bar, text="GARAMI", font=(
            "Segoe UI", 24, "bold")).pack(side="left")
        ttk.Label(top_bar, text="Editor gráfico profissional em Python",
                  foreground="#94a3b8").pack(side="left", padx=(16, 0))

        toolbar = ttk.Frame(self, style="Card.TFrame", padding=10)
        toolbar.pack(fill="x")

        tools = [
            ("Caneta", "pen"),
            ("Linha", "line"),
            ("Retângulo", "rectangle"),
            ("Elipse", "oval"),
            ("Texto", "text"),
            ("Seleção", "select"),
            ("Área", "area"),
            ("Preencher", "fill"),
            ("Borracha", "eraser"),
        ]
        for label, tool_name in tools:
            ttk.Button(
                toolbar,
                text=label,
                style="Tool.TButton",
                command=lambda name=tool_name: self._set_tool(name),
            ).pack(side="left", padx=4)

        ttk.Button(toolbar, text="Desfazer", command=self.undo_last,
                   style="Accent.TButton").pack(side="left", padx=(16, 4))
        ttk.Button(toolbar, text="Limpar", command=self.clear_canvas,
                   style="Accent.TButton").pack(side="left", padx=4)
        ttk.Button(toolbar, text="+ Zoom", command=self.zoom_in,
                   style="Accent.TButton").pack(side="left", padx=4)
        ttk.Button(toolbar, text="- Zoom", command=self.zoom_out,
                   style="Accent.TButton").pack(side="left", padx=4)
        ttk.Button(toolbar, text="100%", command=self.reset_zoom,
                   style="Accent.TButton").pack(side="left", padx=4)
        ttk.Button(toolbar, text="↑ Camada", command=self.bring_forward,
                   style="Accent.TButton").pack(side="left", padx=4)
        ttk.Button(toolbar, text="↓ Camada", command=self.send_backward,
                   style="Accent.TButton").pack(side="left", padx=4)
        ttk.Button(toolbar, text="Copiar", command=self.copy_selection,
                   style="Accent.TButton").pack(side="left", padx=4)
        ttk.Button(toolbar, text="Colar", command=self.paste_selection,
                   style="Accent.TButton").pack(side="left", padx=4)
        ttk.Button(toolbar, text="Dup.", command=self.duplicate_selection,
                   style="Accent.TButton").pack(side="left", padx=4)
        ttk.Button(toolbar, text="Redim.", command=self.resize_selection,
                   style="Accent.TButton").pack(side="left", padx=4)
        ttk.Button(toolbar, text="Rot.", command=self.rotate_selection,
                   style="Accent.TButton").pack(side="left", padx=4)
        ttk.Button(toolbar, text="Esq", command=lambda: self.align_selection("left"),
                   style="Accent.TButton").pack(side="left", padx=4)
        ttk.Button(toolbar, text="Centro", command=lambda: self.align_selection("center"),
                   style="Accent.TButton").pack(side="left", padx=4)
        ttk.Button(toolbar, text="Dir", command=lambda: self.align_selection("right"),
                   style="Accent.TButton").pack(side="left", padx=4)
        ttk.Button(toolbar, text="Topo", command=lambda: self.align_selection("top"),
                   style="Accent.TButton").pack(side="left", padx=4)
        ttk.Button(toolbar, text="Meio", command=lambda: self.align_selection("middle"),
                   style="Accent.TButton").pack(side="left", padx=4)
        ttk.Button(toolbar, text="Base", command=lambda: self.align_selection("bottom"),
                   style="Accent.TButton").pack(side="left", padx=4)
        ttk.Button(toolbar, text="Grupo", command=self.group_selection,
                   style="Accent.TButton").pack(side="left", padx=4)
        ttk.Button(toolbar, text="Espelho H", command=lambda: self.flip_selection("horizontal"),
                   style="Accent.TButton").pack(side="left", padx=4)
        ttk.Button(toolbar, text="Espelho V", command=lambda: self.flip_selection("vertical"),
                   style="Accent.TButton").pack(side="left", padx=4)
        ttk.Button(toolbar, text="Grade", command=self.toggle_grid,
                   style="Accent.TButton").pack(side="left", padx=4)
        ttk.Button(toolbar, text="Snap", command=self.toggle_snap,
                   style="Accent.TButton").pack(side="left", padx=4)
        ttk.Button(toolbar, text="Img Fundo", command=self.add_background_image,
                   style="Accent.TButton").pack(side="left", padx=4)
        ttk.Button(toolbar, text="SVG", command=self.export_svg,
                   style="Accent.TButton").pack(side="left", padx=4)

        controls = ttk.Frame(self, style="Card.TFrame", padding=10)
        controls.pack(fill="x")

        ttk.Label(controls, text="Cor da borda:").pack(side="left")
        tk.Entry(controls, textvariable=self.current_color,
                 width=10).pack(side="left", padx=(6, 8))
        ttk.Button(controls, text="Escolher", command=lambda: self.choose_color(
            self.current_color)).pack(side="left")

        ttk.Label(controls, text="Cor do preenchimento:").pack(
            side="left", padx=(10, 6))
        tk.Entry(controls, textvariable=self.current_fill_color,
                 width=10).pack(side="left", padx=(6, 8))
        ttk.Button(controls, text="Escolher", command=lambda: self.choose_color(
            self.current_fill_color)).pack(side="left")

        ttk.Label(controls, text="Espessura:").pack(side="left", padx=(16, 6))
        ttk.Scale(controls, from_=1, to=20, variable=self.brush_width,
                  orient="horizontal").pack(side="left", padx=(0, 10))

        ttk.Label(controls, text="Tamanho do texto:").pack(
            side="left", padx=(10, 6))
        ttk.Scale(controls, from_=12, to=48, variable=self.font_size,
                  orient="horizontal").pack(side="left")

        ttk.Label(controls, text="Opacidade:").pack(side="left", padx=(10, 6))
        ttk.Scale(controls, from_=0.0, to=1.0, variable=self.opacity_value,
                  orient="horizontal").pack(side="left")

        workspace_frame = ttk.Frame(self, style="Card.TFrame", padding=8)
        workspace_frame.pack(fill="both", expand=True, padx=12, pady=12)

        self.canvas = tk.Canvas(
            workspace_frame, bg="white", highlightthickness=1, highlightbackground="#cbd5e1")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.bind("<Configure>", self.redraw_grid)
        self.canvas.bind("<ButtonPress-1>", self.on_canvas_press)
        self.canvas.bind("<Double-1>", self.on_canvas_double_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.canvas.bind("<Control-c>", self.copy_selection)
        self.canvas.bind("<Control-v>", self.paste_selection)
        self.canvas.bind("<Delete>", self.delete_selection)
        self.canvas.focus_set()
        self.bind_all("<KeyPress-Left>", self.on_key_press)
        self.bind_all("<KeyPress-Right>", self.on_key_press)
        self.bind_all("<KeyPress-Up>", self.on_key_press)
        self.bind_all("<KeyPress-Down>", self.on_key_press)

        layers_panel = ttk.LabelFrame(
            workspace_frame, text="Camadas", padding=8)
        layers_panel.pack(side="right", fill="y", padx=(8, 0))
        self.layers_listbox = tk.Listbox(
            layers_panel, height=12, exportselection=False)
        self.layers_listbox.configure(
            bg="#111827",
            fg="#e5e7eb",
            selectbackground="#38bdf8",
            selectforeground="#0f172a",
            activestyle="none",
        )
        self.layers_listbox.pack(fill="both", expand=True)
        self.layers_listbox.bind("<<ListboxSelect>>", self.on_layer_select)
        ttk.Button(layers_panel, text="Subir", command=self.move_selected_layer_up).pack(
            fill="x", pady=(6, 2))
        ttk.Button(layers_panel, text="Descer",
                   command=self.move_selected_layer_down).pack(fill="x")
        ttk.Button(layers_panel, text="Ocultar/Mostrar",
                   command=self.toggle_selected_layer_visibility).pack(fill="x", pady=(6, 2))
        ttk.Button(layers_panel, text="Mostrar Todas",
                   command=self.show_all_layers).pack(fill="x", pady=(6, 2))
        ttk.Button(layers_panel, text="Ocultar Todas",
                   command=self.hide_all_layers).pack(fill="x", pady=(6, 2))
        ttk.Button(layers_panel, text="Bloquear/Desbloquear",
                   command=self.toggle_selected_layer_lock).pack(fill="x", pady=(6, 2))
        ttk.Button(layers_panel, text="Renomear",
                   command=self.rename_selected_layer).pack(fill="x")

        self.status = ttk.Label(self, text="Modo: Caneta", anchor="w")
        self.status.pack(fill="x", padx=12, pady=(0, 8))
        self._update_status()

    def _set_tool(self, tool_name):
        self.current_tool.set(tool_name)
        self._update_status()

    def _update_status(self):
        labels = {
            "pen": "Modo: Caneta",
            "line": "Modo: Linha",
            "rectangle": "Modo: Retângulo",
            "oval": "Modo: Elipse",
            "text": "Modo: Texto",
            "select": "Modo: Seleção",
            "area": "Modo: Seleção por área",
            "fill": "Modo: Preenchimento",
            "eraser": "Modo: Borracha",
        }
        self.status.config(text=labels.get(
            self.current_tool.get(), "Modo: Caneta"))

    def _refresh_layers_panel(self):
        if not hasattr(self, "layers_listbox"):
            return
        self.layer_order_ids = []
        self.layers_listbox.delete(0, tk.END)
        for item_id in self.canvas.find_all():
            tags = set(self.canvas.gettags(item_id))
            if tags & {"grid", "selection_box", "selection_handle", "background"}:
                continue
            item_type = self.canvas.type(item_id)
            if item_type == "image":
                continue
            self.layer_order_ids.append(item_id)
            visible = self.layer_visibility.get(item_id, True)
            locked = self.layer_locked.get(item_id, False)
            label = {
                "line": "Linha",
                "rectangle": "Retângulo",
                "oval": "Elipse",
                "text": "Texto",
            }.get(item_type, item_type.capitalize())
            custom_name = self.layer_names.get(item_id)
            layer_name = custom_name or f"{label} {len(self.layer_order_ids)}"
            visibility_icon = "👁" if visible else "🙈"
            lock_icon = "🔒" if locked else "🔓"
            self.layers_listbox.insert(
                tk.END, f"{visibility_icon} {lock_icon} {layer_name}")
        if len(self.selected_items) == 1:
            selected_id = self.selected_items[0]
            for index, item_id in enumerate(self.layer_order_ids):
                if item_id == selected_id:
                    self.layers_listbox.selection_clear(0, tk.END)
                    self.layers_listbox.selection_set(index)
                    break

    def on_layer_select(self, event=None):
        if not self.layers_listbox.curselection():
            return
        index = self.layers_listbox.curselection()[0]
        if index >= len(self.layer_order_ids):
            return
        self.selected_items = [self.layer_order_ids[index]]
        self._update_selection_visuals()

    def _is_item_locked(self, item_id):
        return self.layer_locked.get(item_id, False)

    def _is_item_visible(self, item_id):
        return self.layer_visibility.get(item_id, True)

    def toggle_selected_layer_visibility(self):
        if not self.layers_listbox.curselection():
            return
        index = self.layers_listbox.curselection()[0]
        if index >= len(self.layer_order_ids):
            return
        item_id = self.layer_order_ids[index]
        new_visible = not self._is_item_visible(item_id)
        self.layer_visibility[item_id] = new_visible
        self.canvas.itemconfigure(
            item_id, state="normal" if new_visible else "hidden")
        if not new_visible:
            self.selected_items = [
                item for item in self.selected_items if item != item_id]
            self._update_selection_visuals()
        self._refresh_layers_panel()

    def toggle_selected_layer_lock(self):
        if not self.layers_listbox.curselection():
            return
        index = self.layers_listbox.curselection()[0]
        if index >= len(self.layer_order_ids):
            return
        item_id = self.layer_order_ids[index]
        new_locked = not self._is_item_locked(item_id)
        self.layer_locked[item_id] = new_locked
        if new_locked:
            self.selected_items = [
                item for item in self.selected_items if item != item_id]
            self._update_selection_visuals()
        self._refresh_layers_panel()

    def show_all_layers(self):
        for item_id in self.layer_order_ids:
            self.layer_visibility[item_id] = True
            self.canvas.itemconfigure(item_id, state="normal")
        self._refresh_layers_panel()

    def hide_all_layers(self):
        for item_id in self.layer_order_ids:
            self.layer_visibility[item_id] = False
            self.canvas.itemconfigure(item_id, state="hidden")
        self.selected_items.clear()
        self._clear_selection_visuals()
        self._refresh_layers_panel()

    def rename_selected_layer(self):
        if not self.layers_listbox.curselection():
            return
        index = self.layers_listbox.curselection()[0]
        if index >= len(self.layer_order_ids):
            return
        item_id = self.layer_order_ids[index]
        current_name = self.layer_names.get(item_id, "Camada")
        new_name = simpledialog.askstring(
            "Renomear camada",
            "Digite o novo nome da camada:",
            initialvalue=current_name,
            parent=self,
        )
        if new_name:
            self.layer_names[item_id] = new_name
            self._refresh_layers_panel()

    def move_selected_layer_up(self):
        if not self.layers_listbox.curselection():
            return
        index = self.layers_listbox.curselection()[0]
        if index >= len(self.layer_order_ids) - 1:
            return
        item_id = self.layer_order_ids[index]
        self.canvas.tag_raise(item_id)
        self._refresh_layers_panel()
        self.selected_items = [item_id]
        self._update_selection_visuals()

    def move_selected_layer_down(self):
        if not self.layers_listbox.curselection():
            return
        index = self.layers_listbox.curselection()[0]
        if index <= 0:
            return
        item_id = self.layer_order_ids[index]
        self.canvas.tag_lower(item_id)
        self._refresh_layers_panel()
        self.selected_items = [item_id]
        self._update_selection_visuals()

    def _snap_value(self, value):
        if not self.snap_to_grid:
            return value
        return round(value / self.grid_size) * self.grid_size

    def _snap_item_to_grid(self, item_id):
        item_type = self.canvas.type(item_id)
        if item_type in {"rectangle", "oval", "line"}:
            coords = list(self.canvas.coords(item_id))
            if len(coords) >= 4:
                coords[0] = self._snap_value(coords[0])
                coords[1] = self._snap_value(coords[1])
                coords[2] = self._snap_value(coords[2])
                coords[3] = self._snap_value(coords[3])
                self.canvas.coords(item_id, *coords)
        elif item_type == "text":
            coords = list(self.canvas.coords(item_id))
            if coords:
                self.canvas.coords(item_id, self._snap_value(
                    coords[0]), self._snap_value(coords[1]))

    def _snap_selected_items_to_grid(self):
        for item_id in self.selected_items:
            self._snap_item_to_grid(item_id)

    def _get_numeric_option(self, item_id, option, default=None):
        try:
            val = self.canvas.itemcget(item_id, option)
            if val is None or val == "":
                return default
            # Try parse as float first to handle values like '3.0'
            try:
                f = float(val)
            except Exception:
                return val
            # If it is an integer-like value, return as int
            if f.is_integer():
                return int(f)
            return f
        except tk.TclError:
            return default

    def _is_pickable(self, item_id):
        if not item_id:
            return False
        # Exclude tagged helper items
        tags = set(self.canvas.gettags(item_id))
        if tags & {"grid", "selection_box", "selection_handle", "background"}:
            return False
        # Exclude images/background
        if self.canvas.type(item_id) == "image":
            return False
        # Exclude hidden items
        try:
            state = self.canvas.itemcget(item_id, "state")
            if state == "hidden":
                return False
        except tk.TclError:
            pass
        return True

    def _find_pickable_at(self, x, y):
        # Prefer overlapping items near the point, ordered topmost last
        nearby = list(self.canvas.find_overlapping(x - 2, y - 2, x + 2, y + 2))
        if nearby:
            # iterate in reverse so topmost items are considered first
            for item in reversed(nearby):
                if self._is_pickable(item) and not self._is_item_locked(item):
                    return item
        # fallback to find_closest but ensure it's pickable
        try:
            candidate = self.canvas.find_closest(x, y)[0]
            if self._is_pickable(candidate) and not self._is_item_locked(candidate):
                return candidate
        except Exception:
            pass
        return None

    def _clear_selection_visuals(self):
        if self.selection_box_id is not None:
            self.canvas.delete(self.selection_box_id)
            self.selection_box_id = None
        for handle_id in self.selection_handles:
            self.canvas.delete(handle_id)
        self.selection_handles.clear()

    def _get_selection_bbox(self):
        bboxes = []
        for item_id in self.selected_items:
            if self.canvas.type(item_id) != "image":
                bbox = self.canvas.bbox(item_id)
                if bbox:
                    bboxes.append(bbox)
        if not bboxes:
            return None
        return (
            min(bbox[0] for bbox in bboxes),
            min(bbox[1] for bbox in bboxes),
            max(bbox[2] for bbox in bboxes),
            max(bbox[3] for bbox in bboxes),
        )

    def _update_selection_visuals(self):
        self._clear_selection_visuals()
        if not self.selected_items:
            return
        bbox = self._get_selection_bbox()
        if not bbox:
            return
        x1, y1, x2, y2 = bbox
        self.selection_box_id = self.canvas.create_rectangle(
            x1, y1, x2, y2,
            outline="#38bdf8",
            dash=(3, 3),
            width=1,
            tags=("selection_box",),
        )
        handles = [
            (x1, y1, "nw"),
            ((x1 + x2) / 2, y1, "n"),
            (x2, y1, "ne"),
            (x1, (y1 + y2) / 2, "w"),
            (x2, (y1 + y2) / 2, "e"),
            (x1, y2, "sw"),
            ((x1 + x2) / 2, y2, "s"),
            (x2, y2, "se"),
        ]
        for hx, hy, anchor in handles:
            handle_id = self.canvas.create_rectangle(
                hx - 4, hy - 4, hx + 4, hy + 4,
                fill="#38bdf8",
                outline="#0f172a",
                width=1,
                tags=("selection_handle", f"handle_{anchor}"),
            )
            self.selection_handles.append(handle_id)
        self.canvas.tag_raise(self.selection_box_id)

    def _capture_resize_state(self):
        self.resize_start_state = {}
        if not self.selected_items:
            return
        for item_id in self.selected_items:
            item_type = self.canvas.type(item_id)
            state = {
                "type": item_type,
                "coords": list(self.canvas.coords(item_id)),
            }
            # Collect only the attributes that make sense for the item type
            if item_type == "text":
                state["font"] = self.canvas.itemcget(item_id, "font")
                state["text"] = self.canvas.itemcget(item_id, "text")
                state["fill"] = self.canvas.itemcget(item_id, "fill")
                state["angle"] = self.canvas.itemcget(item_id, "angle")
            elif item_type in {"rectangle", "oval"}:
                state["fill"] = self.canvas.itemcget(item_id, "fill")
                state["outline"] = self.canvas.itemcget(item_id, "outline")
                state["width"] = self._get_numeric_option(item_id, "width", 1)
            elif item_type == "line":
                state["fill"] = self.canvas.itemcget(item_id, "fill")
                state["width"] = self._get_numeric_option(item_id, "width", 1)
            else:
                # Best-effort safe reads for unknown/new item types
                try:
                    state["fill"] = self.canvas.itemcget(item_id, "fill")
                except tk.TclError:
                    state["fill"] = None
                try:
                    state["outline"] = self.canvas.itemcget(item_id, "outline")
                except tk.TclError:
                    state["outline"] = None
                try:
                    state["width"] = self._get_numeric_option(
                        item_id, "width", 1)
                except tk.TclError:
                    state["width"] = 1
                try:
                    state["font"] = self.canvas.itemcget(item_id, "font")
                except tk.TclError:
                    state["font"] = None
                try:
                    state["text"] = self.canvas.itemcget(item_id, "text")
                except tk.TclError:
                    state["text"] = None
                try:
                    state["angle"] = self.canvas.itemcget(item_id, "angle")
                except tk.TclError:
                    state["angle"] = None
            self.resize_start_state[item_id] = state
        self.resize_start_bbox = self._get_selection_bbox()

    def _apply_resize(self, new_bbox):
        if not self.selected_items or not self.resize_start_bbox:
            return
        old_bbox = self.resize_start_bbox
        old_x1, old_y1, old_x2, old_y2 = old_bbox
        new_x1, new_y1, new_x2, new_y2 = new_bbox
        old_width = max(1.0, old_x2 - old_x1)
        old_height = max(1.0, old_y2 - old_y1)
        new_width = max(8.0, new_x2 - new_x1)
        new_height = max(8.0, new_y2 - new_y1)
        sx = new_width / old_width if old_width else 1.0
        sy = new_height / old_height if old_height else 1.0

        for item_id, state in self.resize_start_state.items():
            item_type = state["type"]
            if item_type in {"rectangle", "oval", "line"}:
                coords = state["coords"]
                if len(coords) >= 4:
                    x1, y1, x2, y2 = coords[0], coords[1], coords[2], coords[3]
                    new_coords = [
                        new_x1 + (x1 - old_x1) * sx,
                        new_y1 + (y1 - old_y1) * sy,
                        new_x1 + (x2 - old_x1) * sx,
                        new_y1 + (y2 - old_y1) * sy,
                    ]
                    self.canvas.coords(item_id, *new_coords)
            elif item_type == "text":
                coords = state["coords"]
                if coords:
                    x, y = coords[0], coords[1]
                    new_x = new_x1 + (x - old_x1) * sx
                    new_y = new_y1 + (y - old_y1) * sy
                    self.canvas.coords(item_id, new_x, new_y)

    def choose_color(self, variable):
        color = tkcolorchooser.askcolor(color=variable.get())[1]
        if color:
            variable.set(color)

    def on_mouse_wheel(self, event):
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()
        return "break"

    def zoom_in(self):
        self._apply_zoom(1.1)

    def zoom_out(self):
        self._apply_zoom(0.9)

    def reset_zoom(self):
        if self.zoom_level != 1.0:
            self.canvas.scale(
                "all", 0, 0, 1 / self.zoom_level, 1 / self.zoom_level)
            self.zoom_level = 1.0

    def _apply_zoom(self, factor):
        self.canvas.scale("all", 0, 0, factor, factor)
        self.zoom_level *= factor

    def redraw_grid(self, event=None):
        if not self.grid_enabled:
            return
        self.canvas.delete("grid")
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        step = 20
        for x in range(0, width, step):
            self.canvas.create_line(
                x, 0, x, height, fill="#e2e8f0", tags="grid")
        for y in range(0, height, step):
            self.canvas.create_line(
                0, y, width, y, fill="#e2e8f0", tags="grid")
        self.canvas.tag_lower("grid")

    def toggle_grid(self):
        self.grid_enabled = not self.grid_enabled
        if self.grid_enabled:
            self.redraw_grid()
        else:
            self.canvas.delete("grid")

    def toggle_snap(self):
        self.snap_to_grid = not self.snap_to_grid
        if self.selected_items:
            self._snap_selected_items_to_grid()
            self._update_selection_visuals()

    def _rotate_point(self, x, y, cx, cy, angle):
        radians = math.radians(angle)
        dx = x - cx
        dy = y - cy
        return (
            cx + dx * math.cos(radians) - dy * math.sin(radians),
            cy + dx * math.sin(radians) + dy * math.cos(radians),
        )

    def _serialize_item(self, item_id):
        item_type = self.canvas.type(item_id)
        payload = {
            "type": item_type,
            "visible": self.layer_visibility.get(item_id, True),
            "locked": self.layer_locked.get(item_id, False),
            "name": self.layer_names.get(item_id, "Camada"),
        }
        if item_type == "line":
            payload.update({
                "coords": self.canvas.coords(item_id),
                "fill": self.canvas.itemcget(item_id, "fill"),
                "width": self._get_numeric_option(item_id, "width", self.brush_width.get()),
            })
        elif item_type in {"rectangle", "oval"}:
            payload.update({
                "coords": self.canvas.coords(item_id),
                "outline": self.canvas.itemcget(item_id, "outline"),
                "fill": self.canvas.itemcget(item_id, "fill"),
                "width": self._get_numeric_option(item_id, "width", self.brush_width.get()),
            })
        elif item_type == "text":
            payload.update({
                "coords": self.canvas.coords(item_id),
                "text": self.canvas.itemcget(item_id, "text"),
                "fill": self.canvas.itemcget(item_id, "fill"),
                "font": self.canvas.itemcget(item_id, "font"),
                "angle": self.canvas.itemcget(item_id, "angle"),
            })
        return payload

    def _offset_payload(self, payload, dx, dy):
        payload = json.loads(json.dumps(payload))
        if "coords" in payload:
            offset_coords = []
            for index, coord in enumerate(payload["coords"]):
                offset_coords.append(coord + (dx if index % 2 == 0 else dy))
            payload["coords"] = offset_coords
        return payload

    def _create_item_from_payload(self, payload):
        item_type = payload["type"]
        if item_type == "line":
            item_id = self.canvas.create_line(
                *payload["coords"],
                fill=payload.get("fill", self.current_color.get()),
                width=payload.get("width", self.brush_width.get()),
                capstyle="round",
                smooth=True,
            )
            self._apply_layer_state(item_id, payload.get(
                "visible", True), payload.get("locked", False))
            return item_id
        if item_type == "rectangle":
            item_id = self.canvas.create_rectangle(
                *payload["coords"],
                outline=payload.get("outline", self.current_color.get()),
                fill=payload.get("fill", self.current_fill_color.get()),
                width=payload.get("width", self.brush_width.get()),
            )
            self._apply_layer_state(item_id, payload.get(
                "visible", True), payload.get("locked", False))
            return item_id
        if item_type == "oval":
            item_id = self.canvas.create_oval(
                *payload["coords"],
                outline=payload.get("outline", self.current_color.get()),
                fill=payload.get("fill", self.current_fill_color.get()),
                width=payload.get("width", self.brush_width.get()),
            )
            self._apply_layer_state(item_id, payload.get(
                "visible", True), payload.get("locked", False))
            return item_id
        if item_type == "text":
            item_id = self.canvas.create_text(
                *payload["coords"],
                text=payload.get("text", ""),
                fill=payload.get("fill", self.current_color.get()),
                font=payload.get(
                    "font", ("Segoe UI", self.font_size.get(), "normal")),
                anchor="nw",
                angle=payload.get("angle", 0),
            )
        return None

    def _apply_layer_state(self, item_id, visible, locked, name=None):
        if item_id is None:
            return
        self.layer_visibility[item_id] = visible
        self.layer_locked[item_id] = locked
        if name is not None:
            self.layer_names[item_id] = name
        else:
            self.layer_names.setdefault(item_id, "Camada")
        self.canvas.itemconfigure(
            item_id, state="normal" if visible else "hidden")

    def on_canvas_press(self, event):
        self.start_x = self._snap_value(event.x)
        self.start_y = self._snap_value(event.y)
        self.last_x = event.x
        self.last_y = event.y
        self.preview_id = None
        self.drag_items = []
        self.active_resize_handle = None
        self.active_resize_anchor = None

        tool = self.current_tool.get()
        if tool == "select":
            clicked_handle = None
            for handle_id in self.selection_handles:
                if self.canvas.type(handle_id) == "rectangle":
                    bbox = self.canvas.bbox(handle_id)
                    if bbox and bbox[0] <= event.x <= bbox[2] and bbox[1] <= event.y <= bbox[3]:
                        clicked_handle = handle_id
                        break
            if clicked_handle is not None:
                self.active_resize_handle = clicked_handle
                self.active_resize_anchor = next(
                    tag.split("_", 1)[1] for tag in self.canvas.gettags(clicked_handle) if tag.startswith("handle_")
                )
                self._capture_resize_state()
                self.last_drag_x = event.x
                self.last_drag_y = event.y
                self._update_status()
                return

            item = self._find_pickable_at(event.x, event.y)
            if item and not self._is_item_locked(item):
                ctrl_pressed = bool(event.state & 0x0004)
                if ctrl_pressed:
                    if item in self.selected_items:
                        self.selected_items.remove(item)
                    elif item not in self.selected_items:
                        self.selected_items.append(item)
                else:
                    self.selected_items = [item]
                self.drag_items = list(self.selected_items)
                self.last_drag_x = event.x
                self.last_drag_y = event.y
            else:
                if not bool(event.state & 0x0004):
                    self.selected_items.clear()
            self._update_selection_visuals()
            self._update_status()
            self._refresh_layers_panel()
            return

        if tool == "fill":
            item = self._find_pickable_at(event.x, event.y)
            if item and self.canvas.type(item) in {"rectangle", "oval"}:
                self.canvas.itemconfig(
                    item, fill=self.current_fill_color.get())
                self.undo_stack.append(item)
            self._update_status()
            return

        if tool == "area":
            self.preview_id = self.canvas.create_rectangle(
                event.x,
                event.y,
                event.x,
                event.y,
                outline="#38bdf8",
                dash=(3, 3),
                width=1,
            )
            self._update_status()
            return

        if tool == "text":
            # If clicking an existing text item, edit it; otherwise create new
            clicked = self._find_pickable_at(event.x, event.y)
            if clicked and self.canvas.type(clicked) == "text" and not self._is_item_locked(clicked):
                current = self.canvas.itemcget(clicked, "text")
                new_text = simpledialog.askstring(
                    "Editar texto", "Texto:", initialvalue=current, parent=self)
                if new_text is not None:
                    self.canvas.itemconfig(clicked, text=new_text)
                    self.undo_stack.append(clicked)
                    self._refresh_layers_panel()
                self._update_status()
                return

            text = simpledialog.askstring(
                "Texto", "Digite o texto:", parent=self)
            if text:
                item_id = self.canvas.create_text(
                    event.x,
                    event.y,
                    text=text,
                    fill=self.current_color.get(),
                    font=("Segoe UI", self.font_size.get(), "normal"),
                    anchor="nw",
                )
                self._apply_layer_state(
                    item_id, True, False, self.layer_names.get(item_id))
                self.undo_stack.append(item_id)
                self._refresh_layers_panel()
            self._update_status()
            return

        if tool == "line":
            self.preview_id = self.canvas.create_line(
                event.x,
                event.y,
                event.x,
                event.y,
                fill=self.current_color.get(),
                width=self.brush_width.get(),
                capstyle="round",
            )
            self._apply_layer_state(self.preview_id, True, False, "Linha")
        elif tool == "rectangle":
            self.preview_id = self.canvas.create_rectangle(
                event.x,
                event.y,
                event.x,
                event.y,
                outline=self.current_color.get(),
                fill=self.current_fill_color.get(),
                width=self.brush_width.get(),
            )
            self._apply_layer_state(self.preview_id, True, False, "Retângulo")
        elif tool == "oval":
            self.preview_id = self.canvas.create_oval(
                event.x,
                event.y,
                event.x,
                event.y,
                outline=self.current_color.get(),
                fill=self.current_fill_color.get(),
                width=self.brush_width.get(),
            )
            self._apply_layer_state(self.preview_id, True, False, "Elipse")

        self._update_status()

    def on_canvas_drag(self, event):
        tool = self.current_tool.get()
        if tool == "select":
            if self.active_resize_handle is not None:
                initial_bbox = self.resize_start_bbox
                if initial_bbox is None:
                    return
                x1, y1, x2, y2 = initial_bbox
                if self.active_resize_anchor in {"nw", "w", "sw"}:
                    x1 = event.x
                if self.active_resize_anchor in {"ne", "e", "se"}:
                    x2 = event.x
                if self.active_resize_anchor in {"nw", "n", "ne"}:
                    y1 = event.y
                if self.active_resize_anchor in {"sw", "s", "se"}:
                    y2 = event.y
                x1 = min(x1, x2 - 8)
                x2 = max(x2, x1 + 8)
                y1 = min(y1, y2 - 8)
                y2 = max(y2, y1 + 8)
                self._apply_resize((x1, y1, x2, y2))
                self._update_selection_visuals()
                return

            if self.drag_items:
                dx = event.x - self.last_drag_x
                dy = event.y - self.last_drag_y
                for item_id in self.drag_items:
                    self.canvas.move(item_id, dx, dy)
                self._snap_selected_items_to_grid()
                self.last_drag_x = event.x
                self.last_drag_y = event.y
                self._update_selection_visuals()
                return

        if tool in {"pen", "eraser"}:
            color = self.current_color.get() if tool == "pen" else "white"
            item_id = self.canvas.create_line(
                self.last_x,
                self.last_y,
                event.x,
                event.y,
                fill=color,
                width=self.brush_width.get(),
                capstyle="round",
                smooth=True,
            )
            self._apply_layer_state(item_id, True, False, "Caneta")
            self.undo_stack.append(item_id)
            self._refresh_layers_panel()
            self.last_x = event.x
            self.last_y = event.y
        elif self.preview_id is not None:
            if tool == "line":
                self.canvas.coords(self.preview_id, self.start_x,
                                   self.start_y, self._snap_value(event.x), self._snap_value(event.y))
            elif tool in {"rectangle", "oval"}:
                self.canvas.coords(self.preview_id, self.start_x,
                                   self.start_y, self._snap_value(event.x), self._snap_value(event.y))
            elif tool == "area":
                self.canvas.coords(self.preview_id, self.start_x,
                                   self.start_y, self._snap_value(event.x), self._snap_value(event.y))

    def on_canvas_release(self, event):
        tool = self.current_tool.get()
        if self.preview_id is not None:
            if tool == "area":
                self.canvas.delete(self.preview_id)
                self.select_items_in_region(
                    self.start_x, self.start_y, event.x, event.y)
            else:
                self.undo_stack.append(self.preview_id)
            self.preview_id = None
        self.drag_items = []
        self.active_resize_handle = None
        self.active_resize_anchor = None
        self.resize_start_bbox = None
        self.resize_start_state = {}
        self._update_selection_visuals()
        self._refresh_layers_panel()

    def on_canvas_double_click(self, event):
        item = self._find_pickable_at(event.x, event.y)
        if item and self.canvas.type(item) == "text" and not self._is_item_locked(item):
            current = self.canvas.itemcget(item, "text")
            new_text = simpledialog.askstring(
                "Editar texto", "Texto:", initialvalue=current, parent=self)
            if new_text is not None:
                self.canvas.itemconfig(item, text=new_text)
                self.selected_items = [item]
                self._update_selection_visuals()
                self.undo_stack.append(item)
                self._refresh_layers_panel()
            return "break"
        return None

    def on_key_press(self, event):
        if event.keysym not in {"Left", "Right", "Up", "Down"}:
            return
        if not self.selected_items:
            return
        delta = 20 if not (event.state & 0x0001) else 1
        if event.keysym == "Left":
            dx, dy = -delta, 0
        elif event.keysym == "Right":
            dx, dy = delta, 0
        elif event.keysym == "Up":
            dx, dy = 0, -delta
        else:
            dx, dy = 0, delta
        for item_id in self.selected_items:
            self.canvas.move(item_id, dx, dy)
        self._snap_selected_items_to_grid()
        self._update_selection_visuals()
        self._refresh_layers_panel()
        return "break"

    def undo_last(self):
        if not self.undo_stack:
            return
        entry = self.undo_stack.pop()
        if isinstance(entry, dict) and entry.get("type") == "delete":
            for payload in reversed(entry.get("items", [])):
                item_id = self._create_item_from_payload(payload)
                if item_id is not None:
                    self.undo_stack.append(item_id)
            return
        if self.canvas.find_withtag(entry):
            self.canvas.delete(entry)

    def clear_canvas(self):
        if messagebox.askyesno("Limpar tela", "Deseja apagar tudo da área de desenho?"):
            self.canvas.delete("all")
            self.undo_stack.clear()
            self.selected_items.clear()
            self._clear_selection_visuals()
            self.background_image = None
            self._refresh_layers_panel()

    def new_canvas(self):
        self.clear_canvas()

    def bring_forward(self):
        for item_id in self.selected_items:
            self.canvas.tag_raise(item_id)
        self._refresh_layers_panel()

    def send_backward(self):
        for item_id in self.selected_items:
            self.canvas.tag_lower(item_id)
        self._refresh_layers_panel()

    def copy_selection(self, event=None):
        if not self.selected_items:
            return
        self.clipboard_items = [self._serialize_item(
            item_id) for item_id in self.selected_items]
        return "break"

    def cut_selection(self):
        if not self.selected_items:
            return
        self.copy_selection()
        deleted_payloads = []
        for item_id in list(self.selected_items):
            deleted_payloads.append(self._serialize_item(item_id))
            self.canvas.delete(item_id)
        self.undo_stack.append({"type": "delete", "items": deleted_payloads})
        self.selected_items.clear()
        self._refresh_layers_panel()

    def paste_selection(self, event=None):
        if not self.clipboard_items:
            return
        created_ids = []
        offset = 20
        for payload in self.clipboard_items:
            shifted_payload = self._offset_payload(payload, offset, offset)
            item_id = self._create_item_from_payload(shifted_payload)
            if item_id is not None:
                created_ids.append(item_id)
        self.selected_items = created_ids
        self.undo_stack.extend(created_ids)
        return "break"

    def delete_selection(self, event=None):
        if not self.selected_items:
            return
        deleted_payloads = []
        for item_id in list(self.selected_items):
            deleted_payloads.append(self._serialize_item(item_id))
            self.canvas.delete(item_id)
        self.undo_stack.append({"type": "delete", "items": deleted_payloads})
        self.selected_items.clear()
        self._refresh_layers_panel()
        return "break"

    def duplicate_selection(self):
        if not self.selected_items:
            return
        created_ids = []
        for item_id in self.selected_items:
            payload = self._serialize_item(item_id)
            shifted_payload = self._offset_payload(payload, 20, 20)
            new_item_id = self._create_item_from_payload(shifted_payload)
            if new_item_id is not None:
                created_ids.append(new_item_id)
        self.selected_items = created_ids
        self.undo_stack.extend(created_ids)

    def align_selection(self, mode):
        if not self.selected_items:
            return
        bboxes = [self.canvas.bbox(item_id) for item_id in self.selected_items]
        if mode in {"left", "center", "right"}:
            target = min(bbox[0] for bbox in bboxes) if mode == "left" else (
                sum((bbox[0] + bbox[2]) / 2 for bbox in bboxes) /
                len(bboxes) if mode == "center" else max(
                    bbox[2] for bbox in bboxes)
            )
            for item_id, bbox in zip(self.selected_items, bboxes):
                current = self.canvas.bbox(item_id)
                if mode == "left":
                    dx = target - current[0]
                elif mode == "center":
                    dx = target - (current[0] + current[2]) / 2
                else:
                    dx = target - current[2]
                self.canvas.move(item_id, dx, 0)
        else:
            target = min(bbox[1] for bbox in bboxes) if mode == "top" else (
                sum((bbox[1] + bbox[3]) / 2 for bbox in bboxes) /
                len(bboxes) if mode == "middle" else max(
                    bbox[3] for bbox in bboxes)
            )
            for item_id, bbox in zip(self.selected_items, bboxes):
                current = self.canvas.bbox(item_id)
                if mode == "top":
                    dy = target - current[1]
                elif mode == "middle":
                    dy = target - (current[1] + current[3]) / 2
                else:
                    dy = target - current[3]
                self.canvas.move(item_id, 0, dy)

    def flip_selection(self, mode):
        if not self.selected_items:
            return
        for item_id in self.selected_items:
            item_type = self.canvas.type(item_id)
            if item_type in {"rectangle", "oval", "line"}:
                x1, y1, x2, y2 = self.canvas.coords(item_id)
                cx = (x1 + x2) / 2
                cy = (y1 + y2) / 2
                if mode == "horizontal":
                    self.canvas.coords(item_id, x2, y1, x1, y2)
                else:
                    self.canvas.coords(item_id, x1, y2, x2, y1)
            elif item_type == "text":
                self.canvas.itemconfig(
                    item_id, angle=-float(self.canvas.itemcget(item_id, "angle") or 0))

    def apply_opacity(self, item_id):
        try:
            self.canvas.itemconfig(item_id, stipple="")
            if self.canvas.type(item_id) == "text":
                self.canvas.itemconfig(
                    item_id, fill=self.canvas.itemcget(item_id, "fill"))
            else:
                self.canvas.itemconfig(
                    item_id, fill=self.canvas.itemcget(item_id, "fill"))
        except Exception:
            pass

    def resize_selection(self):
        if not self.selected_items:
            return
        item_id = self.selected_items[0]
        width = simpledialog.askinteger(
            "Redimensionar", "Nova largura:", initialvalue=120, parent=self)
        height = simpledialog.askinteger(
            "Redimensionar", "Nova altura:", initialvalue=120, parent=self)
        if width is None or height is None:
            return
        item_type = self.canvas.type(item_id)
        if item_type in {"rectangle", "oval", "line"}:
            x1, y1, x2, y2 = self.canvas.coords(item_id)
            self.canvas.coords(item_id, x1, y1, x1 + width, y1 + height)
        elif item_type == "text":
            self.canvas.itemconfig(item_id, font=(
                "Segoe UI", max(12, height), "normal"))

    def rotate_selection(self):
        if not self.selected_items:
            return
        angle = simpledialog.askinteger(
            "Rotação", "Ângulo em graus:", initialvalue=15, parent=self)
        if angle is None:
            return
        for item_id in self.selected_items:
            item_type = self.canvas.type(item_id)
            if item_type == "text":
                current_angle = float(
                    self.canvas.itemcget(item_id, "angle") or 0)
                self.canvas.itemconfig(item_id, angle=current_angle + angle)
                continue
            x1, y1, x2, y2 = self.canvas.coords(item_id)
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2
            rotated = [
                self._rotate_point(x1, y1, cx, cy, angle),
                self._rotate_point(x2, y2, cx, cy, angle),
            ]
            self.canvas.coords(
                item_id, rotated[0][0], rotated[0][1], rotated[1][0], rotated[1][1])

        for item_id in self.selected_items:
            self.apply_opacity(item_id)

    def select_items_in_region(self, x1, y1, x2, y2):
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
        items = [
            item_id for item_id in self.canvas.find_overlapping(x1, y1, x2, y2)
            if self.canvas.type(item_id) != "image"
        ]
        self.selected_items = items
        self._update_selection_visuals()

    def group_selection(self):
        if len(self.selected_items) < 2:
            return
        group_tag = f"group_{self.group_counter}"
        self.group_counter += 1
        self.groups[group_tag] = list(self.selected_items)
        for item_id in self.selected_items:
            self.canvas.addtag_withtag(group_tag, item_id)

    def ungroup_selection(self):
        for item_id in list(self.selected_items):
            for tag in list(self.canvas.gettags(item_id)):
                if tag.startswith("group_"):
                    self.canvas.dtag(item_id, tag)

    def add_background_image(self):
        path = filedialog.askopenfilename(
            filetypes=[("Imagens", "*.png *.jpg *.jpeg *.gif *.bmp"),
                       ("Todos os arquivos", "*.*")],
            title="Adicionar imagem de fundo",
        )
        if not path:
            return
        try:
            from PIL import Image, ImageTk

            width = max(1, self.canvas.winfo_width() or 1280)
            height = max(1, self.canvas.winfo_height() or 720)
            image = Image.open(path).resize((width, height))
            photo = ImageTk.PhotoImage(image)
            self.background_image = photo
        except Exception:
            try:
                photo = tk.PhotoImage(file=path)
                self.background_image = photo
            except Exception as exc:
                messagebox.showerror(
                    "Garami", f"Não foi possível carregar a imagem: {exc}")
                return
        self.canvas.delete("background")
        self.canvas.create_image(
            0, 0, image=self.background_image, anchor="nw", tags=("background",))
        self.canvas.tag_lower("background")

    def save_file(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("Arquivo Garami", "*.json"),
                       ("Todos os arquivos", "*.*")],
            title="Salvar projeto Garami",
        )
        if not path:
            return
        payload = []
        for item_id in self.canvas.find_all():
            item_type = self.canvas.type(item_id)
            if item_type == "line":
                payload.append({
                    "type": "line",
                    "coords": self.canvas.coords(item_id),
                    "fill": self.canvas.itemcget(item_id, "fill"),
                    "width": self._get_numeric_option(item_id, "width", self.brush_width.get()),
                })
            elif item_type in {"rectangle", "oval"}:
                payload.append({
                    "type": item_type,
                    "coords": self.canvas.coords(item_id),
                    "outline": self.canvas.itemcget(item_id, "outline"),
                    "fill": self.canvas.itemcget(item_id, "fill"),
                    "width": self._get_numeric_option(item_id, "width", self.brush_width.get()),
                })
            elif item_type == "text":
                payload.append({
                    "type": "text",
                    "coords": self.canvas.coords(item_id),
                    "text": self.canvas.itemcget(item_id, "text"),
                    "fill": self.canvas.itemcget(item_id, "fill"),
                    "font": self.canvas.itemcget(item_id, "font"),
                    "angle": self.canvas.itemcget(item_id, "angle"),
                })
        with Path(path).open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
        messagebox.showinfo("Garami", "Projeto salvo com sucesso.")

    def load_file(self):
        path = filedialog.askopenfilename(
            filetypes=[("Arquivo Garami", "*.json"),
                       ("Todos os arquivos", "*.*")],
            title="Abrir projeto Garami",
        )
        if not path:
            return
        with Path(path).open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        self.canvas.delete("all")
        self.undo_stack.clear()
        self.selected_items.clear()
        self._clear_selection_visuals()
        self._clear_selection_visuals()
        self.background_image = None
        for item in payload:
            item_id = self._create_item_from_payload(item)
            if item_id is not None:
                self.undo_stack.append(item_id)
        self._refresh_layers_panel()
        messagebox.showinfo("Garami", "Projeto carregado com sucesso.")

    def export_svg(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".svg",
            filetypes=[("SVG", "*.svg"), ("Todos os arquivos", "*.*")],
            title="Exportar SVG Garami",
        )
        if not path:
            return

        width = max(1, self.canvas.winfo_width())
        height = max(1, self.canvas.winfo_height())
        pieces = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">']
        for item_id in self.canvas.find_all():
            item_type = self.canvas.type(item_id)
            if item_type == "line":
                x1, y1, x2, y2 = self.canvas.coords(item_id)
                pieces.append(
                    f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{self.canvas.itemcget(item_id, "fill")}" stroke-width="{self.canvas.itemcget(item_id, "width")}" />'
                )
            elif item_type == "rectangle":
                x1, y1, x2, y2 = self.canvas.coords(item_id)
                pieces.append(
                    f'<rect x="{min(x1, x2)}" y="{min(y1, y2)}" width="{abs(x2 - x1)}" height="{abs(y2 - y1)}" fill="{self.canvas.itemcget(item_id, "fill")}" stroke="{self.canvas.itemcget(item_id, "outline")}" stroke-width="{self.canvas.itemcget(item_id, "width")}" />'
                )
            elif item_type == "oval":
                x1, y1, x2, y2 = self.canvas.coords(item_id)
                cx = (x1 + x2) / 2
                cy = (y1 + y2) / 2
                rx = abs(x2 - x1) / 2
                ry = abs(y2 - y1) / 2
                pieces.append(
                    f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{self.canvas.itemcget(item_id, "fill")}" stroke="{self.canvas.itemcget(item_id, "outline")}" stroke-width="{self.canvas.itemcget(item_id, "width")}" />'
                )
            elif item_type == "text":
                x, y = self.canvas.coords(item_id)
                pieces.append(
                    f'<text x="{x}" y="{y}" fill="{self.canvas.itemcget(item_id, "fill")}" font-family="Segoe UI" font-size="{self.canvas.itemcget(item_id, "font").split()[-2] if self.canvas.itemcget(item_id, "font") else 18}" transform="rotate({self.canvas.itemcget(item_id, "angle")}, {x}, {y})">{self.canvas.itemcget(item_id, "text")}</text>'
                )
        pieces.append("</svg>")
        Path(path).write_text("\n".join(pieces), encoding="utf-8")
        messagebox.showinfo("Garami", "Arquivo SVG exportado com sucesso.")

    def export_image(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"),
                       ("PostScript", "*.ps")],
            title="Exportar imagem Garami",
        )
        if not path:
            return

        ext = Path(path).suffix.lower()
        try:
            from PIL import Image

            ps = self.canvas.postscript(colormode="color", width=self.canvas.winfo_width(
            ), height=self.canvas.winfo_height())
            image = Image.open(io.BytesIO(ps.encode("utf-8")))
            image.save(path)
            messagebox.showinfo("Garami", "Imagem exportada com sucesso.")
            return
        except Exception:
            fallback_path = str(Path(path).with_suffix(".ps"))
            ps = self.canvas.postscript(colormode="color", width=self.canvas.winfo_width(
            ), height=self.canvas.winfo_height())
            Path(fallback_path).write_text(ps, encoding="utf-8")
            if ext != ".ps":
                messagebox.showwarning(
                    "Garami", "Exportação PNG não disponível no ambiente atual. O arquivo foi salvo como PostScript.")
            else:
                messagebox.showinfo(
                    "Garami", "Imagem exportada como PostScript.")


if __name__ == "__main__":
    app = GaramiEditor()
    app.mainloop()
