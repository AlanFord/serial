"""
Read stream of lines from an Arduino. This
produces 2 values per line every 500ms. Each line looks like:
WOG   1.00    -2.00
with each data line starting with "WOG" and each field separated by
tab characters. Values are integers in ASCII encoding.

Three classes are used
    - GraphWidget is a new widget that draws the data plot and is
      easily resizable.
    - MainWindow handles drawing the widgets
    - Thread handles the serial communication in a separate
    thread. (FakeThread is used if no serial connection is available)
    - The main() function does the following:
        - calls open_serial to establish a serial connection
        - creates the worker thread to manage the serial communication
        - configures all callbacks (signals/slots)
        - starts the worker thread
        - starts the event loop running
    - The open_serial() function encapulsates the code
        required to open a serial port.
"""

from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg
from collections import deque


# ==========================================================
class GraphWidget(qtw.QWidget):
    """!
    A widget to display a running graph of information

    The widget maintains two deques of values to be plotted.
    The plot maintains a vertical zero in the vertical middle
    of the plot.  The plot will rescale as new data is received
    and old data is scrolled off to the left.  The plot is
    refreshed as each new data point is received.
    """

    def __init__(
        self, *args, data_width=100,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        # deques containing the current data to be plotted
        self.Line1 = deque([0] * data_width, maxlen=data_width)
        self.Line2 = deque([0] * data_width, maxlen=data_width)
        self.data_width = data_width
        self.default_data_range = 10
        self.max_all = self.default_data_range

    @qtc.pyqtSlot(float, float)
    def add_value(self, x, y):
        """!
        Adds a set of data (two signals - x and y) to the
        data queues.  Determines the maximum value in the
        queues.  Forces an update of the graph widget.
        """
        self.Line1.append(float(x))  # add the new value.
        self.Line2.append(float(y))  # Add the new value.
        # rescale based on the latest data
        max_X = max(self.Line1) + 1e-5
        min_X = min(self.Line1) - 1e-5
        max_Y = max(self.Line2) + 1e-5
        min_Y = min(self.Line2) - 1e-5
        self.max_all = max(max_X, -min_X, max_Y, -min_Y)
        self.update()

    def scale_values(self, values):
        """!
        Convert a list object of values to scaled display points.
        Scaling assumes the vertical scale has a zero line at the
        veritical midpoint.  X values are scaled to fit the width
        of the widget.
        """
        data_range = self.max_all
        if data_range == 0.0:  # this should never happen, but just in case
            data_range = self.default_data_range
        y = []
        x_scale = self.width() / self.data_width
        for n in range(0, self.data_width):
            value_fraction = values[n] / data_range
            y_offset = round(value_fraction * self.height()/2)
            y.append(n * x_scale)
            y.append(self.height()/2 - y_offset)
        return y

    def paintEvent(self, paint_event):
        """!
        Redraws the widget.  Two display lines are supported;
        one black and one red.
        """
        painter = qtg.QPainter(self)

        # draw the background
        brush = qtg.QBrush(qtc.Qt.white)
        painter.setBrush(brush)
        painter.drawRect(0, 0, self.width(), self.height())

        # Draw Line 1
        pen = qtg.QPen()
        path = self.scale_values(self.Line1)
        myLine = qtg.QPolygon()
        myLine.setPoints(path)
        pen.setColor(qtg.QColor("red"))
        painter.setPen(pen)
        painter.drawPolyline(myLine)

        # Draw Line 2
        path = self.scale_values(self.Line2)
        myLine = qtg.QPolygon()
        myLine.setPoints(path)
        pen.setColor(qtg.QColor("black"))
        painter.setPen(pen)
        painter.drawPolyline(myLine)
