import csv
import speech_recognition as sr

def conexion_csv():
    with open('datos.csv','r',newline='') as datos:
        for linea in datos:
            linea = linea.split(',')
        print(linea)
        ruta = linea[6]
        speech_recognition_API(ruta)
            
        
def speech_recognition_API(ruta):
    r = sr.Recognizer()
    with sr.AudioFile(ruta) as source:
        r.adjust_for_ambient_noise(source)
        audio = r.listen(source)
    print(r.recognize_google(audio,language='es-AR'))

def main():
    conexion_csv()
    
    
    

main()
