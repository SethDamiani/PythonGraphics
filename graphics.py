import time
import os
import matplotlib.path as mpl_path
import numpy as np
from math import sqrt, pow


try:  # import as appropriate for 2.x vs. 3.x
    import tkinter as tk
except:
    import Tkinter as tk


##########################################################################
# Module Exceptions

class GraphicsError(Exception):
    """Generic error class for graphics module exceptions."""
    pass


OBJ_ALREADY_DRAWN = "Object currently drawn"
UNSUPPORTED_METHOD = "Object doesn't support operation"
BAD_OPTION = "Illegal option value"
DEAD_THREAD = "Graphics thread quit unexpectedly"

_root = tk.Tk()
_root.withdraw()
_update_lasttime = time.time()


def update(rate=None):
    global _update_lasttime
    if rate:
        now = time.time()
        pauseLength = 1 / rate - (now - _update_lasttime)
        if pauseLength > 0:
            time.sleep(pauseLength)
            _update_lasttime = now + pauseLength
        else:
            _update_lasttime = now
    _root.update()

############################################################################
# Graphics classes start here


class GraphWin(tk.Canvas):

    """A GraphWin is a top level window for displaying graphics."""

    def __init__(self, title="Graphics Window", width=200, height=200, autoflush=True):
        assert isinstance(title, str), "Title must be a string"
        master = tk.Toplevel(_root)
        master.protocol("WM_DELETE_WINDOW", self.close)
        tk.Canvas.__init__(self, master, width=width, height=height, highlightthickness=0, bd=0)
        self.master.title(title)
        self.pack()
        master.resizable(0, 0)
        self.foreground = "black"
        self.items = []
        self.mouseX1 = None
        self.mouseY1 = None
        self.mouseX2 = None
        self.mouseY2 = None
        self.bind("<Button-1>", self._onClick1)
        self.bind("<Button-2>", self._onClick2)
        self.bind_all("<Key>", self._onKey)
        self.height = height
        self.width = width
        self.autoflush = autoflush
        self._mouseCallback = None
        self._mouseCallback2 = None
        self.trans = None
        self.closed = False
        master.lift()
        self.lastKey = ""
        if autoflush:
            _root.update()

    def __repr__(self):
        if self.isClosed():
            return "<Closed GraphWin>"
        else:
            return "GraphWin('{}', {}, {})".format(self.master.title(), self.getWidth(), self.getHeight())

    def __str__(self):
        return repr(self)

    def __checkOpen(self):
        if self.closed:
            raise GraphicsError("window is closed")

    def _onKey(self, evnt):
        self.lastKey = evnt.keysym

    def setBackground(self, color):
        """Set background color of the window"""
        self.__checkOpen()
        self.config(bg=color)
        self.__autoflush()
        
    def setCoords(self, x1, y1, x2, y2):
        """Set coordinates of window to run from (x1,y1) in the
        lower-left corner to (x2,y2) in the upper-right corner."""
        self.trans = Transform(self.width, self.height, x1, y1, x2, y2)
        self.redraw()

    def close(self):
        """Close the window"""

        if self.closed:
            return
        self.closed = True
        self.master.destroy()
        self.__autoflush()

    def isClosed(self):
        return self.closed

    def isOpen(self):
        return not self.closed

    def __autoflush(self):
        if self.autoflush:
            _root.update()

    def plot(self, x, y, color="black"):
        """Set pixel (x,y) to the given color"""
        self.__checkOpen()
        xs, ys = self.toScreen(x, y)
        self.create_line(xs, ys, xs+1, ys, fill=color)
        self.__autoflush()
        
    def plotPixel(self, x, y, color="black"):
        """Set pixel raw (independent of window coordinates) pixel
        (x,y) to color"""
        self.__checkOpen()
        self.create_line(x, y, x+1, y, fill=color)
        self.__autoflush()
      
    def flush(self):
        """Update drawing to the window"""
        self.__checkOpen()
        self.update_idletasks()
        
    def getMouse(self, mouseButton=1):
        """Wait for mouse click and return Point object representing
        the click"""
        if mouseButton == 1:
            self.update()      # flush any prior clicks
            self.mouseX1 = None
            self.mouseY1 = None
            while self.mouseX1 is None or self.mouseY1 is None:
                self.update()
                if self.isClosed():
                    raise GraphicsError("getMouse in closed window")
                time.sleep(.1)  # give up thread
            x, y = self.toWorld(self.mouseX1, self.mouseY1)
            self.mouseX1 = None
            self.mouseY1 = None
            return Point(x, y)

        elif mouseButton == 2:
            self.update()  # flush any prior clicks
            self.mouseX2 = None
            self.mouseY2 = None
            while self.mouseX2 is None or self.mouseY2 is None:
                self.update()
                if self.isClosed():
                    raise GraphicsError("getMouse in closed window")
                time.sleep(.1)  # give up thread
            x, y = self.toWorld(self.mouseX2, self.mouseY2)
            self.mouseX2 = None
            self.mouseY2 = None
            return Point(x, y)

    def checkMouse(self, mouseButton=1):
        """Return last mouse click or None if mouse has
        not been clicked since last call"""
        if mouseButton == 1:
            if self.isClosed():
                raise GraphicsError("checkMouse in closed window")
            self.update()
            if self.mouseX1 is not None and self.mouseY1 is not None:
                x, y = self.toWorld(self.mouseX1, self.mouseY1)
                self.mouseX1 = None
                self.mouseY1 = None
                return Point(x, y)
            else:
                return None

        elif mouseButton == 2:
            if self.isClosed():
                raise GraphicsError("checkMouse in closed window")
            self.update()
            if self.mouseX2 is not None and self.mouseY2 is not None:
                x, y = self.toWorld(self.mouseX2, self.mouseY2)
                self.mouseX2 = None
                self.mouseY2 = None
                return Point(x, y)
            else:
                return None

    def checkMousePosition(self):
        x = self.master.winfo_pointerx()-self.master.winfo_rootx()
        y = self.master.winfo_pointery()-self.master.winfo_rooty()
        if 0 <= x <= self.width and 0 <= y <= self.height:
            return Point(x, y)
        else:
            return None

    def getKey(self):
        """Wait for user to press a key and return it as a string."""
        self.lastKey = ""
        while self.lastKey == "":
            self.update()
            if self.isClosed():
                raise GraphicsError("getKey in closed window")
            time.sleep(.1)  # give up thread

        key = self.lastKey
        self.lastKey = ""
        return key

    def checkKey(self):
        """Return last key pressed or None if no key pressed since last call"""
        if self.isClosed():
            raise GraphicsError("checkKey in closed window")
        self.update()
        key = self.lastKey
        self.lastKey = ""
        return key
            
    def getHeight(self):
        """Return the height of the window"""
        return self.height
        
    def getWidth(self):
        """Return the width of the window"""
        return self.width
    
    def toScreen(self, x, y):
        trans = self.trans
        if trans:
            return self.trans.screen(x, y)
        else:
            return x, y
                      
    def toWorld(self, x, y):
        trans = self.trans
        if trans:
            return self.trans.world(x, y)
        else:
            return x, y
        
    def setMouseHandler(self, func):
        self._mouseCallback = func

    def setMouseHandler2(self, func):
        self._mouseCallback = func
        
    def _onClick1(self, e):
        self.mouseX1 = e.x
        self.mouseY1 = e.y
        if self._mouseCallback:
            self._mouseCallback(Point(e.x, e.y))

    def _onClick2(self, e):
        self.mouseX2 = e.x
        self.mouseY2 = e.y
        if self._mouseCallback2:
            self._mouseCallback2(Point(e.x, e.y))

    def addItem(self, item):
        self.items.append(item)

    def delItem(self, item):
        self.items.remove(item)

    def redraw(self):
        for item in self.items[:]:
            item.undraw()
            item.draw(self)
        self.update()

    def containsPoint(self, p):
        if p is None:
            return
        x = p.getX()
        y = p.getY()
        return 0 <= x <= self.width and 0 <= y <= self.height
        
                      
