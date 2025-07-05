import cv2
import numpy as np
from multiprocessing import shared_memory

def video_capture_process(shm_name, shape, camera_source, cam_id):
    # Determine the source: if it starts with "http" or contains ":" assume an IP stream.
    if isinstance(camera_source, str) and (camera_source.startswith("http") or ":" in camera_source):
        cap = cv2.VideoCapture(camera_source)
    else:
        try:
            cam_index = int(camera_source)
        except ValueError:
            cam_index = 0
        cap = cv2.VideoCapture(cam_index)
    
    shared_mem = shared_memory.SharedMemory(name=shm_name)
    frame_buffer = np.ndarray(shape, dtype=np.uint8, buffer=shared_mem.buf)
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print(f"[ERROR] Unable to read from camera source: {camera_source} (Camera {cam_id})")
                break
            resized_frame = cv2.resize(frame, (shape[1], shape[0]))
            frame_buffer[:] = resized_frame
            # No GUI display in headless mode.
    finally:
        cap.release()

if __name__ == "__main__":
    print("Run main.py to start the system.")

