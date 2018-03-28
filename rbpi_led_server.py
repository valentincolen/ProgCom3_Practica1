import argparse
import logging
import socket

import RPi.GPIO as GPIO

# Creation of an ArgumentParser object with description of the program.
parser = argparse.ArgumentParser(
    description='Program that create an UDP or TCP Server, it it also collect execution data into a log file with advanced logging')
parser.add_argument('--pin', '-p', help='Pin where is connected the led', type=int)
# With IP 0.0.0.0 the server can listen to any IP from their interfaces.
parser.add_argument('--ip', help='IP of the server', default='0.0.0.0', type=str)
parser.add_argument('--type', '-t', help='Type of server', type=str, choices=['TCP', 'UDP'])
parser.add_argument('--path', '-pt', help='Specify the path where the log is saved', default='', type=str)
parser.add_argument('--file_name', '-f', help='Name of the log file', default='server', type=str)


# Class that include the commons between TCP and UDP
class Server:
    def __init__(self, pin, ip, log_path, file_name, protocol):
        # Advanced Logging
        #   Define format
        logformatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
        self.rootLogger = logging.getLogger()
        self.rootLogger.setLevel(logging.DEBUG)
        #   Handler to send messages to disk files
        filehandler = logging.FileHandler("{0}/{1}.log".format(log_path, file_name))
        filehandler.setFormatter(logformatter)
        filehandler.setLevel(logging.DEBUG)
        self.rootLogger.addHandler(filehandler)
        #   Handler to send messages to streams like sys.stdout, sys.stderr or any file-like object
        consolehandler = logging.StreamHandler()
        consolehandler.setFormatter(logformatter)
        consolehandler.setLevel(logging.INFO)
        self.rootLogger.addHandler(consolehandler)

        self.pin = pin
        self.server_address = (ip, 10000)
        # Socket creation
        self.sock = socket.socket(socket.AF_INET, protocol)
        self.rootLogger.debug('Socket created')
        # Socket binding
        self.sock.bind(self.server_address)
        self.rootLogger.debug('Socket bound')

    def close_server(self):
        # Socket close
        self.sock.close()
        self.rootLogger.debug('Socket closed')


# Class with inheritance from Server class
class ServerUDP(Server):
    def __init__(self, pin, ip, log_path, file_name):
        # Inherit from the Server class the init function
        Server.__init__(self, pin, ip, log_path, file_name, protocol=socket.SOCK_DGRAM)

    # Receive data through UDP protocol.
    def receive_data(self):
        self.rootLogger.info('Waiting for data...')
        self.data, self.client_address = self.sock.recvfrom(4096)
        self.rootLogger.info('New data received from ' + self.client_address[0])
        return self.data

    # Send data through UDP protocol.
    def send_data(self, information_to_send, receiver):
        self.rootLogger.info('Sending to ' + self.client_address[0])
        self.sock.sendto(information_to_send, receiver)
        self.rootLogger.debug('Data sent')


# Class with inheritance from Server class
class ServerTCP(Server):
    def __init__(self, pin, ip, log_path, file_name):
        # Inherit from the Server class the init function
        Server.__init__(self, pin, ip, log_path, file_name, protocol=socket.SOCK_STREAM)
        # Listen for incoming connections
        self.sock.listen(1)
        self.rootLogger.debug('Listening...')

    # Wait for a connection.
    def accept_connections(self):
        self.rootLogger.info('Waiting for a new connection')
        self.connection, self.client_address = self.sock.accept()
        self.rootLogger.debug('Connected to ' + self.client_address[0])

    # Receive data through TCP protocol.
    def receive_data_connected(self):
        data = self.connection.recv(4096)
        return data

    # Send data through TCP protocol.
    def send_data_connected(self, message):
        self.rootLogger.info('Sending to ' + self.client_address[0])
        self.connection.sendall(message)

    # Close the connection.
    def close_connection(self):
        self.connection.close()
        self.rootLogger.debug('Connection with ' + self.client_address[0] + ' closed')


# Check the state of the pin selected.
def check_status(pin):
    return GPIO.input(pin)


# Check actual pin state to perform the right action
def get_led_status(pin):
    if check_status(pin):
        return 'LED is ON'
    else:
        return 'LED is OFF'


def switch_on(pin):
    if check_status(pin):
        return 'ERR: LED is already ON'
    else:
        GPIO.output(pin, GPIO.HIGH)
        return ''


def switch_off(pin):
    if not check_status(pin):
        return 'ERR: LED is already OFF'
    else:
        GPIO.output(pin, GPIO.LOW)
        return ''


# Treat information with available orders in order to send smaller packets
def check_order(data_to_treat, pin):
    if data_to_treat == 'STAT':
        return get_led_status(pin)
    elif data_to_treat == 'ON':
        return switch_on(pin)
    elif data_to_treat == 'OFF':
        return switch_off(pin)


# Configure the mode of the pin and set it up as a output.
def pin_conf(pin):
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(pin, GPIO.OUT)


def servudp():
    servu = ServerUDP(args.pin, args.ip, args.path, args.file_name)  # Create an instance of the ServerUDP class
    pin_conf(servu.pin)
    try:
        # Call the different functions to receive data and do the action asked
        while True:
            data_to_treat = servu.receive_data()
            msg_to_send = check_order(data_to_treat, servu.pin)
            servu.send_data(msg_to_send, servu.client_address)
    finally:
        servu.close_server()


def servtcp():
    servt = ServerTCP(args.pin, args.ip, args.path, args.file_name)
    pin_conf(servt.pin)
    while True:
        servt.accept_connections()
        try:
            msg_received = servt.receive_data_connected()
            msg_to_send = check_order(msg_received, servt.pin)
            servt.send_data_connected(msg_to_send)
        finally:
            servt.close_connection()


if __name__ == "__main__":
    # Create an instance from the parser library.
    args = parser.parse_args()
    # Depending on the type selected a server transport protocol will be chosen
    if args.type == 'TCP':
        servtcp()
    elif args.type == 'UDP':
        servudp()
