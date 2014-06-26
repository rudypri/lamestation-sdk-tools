#!/usr/bin/python

import wx
import Color, Dialog
import logging
from wx.lib.pubsub import Publisher as pub

import DrawWindow
import Bitmap

import EventHandler

BITMAP_MAXSIZE = 256
STYLE = 'plain'

RECT = 32


logging.basicConfig(level=logging.INFO)

class ImageTile(wx.Panel):

    def __init__(self, parent, size, scale=1, style=None):
        wx.Panel.__init__(self, parent, 
                size=size, style=wx.TAB_TRAVERSAL|wx.NO_BORDER)

        self.scale = scale
        self.size = size
        self.bmp = Bitmap.New(size[0],size[1])

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        pub.subscribe(self.UpdateBitmap,"UpdateBitmap")

    def UpdateBitmap(self, message):
        self.bmp = message.data
        self.SetSize((self.bmp.GetWidth()*self.scale,self.bmp.GetWidth()*self.scale))
        self.OnPaint(None)

    def OnPaint(self, event):
        dc = wx.ClientDC(self)
        dc.DrawBitmap(Bitmap.Scale(self.bmp,self.bmp.GetWidth()*self.scale,self.bmp.GetHeight()*self.scale), 0, 0, True)

    def OnMouseMove(self, event):
        self.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))


class ColorTile(wx.Panel):

    def __init__(self, parent, size, color, style=wx.TAB_TRAVERSAL|wx.NO_BORDER):
        wx.Panel.__init__(self, parent, size=size, style=style)

        self.size = self.GetSize()
        self.color = color
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        dc.SetBrush(wx.Brush(self.color))
        dc.SetPen(wx.Pen(self.color))
        print self.size
        dc.DrawRectangle(0, 0, self.size[0],self.size[1])

    def OnLeftDown(self, event):
        Color.Change(self.color)
        pub.sendMessage("COLOR")

class ChosenColor(ColorTile):

    def __init__(self, parent, size, color, style=wx.TAB_TRAVERSAL|wx.NO_BORDER):
        ColorTile.__init__(self, parent, size=size, color=color, style=style)

        pub.subscribe(self.SetColor, "COLOR")

    def SetColor(self, message):
        self.color = Color.COLOR
        self.OnPaint(None)


class ColorPicker(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, 
                size=(RECT*2,RECT*len(Color.color[STYLE]) ), style=wx.SUNKEN_BORDER)

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)

    def OnPaint(self, event):
        dc = wx.PaintDC(self)

        inc = 0
        for c in range(0,4):
            dc.SetBrush(wx.Brush(Color.color[STYLE][c]))
            dc.SetPen(wx.Pen(Color.color[STYLE][c]))
            dc.DrawRectangle(0, RECT*inc, RECT*2, RECT)

            inc += 1

    def OnLeftDown(self, event):
        self.x, self.y = event.GetPosition()
        self.x = self.x/RECT
        self.y = self.y/RECT
        Color.Change(Color.color[STYLE][self.y])
        pub.sendMessage("COLOR")
        logging.info("ColorPicker: clicked! %s %s %s %s" % (self.x, self.y, Color.color[STYLE][self.y], Color.COLOR))


class SideBar(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        cp1 = ColorPicker(self)
        cc = ChosenColor(self,(50,50),'#77FF00')
        tt = ImageTile(self,size=(100,100),scale=4)


        vbox = wx.FlexGridSizer(rows=3,cols=1, hgap=5, vgap=5)
        vbox.Add(cc, 0, wx.ALL|wx.ALIGN_CENTER)
        vbox.Add(cp1, 0, wx.ALL|wx.ALIGN_CENTER)
        vbox.Add(tt, 0, wx.ALL|wx.ALIGN_CENTER)

        hbox = wx.BoxSizer(wx.VERTICAL)
        hbox.Add(vbox, 0, wx.ALL|wx.ALIGN_CENTER, 0)

        self.SetSizer(hbox)


class LSPaint(wx.Frame):
    scale = 4
    scales = ['1x','2x','4x','8x','16x']
    width = 32
    height = 32

    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, size=(600,600))


        self.evt = EventHandler.EventHandler(self)
        self.toolbar = self.ToolBar()
        self.SetMenuBar(self.MenuBar())
        self.menu = self.GetMenuBar()

        panel = wx.ScrolledWindow(self)
        panel.SetScrollbars(1,1,-1,-1)
        hbox = wx.BoxSizer(wx.HORIZONTAL)

        self.draw = DrawWindow.DrawWindow(panel)
        hbox.Add(self.draw, 1, wx.ALL|wx.ALIGN_CENTER, 0)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(hbox, 1, wx.ALL|wx.ALIGN_CENTER, 0)


        panel.SetSizer(vbox)

        hboxm = wx.BoxSizer(wx.HORIZONTAL)
        hboxm.Add(SideBar(self),0,wx.ALL,10)
        hboxm.Add(panel,1,wx.EXPAND,0)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(hboxm,1, wx.EXPAND, 0)


        wx.EVT_TOOL(self.toolbar, wx.ID_UNDO, self.evt.OnUndo)
        wx.EVT_TOOL(self.toolbar, wx.ID_REDO, self.evt.OnRedo)
        wx.EVT_MENU(self,   wx.ID_NEW, self.evt.OnNew)
        wx.EVT_MENU(self,   wx.ID_EXIT, self.evt.OnQuit)
