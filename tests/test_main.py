import pytest

from main import GaramiEditor


class FakeCanvas:
    def __init__(self):
        # items: id -> dict {type, coords, opts, tags, state}
        self.items = {}

    def add_item(self, item_id, item_type, coords, opts=None, tags=None):
        self.items[item_id] = {
            "type": item_type,
            "coords": list(coords),
            "opts": opts or {},
            "tags": set(tags or []),
        }

    def type(self, item_id):
        return self.items[item_id]["type"]

    def coords(self, item_id, *args):
        if args:
            # setter
            self.items[item_id]["coords"] = list(args)
            return
        return list(self.items[item_id]["coords"])

    def itemcget(self, item_id, option):
        return self.items[item_id]["opts"].get(option, "")

    def itemconfig(self, item_id, **kw):
        self.items[item_id]["opts"].update(kw)

    def gettags(self, item_id):
        return tuple(self.items[item_id]["tags"])

    def find_overlapping(self, x1, y1, x2, y2):
        res = []
        for item_id, v in self.items.items():
            c = v["coords"]
            if len(c) >= 4:
                ix1, iy1, ix2, iy2 = min(c[0], c[2]), min(
                    c[1], c[3]), max(c[0], c[2]), max(c[1], c[3])
                if not (ix2 < x1 or ix1 > x2 or iy2 < y1 or iy1 > y2):
                    res.append(item_id)
        return res

    def find_closest(self, x, y):
        # very naive: return first item
        for item_id in self.items:
            return (item_id,)
        raise IndexError

    def find_all(self):
        return list(self.items.keys())


def make_editor():
    editor = object.__new__(GaramiEditor)
    editor.canvas = FakeCanvas()
    editor.selected_items = []
    editor.resize_start_state = {}
    editor.resize_start_bbox = None
    editor.brush_width = 3
    editor.font_size = 18
    editor.layer_visibility = {}
    editor.layer_locked = {}
    editor.layer_names = {}
    editor.snap_to_grid = False
    editor.grid_size = 20
    return editor


def test_get_numeric_option_int_and_float():
    e = make_editor()
    e.canvas.add_item(1, "line", [0, 0, 10, 10], opts={"width": "3.0"})
    assert e._get_numeric_option(1, "width", 1) == 3
    e.canvas.items[1]["opts"]["width"] = "4.5"
    assert e._get_numeric_option(1, "width", 1) == 4.5
    e.canvas.items[1]["opts"]["width"] = "abc"
    assert e._get_numeric_option(1, "width", 1) == "abc"


def test_offset_payload():
    e = make_editor()
    payload = {"coords": [10, 20, 30, 40]}
    out = e._offset_payload(payload, 5, 7)
    assert out["coords"] == [15, 27, 35, 47]


def test_serialize_item_various_types():
    e = make_editor()
    e.canvas.add_item(1, "line", [0, 0, 10, 10], opts={
                      "fill": "#000", "width": "2"})
    e.canvas.add_item(2, "rectangle", [1, 2, 3, 4], opts={
                      "outline": "#111", "fill": "#222", "width": "5"})
    e.canvas.add_item(3, "text", [5, 6], opts={
                      "text": "hi", "fill": "#333", "font": "Segoe UI 12 normal", "angle": "0"})

    p1 = e._serialize_item(1)
    assert p1["type"] == "line"
    assert p1["width"] == 2

    p2 = e._serialize_item(2)
    assert p2["type"] == "rectangle"
    assert p2["width"] == 5

    p3 = e._serialize_item(3)
    assert p3["type"] == "text"
    assert p3["text"] == "hi"


def test_capture_and_apply_resize_rectangle():
    e = make_editor()
    # rectangle with coords x1=10,y1=10,x2=30,y2=30
    e.canvas.add_item(1, "rectangle", [10, 10, 30, 30], opts={
                      "fill": "#fff", "outline": "#000", "width": "2"})
    e.selected_items = [1]
    e._capture_resize_state()
    assert 1 in e.resize_start_state
    old_coords = e.resize_start_state[1]["coords"].copy()
    # apply resize: move bbox from (10,10,30,30) to (10,10,50,50) -> scale x2,y2
    e.resize_start_bbox = (10, 10, 30, 30)
    e._apply_resize((10, 10, 50, 50))
    new_coords = e.canvas.coords(1)
    assert new_coords[2] > old_coords[2]