class Transform:

    """Internal class for 2-D coordinate transformations"""
    
    def __init__(self, w, h, xlow, ylow, xhigh, yhigh):
        # w, h are width and height of window
        # (xlow,ylow) coordinates of lower-left [raw (0,h-1)]
        # (xhigh,yhigh) coordinates of upper-right [raw (w-1,0)]
        xspan = (xhigh-xlow)
        yspan = (yhigh-ylow)
        self.xbase = xlow
        self.ybase = yhigh
        self.xscale = xspan/float(w-1)
        self.yscale = yspan/float(h-1)
        
    def screen(self, x, y):
        # Returns x,y in screen (actually window) coordinates
        xs = (x-self.xbase) / self.xscale
        ys = (self.ybase-y) / self.yscale
        return int(xs+0.5), int(ys+0.5)
        
    def world(self, xs, ys):
        # Returns xs,ys in world coordinates
        x = xs*self.xscale + self.xbase
        y = self.ybase - ys*self.yscale
        return x, y


# Default values for various item configuration options. Only a subset of
#   keys may be present in the configuration dictionary for a given item
DEFAULT_CONFIG = {"fill": "",
                  "outline": "black",
                  "width": "1",
                  "arrow": "none",
                  "text": "",
                  "justify": "center",
                  "font": ("helvetica", 12, "normal")}


