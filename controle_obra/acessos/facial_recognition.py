import face_recognition
import cv2
import numpy as np
from pathlib import Path
from django.conf import settings
from funcionarios.models import Funcionario


class FacialRecognitionSystem:
    def __init__(self):
        self.known_face_encodings = []
        self.known_face_names = []
        self.known_funcionario_ids = []
        self.load_funcionarios()

    def load_funcionarios(self):
        funcionarios = Funcionario.objects.filter(foto__isnull=False).exclude(foto='')
        
        for funcionario in funcionarios:
            if funcionario.foto:
                try:
                    foto_path = Path(settings.MEDIA_ROOT) / str(funcionario.foto)
                    image = face_recognition.load_image_file(str(foto_path))
                    face_encodings = face_recognition.face_encodings(image)
                    
                    if face_encodings:
                        self.known_face_encodings.append(face_encodings[0])
                        self.known_face_names.append(funcionario.nome)
                        self.known_funcionario_ids.append(funcionario.id)
                except Exception as e:
                    print(f"Erro ao processar foto de {funcionario.nome}: {e}")

    def recognize_face(self, frame):
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        results = []

        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(
                self.known_face_encodings,
                face_encoding,
                tolerance=0.6
            )
            name = "Desconhecido"
            funcionario_id = None
            confidence = 0.0

            distances = face_recognition.face_distance(
                self.known_face_encodings,
                face_encoding
            )

            if len(distances) > 0:
                best_match_index = np.argmin(distances)
                
                if matches[best_match_index]:
                    name = self.known_face_names[best_match_index]
                    funcionario_id = self.known_funcionario_ids[best_match_index]
                    confidence = 1 - distances[best_match_index]

            results.append((face_locations, name, funcionario_id, confidence))

        return results

    def capture_and_recognize(self):
        cap = cv2.VideoCapture(0)
        recognized = False

        while not recognized:
            ret, frame = cap.read()
            if not ret:
                break

            results = self.recognize_face(frame)

            for face_locs, name, func_id, confidence in results:
                if face_locs:
                    top, right, bottom, left = face_locs[0]
                    
                    top *= 4
                    right *= 4
                    bottom *= 4
                    left *= 4

                    color = (0, 255, 0) if name != "Desconhecido" else (0, 0, 255)

                    cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

                    label = f"{name} ({confidence:.2f})" if confidence > 0 else name
                    cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
                    cv2.putText(frame, label, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)

                    if name != "Desconhecido" and confidence > 0.6:
                        cv2.imshow('Reconhecimento Facial - Pressione Q para sair', frame)
                        cv2.waitKey(500)
                        recognized = True
                        cap.release()
                        cv2.destroyAllWindows()
                        return name, func_id, confidence

            cv2.imshow('Reconhecimento Facial - Pressione Q para sair', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()
        return None
