import _thread
import math
import os
import time
from _classes import *
from _globals import *
import wx
import wx.adv
import wx.lib.scrolledpanel as scrolled


class EntityButton(wx.Button):
    def __init__(self, *args, entity_id, **kwargs):
        super().__init__(*args, **kwargs)
        self.entity_id = entity_id


class MapPanel(wx.Window):
    def __init__(self, parent, size):
        self.parent = parent
        super().__init__(parent=parent, size=size)
        self.Bind(wx.EVT_PAINT, self.re_draw)
        self.background = wx.StaticBitmap(
            self,
            bitmap=load_bitmap(GRID_SPRITE),
            pos=(0, 0),
            size=(-1, -1)
        )
        self.bitmaps = {}
        self.states = {}
        self.previous_cell_size = 0

    def re_draw(self, event=None):
        size = self.GetSize()
        self.background.SetSize(size)
        self.background.SetBitmap(
            scale_bitmap(
                load_bitmap(GRID_SPRITE),
                size[0],
                size[1]
            )
        )
        self.refresh_bitmaps()

    def refresh_bitmaps(self):
        cell_size = round(self.background.GetSize()[0] / 21, 5)
        entities = self.parent.GetParent().entities

        done = []

        for e in entities:
            e: Entity
            done.append(e.entity_id)
            pos = ((cell_size * (e.pos[0] + 1)) + 3, (cell_size * (e.pos[1] + 1)) + 3)
            if e.entity_id in self.bitmaps:
                if cell_size != self.previous_cell_size or e.facing != self.states[e.entity_id]["facing"] or list(e.pos) != self.states[e.entity_id]["pos"]:
                    bmp: wx.StaticBitmap = self.bitmaps[e.entity_id]
                    bmp.SetBitmap(
                        scale_bitmap(
                            load_bitmap(get_sprite_path(
                                e.type_name.lower(),
                                e.colour.lower()
                                )
                            ),
                            cell_size,
                            cell_size,
                            e.facing
                        )
                    )
                    bmp.SetPosition(pos)
                    bmp.SetSize((cell_size - 3, cell_size - 3))
                    self.states[e.entity_id] = {
                        "facing": e.facing,
                        "pos": list(e.pos)
                    }

            else:
                self.bitmaps[e.entity_id] = wx.StaticBitmap(
                    self.background,
                    bitmap=scale_bitmap(
                        load_bitmap(get_sprite_path(
                            e.type_name.lower(),
                            e.colour.lower()
                        )
                        ),
                        cell_size,
                        cell_size,
                        e.facing
                    ),
                    pos=pos,
                    size=(cell_size - 3, cell_size - 3)
                )
                self.states[e.entity_id] = {
                    "facing": e.facing,
                    "pos": list(e.pos)
                }

            if not (type(e) in (Ship, Station)):
                bmp: wx.StaticBitmap = self.bitmaps[e.entity_id]
                if self.parent.GetParent().is_ship_at_pos(e.pos):
                    if bmp.IsShown():
                        bmp.Hide()
                else:
                    if not bmp.IsShown():
                        bmp.Show()

        for b in list(self.bitmaps.keys()):
            if b not in done:
                p = self.bitmaps.pop(b)
                p.Destroy()
                p = self.states.pop(b)

        self.previous_cell_size = cell_size


