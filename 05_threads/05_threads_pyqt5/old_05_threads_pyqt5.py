"""
Read stream of lines from an Arduino. This
produces 2 values per line every 500ms. Each line looks like:
WOG   1.00    -2.00
with each data line starting with "WOG" and each field separated by
tab characters. Values are integers in ASCII encoding.
"""

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


class ThreadedClient(object):
    """
    Launch the main part of the GUI and the worker thread.  periodicCall and
    endApplication could reside in the GUI part, but putting them here
    means that you have all the thread controls in a single place.
    """
    def __init__(self, master, serialPort):
        """
        Start the GUI and the asynchronous threads.  We are in the main
        (original) thread of the application, which will later be used by
        the GUI as well.  We spawn a new thread for the worker (I/O).
        """
        self.master = master
        self.serialPort = serialPort
        # Create the queue
        self.queue = queue.Queue()
        # Set up the GUI part
        self.gui = GuiPart(master, self.queue, self.endApplication, serialPort)
        # Set up the thread to do asynchronous I/O
        # More threads can also be created and used, if necessary
        self.running = True
        self.thread1 = threading.Thread(target=self.workerThread1)
        self.thread1.start()
        # Start the periodic call in the GUI to check the queue
        self.periodicCall()

    def periodicCall(self):
        """ Check every 200 ms if there is something new in the queue. """
        self.master.after(200, self.periodicCall)
        self.gui.processIncoming()
        if not self.running:
            # This is the brutal stop of the system.  You may want to do
            # some cleanup before actually shutting it down.
            sys.exit(1)

    def workerThread1(self):
        """
        This is where we handle the asynchronous I/O.  For example, it
        may be a 'select()'.  One important thing to remember is that the
        thread has to yield control pretty regularly, be it by select or
        otherwise.
        """
        while self.running:
            if self.serialPort.inWaiting() != 0:
                # Caution: the following line is BLOCKING
                line = self.serialPort.readline()
                self.queue.put(line)

    def endApplication(self):
        self.running = False


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
