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
import sys
import time
import random
from serial import Serial, SerialException


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


# ==========================================================
class MainWindow(qtw.QMainWindow):
    """
    GUI window for the application.
    """
    # create a signal (replot) tied to the slot update_data()
    # new_data = qtc.pyqtSignal()

    def __init__(self):
        """MainWindow constructor."""
        super().__init__()
        # Code starts here
        self.resize(qtw.QDesktopWidget().availableGeometry(self).size() * 0.7)
        # self.new_data.connect(self.update_plot_data)

        # Create the push buttons
        self.button1 = qtw.QPushButton("START")
        self.button2 = qtw.QPushButton("STOP")
        self.button3 = qtw.QPushButton("Done")
        # create a plot from a plot widget
        self.plot = GraphWidget()
        self.plot.setSizePolicy(
            qtw.QSizePolicy.Expanding,
            qtw.QSizePolicy.Expanding,
        )

        # build the layout
        layout = qtw.QVBoxLayout()
        layout.addWidget(self.button1)
        layout.addWidget(self.button2)
        layout.addWidget(self.button3)
        layout.addWidget(self.plot)

        # put the layout in a container
        container = qtw.QWidget()
        container.setLayout(layout)

        # put the containe in the window frame
        self.setCentralWidget(container)

        # Start the Show!
        self.show()

    @qtc.pyqtSlot()
    def done_button(self):
        """
        Event handler for the Done button.
        Stops the application.
        """
        # Terminate the exec_ loop
        qtc.QCoreApplication.quit()


# ==========================================================
class FakeThread(qtc.QThread):
    """
    Fake worker thread.  No serial port is used.
    Data is generated using a random() function.
    """

    result = qtc.pyqtSignal(float, float)

    def __init__(self):
        super().__init__()
        self.remote_is_running = False
        self.is_running = False

    def run(self):
        """
        Fakes data that would be read from a serial port.
        Two values are generated.  The "is_running" flag
        controls when the run() method will terminate.
        The "remote_is_running" determines when to simulate
        receiving a serial packet.
        """
        self.is_running = True
        while self.is_running:
            time.sleep(0.25)
            if self.remote_is_running:
                x = random.random() - 0.5
                y = random.random() - 0.5
                self.result.emit(x, y)

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
        self.remote_is_running = False

    @qtc.pyqtSlot()
    def start_remote(self):
        """
        Event handler for the Start button
        """
        self.remote_is_running = True


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
def open_serial(args):
    """!
    Opens one of several serial ports - uses the first
    one that works.  Returns the serial port object if a serial port is
    connected, None otherwise
    """
    baudrate = 9600
    ports = ['/dev/tty.usbmodem14101',
             '/dev/tty.usbmodem14103']
    if len(args) > 1:
        ports.append(args[1])
    if len(args) > 2:
        baudrate = int(args[2])
    serial_open_failed = False
    # pick a port, depending on the microcontroller used
    for io_unit in ports:
        try:
            serialPort = Serial(io_unit, baudrate, rtscts=True)
        except SerialException:
            serial_open_failed = True
        if not serial_open_failed:  # break if connected
            break
    if serial_open_failed:
        return None
    return serialPort


# ==========================================================
def main(args=None):
    if args is None:
        args = sys.argv

    app = qtw.QApplication(sys.argv)

    serialPort = open_serial(args)
    if serialPort is None:
        print("Serial connection not active, using a dummy\n")
        worker = FakeThread()
    else:
        print("Reset Arduino")
        time.sleep(2)
        # create the worker thread and the window
        worker = Thread(serialPort)

    window = MainWindow()

    # configure the call-backs
    worker.result.connect(window.plot.add_value)
    window.button1.clicked.connect(worker.start_remote)
    window.button2.clicked.connect(worker.stop_remote)
    window.button3.clicked.connect(worker.stop)
    window.button3.clicked.connect(window.done_button)

    # start the thread
    worker.start()

    app.exec_()


if __name__ == '__main__':
    main()
