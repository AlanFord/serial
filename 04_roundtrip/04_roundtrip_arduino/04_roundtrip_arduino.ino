/*
Serial roundtrip example
Arduino will listen on serial RX for a signal to toggle an LED
Once LED is toggled the Arduino will send back a step-changing value

Counts from 1 to 10, sending the value to the computer via serial
*/
String inputString = "";      // a String to hold incoming data
bool stringComplete = false;  // whether the string is complete
int counter = 0;
bool brightness = LOW;

void setup() {
  // initialize digital pin LED_BUILTIN as an output.
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, brightness);   // turn the LED off by making the voltage LOW
  //Initialize serial and wait for port to open:
  Serial.begin(9600);
  while (!Serial) {
    ;  // wait for serial port to connect. Needed for native USB port only
  }
}

void loop() {
  if (stringComplete) {
    String workingString = inputString;
    inputString = "";
    stringComplete = false;
    // if it's a capital H (ASCII 72), turn on the LED:
    if (workingString == "H\n") {
      digitalWrite(LED_BUILTIN, HIGH);
    }
    // if it's an L (ASCII 76) turn off the LED:
    if (workingString == "L\n") {
      digitalWrite(LED_BUILTIN, LOW);
    }
    // respond on serial
    counter++;
    if (counter == 11) counter = 0;
    /*
    Serial.print("MAG \t");
    Serial.print(counter);
    Serial.print("\t");
    Serial.print(-counter);
    Serial.print("\t");
    Serial.println(counter+2);
    */
  }
}


/*
  SerialEvent occurs whenever a new data comes in the hardware serial RX. This
  routine is run between each time loop() runs, so using delay inside loop can
  delay response. Multiple bytes of data may be available.
*/
void serialEvent() {
  while (Serial.available()) {
    // get the new byte:
    char inChar = (char)Serial.read();
    // add it to the inputString:
    inputString += inChar;
    // if the incoming character is a newline, set a flag so the main loop can
    // do something about it:
    if (inChar == '\n') {
      stringComplete = true;
      // Serial.println("String complete");
    }
  }
}

