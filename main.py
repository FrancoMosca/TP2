import csv
import speech_recognition as sr

def crear_csv(texto_audio):
    headers: list = ['Timestamp','Telefono',
                    'Direccion de la infraccion',
                    'Localidad','Provincia',
                    'Patente','descripcion texto',
                    'descripcion audio']
    registro = open("registro.csv", "w")
    writer = csv.DictWriter(
        registro, fieldnames= headers)
    writer.writeheader()
    registro.close()
   
def speech_recognition_API(ruta_audio) -> str:
    r = sr.Recognizer()
    with sr.AudioFile(ruta_audio) as source:
        r.adjust_for_ambient_noise(source)
        audio : str = r.listen(source)
        texto_audio : str = r.recognize_google(audio,language='es-AR')
        print(texto_audio)
    
    return texto_audio

def procesamiento_csv() -> None:
    datos_dict : list[dict] = []
    with open('datos.csv','r',newline='') as datos:
        next(datos)
        for linea in datos:
            linea = linea.split(',')
            dato = {
                "Timestamp":linea[0],
                "Telefono_celular":linea[1],
                "coord_latitud":linea[2],
                "coord_long":linea[3],
                "ruta_foto":linea[4],
                "descripcion_texto":linea[5],
                "ruta_audio":linea[6]
            }
            datos_dict.append(dato)
    return datos_dict
        

def main():
    datos = procesamiento_csv()
    for i in range(len(datos)):
        texto_audio = speech_recognition_API(datos[i]['ruta_audio'])
        crear_csv(texto_audio)

main()
