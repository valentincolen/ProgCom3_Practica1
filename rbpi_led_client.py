import argparse
import socket

parser = argparse.ArgumentParser(
    description='Client to connect to the server ')  # Creation of an ArgumentParser object with description of the program.

parser.add_argument('--ipserver', '-i', help='Ip of the server where you connect', type=str)
parser.add_argument('--message', '-m',
                    help='Request action to the server. Actions available: switch_on, switch_off, status', type=str)
parser.add_argument('--type', '-t', help='Type of client. Available: TCP, UDP', type=str)


class Client:
    def __init__(self, protocol, server_ip):
        self.sock = socket.socket(socket.AF_INET, protocol)
        self.server_address = (server_ip, 10000)
        print 'Socket created'
        self.buffer = 4096

    def close_client(self):
        self.sock.close()
        print 'Socket closed'


class ClientUDP(Client):
    def __init__(self, server_ip):
        Client.__init__(self, socket.SOCK_DGRAM, server_ip)

    def send_data(self, message):
        self.sock.sendto(message, self.server_address)
        print 'Data sent'

    def receive_data(self):
        print 'Waiting for data'
        received_data, server_ip = self.sock.recvfrom(4096)
        print 'Data received'
        return [received_data, server_ip]


class ClientTCP(Client):
    def __init__(self, server_ip):
        Client.__init__(self, socket.SOCK_STREAM, server_ip)

    def connection(self):
        self.sock.connect(self.server_address)
        print 'Connection done'

    def send_data_connected(self, msg_to_send):
        self.sock.sendall(msg_to_send)
        print 'Data sent'

    def receive_data_connected(self):
        print 'Waiting for data'
        return self.sock.recv(self.buffer)


def treat_action():
    msg_to_send = args.message
    while msg_to_send != ('swittch_on' or 'switch_off' or 'status'):
        if msg_to_send == 'switch_on':
            return 'ON'
        elif msg_to_send == 'switch_off':
            return 'OFF'
        elif msg_to_send == 'status':
            return 'STAT'
        else:
            msg_to_send = raw_input('Wrong action. Actions available:\nswitch_on\nswitch_off\nstatus\n')


def cliudp():
    client = ClientUDP(args.ipserver)
    try:
        msg_to_send = treat_action()
        client.send_data(msg_to_send)
        [data, server] = client.receive_data()
        if data:
            print data
    finally:
        client.close_client()


def clitcp():
    client = ClientTCP(args.ipserver)
    try:
        client.connection()
        msg_to_send = treat_action()
        client.send_data_connected(msg_to_send)
        msg_received = client.receive_data_connected()
        print msg_received

    finally:
        client.close_client()


if __name__ == "__main__":
    args = parser.parse_args()
    if args.type == 'TCP':
        clitcp()
    elif args.type == 'UDP':
        cliudp()
    else:
        print'Wrong type. Available:\nTCP\nUDP\n'