class GraphicsObject:

    """Generic base class for all of the drawable objects"""
    # A subclass of GraphicsObject should override _draw and
    #   and _move methods.
    
    def __init__(self, options):
        # options is a list of strings indicating which options are
        # legal for this object.
        
        # When an object is drawn, canvas is set to the GraphWin(canvas)
        #    object where it is drawn and id is the TK identifier of the
        #    drawn shape.
        self.canvas = None
        self.id = None

        # config is the dictionary of configuration options for the widget.
        config = {}
        for option in options:
            config[option] = DEFAULT_CONFIG[option]
        self.config = config
        
    def setFill(self, color):
        """Set interior color to color"""
        self._reconfig("fill", color)
        return self
        
    def setOutline(self, color):
        """Set outline color to color"""
        self._reconfig("outline", color)
        return self
        
    def setWidth(self, width):
        """Set line weight to width"""
        self._reconfig("width", width)
        return self

    def draw(self, graphwin):

        """Draw the object in graphwin, which should be a GraphWin
        object.  A GraphicsObject may only be drawn into one
        window. Raises an error if attempt made to draw an object that
        is already visible."""

        if self.canvas and not self.canvas.isClosed():
            raise GraphicsError(OBJ_ALREADY_DRAWN)
        if graphwin.isClosed():
            raise GraphicsError("Can't draw to closed window")
        self.canvas = graphwin
        self.id = self._draw(graphwin, self.config)
        graphwin.addItem(self)
        if graphwin.autoflush:
            _root.update()
        return self

    def undraw(self):

        """Undraw the object (i.e. hide it). Returns silently if the
        object is not currently drawn."""
        
        if not self.canvas:
            return
        if not self.canvas.isClosed():
            self.canvas.delete(self.id)
            self.canvas.delItem(self)
            if self.canvas.autoflush:
                _root.update()
        self.canvas = None
        self.id = None
        return self

    def move(self, dx, dy):

        """move object dx units in x direction and dy units in y
        direction"""
        
        self._move(dx, dy)
        canvas = self.canvas
        if canvas and not canvas.isClosed():
            trans = canvas.trans
            if trans:
                x = dx / trans.xscale
                y = -dy / trans.yscale
            else:
                x = dx
                y = dy
            self.canvas.move(self.id, x, y)
            if canvas.autoflush:
                _root.update()
        return self
           
    def _reconfig(self, option, setting):
        # Internal method for changing configuration of the object
        # Raises an error if the option does not exist in the config
        #    dictionary for this object
        if option not in self.config:
            raise GraphicsError(UNSUPPORTED_METHOD)
        options = self.config
        options[option] = setting
        if self.canvas and not self.canvas.isClosed():
            self.canvas.itemconfig(self.id, options)
            if self.canvas.autoflush:
                _root.update()

    def _draw(self, canvas, options):
        """draws appropriate figure on canvas with options provided
        Returns Tk id of item drawn"""
        pass  # must override in subclass

    def _move(self, dx, dy):
        """updates internal state of object to move it dx,dy units"""
        pass  # must override in subclass

         
