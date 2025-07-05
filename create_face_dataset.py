import os
import cv2
import face_recognition

def create_face_dataset(person_name, dataset_dir="dataset"):
    """
    Captures frames from the default webcam and saves images (with drawn face bounding boxes)
    into a folder named dataset/<person_name>/. Press 's' to save the current frame and 'q' to quit.
    """
    # Create a directory for the person if it doesn't exist
    person_dir = os.path.join(dataset_dir, person_name)
    os.makedirs(person_dir, exist_ok=True)

    # Start capturing video from the webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Could not open the webcam.")
        return

    print(f"[INFO] Starting capture for '{person_name}'.")
    print("[INFO] Press 's' to save a frame, 'q' to quit.")

    image_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[ERROR] Failed to grab a frame from the camera.")
            break

        # Convert the frame to RGB for face detection
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Detect face locations in the frame
        boxes = face_recognition.face_locations(rgb_frame)

        # Draw bounding boxes for each detected face
        for (top, right, bottom, left) in boxes:
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

        # Display the frame
        cv2.imshow("Create Face Dataset", frame)
        key = cv2.waitKey(1) & 0xFF

        # Save the frame if 's' is pressed and at least one face is detected
        if key == ord('s'):
            if len(boxes) > 0:
                image_count += 1
                save_path = os.path.join(person_dir, f"{person_name}_{image_count}.jpg")
                cv2.imwrite(save_path, frame)
                print(f"[INFO] Saved {save_path}")
            else:
                print("[INFO] No face detected in the frame. Try again.")

        # Exit if 'q' is pressed
        if key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("[INFO] Dataset collection complete.")

if __name__ == "__main__":
    person_name = input("Enter the name of the person to capture: ").strip()
    if not person_name:
        print("[ERROR] No name entered. Exiting.")
    else:
        create_face_dataset(person_name)

