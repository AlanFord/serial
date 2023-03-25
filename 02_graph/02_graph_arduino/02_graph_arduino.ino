/*
Basic sketch to test serial transmission from microcontroller to arduino ide

Counts from 1 to 10, sending the value to the computer via serial
*/
void setup() {
  //Initialize serial and wait for port to open:
  Serial.begin(9600);
  while (!Serial) {
    ;  // wait for serial port to connect. Needed for native USB port only
  }
}

void loop() {
  for (int i = 0; i < 11; i++) {
    Serial.print("WOG \t");
    Serial.print(i);
    Serial.print("\t");
    Serial.println(-i);
    delay(500);
  }
}
