"""
Read stream of lines from an Arduino. This
produces 2 values per line every 500ms. Each line looks like:
WOG   1.00    -2.00
with each data line starting with "WOG" and each field separated by
tab characters. Values are integers in ASCII encoding.
"""
import sys
import time
from random import randint
from serial import Serial, SerialException

from PyQt5.QtCore import (
    Qt,
    QCoreApplication,
    QThread,
    pyqtSignal,
    pyqtSlot,
    QTimer
)
from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget
)
import pyqtgraph as pg  # import PyQtGraph after Qt


class Thread(QThread):
    """
    Worker thread.
    Signals when new data arrives.
    Signal includes string.
    Reads from serial port ONLY if data waiting.
    """

    result = pyqtSignal(str)

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
                line = self.serialPort.readline()
                # self.queue.put(line)
                line = line.decode('ascii').strip("\r\n")
                # Check contents of message,
                if line[0:3] != "WOG":
                    print("Bad Message: ", line)  # line not valid
                else:
                    try:
                        line = line[3:].strip()
                        print("WOG line:",line)
                        #  self.result.emit(line)
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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Create the push buttons
        self.button1 = QPushButton("START")
        self.button2 = QPushButton("STOP")
        self.button3 = QPushButton("Done")
        # button1.pressed.connect(self.start_button)
        # button2.pressed.connect(self.stop_button)
        # button3.pressed.connect(self.done_button)

        # >>>  TEMPORARY: DELETE when plot is added
        self.status = QLabel("Starting...")
        self.status.setAlignment(Qt.AlignCenter)

        # A plot
        self.graphWidget = pg.PlotWidget()

        self.x = list(range(100))  # 100 time points
        self.y = [
            randint(0, 100) for _ in range(100)
        ]  # 100 data points

        self.graphWidget.setBackground("w")

        pen = pg.mkPen(color=(255, 0, 0))
        self.data_line = self.graphWidget.plot(
            self.x, self.y, pen=pen
        )  # <1>

        # self.timer = QTimer()
        # self.timer.setInterval(50)
        # self.timer.timeout.connect(self.update_plot_data)
        # self.timer.start()

        # Window layout
        container = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.button1)
        layout.addWidget(self.button2)
        layout.addWidget(self.button3)
        layout.addWidget(self.status)
        layout.addWidget(self.graphWidget)
        container.setLayout(layout)

        # Start the Show!
        self.setCentralWidget(container)
        self.show()

    # def stop_button(self):
    #     """
    #     Event handler for the Stop button
    #     """
    #     # note the string termination
    #     # self.serialPort.write(bytes('L\n', 'UTF-8'))
    #     self.status.setText("STOP pressed")

    # def start_button(self):
    #     """
    #     Event handler for the Start button
    #     """
    #     # note the string termination
    #     # self.serialPort.write(bytes('H\n', 'UTF-8'))
    #     self.status.setText("START pressed")

    @pyqtSlot()
    def done_button(self):
        # Terminate the exec_ loop
        QCoreApplication.quit()

    @pyqtSlot()
    def update_plot_data(self, data):
        print(data)


"""         self.x = self.x[1:]  # Remove the first y element.
        self.x.append(
            self.x[-1] + 1
        )  # Add a new value 1 higher than the last.

        self.y = self.y[1:]  # Remove the first
        self.y.append(randint(0, 100))  # Add a new random value.

        self.data_line.setData(self.x, self.y)  # Update the data.
 """


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
