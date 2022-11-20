from geopy.geocoders import Nominatim
import folium 
from folium.plugins import MarkerCluster
import math
import webbrowser
import os
import csv
import speech_recognition as sr

def haversine(coordenada1, coordenada2):
    rad=math.pi/180
    dlat=coordenada2[0] - coordenada1[0]
    dlon=coordenada2[1] - coordenada1[1]
    R=6372.795477598
    a=(math.sin(rad*dlat/2))**2 + math.cos(rad*coordenada1[0])*math.cos(rad*coordenada2[0])*(math.sin(rad*dlon/2))**2
    distancia=2*R*math.asin(math.sqrt(a))
    return distancia

#usar esta funcion para el radio
def dentro_radio(coordenada1, coordenada2, radio) -> bool:
    if(haversine(coordenada1, coordenada2) <= radio):
        return True
    return False


def dentro_cuadrante(cuadrante, coordenada):
    if( coordenada[1] > cuadrante['callao_rivadavia'][1] 
        and coordenada[1] > cuadrante['callao_cordoba'][1]
        and coordenada[1] < cuadrante['alem_rivadavia'][1] 
        and coordenada[1] < cuadrante['alem_cordoba'][1]
        
        and coordenada[0] > cuadrante['callao_rivadavia'][0] 
        and coordenada[0] > cuadrante['alem_rivadavia'][0]
        and coordenada[0] < cuadrante['callao_cordoba'][0] 
        and coordenada[0] < cuadrante['alem_cordoba'][0]
        ):
            return True
    return False

def crear_mapa(centro_mapa, bombonera, monumental, cuadrante):
    caba = folium.Map(location=centro_mapa, zoom_start=13)
    
    folium.Circle(location = bombonera, radius = 1000, color = "blue", fill = True).add_to(caba)
    folium.Circle(location = monumental, radius = 1000, color = "blue", fill = True).add_to(caba)

    folium.Marker(  location = bombonera, popup = folium.Popup("""<h1>La bombonera</h1><br/>
                    <img src="bombonera.jpg"  style="max-width:100%;max-height:100%">""", max_width=500),
                    icon=folium.Icon(color="blue", icon = "home")
                    ).add_to(caba)
    
    folium.Marker(  location = monumental, popup = folium.Popup("""<h1>El monumental</h1><br/>
                    <img src="monumental.jpg"  style="max-width:100%;max-height:100%">""", max_width=500), 
                    icon=folium.Icon(color="blue", icon = "home")
                    ).add_to(caba)

    folium.Marker(location = cuadrante['callao_rivadavia'], popup = folium.Popup(f"""<h1>Callao y Rivadavia</h1><br/>"""), icon=folium.Icon(color="green", icon = "pushpin")).add_to(caba)
    folium.Marker(location = cuadrante['callao_cordoba'], popup = folium.Popup(f"""<h1>Callao y Cordoba</h1><br/>"""), icon=folium.Icon(color="green", icon = "pushpin")).add_to(caba)
    folium.Marker(location = cuadrante['alem_rivadavia'], popup = folium.Popup(f"""<h1>Alem y Rivadavia</h1><br/>"""), icon=folium.Icon(color="green", icon = "pushpin")).add_to(caba)
    folium.Marker(location = cuadrante['alem_cordoba'], popup = folium.Popup(f"""<h1>Alem y Cordoba</h1><br/>"""), icon=folium.Icon(color="green", icon = "pushpin")).add_to(caba)

    return caba

def agregar_infraccion(caba, coordenadas, ruta_imagen):
    isFile = os.path.isfile(ruta_imagen)
    if(ruta_imagen == None or isFile == False):
        folium.Marker(location = coordenadas, icon=folium.Icon(color="red", icon = "exclamation-sign")).add_to(caba)
    else:
        folium.Marker(  location = coordenadas, popup = folium.Popup(f"""<h1>Infraccion</h1><br/>
                        <img src={ruta_imagen}  style="max-width:100%;max-height:100%">""", max_width=500), 
                        icon=folium.Icon(color="red", icon = "exclamation-sign")
                        ).add_to(caba)

def crear_csv(Timestamp,Telefono,descripcion_texto,texto_audio):
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

def procesamiento_csv() -> list[dict]:
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
