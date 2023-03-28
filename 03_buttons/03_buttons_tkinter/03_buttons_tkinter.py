import serial
import time
import tkinter


def quit_button():
    global tkTop
    ser.write(bytes('L', 'UTF-8'))
    tkTop.destroy()


def on_button():
    varLabel.set("LED ON ")
    ser.write(bytes('H', 'UTF-8'))


def off_button():
    varLabel.set("LED OFF")
    ser.write(bytes('L', 'UTF-8'))


# change the COM port below
#ser = serial.Serial('/dev/tty.usbmodem14103', 9600, rtscts=True)  # stm32 nucleo
ser = serial.Serial('/dev/tty.usbmodem14101', 9600, rtscts=True)  # arduino
print("Reset Arduino (not really needed for nucleo)")
time.sleep(2)
ser.write(bytes('L', 'UTF-8'))

tkTop = tkinter.Tk()
tkTop.geometry('300x300')  # 300 x 300 window
tkTop.title("LED control")  # name in title bar

# label to display the status
varLabel = tkinter.IntVar()
tkLabel = tkinter.Label(textvariable=varLabel, )
varLabel.set("LED STATUS")
tkLabel.pack()

# button1 - ON
# button1 = tkinter.IntVar()
button1state = tkinter.Button(tkTop,
                              text="ON",
                              command=on_button,
                              height=4,
                              width=8)
button1state.pack(side='top', ipadx=10, padx=10, pady=15)

# button2 - OFF
# button2 = tkinter.IntVar()
button2state = tkinter.Button(tkTop,
                              text="OFF",
                              command=off_button,
                              height=4,
                              width=8)
button2state.pack(side='top', ipadx=10, padx=10, pady=15)

# Quit button
tkButtonQuit = tkinter.Button(
                             tkTop,
                             text="Quit",
                             command=quit_button,
                             height=4,
                             width=8)

tkButtonQuit.pack(side='top', ipadx=10, padx=10, pady=15)
tkinter.mainloop()
