import _thread
import math
import os
import time
from _classes import *
from _globals import *
import wx
import wx.adv
import wx.lib.scrolledpanel as scrolled


OBJECT_BUTTON_ID = 98765
GRID_SIZE = 20


class EntityButton(wx.Button):
    def __init__(self, *args, entity_id, **kwargs):
        super().__init__(*args, **kwargs)
        self.entity_id = entity_id


class MapPanel(wx.Window):
    """Draw a line to a panel."""

    def __init__(self, parent, size):
        self.parent = parent
        super().__init__(parent=parent, size=size)
        self.Bind(wx.EVT_PAINT, self.re_draw)
        self.cell_size = 10
        self.bitmaps = {}

    def re_draw(self, event=None):
        self.Refresh(True)
        dc = wx.PaintDC(self)
        dc.Clear()

        size = [s - 2 for s in self.GetSize()]
        self.cell_size = size[0] / (GRID_SIZE + 1)

        dc.SetFont(
            wx.Font(
                int(self.cell_size * 0.4),
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_NORMAL,
                False
            )
        )
        dc.SetTextForeground(GREEN)
        dc.SetTextBackground(BLACK)

        dc.SetPen(wx.Pen(GREEN))
        for p in range(GRID_SIZE + 1):
            pos = self.cell_size * (p + 1)
            dc.DrawLine(pos, self.cell_size, pos, size[1])
            dc.DrawLine(self.cell_size, pos, size[0], pos)
            if p > 0:
                num_size = dc.GetTextExtent(str(p))
                letter_size = dc.GetTextExtent(chr(64 + p))
                dc.DrawText(
                    str(p),
                    (self.cell_size * p) + ((self.cell_size - num_size.GetWidth()) / 2),
                    (self.cell_size - num_size.GetHeight()) * 0.75,
                )
                dc.DrawText(
                    chr(64 + p),
                    (self.cell_size - letter_size.GetWidth()) * 0.75,
                    (self.cell_size * p) + (self.cell_size - letter_size.GetHeight()) / 2,
                )
        self.refresh_bitmaps()

    def refresh_bitmaps(self):
        entities = self.parent.GetParent().entities
        current_ids = [e.entity_id for e in entities]
        to_go = []
        for b in self.bitmaps:
            if b not in current_ids:
                to_go.append(b)
        for tg in to_go:
            self.bitmaps[tg].Destroy()
            self.bitmaps.pop(tg)
        for e in entities:
            e: Entity
            if e.entity_id not in self.bitmaps.keys():
                bmp = load_bitmap(get_sprite_path(e.type_name.lower(), e.colour.lower()))
                bmp = scale_bitmap(bmp, self.cell_size, self.cell_size, e.facing)
                self.bitmaps[e.entity_id] = {
                    "bmp": wx.StaticBitmap(
                        self,
                        bitmap=bmp,
                        pos=(
                            (self.cell_size * e.pos[0]) - ((bmp.GetWidth() - self.cell_size) / 2),
                            (self.cell_size * e.pos[1]) - ((bmp.GetHeight() - self.cell_size) / 2)
                        )
                    ),
                    "prior_direction": e.facing
                }
            else:
                if self.bitmaps[e.entity_id]["prior_direction"] != e.facing:
                    self.bitmaps[e.entity_id]["bmp"].SetBitmap(
                        scale_bitmap(
                            self.bitmaps[e.entity_id]["bmp"].GetBitmap(),
                            self.cell_size,
                            self.cell_size,
                            e.facing
                        )
                    )
                    self.bitmaps[e.entity_id]["prior_direction"] = e.facing
                self.bitmaps[e.entity_id]["bmp"].SetPosition(
                    (
                        (self.cell_size * e.pos[0]) - ((self.bitmaps[e.entity_id]["bmp"].GetBitmap().GetWidth() - self.cell_size) / 2),
                        (self.cell_size * e.pos[1]) - ((self.bitmaps[e.entity_id]["bmp"].GetBitmap().GetHeight() - self.cell_size) / 2)
                    )
                )


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

        control_panel_width = 300

        self.entity_buttons_window = scrolled.ScrolledPanel(
            self,
            size=(control_panel_width, -1),
            style=wx.TAB_TRAVERSAL | wx.SUNKEN_BORDER,
        )

        self.entity_buttons_window.SetBackgroundColour((255, 255, 255))
        self.entity_buttons_sizer = wx.BoxSizer(wx.VERTICAL)
        self.entity_buttons_window.SetSizer(self.entity_buttons_sizer)
        self.entity_buttons_window.SetAutoLayout(True)
        self.entity_buttons_window.SetupScrolling(False, True)

        controls_sizer = wx.BoxSizer(wx.VERTICAL)
        self.control_panel = wx.Panel(
            self,
            size=(control_panel_width, -1)
        )

        # Controls
        button_height = 40
        up_button = wx.Button(self.control_panel, ID_UP, size=(-1, button_height), label="˄")
        left_button = wx.Button(self.control_panel, ID_LEFT, size=(-1, button_height), label="˂")
        right_button = wx.Button(self.control_panel, ID_RIGHT, size=(-1, button_height), label="˃")
        down_button = wx.Button(self.control_panel, ID_DOWN, size=(-1, button_height), label="˅")
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
        arrows_sizer.Layout()
        # End Controls

        self.control_panel.Disable()

        self.control_panel.SetSizer(controls_sizer)

        main_sizer.Add(
            self.map_bg_panel,
            1,
            wx.EXPAND
        )
        main_sizer.Add(
            self.entity_buttons_window,
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

        self.Show(True)

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
        self.entity_buttons_sizer.Layout()
        self.Layout()

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
        else:
            pass

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
        print("Move", direction)
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
                "entity_id": self.selected_object.entity
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
        angle=math.radians(rotation * 45),
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
