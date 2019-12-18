import _thread
import os
import time
from _classes import *
from _globals import *
import wx
import wx.adv
import wx.lib.scrolledpanel as scrolled


OBJECT_BUTTON_ID = 98765


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

        self.con = create_client_connection(SERVER_ADDR)

        self.events_to_send = queue.SimpleQueue()

        self.default_button_size = (400, 60)

        main_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.map_bg_panel = wx.Panel(
            self,
            size=(600, 600)
        )
        self.map_bg_panel.SetBackgroundColour(BLUE)

        self.map_panel = wx.Panel(
            self.map_bg_panel,
            size=(-1, -1)
        )
        self.map_panel.SetBackgroundColour(BLACK)

        controls_sizer = wx.BoxSizer(wx.VERTICAL)

        control_panel_width = 300

        self.control_panel = wx.Panel(
            self,
            size=(control_panel_width, -1)
        )

        self.entity_buttons_window = scrolled.ScrolledPanel(
            self.control_panel,
            size=(control_panel_width, -1),
            style=wx.TAB_TRAVERSAL | wx.SUNKEN_BORDER,
        )

        self.entity_buttons_window.SetBackgroundColour((255, 255, 255))
        self.entity_buttons_sizer = wx.BoxSizer(wx.VERTICAL)
        self.entity_buttons_window.SetSizer(self.entity_buttons_sizer)
        self.entity_buttons_window.SetAutoLayout(True)
        self.entity_buttons_window.SetupScrolling(False, True)

        controls_sizer.Add(
            self.entity_buttons_window,
            1,
            wx.EXPAND
        )

        main_sizer.Add(
            self.map_bg_panel,
            1,
            wx.EXPAND
        )

        self.control_panel.SetSizerAndFit(controls_sizer)

        main_sizer.Add(
            self.control_panel,
            0,
            wx.EXPAND
        )

        self.SetSizerAndFit(main_sizer)

        self.timer = wx.Timer(self)
        self.timer.Start(100)

        self.Bind(wx.EVT_BUTTON, self.button_press)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(wx.EVT_TIMER, self.timer_handler)
        #self.Bind(wx.EVT_SIZE, self.on_resize)

        self.Show(True)

    def timer_handler(self, e=None):
        if self.con is None:
            self.SetTitle(self._title + " - No Connection")
        else:
            try:
                self.entities = self.con.get_update()
            except ConnectionError:
                self.con = None
        self.on_resize()

    def button_press(self, e=None):
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

    def __del__(self):
        self.timer.Stop()


def scale_bitmap(bitmap, width, height):
    image = bitmap.ConvertToImage()
    image = image.Scale(width, height, wx.IMAGE_QUALITY_HIGH)
    result = wx.Bitmap(image)
    return result


app = wx.App(False)
main_frame = Manager(None, wx.ID_ANY, "Argo 2 - Electric Boogaloo")
app.MainLoop()
