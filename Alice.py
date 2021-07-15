import sys
import zlib
from socket import *

class Alice:

    def __init__(self, port_number):
        self.port_number = port_number
        self.clientSocket = socket(AF_INET, SOCK_DGRAM)  # create a socket on Alice's side
        self.clientSocket.settimeout(0.05)
        self.server_name = 'localhost'
        self.curr_seq_num = False  # flips between 0 and 1, start with 0
        self.num_of_feedback_packets = 0
        self.num_of_corrupt_feedback_packets = 0

    def send_data(self, data):
        # do-while loop for creating packets of 64 bytes from bulk data
        while True:
            # make packet with 58 actual message payload bytes
            packet_pay_load = data[0:58]
            data = data[58:]
            packet = self.make_packet(packet_pay_load, int(self.curr_seq_num))

            # do-while loop for repeated sending of packet until correct ACK is received
            while True:
                try:
                    self.clientSocket.sendto(packet, (self.server_name, self.port_number))
                    feedback_packet, server_address = self.clientSocket.recvfrom(64)

                    self.num_of_feedback_packets += 1

                    if self.is_packet_corrupt(feedback_packet):
                        self.num_of_corrupt_feedback_packets += 1

                    if (not self.is_packet_corrupt(feedback_packet)) and \
                            self.is_ack(int(self.curr_seq_num), feedback_packet):
                        # correct ACK packet received
                        break
                except timeout:
                    continue

            self.curr_seq_num = not self.curr_seq_num  # alternate between 0 and 1

            if len(data) == 0:
                # all data sent through packets
                break

    def make_packet(self, packet_pay_load, seq_num_in_int):
        sub_packet = str(seq_num_in_int) + packet_pay_load
        sub_packet_in_bytes = sub_packet.encode()
        checksum = zlib.crc32(sub_packet_in_bytes)
        checksum_in_bytes = checksum.to_bytes(4, 'big')
        packet_in_bytes = checksum_in_bytes + sub_packet_in_bytes

        return packet_in_bytes

    def is_packet_corrupt(self, packet):
        checksum_from_sender = packet[0:4]
        sub_packet_in_bytes = packet[4:]
        checksum_as_computed = zlib.crc32(sub_packet_in_bytes).to_bytes(4, 'big')

        return not checksum_from_sender.__eq__(checksum_as_computed)

    def is_ack(self, expected_seq_num, feedback_packet):
        seq_num_in_bytes = feedback_packet[4:]
        seq_num = seq_num_in_bytes.decode()

        assert len(seq_num) == 1, "wrong length of seq number"

        seq_num_in_int = int(seq_num)
        return seq_num_in_int == expected_seq_num

    def run(self):
        # question assumes no input delay
        data_to_send = ""

        for line in sys.stdin:
            data_to_send += line

        self.send_data(data_to_send)


alice = Alice(int(sys.argv[1]))
alice.run()

# write corruption rate
writer = open("Alice.txt", "w")
writer.write(format(alice.num_of_corrupt_feedback_packets / alice.num_of_feedback_packets, '.2f'))
writer.flush()
writer.close()


