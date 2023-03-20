# Microcontroller Serial Examples

This project is an attempt to catalog several methods for monitoring the output 
of a microcontroller without just watching the output scroll-by on a serial
terminal.

Each folder documents a separate method - some simple, some more complex.

1. 01_ar_send - A basic Arduino sketch sending data to a serial connection.  This is what we would eventually like to avoid.
2. 02_ar_graph - An arduino sketch sending data to be plotted using a Processing sketch.  Both the Arduino and Processing sketches include multiple comma-delininated data to produce two live plots.
3. 03_ar_graph - Similar to 02_ar_graph but the graphics are handled by Python using the tkinter library.
4. 04_ar_graph - Similar to 02_ar_graph but the graphics are handled by Python using the PyQt5 library.