#        wx.EVT_MENU(self, wx.ID_OPEN, self.evt.OnBrowse)
#        self.Bind(wx.EVT_MENU, self.evt.OnExport, exp)
#        wx.EVT_MENU(self, wx.ID_ABOUT, self.evt.OnAbout)


        self.SetSizer(vbox)
        self.Show(True)


    def FileMenu(self):
        menu = wx.Menu()
        menu.Append(wx.ID_NEW, '&New', 'New Image')        
        menu.Append(wx.ID_OPEN, '&Open', 'Open Image')
        menu.Append(wx.ID_SAVE, '&Save', 'Save Image')
        menu.Append(wx.ID_SAVEAS, 'Save &As...', 'Save Image As...')
        menu.AppendSeparator()
        exp = menu.Append(wx.ID_ANY, '&Export', 'Export Image As Spin')
        menu.AppendSeparator()
        menu.Append(wx.ID_CLOSE, '&Close', 'Close image')
        menu.Append(wx.ID_EXIT, '&Quit\tCtrl+Q', 'Quit application')

        return menu

    def EditMenu(self):
        menu = wx.Menu()
        menu.Append(wx.ID_UNDO, '&Undo\tCtrl+Z', 'New Image')        
        menu.Append(wx.ID_REDO, '&Redo\tCtrl+Shift+Z', 'Open Image')
        menu.AppendSeparator()
        menu.Append(wx.ID_CUT, 'Cu&t', 'Cut To Clipoard')
        menu.Append(wx.ID_COPY, '&Copy', 'Copy To Clipboard')
        menu.Append(wx.ID_PASTE, 'Paste','Paste Into Image')

        return menu

    def HelpMenu(self):
        menu = wx.Menu()
        menu.Append(wx.ID_ABOUT, 'About', 'About LSPaint')

        return menu

    def MenuBar(self):
        menubar = wx.MenuBar()

        menubar.Append(self.FileMenu(), '&File')
        menubar.Append(self.EditMenu(), '&Edit')
        menubar.Append(self.HelpMenu(), '&Help')

        return menubar

    def ToolBar(self):
        self.toolbar = self.CreateToolBar()
        self.toolbar.AddLabelTool(wx.ID_NEW,'New',wx.ArtProvider.GetBitmap(wx.ART_NEW))
        self.toolbar.AddLabelTool(wx.ID_OPEN,'Open Image',wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN))
        self.toolbar.AddLabelTool(wx.ID_SAVE,'Save Image',wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE))
        self.toolbar.AddLabelTool(wx.ID_SAVEAS,'Save Image As...',wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE_AS))

        self.toolbar.AddSeparator()

        self.toolbar.AddLabelTool( wx.ID_UNDO, 'Undo', wx.ArtProvider_GetBitmap(wx.ART_UNDO))
        self.toolbar.AddLabelTool( wx.ID_REDO, 'Redo', wx.ArtProvider_GetBitmap(wx.ART_REDO))
        self.toolbar.EnableTool( wx.ID_UNDO, False )
        self.toolbar.EnableTool( wx.ID_REDO, False )
        self.toolbar.EnableTool( wx.ID_SAVE, False )


        self.toolbar.AddSeparator()

        self.zoom = wx.ComboBox(self.toolbar,-1,value='4x',choices=self.scales,size=(60,-1),style=wx.CB_DROPDOWN)
        self.toolbar.AddControl(self.zoom)

        self.toolbar.Realize()
        
        return self.toolbar


app = wx.App()
LSPaint(None, -1, 'LSPaint')
app.MainLoop()
