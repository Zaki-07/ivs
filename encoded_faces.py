import os
import pickle
from imutils import paths
import cv2
import face_recognition

def encode_faces(dataset_dir="dataset", encodings_file="encodings.pickle"):
    print("[INFO] Quantifying faces...")
    image_paths = list(paths.list_images(dataset_dir))
    
    known_encodings = []
    known_names = []

    for i, image_path in enumerate(image_paths):
        print(f"[INFO] Processing image {i+1}/{len(image_paths)}")
        
        # Extract person name from directory structure
        name = image_path.split(os.path.sep)[-2]

        # Load image and convert to RGB
        image = cv2.imread(image_path)
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Detect face and compute embeddings
        boxes = face_recognition.face_locations(rgb_image)
        encodings = face_recognition.face_encodings(rgb_image, boxes)

        for encoding in encodings:
            known_encodings.append(encoding)
            known_names.append(name)

    # Save encodings to disk
    data = {"encodings": known_encodings, "names": known_names}
    with open(encodings_file, "wb") as f:
        pickle.dump(data, f)

    print("[INFO] Encodings serialized to disk.")

if __name__ == "__main__":
    encode_faces()
