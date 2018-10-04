// TrapDuino Transmitter - BrighSparks 2018
// This is code for the trap app for the Feather 32u4 LoRa that checks at regular intervals to see if the trap 
// is triggered by the magnetic reed switch and then sends a message to the base station. 
// The message includes the trap name, whether the trap is loaded or triggered (0 or 1) and the battery voltage.

#include <SPI.h>
#include <RH_RF95.h>

//for feather32u4 set the LoRa module pins 
#define RFM95_CS 8
#define RFM95_RST 4
#define RFM95_INT 7

// The Name of this trap
const String trapname = "Trap02";

// Setup the pin for the magnetic sensor
const int sensor = 12;

// Set the frequency for communicating value, remeber 1000 = 1 second
unsigned long comtime = 60000L;

// Setup the battery voltage reading pin
#define VBATPIN A9

int state; // 0 close - 1 open trap sensor magnetic switch

// Change to 434.0 or other frequency, must match RX's freq!
#define RF95_FREQ 915.0

// Singleton instance of the radio driver
RH_RF95 rf95(RFM95_CS, RFM95_INT);

void setup() 
{
  pinMode(RFM95_RST, OUTPUT);
  digitalWrite(RFM95_RST, HIGH);
  pinMode(sensor, INPUT_PULLUP);

  Serial.begin(115200);
  // while (!Serial) {
  //   delay(1);
  // }

  delay(100);

  Serial.println("Feather LoRa TX Test!");

  // manual reset
  digitalWrite(RFM95_RST, LOW);
  delay(10);
  digitalWrite(RFM95_RST, HIGH);
  delay(10);

  while (!rf95.init()) {
    Serial.println("LoRa radio init failed");
    while (1);
  }
  Serial.println("LoRa radio init OK!");

  // Defaults after init are 434.0MHz, modulation GFSK_Rb250Fd250, +13dbM
  if (!rf95.setFrequency(RF95_FREQ)) {
    Serial.println("setFrequency failed");
    while (1);
  }
  Serial.print("Set Freq to: "); Serial.println(RF95_FREQ);
  
  // Defaults after init are 434.0MHz, 13dBm, Bw = 125 kHz, Cr = 4/5, Sf = 128chips/symbol, CRC on

  // The default transmitter power is 13dBm, using PA_BOOST.
  // If you are using RFM95/96/97/98 modules which uses the PA_BOOST transmitter pin, then 
  // you can set transmitter powers from 5 to 23 dBm:
  rf95.setTxPower(23, false);

}

void loop()
{
  delay(comtime); // Wait the prescribed interval between transmits, could also 'sleep' here!

  // Check if the trap has been triggered
  state = digitalRead(sensor); 
  
  // Measure the power and calculate
  float measuredvbat = analogRead(VBATPIN);
  measuredvbat *= 2;    // we divided by 2, so multiply back
  measuredvbat *= 3.3;  // Multiply by 3.3V, our reference voltage
  measuredvbat /= 1024; // convert to voltage
  
  // Send a message to base
  String radiopacket = trapname + "," + state + "," + String(measuredvbat, 2);
  Serial.print("Sending "); Serial.println(radiopacket);
  int str_len = radiopacket.length() + 1;
  char radpack[str_len];
  radiopacket.toCharArray(radpack, str_len);
  delay(10);
  rf95.send((uint8_t *)radpack, str_len);
  delay(10);
  rf95.waitPacketSent();
}
