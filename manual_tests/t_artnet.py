# WIP, not working

if __name__ == "__main__":
    IP_ADDRESS = "192.168.188.21"
    PIXEL_COUNT = 144 * 4

    artnet = ArtnetTransmitter(IP_ADDRESS)

    matrix_red = np.full((PIXEL_COUNT, 3), [255, 0, 0], dtype=np.uint8)
    matrix_blue = np.full((PIXEL_COUNT, 3), [0, 0, 255], dtype=np.uint8)
    matrix_black = np.full((PIXEL_COUNT, 3), [0, 0, 0], dtype=np.uint8)

    # Test packet transmission using a strobe (red, pause, blue)
    frames_per_second = 50
    seconds = 2
    for i in range(seconds * frames_per_second):
        output_matrix = matrix_red
        if i % 2 == 0:
            output_matrix = matrix_black
        elif i % 3 == 0:
            output_matrix = matrix_blue
        artnet.transmit_matrix(output_matrix)
        time.sleep(1 / frames_per_second)

    # Test packet transmission using a running dot
    matrix = np.zeros((PIXEL_COUNT, 3), dtype=np.uint8)
    for i in range(PIXEL_COUNT):
        matrix[i] = [255, 0, 255]
        artnet.transmit_matrix(matrix)
        matrix[i] = [0, 0, 0]
        time.sleep(1 / frames_per_second)

    artnet.transmit_matrix(matrix)
