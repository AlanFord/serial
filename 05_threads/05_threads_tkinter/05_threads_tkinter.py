"""
Reference: https://arduino.stackexchange.com/questions/17486/graph-plotting-on-python-using-tkinter-canvas
Reference: https://www.oreilly.com/library/view/python-cookbook/0596001673/ch09s07.html

Read stream of lines from an Arduino. This
produces 2 values per line every 500ms. Each line looks like:
WOG   1.00    -2.00
with each data line starting with "WOG" and each field separated by
tab characters. Values are integers in ASCII encoding.
"""
import sys
import tkinter as tk
import time
import threading
import queue
from serial import Serial, SerialException


class GuiPart(tk.Frame):
    """
    The primary frame for all widgets.  In this case it contains
    all of the gui for the application.  The
    parent window is generically instantiated by the main routine
    prior to the instatiation of GuiPart
    """
    def __init__(self, parent, queue, endCommand, serialPort):
        """
        Intializes the primary tkinter frame
        Arguments:
            parent - the parent window
            queue - the Queue of string received from the microcontroller
            endCommand - command that can be used to terminate the application
        """
        tk.Frame.__init__(self, parent)

        # queue holding strings collected by the serial thread
        self.queue = queue

        self.parent = parent
        self.serialPort = serialPort
        # stop the microcontroller (if it's currently running),
        # empty the serial buffer,
        # and empty the queue (just in case)
        self.stop_button()
        self.serialPort.reset_input_buffer()
        with self.queue.mutex:
            self.queue.queue.clear()

        # these lists hold data for the two lines to be plotted
        self.npoints = 100
        self.Line1 = [0 for x in range(self.npoints)]
        self.Line2 = [0 for x in range(self.npoints)]

        # configure the geometry of parent window
        self.parent.wm_title("Smooth Sailing")
        self.parent.wm_geometry("800x600")
        self.parent.grid_rowconfigure(0, weight=1)
        self.parent.grid_columnconfigure(0, weight=1)

        # configure self (the primary Frame)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=2)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid(sticky="news")

        # configure the "start" button
        button1state = tk.Button(self,
                                 text="START",
                                 command=self.start_button,
                                 height=4,
                                 width=8)
        button1state.grid(row=0, column=0, ipadx=10, padx=10, pady=15)

        # configure the "stop" button
        button2state = tk.Button(self,
                                 text="STOP",
                                 command=self.stop_button,
                                 height=4,
                                 width=8)
        button2state.grid(row=0, column=1, ipadx=10, padx=10, pady=15)

        # configure the "done" button
        button3state = tk.Button(self,
                                 text='Done',
                                 command=endCommand,
                                 height=4,
                                 width=8)
        button3state.grid(row=0, column=2, ipadx=10, padx=10, pady=15)
        # close the thread if the window is closed
        # instead of using the "Done" button
        self.parent.protocol("WM_DELETE_WINDOW", endCommand)

        # configure the canvas for plotting data
        self.canvas = tk.Canvas(self, background="white")
        self.canvas.bind("<Configure>", self.on_resize)
        self.canvas.create_line((0, 0, 0, 0), tag='X',
                                fill='darkblue', width=1)
        self.canvas.create_line((0, 0, 0, 0), tag='Y',
                                fill='darkred', width=1)
        self.canvas.grid(row=1, column=0, columnspan=3,
                         sticky=tk.N + tk.E + tk.W + tk.S)
        self.canvasHalfHeight = self.canvas.winfo_height()/2
        self.canvasWidth = self.canvas.winfo_width()

    def stop_button(self):
        """
        Event handler for the Stop button
        """
        # note the string termination
        self.serialPort.write(bytes('L\n', 'UTF-8'))

    def start_button(self):
        """
        Event handler for the Start button
        """
        # note the string termination
        self.serialPort.write(bytes('H\n', 'UTF-8'))

    def on_resize(self, event):
        """
        Event handler for a window Resize event
        """
        self.canvasHalfHeight = self.canvas.winfo_height()/2
        self.canvasWidth = self.canvas.winfo_width()
        self.replot()

    def replot(self):
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
            coordsX.append(hh * (1 + self.Line1[n] / max_all))
            # coordsX.append(h - ((h * (self.Line1[n]+100)) / max_all))
            coordsY.append(x)
            coordsY.append(hh * (1 + self.Line2[n] / max_all))
            # coordsY.append(h - ((h * (self.Line2[n]+100)) / max_all))
        self.canvas.coords('X', *coordsX)
        self.canvas.coords('Y', *coordsY)

    def processIncoming(self):
        """
        Handle all messages currently in the queue, if any.
        """
        while self.queue.qsize():
            try:
                msg = self.queue.get(0)
                msg = msg.decode('ascii').strip("\r\n")
                # Check contents of message,
                # append values to the list, and replot.
                if msg[0:3] != "WOG":
                    print("Bad Message: ", msg)  # line not valid
                else:
                    try:
                        data = msg.split("\t")
                        x, y = data[1], data[2]
                        self.append_values(x, y)
                        self.after_idle(self.replot)
                    except Exception as e:
                        print(e)
            except queue.Empty:
                # just on general principles, although we don't expect this
                # branch to be taken in this case, ignore this exception!
                pass

    def append_values(self, x, y):
        """
        Update the cached data lists with new sensor values.
        Updating is performed by appending the new sensor values
        to the end of the data lists and then extracting a subset
        of npoints starting at the end of the list (i.e. dropping
        the first value)
        """
        self.Line1.append(float(x))
        self.Line1 = self.Line1[-1 * self.npoints:]

        self.Line2.append(float(y))
        self.Line2 = self.Line2[-1 * self.npoints:]
        return


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
    port, baudrate = '/dev/tty.usbmodem14101', 9600  # uno
    # port, baudrate = '/dev/tty.usbmodem14103', 9600  # stm32
    root = tk.Tk()
    try:
        serialPort = Serial(port, baudrate, rtscts=True)
        print("Reset Arduino")
        time.sleep(2)
    except SerialException:
        print("Sorry, invalid serial port.\n")
        print("Did you update it in the script?\n")
        sys.exit(1)
    client = ThreadedClient(root, serialPort)
    root.mainloop()


if __name__ == '__main__':
    main()
