# Microcontroller Serial Examples

This project is an attempt to catalog several methods for monitoring the output 
of a microcontroller, not just watching the output scroll-by on a serial
terminal.

Each folder documents a separate method - some simple, some more complex.  

Note that python scripts that open a serial port A) do not specify a timeout, and B) set rtscts=True.  These result in proper communication with an Arduino Uno, but do not interfere with proper communication with an STM32 NUCLEO board.  This test has been run on MacOS - if problems occur with Windows or Linux try removing rtscts=True.

1. 01_send - A basic Arduino sketch sending data to a serial connection.  Serial output can be monitored on the Arduino IDE Serial Monitor.  This is what I would eventually like to avoid. It has been tested on both an Arduino Uno as well as an STM32 NUCLEO 746ZG board.

2. 02_graph - An arduino sketch sending data to be plotted on a computer.  Two methods of displaying the results are provided - a processing sketch and a Python script using Tkinter.  The processing sketch displays two variables in separate live graphs.  The Python script displays both variables overlayed in a single live graph.  Both have been tested on both an Arduino Uno as well as an STM32 NUCLEO 746ZG board.

3. 03_buttons - This doesn't really monitor serial output, but demonstrates the ability to use a graphical application with buttons to control the operation of a microcontroller.  This will be used as a building block in a subsequent method.  A Python script using Tkinter displays two buttons, used to control the state of an LED on the microcontroller board.  This script has been tested with a STM32 NUCLEO 746ZG board.  The script does not currently work with an Arduino Uno.

4. 04_roundtrip - 02_graph and 03_buttons are combined in a single application. Buttons in a Python script are used to control the serial transmission of data from the microcontroller to the Python application.  Data is plotted in the Python Tkinter application as it is received.  This script has been tested with a STM32 NUCLEO 746ZG board and an Arduino Uno.

5. 05_threads - This a more sophisticated version of 04_roundtrip.  The "App" class has been divided into two parts - the "GuiPart" class that handles the buttons and the data display, and the "ThreadedClient" class that handles serial communications in a separate thread.  The ThreadedClient class stores data received from the serial port in a queue; the GuiPart periodically retrieves data from the queue and processes it for display.  This program structure is intended to be somewhat more tolerant of serial communication delays and long message lengths.