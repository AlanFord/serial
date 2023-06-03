"""
Read stream of lines from an Arduino. This
produces 2 values per line every 500ms. Each line looks like:
WOG   1.00    -2.00
with each data line starting with "WOG" and each field separated by
tab characters. Values are integers in ASCII encoding.

Three classes are used
    - GraphWidget is a new widget that draws the data plot and is
      easily resizable.
    - MainWindow handles drawing the widgets.  The MainWindow 
      inherits from the classes MW_Ui and MW_Base.  These classes
      are generated driectly from a QtCreator form using
      a call to uic.loadUiType('window.ui').
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
from PyQt5 import uic

MW_Ui, MW_Base = uic.loadUiType('window.ui')


# ==========================================================
class MainWindow(MW_Base, MW_Ui):
    """
    GUI window for the application.
    """

    def __init__(self):
        """MainWindow constructor."""
        super().__init__()
        self.setupUi(self)
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
             '/dev/tty.usbmodem14201',
             '/dev/tty.usbmodem14103',
             '/dev/tty.usbmodem14203']
    if len(args) > 1:
        ports.append(args[1])
    if len(args) > 2:
        baudrate = int(args[2])
    # pick a port, depending on the microcontroller used
    serial_success = False
    for io_unit in ports:
        try:
            print("Trying ", io_unit)
            serialPort = Serial(io_unit, baudrate, rtscts=True)
            serial_success = True
        except SerialException:
            print("Serial exception")
        if serial_success:  # break if connected
            break
    if serial_success:
        return serialPort
    else:
        return None


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
