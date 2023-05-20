"""
Read stream of lines from an Arduino. This
produces 2 values per line every 500ms. Each line looks like:
WOG   1.00    -2.00
with each data line starting with "WOG" and each field separated by
tab characters. Values are integers in ASCII encoding.

Two classes are used
    - MainWindow handles all of the graphics, including generating
    the data plot
    - Threaded handles the serial communication in a separate
    thread.
    - The main() function does the following:
        - establishes the serial connection
        - creates instances of the aformentioned classes
        - creates the signal/slot connections between the instances
"""
import sys
import time
from serial import Serial, SerialException


from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg
from collections import deque


# ==========================================================
class GraphWidget(qtw.QWidget):
    """A widget to display a running graph of information"""

    crit_color = qtg.QColor(255, 0, 0)  # red
    warn_color = qtg.QColor(255, 255, 0)  # yellow
    good_color = qtg.QColor(0, 255, 0)  # green

    def __init__(
        self, *args, data_width=100,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.Line1 = deque([0] * data_width, maxlen=data_width)
        self.Line2 = deque([0] * data_width, maxlen=data_width)
        self.max_all = 10
        
    def add_value(self, x, y):
        self.Line1.append(int(x))  # add the new value.
        self.Line2.append(int(y))  # Add the new value.
        # rescale based on the latest data
        max_X = max(self.Line1) + 1e-5
        min_X = min(self.Line1) - 1e-5
        max_Y = max(self.Line2) + 1e-5
        min_Y = min(self.Line2) - 1e-5
        self.max_all = max(max_X, -min_X, max_Y, -min_Y)
        self.update()

    def val_to_y(self, value):
        data_range = self.maximum - self.minimum
        value_fraction = value / data_range
        y_offset = round(value_fraction * self.height())
        y = self.height() - y_offset
        return y

    def paintEvent(self, paint_event):
        painter = qtg.QPainter(self)

        # draw the background
        brush = qtg.QBrush(qtg.QColor(48, 48, 48))
        painter.setBrush(brush)
        painter.drawRect(0, 0, self.width(), self.height())

        # draw the boundary lines
        pen = qtg.QPen()
        pen.setDashPattern([1, 0])

        # warning line
        warn_y = self.val_to_y(self.warn_val)
        pen.setColor(self.warn_color)
        painter.setPen(pen)
        painter.drawLine(0, warn_y, self.width(), warn_y)

        # critical line
        crit_y = self.val_to_y(self.crit_val)
        pen.setColor(self.crit_color)
        painter.setPen(pen)
        painter.drawLine(0, crit_y, self.width(), crit_y)

        # set up gradient brush
        gradient = qtg.QLinearGradient(
            qtc.QPointF(0, self.height()), qtc.QPointF(0, 0))
        gradient.setColorAt(0, self.good_color)
        gradient.setColorAt(
            self.warn_val/(self.maximum - self.minimum),
            self.warn_color)
        gradient.setColorAt(
            self.crit_val/(self.maximum - self.minimum),
            self.crit_color)
        brush = qtg.QBrush(gradient)
        painter.setBrush(brush)
        painter.setPen(qtc.Qt.NoPen)

        # Draw the paths for the chart
        self.start_value = getattr(self, 'start_value', self.minimum)
        last_value = self.start_value
        self.start_value = self.values[0]
        for indx, value in enumerate(self.values):
            x = (indx + 1) * self.scale
            last_x = indx * self.scale
            y = self.val_to_y(value)
            last_y = self.val_to_y(last_value)
            path = qtg.QPainterPath()
            path.moveTo(x, self.height())
            path.lineTo(last_x, self.height())
            path.lineTo(last_x, last_y)
            # Straight tops
            #path.lineTo(x, y)

            # Curvy tops
            c_x = round(self.scale * .5) + last_x
            c1 = (c_x, last_y)
            c2 = (c_x, y)
            path.cubicTo(*c1, *c2, x, y)

            # Draw path
            painter.drawPath(path)
            last_value = value


# ==========================================================
class MainWindow(qtw.QMainWindow):
    """
    GUI window for the application.
    """
    # create a signal (replot) tied to the slot update_data()
    new_data = qtc.pyqtSignal()

    def __init__(self):
        """MainWindow constructor."""
        super().__init__()
        # Code starts here
        self.resize(qtw.QDesktopWidget().availableGeometry(self).size() * 0.7)
        self.replot.connect(self.update_plot_data)

        # Create the push buttons
        self.button1 = qtw.QPushButton("START")
        self.button2 = qtw.QPushButton("STOP")
        self.button3 = qtw.QPushButton("Done")
        # create a plot from a label widget
        self.label = QResizingPixmapLabel()
        self.label.setSizePolicy(
            qtw.QSizePolicy.Expanding,
            qtw.QSizePolicy.Expanding,
        )

        # build the layout
        layout = qtw.QVBoxLayout()
        layout.addWidget(self.button1)
        layout.addWidget(self.button2)
        layout.addWidget(self.button3)
        layout.addWidget(self.label)

        # put the layout in a container
        container = qtw.QWidget()
        container.setLayout(layout)

        # put the containe in the window frame
        self.setCentralWidget(container)

        # Start the Show!
        # This must be done to retrieve the proper
        # label dimensions
        # self.show()

        # now add a canvas to the Qlabel widget
        # this is done after the layout enabling us
        # to capture the final label size
        print("Initial Canvas: x is ", self.label.width(), " y is ", self.label.height())
        canvas = qtg.QPixmap(self.label.width(), self.label.height())
        canvas.fill(qtc.Qt.white)
        self.label.setPixmap(canvas)
        self.w = self.label.pixmap().width()
        self.hh = self.label.pixmap().height()//2

        # these lists hold data for the two lines to be plotted
        self.npoints = 100
        self.Line1 = [0 for x in range(self.npoints)]
        self.Line2 = [0 for x in range(self.npoints)]
        self.replot.emit()

        # Code ends here
        self.show()

    @qtc.pyqtSlot()
    def done_button(self):
        """
        Event handler for the Done button.
        Stops the application.
        """
        # Terminate the exec_ loop
        qtw.QCoreApplication.quit()

    @qtc.pyqtSlot(float, float)
    def append_data(self, x, y):
        """
        Updates the display with the latest data
        received from the serial connection.
        """
        self.Line1 = self.Line1[1:]  # Remove the first element.
        self.Line1.append(int(x))  # add the new value.

        self.Line2 = self.Line2[1:]  # Remove the first element.
        self.Line2.append(int(y))  # Add the new value.

        # use a signal here (as opposed to a function call)
        # to avoid tangling with replotting
        # that may be done when resizing
        self.replot.emit()

    @qtc.pyqtSlot()
    def update_plot_data(self):
        """
        replot the canvas with current data
        """
        w = self.label.pixmap().width()
        hh = self.label.pixmap().height()//2
        # rescale based on the latest data
        max_X = max(self.Line1) + 1e-5
        min_X = min(self.Line1) - 1e-5
        max_Y = max(self.Line2) + 1e-5
        min_Y = min(self.Line2) - 1e-5
        max_all = max(max_X, -min_X, max_Y, -min_Y)

        # build the lists reqired for drawPolyLine
        coordsX, coordsY = [], []
        for n in range(0, self.npoints):
            x = (self.w * n) / self.npoints
            coordsX.append(x)
            coordsY.append(x)
            # scale and translate the data to screen
            # coordinates with 0 at the vertical centerline
            # of the plot
            coordsX.append(self.hh * (1 - self.Line1[n] / max_all))
            coordsY.append(self.hh * (1 - self.Line2[n] / max_all))
        # retrieve the current canvas from the pixmap
        canvas = self.label.pixmap()
        # blank the canvas for repainting
        canvas.fill(qtc.Qt.white)
        painter = qtg.QPainter(self.label.pixmap())
        pen = qtg.QPen()
        myLine = qtg.QPolygon()

        pen.setColor(qtg.QColor("red"))
        painter.setPen(pen)
        myLine.setPoints(coordsX)
        painter.drawPolyline(myLine)

        pen.setColor(qtg.QColor("black"))
        painter.setPen(pen)
        myLine.setPoints(coordsY)
        painter.drawPolyline(myLine)

        painter.end()
        self.update()


# ==========================================================
class Thread(qtc.QThread):
    """
    Worker thread.
    Signals when new data arrives.
    Signal includes string.
    Reads from serial port ONLY if data waiting.
    """

    result = qtc.pyqtSignal(float, float)

    def __init__(self, serialPort):
        super().__init__()
        self.serialPort = serialPort

    def run(self):
        """
        This method reads text from the serial port,
        parses the text into two floats, and signals
        to GUI to update the plot.
        """
        self.is_running = True
        while self.is_running:
            if self.serialPort.inWaiting() != 0:
                # Caution: the following line is BLOCKING
                msg = self.serialPort.readline()
                # self.queue.put(line)
                msg = msg.decode('ascii').strip("\r\n")
                # Check contents of message,
                if msg[0:3] != "WOG":
                    print("Bad Message: ", msg)  # line not valid
                else:
                    try:
                        data = msg.split("\t")
                        x, y = float(data[1]), float(data[2])
                        self.result.emit(x, y)
                    except Exception as e:
                        print(e)

    @qtc.pyqtSlot()
    def stop(self):
        """
        Event handler for the Done button
        """
        self.stop_remote()
        self.is_running = False

    @qtc.pyqtSlot()
    def stop_remote(self):
        """
        Event handler for the Stop button
        """
        # note the string termination
        self.serialPort.write(bytes('L\n', 'UTF-8'))

    @qtc.pyqtSlot()
    def start_remote(self):
        """
        Event handler for the Start button
        """
        # note the string termination
        self.serialPort.write(bytes('H\n', 'UTF-8'))


# ==========================================================
def main(args=None):
    if args is None:
        args = sys.argv
    if len(args) > 1:
        port = args[1]
    if len(args) > 2:
        baudrate = int(args[2])
    # pick a port, depending on the microcontroller used
    # port, baudrate = '/dev/tty.usbmodem14101', 9600  # uno
    port, baudrate = '/dev/tty.usbmodem14103', 9600  # stm32

    app = qtc.QApplication(sys.argv)
    try:
        serialPort = Serial(port, baudrate, rtscts=True)
        print("Reset Arduino")
        time.sleep(2)
    except SerialException:
        print("Sorry, invalid serial port.\n")
        print("Did you update it in the script?\n")
        sys.exit(1)

    # create the worker thread and the window
    worker = Thread(serialPort)
    window = MainWindow()

    # configure the call-backs
    worker.result.connect(window.append_data)
    window.button1.clicked.connect(worker.start_remote)
    window.button2.clicked.connect(worker.stop_remote)
    window.button3.clicked.connect(worker.stop)
    window.button3.clicked.connect(window.done_button)

    # start the thread
    worker.start()

    app.exec_()


if __name__ == '__main__':
    main()
