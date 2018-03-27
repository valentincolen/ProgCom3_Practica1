import argparse
import logging
import socket

# Creation of an ArgumentParser object with description of the program.
parser = argparse.ArgumentParser(
    description='Client to connect to an UDP or TCP server, it also collect execution data into a log file with advanced logging')

parser.add_argument('--ipserver', '-i', help='Ip of the server where you connect', type=str)
parser.add_argument('--message', '-m',
                    help='Request action to the server', type=str,
                    choices=['switch_on', 'switch_off', 'status'])
parser.add_argument('--type', '-t', help='Type of client', type=str, choices=['TCP', 'UDP'])
parser.add_argument('--path', '-pt', help='Specify the path where the log is saved', default='', type=str)
parser.add_argument('--file_name', '-f', help='Name of the log file', default='client', type=str)


# Class that include the commons between TCP and UDP
class Client:
    def __init__(self, server_ip, filename, logpath, protocol):
        # Advanced Logging
        #   Define format
        logformatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
        self.rootLogger = logging.getLogger()
        self.rootLogger.setLevel(logging.DEBUG)
        #   Handler to send messages to disk files
        filehandler = logging.FileHandler("{0}/{1}.log".format(logpath, filename))
        filehandler.setFormatter(logformatter)
        filehandler.setLevel(logging.DEBUG)
        self.rootLogger.addHandler(filehandler)
        #   Handler to send messages to streams like sys.stdout, sys.stderr or any file-like object
        consolehandler = logging.StreamHandler()
        consolehandler.setFormatter(logformatter)
        consolehandler.setLevel(logging.INFO)
        self.rootLogger.addHandler(consolehandler)

        self.sock = socket.socket(socket.AF_INET, protocol)
        self.server_address = (server_ip, 10000)
        self.rootLogger.debug('Socket created')
        self.buffer = 4096

    def close_client(self):
        self.sock.close()
        self.rootLogger.debug('Socket closed')

    #Function to add advanced logging INFO mesages
    def logg_info(self, msg):
        self.rootLogger.info(msg)

    # Function to add advanced logging DEBUG mesages
    def logg_debug(self, msg):
        self.rootLogger.debug(msg)


# Class with inheritance from Client class
class ClientUDP(Client):
    def __init__(self, server_ip, filename, logpath):
        # Inherit from the Client class the init function
        Client.__init__(self, server_ip, filename, logpath, protocol=socket.SOCK_DGRAM)

    # Send data through UDP protocol
    def send_data(self, message):
        self.logg_debug('Sending data')
        self.sock.sendto(message, self.server_address)
        self.logg_debug('Data sent')

    # Receive data through UDP protocol
    def receive_data(self):
        self.logg_debug('Waiting for data')
        received_data, server_ip = self.sock.recvfrom(4096)
        self.logg_debug('Data received')
        return [received_data, server_ip]


class ClientTCP(Client):
    def __init__(self, server_ip, filename, logpath):
        Client.__init__(self, server_ip, filename, logpath, protocol=socket.SOCK_STREAM)

    def connection(self):
        self.sock.connect(self.server_address)
        self.logg_debug('Connection done')

    def send_data_connected(self, msg_to_send):
        self.sock.sendall(msg_to_send)
        self.logg_debug('Data sent')

    def receive_data_connected(self):
        self.logg_debug('Waiting for data')
        new_data = self.sock.recv(self.buffer)
        self.logg_debug('New data received')
        return new_data


def treat_action(msg_to_send):
    if msg_to_send == 'switch_on':
        return 'ON'
    elif msg_to_send == 'switch_off':
        return 'OFF'
    elif msg_to_send == 'status':
        return 'STAT'


def cliudp():
    client = ClientUDP(args.ipserver, args.file_name, args.path)
    try:
        msg_to_send = treat_action(args.message)
        client.logg_debug(msg_to_send)
        client.send_data(msg_to_send)
        [data, server] = client.receive_data()
        if data:
            client.logg_info(data)
    finally:
        client.close_client()


def clitcp():
    client = ClientTCP(args.ipserver, args.file_name, args.path)
    try:
        client.connection()
        msg_to_send = treat_action(args.message)
        client.send_data_connected(msg_to_send)
        msg_received = client.receive_data_connected()
        client.logg_info(msg_received)

    finally:
        client.close_client()


if __name__ == "__main__":
    args = parser.parse_args()
    if args.type == 'TCP':
        clitcp()
    elif args.type == 'UDP':
        cliudp()
