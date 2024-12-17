import cv2

def main():
    # Загрузка предобученного каскада для распознавания лиц
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    # Инициализация видеопотока с веб-камеры
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Не удалось получить доступ к веб-камере")
        return

    print("Нажмите 'q' для выхода из программы")

    while True:
        # Считываем кадр с камеры
        ret, frame = cap.read()

        if not ret:
            print("Не удалось считать кадр")
            break

        # Конвертируем кадр в оттенки серого (для ускорения обработки)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Обнаружение лиц на кадре
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        # Отрисовка прямоугольников вокруг обнаруженных лиц
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Отображаем кадр с обведенными лицами
        cv2.imshow('Face Detection', frame)

        # Выход из программы по нажатию 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Освобождаем ресурсы
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

