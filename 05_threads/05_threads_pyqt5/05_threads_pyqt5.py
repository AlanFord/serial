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

from PyQt5.QtCore import (
    Qt,
    QCoreApplication,
    QThread,
    pyqtSignal,
    pyqtSlot,
)
from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QDesktopWidget,
    QSizePolicy,
)

from PyQt5.QtGui import (
    QPixmap,
    QPainter,
    QPolygon,
    QPen,
    QColor,
)


# ==========================================================
class Thread(QThread):
    """
    Worker thread.
    Signals when new data arrives.
    Signal includes string.
    Reads from serial port ONLY if data waiting.
    """

    result = pyqtSignal(float, float)

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

    @pyqtSlot()
    def stop(self):
        """
        Event handler for the Done button
        """
        self.stop_remote()
        self.is_running = False

    @pyqtSlot()
    def stop_remote(self):
        """
        Event handler for the Stop button
        """
        # note the string termination
        self.serialPort.write(bytes('L\n', 'UTF-8'))

    @pyqtSlot()
    def start_remote(self):
        """
        Event handler for the Start button
        """
        # note the string termination
        self.serialPort.write(bytes('H\n', 'UTF-8'))


# ==========================================================
class MainWindow(QMainWindow):
    """
    GUI window for the application.
    """
    # create a signal (replot) tied to the slot update_plot_data()
    replot = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.resize(QDesktopWidget().availableGeometry(self).size() * 0.7)
        self.replot.connect(self.update_plot_data)

        # Create the push buttons
        self.button1 = QPushButton("START")
        self.button2 = QPushButton("STOP")
        self.button3 = QPushButton("Done")
        # create a plot from a label widget
        self.label = QLabel()
        self.label.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        # build the layout
        layout = QVBoxLayout()
        layout.addWidget(self.button1)
        layout.addWidget(self.button2)
        layout.addWidget(self.button3)
        layout.addWidget(self.label)

        # put the layout in a container
        container = QWidget()
        container.setLayout(layout)

        # put the containe in the window frame
        self.setCentralWidget(container)

        # Start the Show!
        # This must be done to retrieve the proper
        # label dimensions
        self.show()

        # now add a canvas to the Qlabel widget
        # this is done after the layout enabling us
        # to capture the final label size
        print("x is ", self.label.width(), " y is ", self.label.height())
        canvas = QPixmap(self.label.width(), self.label.height())
        canvas.fill(Qt.white)
        self.label.setPixmap(canvas)

        # these lists hold data for the two lines to be plotted
        self.npoints = 100
        self.Line1 = [0 for x in range(self.npoints)]
        self.Line2 = [0 for x in range(self.npoints)]
        self.replot.emit()

    @pyqtSlot()
    def done_button(self):
        """
        Event handler for the Done button.
        Stops the application.
        """
        # Terminate the exec_ loop
        QCoreApplication.quit()

    @pyqtSlot(float, float)
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

    @pyqtSlot()
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
            x = (w * n) / self.npoints
            coordsX.append(x)
            coordsY.append(x)
            # scale and translate the data to screen
            # coordinates with 0 at the vertical centerline
            # of the plot
            coordsX.append(hh * (1 - self.Line1[n] / max_all))
            coordsY.append(hh * (1 - self.Line2[n] / max_all))
        # retrieve the current canvas from the pixmap
        canvas = self.label.pixmap()
        # blank the canvas for repainting
        canvas.fill(Qt.white)
        painter = QPainter(self.label.pixmap())
        pen = QPen()
        myLine = QPolygon()

        pen.setColor(QColor("red"))
        painter.setPen(pen)
        myLine.setPoints(coordsX)
        painter.drawPolyline(myLine)

        pen.setColor(QColor("black"))
        painter.setPen(pen)
        myLine.setPoints(coordsY)
        painter.drawPolyline(myLine)

        painter.end()
        self.update()


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

    app = QApplication(sys.argv)
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
