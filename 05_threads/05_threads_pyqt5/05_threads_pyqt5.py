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
        Your code goes in this method
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
    def __init__(self):
        super().__init__()

        # Create the push buttons
        self.button1 = QPushButton("START")
        self.button2 = QPushButton("STOP")
        self.button3 = QPushButton("Done")

        # create a plot from a label widget
        self.label = QLabel()
        self.canvasWidth = 400
        self.canvasHalfHeight = 150
        canvas = QPixmap(self.canvasWidth, self.canvasHalfHeight*2)
        canvas.fill(Qt.white)
        self.label.setPixmap(canvas)

        # these lists hold data for the two lines to be plotted
        self.npoints = 100
        self.Line1 = [0 for x in range(self.npoints)]
        self.Line2 = [0 for x in range(self.npoints)]

        # painter = QPainter(self.label.pixmap())
        # painter.drawPolyLine
        # painter.end()

        # pen = pg.mkPen(color=(255, 0, 0))
        # self.data_line = self.graphWidget.plot(
        #     self.x, self.y, pen=pen
        # )

        # Window layout
        container = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.button1)
        layout.addWidget(self.button2)
        layout.addWidget(self.button3)
        layout.addWidget(self.label)
        container.setLayout(layout)

        # Start the Show!
        self.setCentralWidget(container)
        self.show()

    @pyqtSlot()
    def done_button(self):
        # Terminate the exec_ loop
        QCoreApplication.quit()

    @pyqtSlot(float, float)
    def update_plot_data(self, x, y):
        # scale and transform the data
        print("x is ", x, ", y is ", y)
        self.Line1 = self.Line1[1:]  # Remove the first element.
        self.Line1.append(int(x))  # add the new value.

        self.Line2 = self.Line2[1:]  # Remove the first element.
        self.Line2.append(int(y))  # Add the new value.
        """
        Update the canvas graph lines from the cached data lists.
        The lines are scaled to match the canvas size as the window may
        be resized by the user.
        """
        w = self.canvasWidth
        hh = self.canvasHalfHeight
        max_X = max(self.Line1) + 1e-5
        min_X = min(self.Line1) - 1e-5
        max_Y = max(self.Line2) + 1e-5
        min_Y = min(self.Line2) - 1e-5
        max_all = max(max_X, -min_X, max_Y, -min_Y)
        coordsX, coordsY = [], []
        for n in range(0, self.npoints):
            x = (w * n) / self.npoints
            coordsX.append(x)
            coordsX.append(hh * (1 - self.Line1[n] / max_all))
            coordsY.append(x)
            coordsY.append(hh * (1 - self.Line2[n] / max_all))
        canvas = self.label.pixmap()
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

    # create the worker and the window
    worker = Thread(serialPort)
    window = MainWindow()

    # configure the call-backs
    worker.result.connect(window.update_plot_data)
    window.button1.clicked.connect(worker.start_remote)
    window.button2.clicked.connect(worker.stop_remote)
    window.button3.clicked.connect(worker.stop)
    window.button3.clicked.connect(window.done_button)

    # start the thread
    worker.start()

    app.exec_()


if __name__ == '__main__':
    main()