class Manager(wx.Frame):
    def __init__(self, parent, frame_id, title):
        super().__init__(parent,
                         frame_id,
                         title,
                         style=wx.DEFAULT_FRAME_STYLE,  # & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX),
                         )

        self._title = title

        self.running = True

        self.selected_object = None
        self.entities = []
        self.entity_buttons = []

        self.SetBackgroundColour((255, 255, 255))

        self.con = create_client_connection(SERVER_ADDR)

        self.events_to_send = queue.SimpleQueue()

        self.default_button_size = (400, 60)

        main_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.map_bg_panel = wx.Panel(
            self,
            size=(600, 600)
        )
        self.map_bg_panel.SetBackgroundColour(BLACK)

        self.map_panel = MapPanel(
            self.map_bg_panel,
            size=(-1, -1)
        )
        self.map_panel.SetBackgroundColour(BLACK)

        button_panel_width = 250
        control_panel_width = 250

        button_height = 40

        # Selectors
        selectors_panel = wx.Panel(self)
        selectors_sizer = wx.BoxSizer(wx.VERTICAL)

        check_box_sizer = wx.GridBagSizer(5, 5)
        self.show_ships = wx.CheckBox(
            selectors_panel,
            label="Ships"
        )
        self.show_ships.SetValue(True)
        check_box_sizer.Add(
            self.show_ships,
            pos=(0, 0)
        )
        self.show_stations = wx.CheckBox(
            selectors_panel,
            label="Stations"
        )
        check_box_sizer.Add(
            self.show_stations,
            pos=(0, 1)
        )
        self.show_trails = wx.CheckBox(
            selectors_panel,
            label="Trails"
        )
        check_box_sizer.Add(
            self.show_trails,
            pos=(1, 0)
        )
        self.show_debris = wx.CheckBox(
            selectors_panel,
            label="Debris"
        )
        check_box_sizer.Add(
            self.show_debris,
            pos=(1, 1)
        )
        check_box_sizer.Add(
            wx.Button(
                selectors_panel,
                ID_ALL,
                label="All"
            ),
            pos=(2, 0)
        )
        check_box_sizer.Add(
            wx.Button(
                selectors_panel,
                ID_NONE,
                label="None"
            ),
            pos=(2, 1)
        )

        selectors_sizer.Add(
            check_box_sizer,
            0,
            wx.EXPAND | wx.ALL,
            5
        )

        self.entity_buttons_window = scrolled.ScrolledPanel(
            selectors_panel,
            size=(button_panel_width, -1),
            style=wx.TAB_TRAVERSAL | wx.SUNKEN_BORDER,
        )
        self.entity_buttons_window.SetBackgroundColour((255, 255, 255))
        self.entity_buttons_sizer = wx.BoxSizer(wx.VERTICAL)
        self.entity_buttons_window.SetSizer(self.entity_buttons_sizer)
        self.entity_buttons_window.SetAutoLayout(True)
        self.entity_buttons_window.SetupScrolling(False, True)

        selectors_sizer.Add(
            self.entity_buttons_window,
            1,
            wx.EXPAND
        )

        selectors_sizer.Add(
            wx.StaticText(
                selectors_panel,
                label="Selected:"
            ),
            0,
            wx.EXPAND | wx.ALL,
            3
        )

        self.selected_icon = wx.StaticBitmap(
            selectors_panel,
            size=(40, 40)
        )
        selectors_sizer.Add(
            self.selected_icon,
            0,
            wx.RESERVE_SPACE_EVEN_IF_HIDDEN | wx.ALL,
            3
        )
        create_button = wx.Button(
            selectors_panel,
            label="Create Entity",
            size=(-1, button_height)
        )
        create_button.SetBackgroundColour((0, 200, 0))
        create_button.SetForegroundColour((255, 255, 255))
        selectors_sizer.Add(
            create_button,
            0,
            wx.EXPAND
        )
        selectors_panel.SetSizer(selectors_sizer)

        # Controls
        controls_sizer = wx.BoxSizer(wx.VERTICAL)
        self.control_panel = wx.Panel(
            self,
            size=(control_panel_width, -1)
        )

        up_button = wx.Button(self.control_panel, ID_UP, size=(control_panel_width / 3, button_height), label="˄")
        left_button = wx.Button(self.control_panel, ID_LEFT, size=(control_panel_width / 3, button_height), label="˂")
        right_button = wx.Button(self.control_panel, ID_RIGHT, size=(control_panel_width / 3, button_height), label="˃")
        down_button = wx.Button(self.control_panel, ID_DOWN, size=(control_panel_width / 3, button_height), label="˅")
        delete_button = wx.Button(self.control_panel, ID_DELETE, size=(-1, button_height), label="Delete")
        delete_button.SetBackgroundColour((220, 0, 0))
        delete_button.SetForegroundColour((255, 255, 255))

        arrows_sizer = wx.GridBagSizer()
        arrows_sizer.Add(
            up_button,
            pos=(0, 1),
            flag=wx.EXPAND
        )
        arrows_sizer.Add(
            right_button,
            pos=(1, 2),
            flag=wx.EXPAND
        )
        arrows_sizer.Add(
            down_button,
            pos=(1, 1),
            flag=wx.EXPAND
        )
        arrows_sizer.Add(
            left_button,
            pos=(1, 0),
            flag=wx.EXPAND
        )
        arrows_sizer.AddGrowableCol(0, 1)
        arrows_sizer.AddGrowableCol(1, 1)
        arrows_sizer.AddGrowableCol(2, 1)

        controls_sizer.AddStretchSpacer(1)
        controls_sizer.Add(
            arrows_sizer,
            0,
            wx.EXPAND
        )
        controls_sizer.AddSpacer(5)
        controls_sizer.Add(
            delete_button,
            0,
            wx.EXPAND
        )

        # End Controls

        self.control_panel.Disable()

        self.control_panel.SetSizer(controls_sizer)
        controls_sizer.Layout()

        main_sizer.Add(
            self.map_bg_panel,
            1,
            wx.EXPAND
        )
        main_sizer.Add(
            selectors_panel,
            0,
            wx.EXPAND
        )
        main_sizer.Add(
            self.control_panel,
            0,
            wx.EXPAND
        )

        self.SetSizerAndFit(main_sizer)

        self.timer = wx.Timer(self)
        self.timer.Start(100)

        self.Bind(wx.EVT_CHAR_HOOK, self.on_key)
        self.Bind(wx.EVT_BUTTON, self.button_press)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(wx.EVT_TIMER, self.timer_handler)
        self.map_panel.background.Bind(wx.EVT_LEFT_UP, self.map_click)

        self.Show(True)

    def map_click(self, e=None):
        e: wx.MouseEvent
        print("Click")
        print(e.GetPosition())

    def timer_handler(self, e=None):
        if self.con is None:
            self.SetTitle(self._title + " - No Connection")
        else:
            try:
                old = list(self.entities)
                self.entities = self.con.get_update()["entities"]
                if len(self.entities) != len(old):
                    print(self.entities)
            except ConnectionError:
                self.con = None
        self.on_resize()
        self.update_entity_buttons()
        self.map_panel.refresh_bitmaps()
        if self.selected_object is not None and not (self.selected_object.entity_id in [e.entity_id for e in self.entities]):
            self.deselect_object()

    def update_entity_buttons(self):
        current_ids = [e.entity_id for e in self.entities]
        flags = [False] * len(current_ids)
        to_go = []
        for b in self.entity_buttons:
            b: EntityButton
            if b.entity_id in current_ids:
                i = current_ids.index(b.entity_id)
                flags[i] = True
            else:
                to_go.append(b)
        for b in to_go:
            b.Destroy()
            self.entity_buttons.remove(b)

        for i, e in enumerate(self.entities):
            if not flags[i]:
                print("New!")
                new = EntityButton(
                    self.entity_buttons_window,
                    label=e.name,
                    entity_id=e.entity_id,
                    size=(-1, 40)
                )
                bmp = load_bitmap(
                    get_sprite_path(
                        object_type=e.type_name.lower(),
                        colour=e.colour.lower()
                    )
                )
                bmp = scale_bitmap(
                    bmp,
                    40,
                    40
                )
                new.SetBitmap(bmp)
                self.entity_buttons_sizer.Add(
                    new,
                    0,
                    wx.EXPAND
                )
                self.entity_buttons.append(new)
        for b in self.entity_buttons:
            e_type = type(self.get_entity(b.entity_id))
            if e_type is Ship and self.show_ships.GetValue():
                b.Show()
            elif e_type is Station and self.show_stations.GetValue():
                b.Show()
            elif e_type is Trail and self.show_trails.GetValue():
                b.Show()
            elif e_type is Debris and self.show_debris.GetValue():
                b.Show()
            else:
                b.Hide()
        self.entity_buttons_sizer.Layout()
        self.Layout()

    def get_entity(self, entity_id):
        for e in self.entities:
            if e.entity_id == entity_id:
                return e

    def button_press(self, e: wx.Event):
        button_id = e.GetEventObject().GetId()

        if button_id == ID_UP:
            self.move_object(0)
        elif button_id == ID_RIGHT:
            self.move_object(1)
        elif button_id == ID_DOWN:
            self.move_object(2)
        elif button_id == ID_LEFT:
            self.move_object(3)
        elif button_id == ID_ALL:
            self.set_check_boxes(True)
        elif button_id == ID_NONE:
            self.set_check_boxes(False)
        else:
            if hasattr(e.GetEventObject(), "entity_id"):
                self.select_object(e.GetEventObject().entity_id)

    def set_check_boxes(self, state):
        self.show_ships.SetValue(state)
        self.show_stations.SetValue(state)
        self.show_trails.SetValue(state)
        self.show_debris.SetValue(state)

    def select_object(self, target):
        if self.selected_object is not None and self.selected_object.entity_id == target:
            self.deselect_object()
        else:
            for e in self.entities:
                if e.entity_id == target:
                    self.selected_object = e
                    self.selected_icon.SetBitmap(
                        scale_bitmap(
                            load_bitmap(get_sprite_path(e.type_name.lower(), e.colour.lower())),
                            self.selected_icon.GetSize()[0],
                            self.selected_icon.GetSize()[1]
                        )
                    )
                    self.selected_icon.Show()
                    self.control_panel.Enable()
                    break

    def deselect_object(self):
        self.selected_object = None
        self.selected_icon.Hide()
        self.control_panel.Disable()

    def on_close(self, e=None):
        self.running = False
        self.timer.Stop()
        self.Destroy()

    def on_resize(self, e=None):
        wh = self.map_bg_panel.GetSize()
        s = min(wh)
        self.map_panel.SetSize((s, s))
        self.map_panel.SetPosition((int((wh[0] - s) / 2), int((wh[1] - s) / 2)))
        if e is not None:
            e.Skip()

    def on_key(self, e):
        key_code = e.GetKeyCode()
        handled = True
        if key_code == wx.WXK_UP:
            self.move_object(0)
        elif key_code == wx.WXK_RIGHT:
            self.move_object(1)
        elif key_code == wx.WXK_DOWN:
            self.move_object(2)
        elif key_code == wx.WXK_LEFT:
            self.move_object(3)
        elif key_code == wx.WXK_DELETE:
            self.delete_entity()
        elif key_code == ord("Z") and wx.GetKeyState(wx.WXK_CONTROL):
            self.undo()
        else:
            handled = False
        if not handled:
            e.Skip()

    def move_object(self, direction):
        print("Move")
        if self.selected_object is None:
            return

        if direction in [0, 2]:
            action = "move"
            if direction == 0:
                v = FORWARD
            else:
                v = BACKWARD
        else:
            action = "turn"
            if direction == 1:
                v = RIGHT
            else:
                v = LEFT

        self.con.send_update(
            action=action,
            value={
                "entity_id": self.selected_object.entity_id,
                "direction": v
            }
        )

    def delete_entity(self):
        if self.selected_object is None:
            return
        self.con.send_update(
            action="destroy",
            value={
                "entity_id": self.selected_object.entity_id
            }
        )

    def undo(self):
        print("Undo")
        if self.selected_object is None:
            return
        self.con.send_update(
            action="undo",
            value={
                "entity_id": self.selected_object.entity,
            }
        )

    def is_ship_at_pos(self, pos):
        pos = tuple(pos)
        for e in self.entities:
            if type(e) is Ship and tuple(e.pos) == pos:
                return True
        return False

    def __del__(self):
        self.timer.Stop()



def load_bitmap(path):
    image = wx.Image(path, type=wx.BITMAP_TYPE_ANY)
    return wx.Bitmap(image)


def scale_bitmap(bitmap, width, height, rotation=0):
    image = bitmap.ConvertToImage()
    assert width > 0 and height > 0
    image = image.Scale(width, height, wx.IMAGE_QUALITY_HIGH)
    new_w = max([width / 2, 1])
    new_h = max([height / 2, 1])
    image = image.Rotate(
        angle=math.radians(rotation * -45),
        rotationCentre=(
            new_w,
            new_h
        )
    )
    result = wx.Bitmap(image)
    return result


app = wx.App(False)
main_frame = Manager(None, wx.ID_ANY, "Argo 2 - Electric Boogaloo")
app.MainLoop()
