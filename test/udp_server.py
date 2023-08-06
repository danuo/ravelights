import socket


def extract_int_from_udp_packet(data):
    # Assuming data is a bytes object received in the UDP packet
    # The data is 16-bit long (2 bytes) with the lower bit at index 14 and the higher bit at index 15
    # Extract the 16-bit value using bitwise operations
    lower_bit = data[14]
    higher_bit = data[15]
    int_value = (higher_bit << 8) | lower_bit

    return int_value


def start_udp_server(ip, port):
    # Create a UDP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Bind the socket to the specified IP and port
    server_socket.bind((ip, port))
    print(f"UDP server listening on {ip}:{port}")

    while True:
        # Receive data from the client
        data, addr = server_socket.recvfrom(1024)  # 1024 is the buffer size

        # Process the received data
        int_value = extract_int_from_udp_packet(data)
        print(f"Received int value: {int_value} from {addr[0]}:{addr[1]}")


if __name__ == "__main__":
    # Change these values to your desired IP and port
    server_ip = "0.0.0.0"  # Listen on all available interfaces
    server_port = 6454

    start_udp_server(server_ip, server_port)