class Point(GraphicsObject):
    def __init__(self, x, y):
        GraphicsObject.__init__(self, ["outline", "fill"])
        self.setFill = self.setOutline
        self.x = x
        self.y = y

    def __repr__(self):
        return "Point({}, {})".format(self.x, self.y)
        
    def _draw(self, canvas, options):
        x, y = canvas.toScreen(self.x, self.y)
        return canvas.create_rectangle(x, y, x+1, y+1, options)
        
    def _move(self, dx, dy):
        self.x = self.x + dx
        self.y = self.y + dy
        
    def clone(self):
        other = Point(self.x, self.y)
        other.config = self.config.copy()
        return other
                
    def getX(self):
        return self.x

    def getY(self):
        return self.y

    def isInside(self, obj):
        click_x = self.getX()
        click_y = self.getY()
        item_p1_x = 0
        item_p1_y = 0
        item_p2_x = 0
        item_p2_y = 0
        if isinstance(obj, Circle):
            from math import sqrt, pow
            r = obj.getRadius()
            center_x = obj.getCenter().getX()
            center_y = obj.getCenter().getY()
            d = sqrt(pow((click_x - center_x), 2) + pow((click_y - center_y), 2))
            if d <= r:
                return True
            else:
                return False
        elif isinstance(obj, Polygon):
            points = obj.getPoints()
            final_points = []
            for point in points:
                temp = [point.getX(), point.getY()]
                final_points.append(temp)
            polygon = mpl_path.Path(np.array(final_points))
            return polygon.contains_point((click_x, click_y))
        elif isinstance(obj, Rectangle):
            item_p1 = obj.getP1()
            item_p1_x = item_p1.getX()
            item_p1_y = item_p1.getY()
            item_p2 = obj.getP2()
            item_p2_x = item_p2.getX()
            item_p2_y = item_p2.getY()
        if min(item_p1_x, item_p2_x) < click_x < max(item_p1_x, item_p2_x) \
                and min(item_p1_y, item_p2_y) < click_y < max(item_p1_y, item_p2_y):
            return True
        else:
            return False


class _BBox(GraphicsObject):
    # Internal base class for objects represented by bounding box
    # (opposite corners) Line segment is a degenerate case.
    
    def __init__(self, p1, p2, options=None):
        if options is None:
            options = ["outline", "width", "fill"]
        GraphicsObject.__init__(self, options)
        self.p1 = p1.clone()
        self.p2 = p2.clone()

    def _move(self, dx, dy):
        self.p1.x = self.p1.x + dx
        self.p1.y = self.p1.y + dy
        self.p2.x = self.p2.x + dx
        self.p2.y = self.p2.y + dy
                
    def getP1(self): return self.p1.clone()

    def getP2(self): return self.p2.clone()
    
    def getCenter(self):
        p1 = self.p1
        p2 = self.p2
        return Point((p1.x+p2.x)/2.0, (p1.y+p2.y)/2.0)

    def containsPoint(self, p):
        if p is None:
            return
        return min(self.p1.x, self.p2.x) < p.x < max(self.p1.x, self.p2.x) \
            and min(self.p1.y, self.p2.y) < p.y < max(self.p1.y, self.p2.y)


