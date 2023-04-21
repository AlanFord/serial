import sys
from serial import Serial, SerialException
import time
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import \
    QApplication, \
    QMainWindow, \
    QPushButton, \
    QVBoxLayout, \
    QWidget, \
    QLabel


class MainWindow(QMainWindow):
    def __init__(self, serialPort):
        super().__init__()
        self.serialPort = serialPort
        self.setWindowTitle("LED control")
        self.status = QLabel("Starting...")
        self.status.setAlignment(Qt.AlignCenter)
        button1 = QPushButton("On")
        button2 = QPushButton("Off")
        button3 = QPushButton("Quit")
        button1.clicked.connect(self.on_button)
        button2.clicked.connect(self.off_button)
        button3.clicked.connect(self.quit_button)

        # perform the layout
        layout = QVBoxLayout()
        layout.addWidget(self.status)
        layout.addWidget(button1)
        layout.addWidget(button2)
        layout.addWidget(button3)
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def quit_button(self):
        self.serialPort.write(bytes('L', 'UTF-8'))
        # app will close when last (only) window is closed
        self.close()

    def on_button(self):
        self.status.setText("LED ON")
        self.serialPort.write(bytes('H', 'UTF-8'))

    def off_button(self):
        self.status.setText("LED OFF")
        self.serialPort.write(bytes('L', 'UTF-8'))


def main(args=None):
    if args is None:
        args = sys.argv
    if len(args) > 1:
        port = args[1]
    if len(args) > 2:
        baudrate = int(args[2])
    # port, baudrate = '/dev/tty.usbmodem14101', 9600  # uno
    port, baudrate = '/dev/tty.usbmodem14103', 9600  # stm32
    try:
        serialPort = Serial(port, baudrate, rtscts=True)
        print("Reset Arduino")
        time.sleep(2)
    except SerialException:
        print("Sorry, invalid serial port.\n")
        print("Did you update it in the script?\n")
        sys.exit(1)
    serialPort.write(bytes('L', 'UTF-8'))

    app = QApplication(sys.argv)
    window = MainWindow(serialPort)
    window.show()
    app.exec_()


if __name__ == '__main__':
    main()
