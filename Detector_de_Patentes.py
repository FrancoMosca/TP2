from geopy.geocoders import Nominatim
import folium 
from folium.plugins import MarkerCluster
import math
import webbrowser
import os
import csv
import speech_recognition as sr
import matplotlib.pyplot as gf
import datetime
import cv2
import numpy as np
import argparse
import time
import imutils
import pytesseract 

def Limpiar_Pantalla():
    """
    Precondiciones: No requiere parametros
    Postcondiciones: Limpia la pantalla donde se este ejecutando
    """

    if os.name == "posix":
        os.system ("clear")
    elif os.name == "ce" or os.name == "nt" or os.name == "dos":
       os.system ("cls")

def Limpieza(Texto_Ingresado:str)->str:
    """
    Precondiciones: Requiere un texto
    Postcondiciones: Devuelve el texto sin alfanumericos, exeptuando las mayusculas y los numeros
    """

    Texto_Ingresado:list = list(Texto_Ingresado)
    Permitidos:list = ["Q","W","E","R","T","Y","U","I","O","P","A","S","D","F","G","H","J","K","L","Ñ","Z","X","C","V","B","N","M","0","1","2","3","4","5","6","7","8","9"]
    Texto_Devuelto:list = []
    for letra in Texto_Ingresado:
        if letra in Permitidos:
            Texto_Devuelto.append(letra)
    Texto_Devuelto = "".join(Texto_Devuelto)

    return Texto_Devuelto

def Aplicar_Filtros(Direccion_Imagen:str):
    """
    Precondiciones: Requiere la direccion de una imagen que exista
    Postcondiciones: Devuelve la imagen a color, en gris y tambien en gris con el filtro canny
    """

    Imagen = cv2.imread(Direccion_Imagen, cv2.IMREAD_COLOR)
    Imagen = cv2.resize(Imagen, (400,400))
    Gris = cv2.cvtColor(Imagen, cv2.COLOR_BGR2GRAY) 
    Gris = cv2.bilateralFilter(Gris, 13, 15, 15) 
    Edged = cv2.Canny(Gris, 30, 200)

    return Imagen, Gris, Edged

