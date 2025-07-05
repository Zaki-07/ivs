# import smtplib
# import cv2
# import numpy as np
# import os
# import time
# import sqlite3
# import json
# from datetime import datetime
# from email.mime.multipart import MIMEMultipart
# from email.mime.text import MIMEText
# from email.mime.base import MIMEBase
# from email import encoders
# import plyer

# # 🔹 Global settings
# ALERT_INTERVAL = 60  
# last_alert_time = {}  

# # 🔹 Load Camera Settings
# def load_camera_settings():
#     if os.path.exists("camera_settings.json"):
#         with open("camera_settings.json", "r") as f:
#             data = json.load(f)
#             if data and isinstance(data[0], str):
#                 return [{"source": src, "detections": ["motion", "object", "face"]} for src in data]
#             return data
#     else:
#         return [{"source": "0", "detections": ["motion", "object", "face"]}]

# # 🔹 Capture Frame Function
# def capture_frame(cam_id):
#     cap = cv2.VideoCapture(cam_id , cv2.CAP_DSHOW)
#     if not cap.isOpened():
#         print(f"[ERROR] Could not access camera {cam_id}")
#         return None

#     ret, frame = cap.read()
#     cap.release()

#     if ret:
#         image_path = f"alert_frame_cam{cam_id}.jpg"
#         cv2.imwrite(image_path, frame)
#         print(f"[INFO] Frame captured: {image_path}")
#         return image_path
#     else:
#         print("[ERROR] Failed to capture frame.")
#         return None

# # 🔹 Send Email with Attachment
# def send_email_notification(subject, message, attachment_path=None):
#     sender_email = "shafaqali.3101@gmail.com"
#     receiver_email = "khuninha0109@gmail.com"
#     password = "rryc jjyi hcrx pdqg"

#     msg = MIMEMultipart()
#     msg['From'] = sender_email
#     msg['To'] = receiver_email
#     msg['Subject'] = subject
#     msg.attach(MIMEText(message, 'plain'))

#     if attachment_path and os.path.exists(attachment_path):
#         with open(attachment_path, "rb") as attachment:
#             part = MIMEBase("application", "octet-stream")
#             part.set_payload(attachment.read())
#             encoders.encode_base64(part)
#             part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(attachment_path)}")
#             msg.attach(part)
#         print(f"[INFO] Image attached: {attachment_path}")
#     else:
#         print("[WARNING] No image attached.")

#     try:
#         server = smtplib.SMTP('smtp.gmail.com', 587)
#         server.starttls()
#         server.login(sender_email, password)
#         server.sendmail(sender_email, receiver_email, msg.as_string())
#         server.quit()
#         print("[INFO] Email sent successfully.")
#     except Exception as e:
#         print(f"[ERROR] Failed to send email: {e}")

# # 🔹 Send Local Notification
# def send_local_notification(title, message):
#     plyer.notification.notify(
#         title=title,
#         message=message,
#         app_name='Alert System',
#         timeout=10
#     )

# # 🔹 Store Alert in SQLite
# def store_alert(camera, location, message, severity):
#     db_path = os.path.join(os.getcwd(), 'alerts.db')
#     conn = sqlite3.connect(db_path)
#     c = conn.cursor()
#     c.execute('''
#     CREATE TABLE IF NOT EXISTS alerts (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         camera TEXT,
#         location TEXT,
#         time TEXT,
#         message TEXT,
#         severity TEXT
#     )
#     ''')
#     alert_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#     c.execute("INSERT INTO alerts (camera, location, time, message, severity) VALUES (?, ?, ?, ?, ?)",
#               (camera, location, alert_time, message, severity))
#     conn.commit()
#     conn.close()
#     print(f"[INFO] Alert stored: {camera}, {location}, {alert_time}, {message}, {severity}")

# # 🔹 Check Alert Interval
# def can_trigger_alert(cam_id):
#     global last_alert_time
#     current_time = time.time()
    
#     if cam_id not in last_alert_time or (current_time - last_alert_time[cam_id] >= ALERT_INTERVAL):
#         last_alert_time[cam_id] = current_time
#         return True
#     else:
#         print(f"[DEBUG] Skipping alert for Camera {cam_id} due to time restriction.")
#         return False

# # 🔹 Main Alert Processing Function
# def alert_process(object_queue, face_queue, motion_queue):
#     while True:
#         camera_settings = load_camera_settings()