class Rectangle(_BBox):
    
    def __init__(self, p1, p2, **kwargs):
        _BBox.__init__(self, p1, p2)
        for key in kwargs:
            if key == "fill":
                self.setFill(kwargs[key])
            elif key == "outline":
                self.setOutline(kwargs[key])
            elif key == "width":
                self.setWidth(kwargs[key])

    def __repr__(self):
        return "Rectangle({}, {})".format(str(self.p1), str(self.p2))
    
    def _draw(self, canvas, options):
        p1 = self.p1
        p2 = self.p2
        x1, y1 = canvas.toScreen(p1.x, p1.y)
        x2, y2 = canvas.toScreen(p2.x, p2.y)
        return canvas.create_rectangle(x1, y1, x2, y2, options)
        
    def clone(self):
        other = Rectangle(self.p1, self.p2)
        other.config = self.config.copy()
        return other


class Oval(_BBox):
    
    def __init__(self, p1, p2, **kwargs):
        _BBox.__init__(self, p1, p2)
        for key in kwargs:
            if key == "fill":
                self.setFill(kwargs[key])
            elif key == "outline":
                self.setOutline(kwargs[key])
            elif key == "width":
                self.setWidth(kwargs[key])

    def __repr__(self):
        return "Oval({}, {})".format(str(self.p1), str(self.p2))
        
    def clone(self):
        other = Oval(self.p1, self.p2)
        other.config = self.config.copy()
        return other
   
    def _draw(self, canvas, options):
        p1 = self.p1
        p2 = self.p2
        x1, y1 = canvas.toScreen(p1.x, p1.y)
        x2, y2 = canvas.toScreen(p2.x, p2.y)
        return canvas.create_oval(x1, y1, x2, y2, options)


class Circle(Oval):
    
    def __init__(self, center, radius, **kwargs):
        p1 = Point(center.x-radius, center.y-radius)
        p2 = Point(center.x+radius, center.y+radius)
        Oval.__init__(self, p1, p2)
        self.radius = radius
        for key in kwargs:
            if key == "fill":
                self.setFill(kwargs[key])
            elif key == "outline":
                self.setOutline(kwargs[key])
            elif key == "width":
                self.setWidth(kwargs[key])

    def __repr__(self):
        return "Circle({}, {})".format(str(self.getCenter()), str(self.radius))
        
    def clone(self):
        other = Circle(self.getCenter(), self.radius)
        other.config = self.config.copy()
        return other
        
    def getRadius(self):
        return self.radius

    def containsPoint(self, p):
        if p is None:
            return
        center_x = self.getCenter().getX()
        center_y = self.getCenter().getY()
        d = sqrt(pow((p.x - center_x), 2) + pow((p.y - center_y), 2))
        return d <= self.radius


class Line(_BBox):
    
    def __init__(self, p1, p2, **kwargs):
        _BBox.__init__(self, p1, p2, ["arrow", "fill", "width"])
        self.setFill(DEFAULT_CONFIG['outline'])
        self.setOutline = self.setFill
        for key in kwargs:
            if key == "fill":
                self.setFill(kwargs[key])
            elif key == "outline":
                self.setOutline(kwargs[key])
            elif key == "width":
                self.setWidth(kwargs[key])
            elif key == "arrow":
                self.setArrow(kwargs[key])

    def __repr__(self):
        return "Line({}, {})".format(str(self.p1), str(self.p2))
   
    def clone(self):
        other = Line(self.p1, self.p2)
        other.config = self.config.copy()
        return other
  
    def _draw(self, canvas, options):
        p1 = self.p1
        p2 = self.p2
        x1, y1 = canvas.toScreen(p1.x, p1.y)
        x2, y2 = canvas.toScreen(p2.x, p2.y)
        return canvas.create_line(x1, y1, x2, y2, options)
        
    def setArrow(self, option):
        if option not in ["first", "last", "both", "none"]:
            raise GraphicsError(BAD_OPTION)
        self._reconfig("arrow", option)
        return self

    def containsPoint(self, p):
        if p is None:
            return
        def distance(a, b):
            return sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)
        return distance(self.p1, p) + distance(p, self.p2) == distance(self.p1, self.p2)
        

