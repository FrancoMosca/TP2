from geopy.geocoders import Nominatim
import folium 
from folium.plugins import MarkerCluster
import math
import webbrowser
import os
import csv
import speech_recognition as sr
import matplotlib.pyplot as gf
import Detector_Patentes as dp


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
        
def direccion_coordenadas(coordenadas):
    coordenadas_str = str(coordenadas[0]) + ", " + str(coordenadas[1])
    mini_dict = {}
    localizador = Nominatim(user_agent="fede")
    ubicacion = localizador.reverse(coordenadas_str)
    if(ubicacion == None):
        return mini_dict 
  
    if(("road" in ubicacion.raw["address"]) and ("house_number" in ubicacion.raw["address"])):
        mini_dict["direccion"] = ubicacion.raw["address"]["road"] + " " + ubicacion.raw["address"]["house_number"]

    if("suburb" in ubicacion.raw["address"]):
        mini_dict["localidad"] = ubicacion.raw["address"]["suburb"]

    if("state" in ubicacion.raw["address"]):
        mini_dict["provincia"] = ubicacion.raw["address"]["state"]

    if("city" in ubicacion.raw["address"]):
        mini_dict["ciudad"] = ubicacion.raw["address"]["city"]

    if("country" in ubicacion.raw["address"]):
        mini_dict["pais"] = ubicacion.raw["address"]["country"]

    return mini_dict

def crear_csv(data):
    headers: list = ['Timestamp','Telefono',
                    'Direccion de la infraccion',
                    'Localidad','Provincia',
                    'Patente','descripcion texto',
                    'descripcion audio']
    with open('registro.csv', 'w') as f:
        write = csv.writer(f)
        write.writerow(headers)
        write.writerows(data)
   
def speech_recognition_API(ruta_audio) -> str:
    r = sr.Recognizer()
    with sr.AudioFile(ruta_audio) as source:
        r.adjust_for_ambient_noise(source)
        audio : str = r.listen(source)
        texto_audio : str = r.recognize_google(audio,language='es-AR')
    return texto_audio

#Punto 1
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

def procesar_radio(datos,coordenadas_dict):
    for i in range(len(datos)):
        coordenadas : list = [float(datos[i]['coord_latitud']),float(datos[i]['coord_long'])]
        for i in range(2):
            if dentro_radio(coordenadas,coordenadas_dict['bombonera'],1000):
                print("entre")
            if dentro_radio(coordenadas,coordenadas_dict['monumental'],1000):
                print("entre")
           
def procesar_cuadrante(datos,coordenadas_dict):
    for i in range(len(datos)):
        coordenadas : list = [float(datos[i]['coord_latitud']),float(datos[i]['coord_long'])]
        if dentro_cuadrante(coordenadas_dict['cuadrante'],coordenadas):
            print("entre")
    
def formatear_datos_csv(datos,caba):
    datos_csv: list[list] = []
    for i in range(len(datos)):
        formato_csv: list = []
        coordenadas : list = [float(datos[i]['coord_latitud']),float(datos[i]['coord_long'])]
        datos_coords = direccion_coordenadas(coordenadas)
        texto_audio = speech_recognition_API((datos[i]['ruta_audio']).rstrip())
        
        formato_csv.append(datos[i]['Timestamp'])
        formato_csv.append(datos[i]['Telefono_celular'])
        formato_csv.append(datos_coords['direccion'])
        formato_csv.append(datos_coords['localidad'])
        formato_csv.append(datos_coords['provincia'])
        formato_csv.append(dp.Patente(datos[i]['ruta_foto']))
        formato_csv.append(datos[i]['descripcion_texto'])
        formato_csv.append(texto_audio)
        
        datos_csv.append(formato_csv)
        
        agregar_infraccion(caba, coordenadas, datos[i]['ruta_foto'])
        
    return datos_csv

def grafico_xy(xy):
    gf.plot(xy.keys(), xy.values())
    gf.title('Cantidad de denuncias mensuales')
    gf.xlabel('Mes')
    gf.ylabel('Cantidad de denuncias')
    gf.xticks(rotation=90,fontsize=9)
    gf.show()
    
def contador_denuncias(datos)-> dict:
    cantidad_de_denuncias: dict = {
        'Enero':0,
        'Febrero':0,
        'Marzo':0,
        'Abril':0,
        'Mayo':0,
        'Junio':0,
        'Julio':0,
        'Agosto':0,
        'Septiembre':0,
        'Octubre':0,
        'Noviembre':0,
        'Diciembre':0   
    }
    mes = '0'
    for i in range(len(datos)):
        mes = str(datos[i]['Timestamp'][16] + datos[i]['Timestamp'][17])
        if mes == '01':
            cantidad_de_denuncias['Enero'] += 1
        elif mes == '02':
            cantidad_de_denuncias['Febrero'] += 1
        elif mes == '03':
            cantidad_de_denuncias['Marzo'] += 1
        elif mes == '04':
            cantidad_de_denuncias['Abril'] += 1
        elif mes == '05':
            cantidad_de_denuncias['Mayo'] += 1
        elif mes == '06':
            cantidad_de_denuncias['Junio'] += 1
        elif mes == '07':
            cantidad_de_denuncias['Julio'] += 1
        elif mes == '08':
            cantidad_de_denuncias['Agosto'] += 1
        elif mes == '09':
            cantidad_de_denuncias['Septiembre'] += 1
        elif mes == '10':
            cantidad_de_denuncias['Octubre'] += 1
        elif mes == '11':
            cantidad_de_denuncias['Noviembre'] += 1
        else:
            cantidad_de_denuncias['Diciembre'] += 1
            
    return cantidad_de_denuncias

def menu(datos,coordenadas_dict)-> None:
    opcion = 0
    while not(opcion == 5):
        print(' 1. Mostrar denuncias realizadas a 1km de los estadios')
        print(' 2. Mostrar todas las infracciones dentro del centro de la ciudad')
        print(' 3. Autos robados')
        print(' 4. Ingresar una patente')
        print(' 5. Mostras mapa cantidad de denuncias recibidas')
        print(' 6. Salir')

        opcion=int(input("Que accion desea realizar?: "))
        
        if (opcion==1):
            procesar_radio(datos,coordenadas_dict)
            
        elif (opcion==2):
            procesar_cuadrante(datos,coordenadas_dict['cuadrante'])
            
        elif (opcion==3):
            print(' **** menu opcion 03 ****')
            
        elif (opcion==4):
            print(' **** menu opcion 04 ****')
                    
        elif (opcion==5):
            cantidad_de_denuncias = contador_denuncias(datos)
            grafico_xy(cantidad_de_denuncias)
        elif (opcion==6):
            print(' **** Saliendo del menu  ****')   
        else:
            print('No existe la opcion')
        

    