#         # 🔥 Motion Detection Alerts
#         if not motion_queue.empty():
#             motion_alert = motion_queue.get()
#             cam_id = motion_alert.get("cam_id")
#             detection_type = motion_alert.get("detection_type", "motion")

#             if cam_id is not None and cam_id < len(camera_settings):
#                 detections_enabled = camera_settings[cam_id].get("detections", [])
#                 if detection_type in detections_enabled and can_trigger_alert(cam_id):
#                     image_path = capture_frame(cam_id)  # Capture frame
#                     store_alert(f"Camera {cam_id}", "Motion Detection",
#                                 motion_alert.get('message', 'Motion detected'),
#                                 motion_alert.get('severity', 'medium'))
#                     send_email_notification("Motion Detected", motion_alert.get('message', 'Motion detected.'), image_path)
#                     send_local_notification("Motion Detected", motion_alert.get('message', 'Motion detected.'))

#         # 🔥 Object Detection Alerts
#         if not object_queue.empty():
#             obj_event = object_queue.get()
#             cam_id = obj_event.get("cam_id")
#             detection_type = obj_event.get("detection_type", "object")

#             print("[DEBUG] Object event received:", obj_event)  # Debugging log

#             if cam_id is not None and cam_id < len(camera_settings):
#                 detections_enabled = camera_settings[cam_id].get("detections", [])
#                 detections = obj_event.get("detections", [])

#                 if not detections:
#                     print(f"[DEBUG] No objects detected in Camera {cam_id}.")
#                     continue  

#                 if detections_enabled:
#                     detected_objects = ", ".join(obj.get('label', 'Unknown') for obj in detections)
#                     image_path = capture_frame(cam_id)  # Capture frame
#                     store_alert(f"Camera {cam_id}", "Object Detection",
#                                 f"Objects detected: {detected_objects}", "high")
#                     send_email_notification("Object Detected", f"Objects detected: {detected_objects}", image_path)
#                     send_local_notification("Object Detected", f"Objects detected: {detected_objects}")

#         # 🔥 Face Recognition Alerts
#         if not face_queue.empty():
#             face_event = face_queue.get()
#             cam_id = face_event.get("cam_id")
#             detection_type = face_event.get("detection_type", "face")

#             if cam_id is not None and cam_id < len(camera_settings):
#                 detections_enabled = camera_settings[cam_id].get("detections", [])
#                 if detection_type in detections_enabled and can_trigger_alert(cam_id):
#                     detected_name = face_event.get('name', 'Unknown')
#                     image_path = capture_frame(cam_id)  # Capture frame
#                     alert_message = f"Face detected: {detected_name}"
#                     store_alert(f"Camera {cam_id}", "Face Recognition", alert_message, "high")
#                     send_email_notification("Face Detected", alert_message, image_path)
#                     send_local_notification("Face Detected", alert_message)

#         time.sleep(ALERT_INTERVAL)


import smtplib
import cv2
import numpy as np
import os
import time
import sqlite3
import json
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import plyer

# 🔹 Global settings
ALERT_INTERVAL = 60  
last_alert_time = {}  

# 🔹 Load Camera Settings
def load_camera_settings():
    if os.path.exists("camera_settings.json"):
        with open("camera_settings.json", "r") as f:
            data = json.load(f)
            if data and isinstance(data[0], str):
                return [{"source": src, "detections": ["motion", "object", "face"]} for src in data]
            return data
    else:
        return [{"source": "0", "detections": ["motion", "object", "face"]}]

# 🔹 Capture Frame Function (✅ FIXED)
def capture_frame(cam_id):
    cap = cv2.VideoCapture(cam_id, cv2.CAP_DSHOW)
    time.sleep(2)  # ✅ Allow camera to adjust

    if not cap.isOpened():
        print(f"[ERROR] Could not access camera {cam_id}")
        return None

    ret, frame = cap.read()
    cap.release()

    if ret and frame is not None:
        image_path = f"alert_frame_cam{cam_id}.jpg"
        cv2.imwrite(image_path, frame)

        # ✅ Ensure the image is valid before returning
        if os.path.exists(image_path) and os.path.getsize(image_path) > 0:
            print(f"[INFO] Frame captured successfully: {image_path}")
            return image_path
        else:
            print("[ERROR] Captured image is empty or corrupted.")
            return None
    else:
        print("[ERROR] Failed to capture frame.")
        return None