class Polygon(GraphicsObject):
    
    def __init__(self, *points, **kwargs):
        # if points passed as a list, extract it
        if len(points) == 1 and type(points[0]) == type([]):
            points = points[0]
        self.points = list(map(Point.clone, points))
        GraphicsObject.__init__(self, ["outline", "width", "fill"])
        for key in kwargs:
            if key == "fill":
                self.setFill(kwargs[key])
            elif key == "outline":
                self.setOutline(kwargs[key])
            elif key == "width":
                self.setWidth(kwargs[key])

    def __repr__(self):
        return "Polygon" + str(tuple(p for p in self.points))
        
    def clone(self):
        other = Polygon(*self.points)
        other.config = self.config.copy()
        return other

    def getPoints(self):
        return list(map(Point.clone, self.points))

    def _move(self, dx, dy):
        for p in self.points:
            p.move(dx, dy)
   
    def _draw(self, canvas, options):
        args = [canvas]
        for p in self.points:
            x, y = canvas.toScreen(p.x, p.y)
            args.append(x)
            args.append(y)
        args.append(options)
        return GraphWin.create_polygon(*args)

    def containsPoint(self, p):
        if p is None:
            return
        points = self.getPoints()
        final_points = []
        for point in points:
            temp = [point.getX(), point.getY()]
            final_points.append(temp)
        polygon = mpl_path.Path(np.array(final_points))
        return polygon.contains_point((p.x, p.y))


class Text(GraphicsObject):
    
    def __init__(self, p, text, **kwargs):
        GraphicsObject.__init__(self, ["justify", "fill", "text", "font"])
        self.setText(text)
        self.anchor = p.clone()
        self.setFill(DEFAULT_CONFIG['outline'])
        self.setOutline = self.setFill
        for key in kwargs:
            if key == "fill":
                self.setFill(kwargs[key])
            elif key == "outline":
                self.setOutline(kwargs[key])
            elif key == "width":
                self.setWidth(kwargs[key])
            elif key == "text":
                self.setText(kwargs[key])
            elif key == "face":
                self.setFace(kwargs[key])
            elif key == "size":
                self.setSize(kwargs[key])

    def __repr__(self):
        return "Text({}, '{}')".format(self.anchor, self.getText())
        
    def _draw(self, canvas, options):
        p = self.anchor
        x, y = canvas.toScreen(p.x, p.y)
        return canvas.create_text(x, y, options)
        
    def _move(self, dx, dy):
        self.anchor.move(dx, dy)
        
    def clone(self):
        other = Text(self.anchor, self.config['text'])
        other.config = self.config.copy()
        return other

    def setText(self, text):
        self._reconfig("text", text)
        return self
        
    def getText(self):
        return self.config["text"]
            
    def getAnchor(self):
        return self.anchor.clone()

    def setFace(self, face):
        if face in ['helvetica', 'arial', 'courier', 'times roman']:
            f, s, b = self.config['font']
            self._reconfig("font", (face, s, b))
        else:
            raise GraphicsError(BAD_OPTION)
        return self

    def setSize(self, size):
        if 5 <= size <= 150:
            f, s, b = self.config['font']
            self._reconfig("font", (f, size, b))
        else:
            raise GraphicsError(BAD_OPTION)
        return self

    def setStyle(self, style):
        if style in ['bold', 'normal', 'italic', 'bold italic']:
            f, s, b = self.config['font']
            self._reconfig("font", (f, s, style))
        else:
            raise GraphicsError(BAD_OPTION)
        return self

    def setTextColor(self, color):
        self.setFill(color)
        return self