def Buscar_Contornos(Imagen)->list:
    """
    Precondiciones: Requiere una imagen
    Postcondiciones: Devuelve una lista ordenada con todos los contornos que se detectan
    """

    Contornos = cv2.findContours(Imagen.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    Contornos = imutils.grab_contours(Contornos)
    Contornos = sorted(Contornos, key = cv2.contourArea, reverse = True)[:10]

    return Contornos

def Buscar_Rectangulo(Contornos):
    """
    Precondiciones: Requiere una lista con contornos de una imagen
    Postcondiciones: Devuelve el contorno mas similar a un rectangulo
    """

    screenCnt = None
    for Cont in Contornos:
        Peri = cv2.arcLength(Cont, True)
        Approx = cv2.approxPolyDP(Cont, 0.018*Peri, True)
        if len(Approx) == 4:
            screenCnt = Approx
            break

    return screenCnt

def Obtener_Alfanumericos(Imagen, Gris, Recorte)->str:
    """
    Precondiciones: Requiere una imagen a color, la misma en gris y el recorte donde se quiere buscar los alfanumericos
    Postcondiciones: Devuelve los alfanumericos del recorte de la imagen
    """

    cv2.drawContours(Imagen, [Recorte], -1, (0, 0, 255), 3)
    Mask = np.zeros(Gris.shape,np.uint8)
    New_Imagen = cv2.drawContours(Mask,[Recorte],0,255,-1,)
    New_Imagen = cv2.bitwise_and(Imagen,Imagen,mask=Mask)
    (x, y) = np.where(Mask == 255)
    (topx, topy) = (np.min(x), np.min(y))
    (bottomx, bottomy) = (np.max(x), np.max(y))
    Cropped = Gris[topx:bottomx+1, topy:bottomy+1]
    Texto:str   = pytesseract.image_to_string(Cropped, config='--psm 11')

    return Texto

def Obtener_Patente(Direccion_Imagen:str)->str:
    """
    Precondiciones: Requiere una direccion de imagen que exista
    Postcondiciones: Devuelve alfanumericos detectados en un contorno similar a un rectangulo de la imagen
    """
    
    Imagen, Gris, Edged = Aplicar_Filtros(Direccion_Imagen)
    Contornos = Buscar_Contornos(Edged)
    screenCnt = Buscar_Rectangulo(Contornos)
    if screenCnt is None:
        Limpiar_Pantalla()
        Patente:str = "¡Error!"
    else:
        Limpiar_Pantalla()
        Texto:str = Obtener_Alfanumericos(Imagen, Gris, screenCnt)
        Patente:str = Limpieza(Texto)

    return Patente 
 
def Cargar_Yolo(Yolo_W, Yolo_C, Coco):
    """
    Precondiciones: Requiere la direccion de 2 archivos para la ejecucion de la red neuronal y un archivo donde esten los nombres de los objetos que esta detecta 
    Postcondiciones: Devuelve caracteristicas al cargar yolov3
    """

    net = cv2.dnn.readNet(Yolo_W, Yolo_C)
    classes = []
    with open(Coco, "r") as f:
        classes = [line.strip() for line in f.readlines()] 
    output_layers = [layer_name for layer_name in net.getUnconnectedOutLayersNames()]
    colors = np.random.uniform(0, 255, size=(len(classes), 3))

    return net, classes, colors, output_layers

def Cargar_Imagen(Direccion_Imagen):
    """
    Precondiciones: Requiere la direccion de una imagen que exita
    Postcondiciones: Devuelve la imagen y caracteristicas de la misma
    """

    Imagen = cv2.imread(Direccion_Imagen)
    Imagen = cv2.resize(Imagen,(600,400))
    height, width, channels = Imagen.shape

    return Imagen, height, width, channels

def Detector_Objetos(Imagen, net, outputLayers):
    """
    Precondiciones: Requiere una imagen y caracteristicas de la misma
    Postcondiciones: Devuelve objetos de la imagen
    """

    blob = cv2.dnn.blobFromImage(Imagen, scalefactor=0.00392, size=(320, 320), mean=(0, 0, 0), swapRB=True, crop=False)
    net.setInput(blob)
    outputs = net.forward(outputLayers)

    return blob, outputs

def Dimencion_Cajas(outputs, height, width):
    """
    Precondiciones: Requiere la ubicacion de los objetos y caracteristicas de la imagen
    Postcondiciones: Devuelve coordenadas de cajas que contienen a cada objeto distinto
    """

    boxes = []
    confs = []
    class_ids = []
    for output in outputs:
        for detect in output:
            scores = detect[5:]
            print(scores)
            class_id = np.argmax(scores)
            conf = scores[class_id]
            if conf > 0.5:
                center_x = int(detect[0] * width)
                center_y = int(detect[1] * height)
                w = int(detect[2] * width)
                h = int(detect[3] * height)
                x = int(center_x - w/2)
                y = int(center_y - h / 2)
                boxes.append([x, y, w, h])
                confs.append(float(conf))
                class_ids.append(class_id)

    return boxes, confs, class_ids

def Recorte_Auto(boxes, confs, class_ids, classes, Imagen):
    """
    Precondiciones: Requiere una imagen y coordenadas de las cajas que contienen a los objetos pertenecientes a la misma imagen
    Postcondiciones: Crea una imagen que solo contiene al auto principal de la imagen ingresada
    """

    indexes = cv2.dnn.NMSBoxes(boxes, confs, 0.5, 0.4)
    font = cv2.FONT_HERSHEY_PLAIN
    try:
        tam_max = boxes[indexes[0]][2]*boxes[indexes[0]][3]
        if tam_max < 0:
            tam_max = tam_max*-1
        for i in range(len(boxes)):
            if i in indexes:
                x, y, w, h = boxes[i]
                tam = w*h
                if tam < 0:
                    tam = tam*-1
                if tam > tam_max:
                    tam_max = tam 
        for i in range(len(boxes)):
            if i in indexes:
                x, y, w, h = boxes[i]
                tam = w*h
                if tam < 0:
                    tam = w*h*-1
                if tam == tam_max:
                    label = str(classes[class_ids[i]])
                    if label == "car" or label == "motorbike" or label == "truck" or label == "bus":
                        cv2.imwrite("Imagen.png",Imagen[y:y+h,x:x+w])
    except:
        print("Las coordenadas no son correctas, no se puede realizar el recorte")

def Validacion(boxes, confs, class_ids, classes)->bool:
    """
    Precondiciones: Requiere coordenadas y el tipo de los objetos
    Postcondiciones: Devuelve True solo si algun objeto es un automovil
    """

    indexes = cv2.dnn.NMSBoxes(boxes, confs, 0.5, 0.4)
    Verificacion = False
    for i in range(len(boxes)):
        if i in indexes:
            label = str(classes[class_ids[i]])
            if label == "car" or label == "motorbike" or label == "truck" or label == "bus":
                Verificacion = True

    return Verificacion

def Detector_Auto(Direccion_Imagen, Yolo_W, Yolo_C, Coco):
    """
    Precondiciones: Requiere la direccion de una imagen que exista, 2 archivos para ejecutar la red neuronal y 1 archivo que contiene los nombres de los objetos reconosibles
    Postcondiciones: Devuelve True si y solo si se detecta un automovil en la imagen
    """

    model, classes, colors, output_layers = Cargar_Yolo(Yolo_W, Yolo_C, Coco)
    image, height, width, channels = Cargar_Imagen(Direccion_Imagen)
    blob, outputs = Detector_Objetos(image, model, output_layers)
    boxes, confs, class_ids = Dimencion_Cajas(outputs, height, width)
    Verificacion = Validacion(boxes, confs, class_ids, classes)
    if Verificacion == True:
        Recorte_Auto(boxes, confs, class_ids, classes, image)

    return Verificacion

def Patente(Direccion_Imagen:str)->str:
    """
    Precondicones: Requiere la direccion de una imagen que exista
    Postcondiciones: Devuelve la patente del auto si es que esta imagen contiene un auto
    """

    Yolo_W:str = "yolov3.weights"
    Yolo_C:str = "yolov3.cfg"
    Coco:str = "coco.names"

    Verificado = Detector_Auto(Direccion_Imagen, Yolo_W, Yolo_C, Coco)
    if Verificado == True:
        Patente = Obtener_Patente("Imagen.png")
        Limpiar_Pantalla()
    else:
        Patente = "¡Error!"

    return Patente

def Abrir_Imagen(Direccion_Imagen):
    """
    Precondiciones: Requiere la direccion de una imagen que exista
    Postcondiciones: Muestra en pantalla la imagen ingresada
    """

    Imagen = cv2.imread(Direccion_Imagen,cv2.IMREAD_COLOR)
    Imagen = cv2.resize(Imagen, None, fx=0.4, fy=0.4)
    cv2.imshow('Auto.jpg',Imagen)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def Dentro_Radio(coordenada1:list, coordenada2:list, radio:float)->bool:
    """
    Precondicion: Recibe 2 coordenadas y un radio
    Postcondicion: Devuelve True solo si la coordenada 1 se encuentra a una distancia menor al radio de la coordenada 2
    """

    Verificacion = False
    rad=math.pi/180
    dlat=coordenada2[0] - coordenada1[0]
    dlon=coordenada2[1] - coordenada1[1]
    R=6372.795477598
    a=(math.sin(rad*dlat/2))**2 + math.cos(rad*coordenada1[0])*math.cos(rad*coordenada2[0])*(math.sin(rad*dlon/2))**2
    distancia=2*R*math.asin(math.sqrt(a))
    if distancia <= radio:
        Verificacion = True

    return Verificacion

def Dentro_Cuadrante(cuadrante:dict, coordenada:list)->bool:
    """
    Precondicion: Recibe un diccionario con las coordenadas que definen un cuadrante y una coordenada
    Postcondicion: Devuelve True solo si la coordenada se encuentra dentro del cuadrante
    """

    Verificacion = False
    if( coordenada[1] > cuadrante['callao_rivadavia'][1] 
        and coordenada[1] > cuadrante['callao_cordoba'][1]
        and coordenada[1] < cuadrante['alem_rivadavia'][1] 
        and coordenada[1] < cuadrante['alem_cordoba'][1]
        
        and coordenada[0] > cuadrante['callao_rivadavia'][0] 
        and coordenada[0] > cuadrante['alem_rivadavia'][0]
        and coordenada[0] < cuadrante['callao_cordoba'][0] 
        and coordenada[0] < cuadrante['alem_cordoba'][0]
        ):
            Verificacion = True

    return Verificacion

def Crear_Mapa(Centro_Mapa:list, Bombonera:list, Monumental:list, Cuadrante:dict):
    """
    Precondicion: Recibe coordenadas de 3 ubicaciones y un diccionario con 4 coordenadas que definen un cuadrante
    Postcondicion: Devuelve un mapa centrado en la 1 coordanada con las 2 siguientes ubicaciones marcadas junto a una circunferencia de 1000 metros ademas del cuadrante
    """

    Mapa = folium.Map(location=Centro_Mapa, zoom_start=13)
    folium.Circle(location = Bombonera, radius = 1000, color = "blue", fill = True).add_to(Mapa)
    folium.Circle(location = Monumental, radius = 1000, color = "blue", fill = True).add_to(Mapa)
    folium.Marker(location = Bombonera, popup = folium.Popup("""<h1>La bombonera</h1><br/>
                  <img src="bombonera.jpg"  style="max-width:100%;max-height:100%">""", max_width=500),
                  icon=folium.Icon(color="blue", icon = "home")).add_to(Mapa)
    folium.Marker(location = Monumental, popup = folium.Popup("""<h1>El monumental</h1><br/>
                  <img src="monumental.jpg"  style="max-width:100%;max-height:100%">""", max_width=500), 
                  icon=folium.Icon(color="blue", icon = "home")).add_to(Mapa)
    folium.Marker(location = Cuadrante['callao_rivadavia'], popup = folium.Popup(f"""<h1>Callao y Rivadavia</h1><br/>"""), icon=folium.Icon(color="green", icon = "pushpin")).add_to(Mapa)
    folium.Marker(location = Cuadrante['callao_cordoba'], popup = folium.Popup(f"""<h1>Callao y Cordoba</h1><br/>"""), icon=folium.Icon(color="green", icon = "pushpin")).add_to(Mapa)
    folium.Marker(location = Cuadrante['alem_rivadavia'], popup = folium.Popup(f"""<h1>Alem y Rivadavia</h1><br/>"""), icon=folium.Icon(color="green", icon = "pushpin")).add_to(Mapa)
    folium.Marker(location = Cuadrante['alem_cordoba'], popup = folium.Popup(f"""<h1>Alem y Cordoba</h1><br/>"""), icon=folium.Icon(color="green", icon = "pushpin")).add_to(Mapa)

    return Mapa

def Agregar_Infraccion(caba, coordenadas:list , ruta_imagen:str):
    """
    Precondicion: Recibe un mapa, una coordenada y una dirrecion de una imagen
    Postcondicion: Devuele el mapa con la coordenada marcada, y en esta la imagen ingresada si es que existe
    """

    isFile = os.path.isfile(ruta_imagen)
    if(ruta_imagen == None or isFile == False):
        folium.Marker(location = coordenadas, icon=folium.Icon(color="red", icon = "exclamation-sign")).add_to(caba)
    else:
        folium.Marker(  location = coordenadas, popup = folium.Popup(f"""<h1>Infraccion</h1><br/>
                        <img src={ruta_imagen}  style="max-width:100%;max-height:100%">""", max_width=500), 
                        icon=folium.Icon(color="red", icon = "exclamation-sign")
                        ).add_to(caba)
        
def Direccion_Coordenadas(coordenadas:list)->dict:
    """
    Precondicion: Recibe una coordenada
    Postcondicion: Devuelve un diccionario con la direccion, localidad, provincia, ciudad y pais de la ubicacion marcada por la coordenada
    """

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

def Crear_csv(data:list[list]):
    """
    Precondicion: Recibe una lista de listas que contiene informacion
    Postcondicion: Crea un csv con un header y toda la informacion
    """

    headers: list = ['Timestamp','Telefono',
                    'Direccion de la infraccion',
                    'Localidad','Provincia',
                    'Patente','descripcion texto',
                    'descripcion audio']
    with open('registro.csv', 'w') as f:
        write = csv.writer(f)
        write.writerow(headers)
        write.writerows(data)        
   
def speech_recognition_API(ruta_audio:str)->str:
    """
    Precondicion: Recibe una ruta de un audio
    Postcondicion: Devuelve un texto con todo lo que se dice en el audio
    """

    r = sr.Recognizer()
    with sr.AudioFile(ruta_audio) as source:
        r.adjust_for_ambient_noise(source)
        audio : str = r.listen(source)
        texto_audio : str = r.recognize_google(audio,language='es-AR')
    
    return texto_audio

def Procesamiento_csv(Direccion_Datos)->list[dict]:
    """
    Precondicion: Recibe la direccion de un csv con header
    Postcondicion: Devuelve un diccionario con toda la informacion que contiene
    """

    with open(Direccion_Datos,'r',newline='') as D:
        cont:int = 0
        for linea in D:
            if cont == 0:
                linea = linea.rstrip()
                linea = linea.split(',')
                Titulo = linea
            cont = cont+1 

    Datos:list[dict] = []
    with open(Direccion_Datos,'r',newline='') as D:    
        next(D)
        for linea in D:
            linea = linea.rstrip()
            linea = linea.split(',')
            dato = {
                Titulo[0]:linea[0],
                Titulo[1]:linea[1],
                Titulo[2]:linea[2],
                Titulo[3]:linea[3],
                Titulo[4]:linea[4],
                Titulo[5]:linea[5],
                Titulo[6]:linea[6]}
            Datos.append(dato)
    
    return Datos

def Procesar_Radio(datos:list[dict],coordenadas_dict:dict):
    """
    Precondicion: Requiere una lista de datos que tengan las coordenadas de los autos y un diccionario con las coordenadas de la bombonera y el monumental
    Postcondicion: Imprime cuales son los autos que se encuentran a 1 km de la bombonera o de la monumental
    """

    Patentes:dict = {}
    with open('registro.csv','r',newline='') as R:
        next(R)
        cont:int = 0
        for linea in R:
            linea = linea.rstrip()
            linea = linea.split(',')
            Patentes[cont] = linea[5]
            cont=cont+1

    for i in range(len(datos)):
        coordenadas : list = [float(datos[i]['coord_latitud']),float(datos[i]['coord_longitud'])]
        if Dentro_Radio(coordenadas,coordenadas_dict['monumental'],1):
            print(f"El auto: {Patentes[i]} se encuentra a 1km de la monumental")
        elif Dentro_Radio(coordenadas,coordenadas_dict['bombonera'],1):
            print(f"El auto: {Patentes[i]} se encuentra a 1km de la bombonera")
           
def Procesar_Cuadrante(datos,coordenadas_dict):
    """
    Precondicion: Recibe datos que contiene coordenadas y un diccionario con las coordenadas de un cuadrante
    Postcondicion: Imprime cuales coordenadas se encuentran dentro del cuadrante
    """

    Patentes:dict = {}
    with open('registro.csv','r',newline='') as R:
        next(R)
        cont:int = 0
        for linea in R:
            linea = linea.rstrip()
            linea = linea.split(',')
            Patentes[cont] = linea[5]
            cont=cont+1
    for i in range(len(datos)):
        coordenadas : list = [float(datos[i]['coord_latitud']),float(datos[i]['coord_longitud'])]
        if Dentro_Cuadrante(coordenadas_dict,coordenadas):
            print(F"El auto: {Patentes[i]} se encuentra en el cuadrante")
    
def Formatear_Datos_csv(datos:list ,caba):
    """
    Precondicion: Recibe una lista de datos y un mapa
    Postcondicion: Devuelve nuevos datos para otro csv
    """

    Nuevos_Datos: list[list] = []
    for i in range(len(datos)):
        formato_csv: list = []
        coordenadas : list = [float(datos[i]['coord_latitud']),float(datos[i]['coord_longitud'])]
        datos_coords = Direccion_Coordenadas(coordenadas)
        texto_audio = speech_recognition_API((datos[i]['ruta_audio']).rstrip())

        formato_csv.append(datos[i]['Timestamp'])
        formato_csv.append(datos[i]['Telefono'])
        formato_csv.append(datos_coords['direccion'])
        formato_csv.append(datos_coords['localidad'])
        formato_csv.append(datos_coords['provincia'])
        formato_csv.append(Patente(datos[i]['ruta_foto']))
        formato_csv.append(datos[i]['descripcion_texto'])
        formato_csv.append(texto_audio)

        Nuevos_Datos.append(formato_csv)
        Agregar_Infraccion(caba, coordenadas, datos[i]['ruta_foto'])
        
    return Nuevos_Datos

def grafico_xy(xy:dict):
    """
    Precondicion: Recibe un diccionario con la cantidad de denuncias por mez 
    Postcondicion: Imprime en pantalla un grafico de la cantidad de denuncias en funcion del mez
    """

    gf.plot(xy.keys(), xy.values())
    gf.title('Cantidad de denuncias mensuales')
    gf.xlabel('Mes')
    gf.ylabel('Cantidad de denuncias')
    gf.xticks(rotation=90,fontsize=9)
    gf.show()
    
def contador_denuncias(datos:list)-> dict:
    """
    Precondicion: Recibe una lista de datos que contiene la fecha de las denuncias
    Postcondicion: Devuelve un diccionario con la cantidad de denuncias por mez
    """

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
        fecha = datetime.datetime.strptime(datos[i]['Timestamp'],'%Y-%m-%d %H:%M:%S')
        mes = fecha.month
        
        if mes == 1:
            cantidad_de_denuncias['Enero'] += 1
        elif mes == 2:
            cantidad_de_denuncias['Febrero'] += 1
        elif mes == 3:
            cantidad_de_denuncias['Marzo'] += 1
        elif mes == 4:
            cantidad_de_denuncias['Abril'] += 1
        elif mes == 5:
            cantidad_de_denuncias['Mayo'] += 1
        elif mes == 6:
            cantidad_de_denuncias['Junio'] += 1
        elif mes == 7:
            cantidad_de_denuncias['Julio'] += 1
        elif mes == 8:
            cantidad_de_denuncias['Agosto'] += 1
        elif mes == 9:
            cantidad_de_denuncias['Septiembre'] += 1
        elif mes == 10:
            cantidad_de_denuncias['Octubre'] += 1
        elif mes == 11:
            cantidad_de_denuncias['Noviembre'] += 1
        else:
            cantidad_de_denuncias['Diciembre'] += 1
            
    return cantidad_de_denuncias

def Robados(Robos:str):
    """
    Precondicion: Recibe la direccion de un documento de texto que contiene las patentes de los autos robados
    Postcondicion: Imprime en pantalla la direccion y el horario en que se denuncio el auto como mal estacionado
    """

    Patente:list=[]
    with open(Robos,'r') as P:
        for linea in P:
            Patente.append(linea.rstrip())
    with open('registro.csv','r',newline='') as R:
        next(R)
        for linea in R:
            linea=linea.rstrip()
            linea = linea.split(',')
            if linea[5] in Patente:
                print("ALERTA!!!!!")
                print(f"Se registro un auto robado en la direccion: {linea[2]}")
                print(f"Y en el horario: {linea[0]}")
                print("-------------------------------------------------------------------------------------")

def Busqueda_Patente(centro_mapa:list, coordenadas_dict:dict):
    """
    Precondicion: Recibe unas coordenadas y un diccionario de coordenadas
    Postcondicion: Imprime en pantalla una foto del auto que se selecciona y un mapa con la ubicacion del mismo centrado en las primeras coordenadas ingresadas
    """

    print("Ingrese una patente: ")
    patente = input()
    Patentes_list:list=[]
    with open('registro.csv','r',newline='') as R:
        next(R)
        for linea in R:
            linea = linea.rstrip()
            linea = linea.split(',')
            Patentes_list.append(linea[5])

    if patente in Patentes_list:
        cont=0
        for i in Patentes_list:
            if i == patente:
                index=cont
            cont=cont+1
        with open('datos.csv','r',newline='') as D:
            next(D)
            cont=0
            for linea in D:
                linea = linea.rstrip()
                linea = linea.split(',')
                if cont == index:
                    ruta = linea[4]
                    cord1 = linea[2]
                    cord2 = linea[3]
                    coordenadas:list=[cord1,cord2]
                cont = cont+1

        Abrir_Imagen(ruta)
        Mapa = Crear_Mapa(coordenadas,coordenadas_dict['bombonera'],coordenadas_dict['monumental'],coordenadas_dict['cuadrante'])
        Agregar_Infraccion(Mapa,coordenadas,ruta)
        Mapa.save('Ubi_Auto.html')
        webbrowser.open_new_tab('Ubi_Auto.html')
    else:
        print("La Patente ingresada no fue registrada")

def Localizacion_Auto(centro_mapa,coordenadas):
    """
    Precondicion: Recibe dos coordenadas
    Postcondicion: Devuelve un mapa centrado en la primera coordenadas con la segunda marcada en verde
    """

    ubi = folium.Map(location=centro_mapa, zoom_start=13)
    folium.Marker(location = coordenadas, popup = folium.Popup(f"""<h1>Auto Seleccionado</h1><br/>"""), icon=folium.Icon(color="green", icon = "pushpin")).add_to(ubi)

    return ubi

def Menu(datos,coordenadas_dict,caba):

    opcion = 0
    while opcion != 6:
        print(' 1. Mostrar denuncias realizadas a 1km de los estadios')
        print(' 2. Mostrar todas las infracciones dentro del centro de la ciudad')
        print(' 3. Autos robados')
        print(' 4. Ingresar una patente')
        print(' 5. Mostras mapa cantidad de denuncias recibidas')
        print(' 6. Salir')

        opcion=int(input("Que accion desea realizar?: "))
        
        if (opcion==1):
            Procesar_Radio(datos,coordenadas_dict)
            
        elif (opcion==2):
            Procesar_Cuadrante(datos,coordenadas_dict['cuadrante'])
            
        elif (opcion==3):
            Robados('Robados.txt')
            
        elif (opcion==4):
            Busqueda_Patente(coordenadas_dict['centro_mapa'],coordenadas_dict)
                    
        elif (opcion==5):
            cantidad_de_denuncias = contador_denuncias(datos)
            grafico_xy(cantidad_de_denuncias)
        elif (opcion==  6):
            print(' **** Saliendo del menu  ****')   
        else:
            print('No existe la opcion')

def main():

    Direccion_Datos:str = 'datos.csv'

    Bombonera:list = [-34.63561750108096, -58.364769713435194]
    Monumental:list = [-34.545272094172674, -58.449752491858995]
    Centro_Mapa:list = [-34.60854928213016, -58.420043778191804]
    Callao_Rivadavia:list = [-34.60915405648046, -58.39196523234133]
    Callao_Cordoba:list = [-34.59964035141302, -58.392944435644694]
    Alem_Rivadavia:list = [-34.607710627889254, -58.370401504661324]
    Alem_Cordoba:list = [-34.59836493767683, -58.370976016505566]
    Cuadrante:dict = {'Callao_Rivadavia':Callao_Rivadavia,'Callao_Cordoba':Callao_Cordoba,'Alem_Rivadavia':Alem_Rivadavia,'Alem_Cordoba':Alem_Cordoba}

    Datos = Procesamiento_csv(Direccion_Datos)
    Mapa = Crear_Mapa(Centro_Mapa,Bombonera,Monumental,Cuadrante)
    Nuevos_Datos = Formatear_Datos_csv(Datos,Mapa)
    Crear_csv(Nuevos_Datos)

    Menu(Datos,coordenadas_dict,Mapa)
    
main()