# 🔹 Send Email with Attachment (✅ FIXED)
def send_email_notification(subject, message, attachment_path=None):
    sender_email = "@gmail.com"
    receiver_email = "@gmail.com"
    password = ""

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.attach(MIMEText(message, 'plain'))

    if attachment_path and os.path.exists(attachment_path) and os.path.getsize(attachment_path) > 0:
        with open(attachment_path, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(attachment_path)}")
            msg.attach(part)
        print(f"[INFO] Image attached: {attachment_path}")
    else:
        print("[WARNING] No valid image attached.")

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        print("[INFO] Email sent successfully.")
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")

# 🔹 Send Local Notification
def send_local_notification(title, message):
    plyer.notification.notify(
        title=title,
        message=message,
        app_name='Alert System',
        timeout=10
    )

# 🔹 Store Alert in SQLite
def store_alert(camera, location, message, severity):
    db_path = os.path.join(os.getcwd(), 'alerts.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        camera TEXT,
        location TEXT,
        time TEXT,
        message TEXT,
        severity TEXT
    )
    ''')
    alert_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO alerts (camera, location, time, message, severity) VALUES (?, ?, ?, ?, ?)",
              (camera, location, alert_time, message, severity))
    conn.commit()
    conn.close()
    print(f"[INFO] Alert stored: {camera}, {location}, {alert_time}, {message}, {severity}")

# 🔹 Check Alert Interval
def can_trigger_alert(cam_id):
    global last_alert_time
    current_time = time.time()
    
    if cam_id not in last_alert_time or (current_time - last_alert_time[cam_id] >= ALERT_INTERVAL):
        last_alert_time[cam_id] = current_time
        return True
    else:
        print(f"[DEBUG] Skipping alert for Camera {cam_id} due to time restriction.")
        return False

# 🔹 Main Alert Processing Function (✅ FIXED)
def alert_process(object_queue, face_queue, motion_queue):
    while True:
        camera_settings = load_camera_settings()

        # 🔥 Motion Detection Alerts
        if not motion_queue.empty():
            motion_alert = motion_queue.get()
            cam_id = motion_alert.get("cam_id")
            detection_type = motion_alert.get("detection_type", "motion")

            if cam_id is not None and cam_id < len(camera_settings):
                detections_enabled = camera_settings[cam_id].get("detections", [])
                if detection_type in detections_enabled and can_trigger_alert(cam_id):
                    image_path = capture_frame(cam_id)

                    if image_path:
                        store_alert(f"Camera {cam_id}", "Motion Detection",
                                    motion_alert.get('message', 'Motion detected'),
                                    motion_alert.get('severity', 'medium'))
                        send_email_notification("Motion Detected", motion_alert.get('message', 'Motion detected.'), image_path)
                        send_local_notification("Motion Detected", motion_alert.get('message', 'Motion detected.'))
                    else:
                        print("[ERROR] No valid image captured. Skipping email alert.")

        # 🔥 Object Detection Alerts
        if not object_queue.empty():
            obj_event = object_queue.get()
            cam_id = obj_event.get("cam_id")
            detections = obj_event.get("detections", [])

            if cam_id is not None and cam_id < len(camera_settings) and detections:
                detected_objects = ", ".join(obj.get('label', 'Unknown') for obj in detections)
                image_path = capture_frame(cam_id)

                if image_path:
                    store_alert(f"Camera {cam_id}", "Object Detection",
                                f"Objects detected: {detected_objects}", "high")
                    send_email_notification("Object Detected", f"Objects detected: {detected_objects}", image_path)
                    send_local_notification("Object Detected", f"Objects detected: {detected_objects}")
                else:
                    print("[ERROR] No valid image captured. Skipping email alert.")

        # 🔥 Face Recognition Alerts
        if not face_queue.empty():
            face_event = face_queue.get()
            cam_id = face_event.get("cam_id")
            detected_name = face_event.get('name', 'Unknown')

            if cam_id is not None and cam_id < len(camera_settings):
                image_path = capture_frame(cam_id)

                if image_path:
                    alert_message = f"Face detected: {detected_name}"
                    store_alert(f"Camera {cam_id}", "Face Recognition", alert_message, "high")
                    send_email_notification("Face Detected", alert_message, image_path)
                    send_local_notification("Face Detected", alert_message)
                else:
                    print("[ERROR] No valid image captured. Skipping email alert.")

        time.sleep(ALERT_INTERVAL)