class Entry(GraphicsObject):

    def __init__(self, p, width, **kwargs):
        GraphicsObject.__init__(self, [])
        self.anchor = p.clone()
        # print self.anchor
        self.width = width
        self.text = tk.StringVar(_root)
        self.text.set("")
        self.fill = "gray"
        self.color = "black"
        self.font = DEFAULT_CONFIG['font']
        self.entry = None
        for key in kwargs:
            if key == "fill":
                self.setFill(kwargs[key])
            elif key == "outline":
                self.setOutline(kwargs[key])
            elif key == "width":
                self.setWidth(kwargs[key])
            elif key == "text":
                self.setText(kwargs[key])
            elif key == "face":
                self.setFace(kwargs[key])
            elif key == "size":
                self.setSize(kwargs[key])
            elif key == "style":
                self.setStyle(kwargs[key])

    def __repr__(self):
        return "Entry({}, {})".format(self.anchor, self.width)

    def _draw(self, canvas, options):
        p = self.anchor
        x, y = canvas.toScreen(p.x, p.y)
        frm = tk.Frame(canvas.master)
        self.entry = tk.Entry(frm,
                              width=self.width,
                              textvariable=self.text,
                              bg=self.fill,
                              fg=self.color,
                              font=self.font)
        self.entry.pack()
        # self.setFill(self.fill)
        self.entry.focus_set()
        return canvas.create_window(x, y, window=frm)

    def getText(self):
        return self.text.get()

    def _move(self, dx, dy):
        self.anchor.move(dx, dy)

    def getAnchor(self):
        return self.anchor.clone()

    def clone(self):
        other = Entry(self.anchor, self.width)
        other.config = self.config.copy()
        other.text = tk.StringVar()
        other.text.set(self.text.get())
        other.fill = self.fill
        return other

    def setText(self, t):
        self.text.set(t)
        return self
            
    def setFill(self, color):
        self.fill = color
        if self.entry:
            self.entry.config(bg=color)
        return self

    def _setFontComponent(self, which, value):
        font = list(self.font)
        font[which] = value
        self.font = tuple(font)
        if self.entry:
            self.entry.config(font=self.font)

    def setFace(self, face):
        if face in ['helvetica', 'arial', 'courier', 'times roman']:
            self._setFontComponent(0, face)
        else:
            raise GraphicsError(BAD_OPTION)
        return self

    def setSize(self, size):
        if 5 <= size <= 36:
            self._setFontComponent(1, size)
        else:
            raise GraphicsError(BAD_OPTION)
        return self

    def setStyle(self, style):
        if style in ['bold', 'normal', 'italic', 'bold italic']:
            self._setFontComponent(2, style)
        else:
            raise GraphicsError(BAD_OPTION)
        return self

    def setTextColor(self, color):
        self.color = color
        if self.entry:
            self.entry.config(fg=color)
        return self


class Image(GraphicsObject):

    idCount = 0
    imageCache = {}  # tk photoimages go here to avoid GC while drawn
    
    def __init__(self, p, *pixmap, **kwargs):
        GraphicsObject.__init__(self, [])
        self.anchor = p.clone()
        self.imageId = Image.idCount
        Image.idCount += 1
        if len(pixmap) == 1:  # file name provided
            self.img = tk.PhotoImage(file=pixmap[0], master=_root)
        else:  # width and height provided
            width, height = pixmap
            self.img = tk.PhotoImage(master=_root, width=width, height=height)
        for key in kwargs:
            if key == "fill":
                self.setFill(kwargs[key])
            elif key == "outline":
                self.setOutline(kwargs[key])
            elif key == "width":
                self.setWidth(kwargs[key])

    def __repr__(self):
        return "Image({}, {}, {})".format(self.anchor, self.getWidth(), self.getHeight())
                
    def _draw(self, canvas, options):
        p = self.anchor
        x, y = canvas.toScreen(p.x, p.y)
        self.imageCache[self.imageId] = self.img  # save a reference
        return canvas.create_image(x, y, image=self.img)
    
    def _move(self, dx, dy):
        self.anchor.move(dx, dy)
        
    def undraw(self):
        try:
            del self.imageCache[self.imageId]  # allow gc of tk photoimage
        except KeyError:
            pass
        GraphicsObject.undraw(self)

    def getAnchor(self):
        return self.anchor.clone()
        
    def clone(self):
        other = Image(Point(0, 0), 0, 0)
        other.img = self.img.copy()
        other.anchor = self.anchor.clone()
        other.config = self.config.copy()
        return other

    def getWidth(self):
        """Returns the width of the image in pixels"""
        return self.img.width() 

    def getHeight(self):
        """Returns the height of the image in pixels"""
        return self.img.height()

    def getPixel(self, x, y):
        """Returns a list [r,g,b] with the RGB color values for pixel (x,y)
        r,g,b are in range(256)

        """
        
        value = self.img.get(x, y)
        if type(value) == type(0):
            return [value, value, value]
        elif type(value) == type((0, 0, 0)):
            return list(value)
        else:
            return list(map(int, value.split())) 

    def setPixel(self, x, y, color):
        """Sets pixel (x,y) to the given color
        
        """
        self.img.put("{" + color + "}", (x, y))
        return self

    def save(self, filename):
        """Saves the pixmap image to filename.
        The format for the save image is determined from the filname extension.

        """
        path, name = os.path.split(filename)
        ext = name.split(".")[-1]
        self.img.write(filename, format=ext)

        
