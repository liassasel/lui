import socket
import threading
import cv2
import numpy as np
import pygame
from pygame.locals import *
import os


#Config Server
IP = "0.0.0.0"
PORT_VIDEO = 9998
PORT_INPUT = 9999
PORT_FILE = 9997 

pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Pantalla Luis")

def receive_video():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(( IP, PORT_VIDEO ))
    sock.listen(1)
    conn, addr = sock.accept()
    
    while True: 
        size_data = conn.recv(4)
        if not size_data:
            break
        size = int.from_bytes(size_data, byteorder="big")
        
        frame_data = b""
        while len(frame_data) < size:
            packet = conn.recv(size - len(frame_data))
            if not packet:
                break
            frame_data += packet
            
        frame = cv2.imdecode(np.frombuffer(frame_data, dtype=np.uint8), cv2.IMREAD_COLOR)
        if frame is not None:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (800, 600))
            pygame_frame = pygame.image.frombuffer(frame.tobytes(), frame.shape[1::-1], "RGB")
            screen.blit(pygame_frame, (0, 0))
            pygame.display.flip()
            
    conn.close()
    
    def send_input_events(): 
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(( IP, PORT_INPUT ))
        
        while True:
            for event in pygame.event.get():
                if event.type == KEYDOWN:
                    sock.send(f"keydown:{event.key}".encde())
                elif event.type == KEYUP:
                    sock.send(f"keyup:{event.key}".encde())
                elif event.type == MOUSEMOTION:
                    x, y = event.pos
                    sock.send(f"mouse_move:{x}:{y}".encode())
                elif event.type == MOUSEBUTTONDOWN:
                    sock.send(f"mouse_click:{event.button}".encode())
                    
    def request_file(file_path):
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(( IP, PORT_FILE ))
        sock.send(file_path.encode())
        
        output_path = os.path.basename(file_path)
        with open(output_path, "wb")as f:
            while True:
                data = sock.recv(1024)
                if not data:
                    break
                f.write(data)
                
        print(f"Archivo/carpeta '{output_path}' descargado.")
        sock.close()
        
    if __name__ == "__main__":
        
        video_thread = threading.Thread(target=receive_video)
        input_thread = threading.Thread(target=send_input_events)
        
        video_thread.start()
        input_thread.start()