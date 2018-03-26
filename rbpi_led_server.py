import argparse
import socket

import RPi.GPIO as GPIO

parser = argparse.ArgumentParser(description='Program that create an UDP or TCP Server ')
parser.add_argument('--pin', '-p', help='Pin where is connected the led', type=int)
parser.add_argument('--ip', help='', default='0.0.0.0', type=str)
parser.add_argument('--type', '-t', help='Type of server. Available: TCP, UDP', type=str)


class Server:
    def __init__(self, pin, ip, protocol):
        self.pin = pin
        self.server_address = (ip, 10000)
        self.sock = socket.socket(socket.AF_INET, protocol)
        self.sock.bind(self.server_address)
        print '\nSocket bound'

    def close_server(self):
        self.sock.close()
        print 'Socket closed'


class ServerUDP(Server):
    def __init__(self, pin, ip):
        Server.__init__(self, pin, ip, socket.SOCK_DGRAM)

    def receive_data(self):
        print '\nWaiting for data...'
        self.data, self.client_address = self.sock.recvfrom(4096)
        return self.data

    def send_data(self, information_to_send, destinatary):
        print 'Sending to ' + self.client_address[0]
        self.sock.sendto(information_to_send, destinatary)
        print 'Data sent'


class ServerTCP(Server):
    def __init__(self, pin, ip):
        Server.__init__(self, pin, ip, socket.SOCK_STREAM)
        self.sock.listen(1)  # This will start the server to 'listen' for new connections

    def accept_conections(self):
        self.connection, self.client_address = self.sock.accept()


    def receive_data_connected(self):
        data = self.connection.recv(4096)
        return data
        
    def send_data_connected(self, message):
        self.connection.sendall(message)

    def close_connection(self):
        self.connection.close()


def check_status(pin):
    return GPIO.input(pin)


def get_led_status(pin):
    print 'Checking status'
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


def check_order(data_to_treat, pin):
    if data_to_treat == 'STAT':
        return get_led_status(pin)
    elif data_to_treat == 'ON':
        return switch_on(pin)
    elif data_to_treat == 'OFF':
        return switch_off(pin)


def pin_conf(pin):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin, GPIO.OUT)


def servudp():
    servu = ServerUDP(args.pin, args.ip)
    pin_conf(servu.pin)
    try:
        while True:
            data_to_treat = servu.receive_data()
            print 'New data received\n'
            msg_to_send = check_order(data_to_treat, servu.pin)
            servu.send_data(msg_to_send, servu.client_address)
    finally:
        servu.close_server()


def servtcp():
    servt = ServerTCP(args.pin, args.ip)
    pin_conf(servt.pin)
    while True:
        print 'Waiting for a new connection'
        servt.accept_conections()
        print 'Connection accepted'
        try:
            msg_received = servt.receive_data_connected()
            msg_to_send = check_order(msg_received, servt.pin)
            servt.send_data_connected(msg_to_send)
        finally:
            servt.close_connection()
            print 'Connection closed'


if __name__ == "__main__":
    args = parser.parse_args()
    if args.type == 'TCP':
        servtcp()
    elif args.type == 'UDP':
        servudp()
    else:
        print 'Wrong type. Available:\nTCP\nUDP\n'
