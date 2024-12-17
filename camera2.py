import cv2

def main():
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 5)

        for (x, y, w, h) in faces:
            face_roi = frame[y:y+h, x:x+w]

            # Применяем тепловой фильтр (color mapping)
            face_roi_colored = cv2.applyColorMap(face_roi, cv2.COLORMAP_JET)

            # Заменяем лицо тепловым фильтром
            frame[y:y+h, x:x+w] = face_roi_colored

        cv2.imshow('Thermal Face Filter', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

