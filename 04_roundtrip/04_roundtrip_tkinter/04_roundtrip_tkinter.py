#
# Reference: https://arduino.stackexchange.com/questions/17486/graph-plotting-on-python-using-tkinter-canvas
#
# Read stream of lines from an Arduino. This
# produces 2 values per line every 500ms. Each line looks like:
# WOG   1.00    -2.00
# with each data line starting with "WOG" and each field separated by
# tab characters. Values are integers in ASCII encoding.
#
import sys
import time
import tkinter as tk
from serial import Serial, SerialException


class App(tk.Frame):
    def __init__(self, parent, title, serialPort):
        tk.Frame.__init__(self, parent)
        self.serialPort = serialPort
        self.npoints = 100
        self.Line1 = [0 for x in range(self.npoints)]
        self.Line2 = [0 for x in range(self.npoints)]

        # configure the parent window
        parent.wm_title(title)
        parent.wm_geometry("800x600")
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)

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

        # configure the canvas for plotting data
        self.canvas = tk.Canvas(self, background="white")
        self.canvas.bind("<Configure>", self.on_resize)
        self.canvas.create_line((0, 0, 0, 0), tag='X',
                                fill='darkblue', width=1)
        self.canvas.create_line((0, 0, 0, 0), tag='Y',
                                fill='darkred', width=1)
        self.canvas.grid(row=1, column=0, columnspan=2,
                         sticky=tk.N + tk.E + tk.W + tk.S)
        self.canvasHalfHeight = self.canvas.winfo_height()/2
        self.canvasWidth = self.canvas.winfo_width()

    def stop_button(self):
        self.serialPort.write(bytes('L\n', 'UTF-8'))  # note the string termination

    def start_button(self):
        self.serialPort.write(bytes('H\n', 'UTF-8'))  # note the string termination

    def on_resize(self, event):
        self.canvasHalfHeight = self.canvas.winfo_height()/2
        self.canvasWidth = self.canvas.winfo_width()
        self.replot()

    def read_serial(self):
        """
        Check for input from the serial port. On fetching a line, parse
        the sensor values and append to the stored data and post a replot
        request.
        """
        if self.serialPort.inWaiting() != 0:
            # Caution: the following line is BLOCKING
            # Limit the line length of commands
            line = self.serialPort.readline()
            line = line.decode('ascii').strip("\r\n")
            if line[0:3] != "WOG":
                print("Bad Line: ", line)  # line not a valid sensor result.
            else:
                try:
                    data = line.split("\t")
                    x, y = data[1], data[2]
                    self.append_values(x, y)
                    self.after_idle(self.replot)
                except Exception as e:
                    print(e)
        self.after(10, self.read_serial)

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
            coordsY.append(x)
            coordsY.append(hh * (1 + self.Line2[n] / max_all))
        self.canvas.coords('X', *coordsX)
        self.canvas.coords('Y', *coordsY)


def main(args=None):
    if args is None:
        args = sys.argv
    port, baudrate = '/dev/tty.usbmodem14101', 9600  # uno
    # port, baudrate = '/dev/tty.usbmodem14103', 9600  # stm32
    if len(args) > 1:
        port = args[1]
    if len(args) > 2:
        baudrate = int(args[2])
    root = tk.Tk()
    try:
        serialPort = Serial(port, baudrate, rtscts=True)
        print("Reset Arduino")
        time.sleep(2)
    except SerialException:
        print("Sorry, invalid serial port.\n")
        print("Did you update it in the script?\n")
        return 0
    app = App(root, "Smooth Sailing", serialPort)
    app.read_serial()
    app.mainloop()
    return 0


if __name__ == '__main__':
    main()
