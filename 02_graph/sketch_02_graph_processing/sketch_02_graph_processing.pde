// Graphing sketch

//Reference:  https://hellocircuits.com/2013/10/04/arduino-to-processing-graphing-multiple-sensors/

// This program takes ASCII-encoded strings from the serial port at 9600 baud
// and graphs them. It expects values in the range 0 to 10, followed by a
// newline, or newline and carriage return

import processing.serial.*;

Serial myPort;        // The serial port

int numValues = 2; // number of input values or sensors
// * change this to match how many values your Arduino is sending *


float[] values = new float[numValues];
String[] strings = new String[numValues+1];
int[] min = new int[numValues];
int[] max = new int[numValues];
color[] valColor = new color[numValues];

float partH; // partial screen height

int xPos = 0; // horizontal position of the graph
boolean clearScreen = true; // flagged when graph has filled screen


void setup () {
  // set the window size:
  size(800, 600);
  partH = height / numValues;

  // List all the available serial ports
  // if using Processing 2.1 or later, use Serial.printArray()
  printArray(Serial.list());
  // First port [0] in serial list is usually Arduino, but *check every time*:
  String portName = Serial.list()[5];
  myPort = new Serial(this, portName, 9600);

  // don't generate a serialEvent() unless you get a newline character:
  myPort.bufferUntil('\n');

  // set initial background:
  background(0);
  noStroke();

  // initialize:
  // *edit these* to match how many values you are reading, and what colors you like
  values[0] = 0;
  min[0] = 0;
  max[0] = 10; // full range example, e.g. any analogRead
  valColor[0] = color(255, 0, 0); // red

  values[1] = 0;
  min[1] = -10;
  max[1] = 0;  // partial range example, e.g. IR distance sensor
  valColor[1] = color(0, 255, 0); // green

  /*
   values[2] = 0;
   min[2] = 0;
   max[2] = 1;    // digital input example, e.g. a button
   valColor[2] = color(0, 0, 255); // blue
   // example for adding a 4th value:
   values[3] = 0;
   min[3] = 0;
   max[3] = 400; // custom range example
   valColor[3] = color(255, 0, 255); // purple
   */
}

void draw () {
  // In the Arduino website example, everything is done in serialEvent.
  // Here, data is handled in serialEvent, and drawing is handled in draw()
  // When drawing every loop in draw(), you can see gaps when not updating as fast as data comes in
  // When drawing in serialEvent(), you can see frequency of data updates reflected in how fast graph moves
  // (either method can work)

  if (clearScreen) {
    // two options for erasing screen, i like the translucent option to see "history"
    // erase screen with black:
    background(0);

    // or, erase screen with translucent black:
    //fill(0,200);
    //noStroke();
    //rect(0,0,width,height);

    clearScreen = false; // reset flag
  }

  for (int i=0; i<numValues; i++) {

    // map to the range of partial screen height:
    float mappedVal = map(values[i], min[i], max[i], 0, partH);

    // draw lines:
    stroke(valColor[i]);
    line(xPos, partH*(i+1), xPos, partH*(i+1) - mappedVal);

    // draw dividing line:
    stroke(255);
    line(0, partH*(i+1), width, partH*(i+1));

    // display values on screen:
    fill(50);
    noStroke();
    rect(0, partH*i+1, 70, 12);
    fill(255);
    text(round(values[i]), 2, partH*i+10);
    fill(125);
    text(max[i], 40, partH*i+10);

    //print(i + ": " + values[i] + "\t"); // <- uncomment this to debug values in array
    //println("\t"+mappedVal); // <- uncomment this to debug mapped values
  }
  //println(); // <- uncomment this to read debugged values easier

  // increment the graph's horizontal position:
  xPos++;
  // if at the edge of the screen, go back to the beginning:
  if (xPos > width) {
    xPos = 0;
    clearScreen = true;
  }
}

void serialEvent (Serial myPort) {
  try {
    // get the ASCII string:
    String inString = myPort.readStringUntil('\n');
    // println("raw: \t" + inString); // <- uncomment this to debug serial input from Arduino

    if (inString != null) {
      // trim off any whitespace:
      inString = trim(inString);

      // split the string on the delimiters and convert the resulting substrings into an float array:
      // values = float(splitTokens(inString, ", \t")); // delimiter can be comma space or tab
      strings = splitTokens(inString, ", \t"); // delimiter can be comma space or tab
      if (strings[0].equals("WOG")) { // bad serial data
        values = float(subset(strings, 1)); // skip the "WOG" string
        // if the array has at least the # of elements as your # of sensors, you know
        //   you got the whole data packet.
        if (values.length >= numValues+1) {
          /* you can increment xPos here instead of in draw():
           xPos++;
           if (xPos > width) {
           xPos = 0;
           clearScreen = true;
           }
           */
        }
      }
    }
  }
  catch(RuntimeException e) {
    // only if there is an error:
    e.printStackTrace();
  }
}