def color_rgb(r, g, b):
    """r,g,b are intensities of red, green, and blue in range(256)
    Returns color specifier string for the resulting color"""
    return "#%02x%02x%02x" % (r, g, b)


def _clickedOn(item, check):
    if check is None:
        return None
    click_x = check.getX()
    click_y = check.getY()
    item_p1_x = 0
    item_p1_y = 0
    item_p2_x = 0
    item_p2_y = 0
    if isinstance(item, Circle):
        from math import sqrt, pow
        r = item.getRadius()
        center_x = item.getCenter().getX()
        center_y = item.getCenter().getY()
        d = sqrt(pow((click_x-center_x), 2)+pow((click_y-center_y), 2))
        if d <= r:
            return True
        else:
            return False
    elif isinstance(item, Polygon):
        points = item.getPoints()
        final_points = []
        for point in points:
            temp = [point.getX(), point.getY()]
            final_points.append(temp)
        polygon = mpl_path.Path(np.array(final_points))
        return polygon.contains_point((click_x, click_y))
    elif isinstance(item, Rectangle):
        item_p1 = item.getP1()
        item_p1_x = item_p1.getX()
        item_p1_y = item_p1.getY()
        item_p2 = item.getP2()
        item_p2_x = item_p2.getX()
        item_p2_y = item_p2.getY()
    if min(item_p1_x, item_p2_x) < click_x < max(item_p1_x, item_p2_x) \
            and min(item_p1_y, item_p2_y) < click_y < max(item_p1_y, item_p2_y):
        return True
    else:
        return False


def test():
    win = GraphWin()
    win.setCoords(0, 0, 10, 10)
    t = Text(Point(5, 5), "Centered Text")
    t.draw(win)
    p = Polygon(Point(1, 1), Point(5, 3), Point(2, 7))
    p.draw(win)
    e = Entry(Point(5, 6), 10)
    e.draw(win)
    win.getMouse()
    p.setFill("red")
    p.setOutline("blue")
    p.setWidth(2)
    s = ""
    for pt in p.getPoints():
        s += "(%0.1f,%0.1f) " % (pt.getX(), pt.getY())
    t.setText(e.getText())
    e.setFill("green")
    e.setText("Spam!")
    e.move(2, 0)
    win.getMouse()
    p.move(2, 3)
    s = ""
    for pt in p.getPoints():
        s += "(%0.1f,%0.1f) " % (pt.getX(), pt.getY())
    t.setText(s)
    win.getMouse()
    p.undraw()
    e.undraw()
    t.setStyle("bold")
    win.getMouse()
    t.setStyle("normal")
    win.getMouse()
    t.setStyle("italic")
    win.getMouse()
    t.setStyle("bold italic")
    win.getMouse()
    t.setSize(14)
    win.getMouse()
    t.setFace("arial")
    t.setSize(20)
    win.getMouse()
    win.close()

# MacOS fix 2
# tk.Toplevel(_root).destroy()

# MacOS fix 1
update()

if __name__ == "__main__":
    test()
