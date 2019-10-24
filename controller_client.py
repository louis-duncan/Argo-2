import _thread
import time
from _classes import *
from _globals import *
import wx
import wx.lib.scrolledpanel as scrolled


OBJECT_BUTTON_ID = 9876


class Manager(wx.Frame):
    def __init__(self, parent, frame_id, title):
        super().__init__(parent,
                         frame_id,
                         title,
                         style=wx.DEFAULT_FRAME_STYLE,  # & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX),
                         )

        self.selected_object = None
        self.entities = []

        self.default_button_size = (400, 60)
        self.object_button_size = ((400 - wx.SystemSettings.GetMetric(wx.SYS_VSCROLL_X)) - 4, 60)

        self.com = create_client_connection(SERVER_ADDR)

        self.canvas = wx.Panel(self)
        self.canvas.SetBackgroundColour(WHITE)
        self.canvas.SetMinSize((800, 800))

        self.controls_panel = wx.Panel(self, size=(400, -1))

        self.objects_panel = scrolled.ScrolledPanel(
            self.controls_panel,
            size=(self.controls_panel.GetSize()[0], -1),
            style=wx.BORDER_SUNKEN
        )
        self.objects_panel.SetBackgroundColour(LIGHT_GREY)

        objects_sizer = wx.BoxSizer(wx.VERTICAL)

        objects_sizer.Add(wx.Button(self.objects_panel, OBJECT_BUTTON_ID, label="A thing", size=self.object_button_size))

        scroll_bar_sizer = wx.BoxSizer(wx.HORIZONTAL)
        scroll_bar_sizer.Add(objects_sizer, 1, wx.EXPAND)

        self.objects_panel.SetSizer(scroll_bar_sizer)
        self.objects_panel.SetAutoLayout(1)
        self.objects_panel.SetupScrolling(False, True)

        controls_sizer = wx.BoxSizer(wx.VERTICAL)
        controls_sizer.AddSpacer(100)
        controls_sizer.Add(self.objects_panel, 1, wx.EXPAND)
        controls_sizer.AddSpacer(200)

        self.controls_panel.SetSizer(controls_sizer)

        # Create a sizer to manage the Canvas and control panel.
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        main_sizer.Add(self.canvas, 1, wx.EXPAND)
        main_sizer.Add(self.controls_panel, 0, wx.EXPAND)

        self.SetSizerAndFit(main_sizer)

        self.Bind(wx.EVT_BUTTON, self.button_press)
        self.Bind(wx.EVT_SIZING, self.on_resize)
        self.Bind(wx.EVT_CLOSE, self.on_close)

        self.Show(True)

        #self.get_state_update()

    def on_close(self, e=None):
        self.Destroy()

    def on_resize(self, e=None):
        if e is not None:
            e.Skip()

    def button_press(self, e=None):
        if e is None:
            return
        if e.EventObject.GetId() == OBJECT_BUTTON_ID:
            self.select_object(e.EventObject.GetLabel())
        else:
            pass

    def select_object(self, name):
        for entity in self.entities:
            if entity.name == name:
                self.selected_object = entity
                break
        else:
            self.selected_object = None

    def get_state_update(self):
        self.com.object_send({"action": "update_request"})
        resp = self.com.object_recv()
        if type(resp) is not None and "entities" in resp.keys():
            self.entities = resp["entities"]
        else:
            raise ConnectionError

    def send_action(self):
        pass


def scale_bitmap(bitmap, width, height):
    image = bitmap.ConvertToImage()
    image = image.Scale(width, height, wx.IMAGE_QUALITY_HIGH)
    result = wx.Bitmap(image)
    return result


app = wx.App(False)
main_frame = Manager(None, wx.ID_ANY, "Argo 2 - Electric Boogaloo")
app.MainLoop()
