# This is the Trapduino Base Station program.
# It receives LoRa radio messages from the trap nodes 
# and then sends the data recieved to the Adafruit IO service
# and a notification email if the trap is triggered.

import config
import board
import busio
import digitalio
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Import Adafruit LoRa Python library
import adafruit_rfm9x

# import Adafruit IO REST client.
from Adafruit_IO import Client, Feed, RequestError

# start an instance of the Adafruit IO REST client
aio = Client(config.ADAFRUIT_IO_USERNAME, config.ADAFRUIT_IO_KEY)

# send email function
def emailme(trapname):
    fromaddr = config.MAILUSERNAME
    toaddr = "john_mccartney@hotmail.com,oscar.mccartney@queenstown.school.nz"
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = "TrapDuino"
    
    body = trapname + " has been triggered."
    msg.attach(MIMEText(body, 'plain'))
    
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(fromaddr, config.MAILPASSWORD)
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    server.quit()
    
# Define radio parameters.
# Frequency of the radio in Mhz. This must match our
# module! Can be a value like 915.0, 433.0, etc.
RADIO_FREQ_MHZ = 915.0

# Define pins connected to the chip
CS = digitalio.DigitalInOut(board.D5)
RESET = digitalio.DigitalInOut(board.D6)

# Initialize SPI bus.
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

# Initialze RFM radio
rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, RADIO_FREQ_MHZ)

# Adjust the transmit power (in dB).  The default is 13 dB but
# high power radios like the RFM95 can go up to 23 dB:
rfm9x.tx_power = 23

# Wait to receive packets.  
print('Waiting for packets...')
while True:
    # Wait to receive packets for timeout period of 10 seconds:
    packet = rfm9x.receive(timeout=10.0)
    # If no packet was received during the timeout then None is returned.
    if packet is None:
        print('Received nothing! Listening again...')
    else:
        # Received a packet!
        # Print out the raw bytes of the packet:
        print('Received (raw bytes): {0}'.format(packet))
        # Send reply
        rfm9x.send(bytes("Message Received!\r\n", "utf-8"))
        # And decode to ASCII text and print it too.  
        try:
            packet_text = str(packet, 'ascii')
        except:
            print(
                "There was an error during conversion of the received packet")
        else:
            print('Received (ASCII): {0}'.format(packet_text))
            # Also read the RSSI (signal strength) of the last received message
            # and print it.
            rssi = rfm9x.rssi
            print('Received signal strength: {0} dB'.format(rssi))
            # Extract the Trap information from the paacket
            print("Trap is: "+packet_text[:6])
            # Extract the state of the trap from the packet
            # 0 means the trap is live
            # 1 means the trap has been triggered
            print("State is: "+packet_text[7])
            # Extract the battery voltage from the packet
            print("Battery voltage is: "+packet_text[9:13])
            # Get list of feeds
            feeds = aio.feeds()
            # Check to see if there is an appropriate feed for our data
            # corresponding to the trap sending the data.
            try:
                trapfeed = aio.feeds('trapduino-'+packet_text[:6].lower())
            except:  # print error message
                print("The feed does not exist")
            else:
                # Get the current feed value and see if it has changed
                data = aio.receive(trapfeed.key)
                if int(data.value) != int(packet_text[7]):
                    # It's changed so update the feed value
                    aio.send_data(trapfeed.key, int(packet_text[7]))
                    # If its triggered then send an email
                    if int(packet_text[7]) == 1:
                        emailme(packet_text[:6])
                try:  # if we have a trap battery feed
                    trapbattfeed = aio.feeds(
                        'trapduino-'+packet_text[:6].lower()+'-batt')
                except RequestError:  # create a digital feed
                    feed = Feed(
                        name='trapduino-'+packet_text[:6].lower()+'-batt')
                    trapbattfeed = aio.create_feed(feed)
                # Check to see if we have a valid voltage number
                try:
                    voltage = float(packet_text[9:13])
                except:
                    print("Error converting voltage to float")
                else:
                    aio.send_data(trapbattfeed.key, voltage)
                    try:  # if we have a trap rssi feed
                        traprssifeed = aio.feeds(
                            'trapduino-'+packet_text[:6].lower()+'-rssi')
                    except RequestError:  # create a digital feed
                        feed = Feed(
                            name='trapduino-'+packet_text[:6].lower()+'-rssi')
                        traprssifeed = aio.create_feed(feed)
                    # Check to see if we have a valid RSSI number
                    # RSSI is the Received Signal Strength
                    try:
                        rssidata = float(rssi)
                    except:
                        print("Error converting rssi to float")
                    else:
                        aio.send_data(traprssifeed.key, rssidata)