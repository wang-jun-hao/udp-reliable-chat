import sys, zlib
from socket import *


class Bob:

    def __init__(self, port_number):
        self.port_number = port_number
        self.server_socket = socket(AF_INET, SOCK_DGRAM)  # create a socket on Bob's side
        self.server_socket.bind(('localhost', port_number))
        self.expected_seq_num = False  # flips between 0 and 1, start with 0
        self.num_of_data_packets = 0
        self.num_of_corrupt_data_packets = 0

    def read_data(self):
        # loop infinitely to keep listening from socket
        while True:

            # do-while loop until packet is well received
            while True:
                data_packet, client_address = self.server_socket.recvfrom(64)
                self.num_of_data_packets += 1

                if self.is_packet_corrupt(data_packet):
                    self.num_of_corrupt_data_packets += 1

                if self.is_packet_corrupt(data_packet) or \
                        self.has_seq_num_of(int(not self.expected_seq_num), data_packet):
                    # ack last well received packet's seq num
                    prev_feedback_packet = self.create_ack_packet(int(not self.expected_seq_num))
                    self.server_socket.sendto(prev_feedback_packet, client_address)

                if (not self.is_packet_corrupt(data_packet)) and \
                    self.has_seq_num_of(int(self.expected_seq_num), data_packet):
                    # packet is well received
                    # extract
                    payload_of_packet = data_packet[5:]

                    # deliver
                    sys.stdout.write(payload_of_packet.decode())
                    sys.stdout.flush()

                    # send feedback packet
                    feedback_packet = self.create_ack_packet(int(self.expected_seq_num))
                    self.server_socket.sendto(feedback_packet, client_address)

                    # set up for receipt of next packet
                    self.expected_seq_num = not self.expected_seq_num  # alternate between 0 and 1
                    break

    def is_packet_corrupt(self, packet):
        checksum_from_sender = packet[0:4]
        sub_packet_in_bytes = packet[4:]
        checksum_as_computed = zlib.crc32(sub_packet_in_bytes).to_bytes(4, 'big')

        return not checksum_from_sender.__eq__(checksum_as_computed)

    def has_seq_num_of(self, expected_seq_num, feedback_packet):
        seq_num_in_bytes = feedback_packet[4:5]
        seq_num = seq_num_in_bytes.decode()

        seq_num_in_int = int(seq_num)
        return seq_num_in_int == expected_seq_num

    def make_packet(self, packet_pay_load, seq_num_in_int):
        sub_packet = str(seq_num_in_int) + packet_pay_load
        sub_packet_in_bytes = sub_packet.encode()
        checksum = zlib.crc32(sub_packet_in_bytes)
        checksum_in_bytes = checksum.to_bytes(4, 'big')
        packet_in_bytes = checksum_in_bytes + sub_packet_in_bytes

        return packet_in_bytes

    def create_ack_packet(self, last_well_received_seq_num):
        return self.make_packet("", last_well_received_seq_num)

    def run(self):
        bob.read_data()


try:
    bob = Bob(int(sys.argv[1]))
    bob.run()
except KeyboardInterrupt:
    # write corruption rate
    writer = open("Bob.txt", "w")
    writer.write(format(bob.num_of_corrupt_data_packets / bob.num_of_data_packets, '.2f'))
    writer.flush()
    writer.close()
