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
    Worker thread
    """

    result = pyqtSignal(str)

    def __init__(self, initial_counter):
        super().__init__()
        self.counter = initial_counter

    @pyqtSlot()
    def run(self):
        """
        Your code goes in this method
        """
        self.is_running = True
        self.waiting_for_data = True
        while True:
            while self.waiting_for_data:
                if not self.is_running:
                    return  # Exit thread.
                time.sleep(0.1)  # wait for data <1>.

            # Output the number as a formatted string.
            self.counter += self.input_add
            self.counter *= self.input_multiply
            # self.result.emit(f"The cumulative total is {self.counter}")
            self.waiting_for_data = True

    def send_data(self, add, multiply):
        """
        Receive data onto internal variable.
        """
        self.input_add = add
        self.input_multiply = multiply
        self.waiting_for_data = False

    def stop(self):
        self.is_running = False


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Create thread and start it.
        self.thread = Thread(500)
        self.thread.start()

        # Create the push buttons
        button1 = QPushButton("START")
        button2 = QPushButton("STOP")
        button3 = QPushButton("Done")
        button1.pressed.connect(self.start_button)
        button2.pressed.connect(self.stop_button)
        button3.pressed.connect(self.done_button)

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

        self.timer = QTimer()
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.update_plot_data)
        self.timer.start()

        # Window layout
        container = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(button1)
        layout.addWidget(button2)
        layout.addWidget(button3)
        layout.addWidget(self.status)
        layout.addWidget(self.graphWidget)
        container.setLayout(layout)

        # Start the Show!
        self.setCentralWidget(container)
        self.show()

    def stop_button(self):
        """
        Event handler for the Stop button
        """
        # note the string termination
        # self.serialPort.write(bytes('L\n', 'UTF-8'))
        self.status.setText("STOP pressed")

    def start_button(self):
        """
        Event handler for the Start button
        """
        # note the string termination
        # self.serialPort.write(bytes('H\n', 'UTF-8'))
        self.status.setText("START pressed")

    def done_button(self):
        # Shutdown the thread nicely.
        self.thread.stop()
        # Terminate the exec_ loop
        QCoreApplication.quit()

    def update_plot_data(self):

        self.x = self.x[1:]  # Remove the first y element.
        self.x.append(
            self.x[-1] + 1
        )  # Add a new value 1 higher than the last.

        self.y = self.y[1:]  # Remove the first
        self.y.append(randint(0, 100))  # Add a new random value.

        self.data_line.setData(self.x, self.y)  # Update the data.


app = QApplication(sys.argv)
window = MainWindow()
app.exec_()
