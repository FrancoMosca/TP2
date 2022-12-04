"""APP Multas"""
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
import imutils
import pytesseract

def borrar_pantalla()->None:
    """borrar_pantalla
    Pre: No recibe nada
    Post: Borra la pantalla. No devuelve nada
    """
    if os.name == "posix":
        os.system ("clear")
    elif os.name == "ce" or os.name == "nt" or os.name == "dos":
       os.system ("cls")

def detector_placas(Imagen)->str:
    """detector_placas
    Pre: Debe haber una patente en la imagen con la mejor calidad posible y sin rudio
    Post: Se devuelve un string en el que se ecuentra la patente
    """
    #Cambia el tamaño de la imagen
    img = cv2.imread(Imagen,cv2.IMREAD_COLOR)
    img = cv2.resize(img, (400,400) )
    #Cambia el color de la imagen a gris y luego aplica el filtro Canny
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) 
    gray = cv2.bilateralFilter(gray, 13, 15, 15) 
    edged = cv2.Canny(gray, 30, 200)
    #Busca contornos en la imagen
    contours = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(contours)
    contours = sorted(contours, key = cv2.contourArea, reverse = True)[:10]
    screenCnt = None

    #Busca el contorno en la imagen que se asemeje a una patente
    for c in contours:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.018 * peri, True)
        if len(approx) == 4:
            screenCnt = approx
            break
    if screenCnt is None:
        detected = 0
    else:
        detected = 1
    if detected == 1:
        borrar_pantalla()
        cv2.drawContours(img, [screenCnt], -1, (0, 0, 255), 3)
        mask = np.zeros(gray.shape,np.uint8)
        new_image = cv2.drawContours(mask,[screenCnt],0,255,-1,)
        new_image = cv2.bitwise_and(img,img,mask=mask)
        (x, y) = np.where(mask == 255)
        (topx, topy) = (np.min(x), np.min(y))
        (bottomx, bottomy) = (np.max(x), np.max(y))
        Cropped = gray[topx:bottomx+1, topy:bottomy+1]
        
        #Imprime en un string a los alfanumericos que detecta de la patente
        text = pytesseract.image_to_string(Cropped, config='--psm 11')
    else:
        borrar_pantalla()
        text="ERROR"

    return text

def cargar_yolo()->any:
    """cargar_yolo
    Pre: Deben estar los 2 archivos yolov3.weights y yolov3.cfg
    Post: Devuelve variables de distintos tipos.
    """

    net = cv2.dnn.readNet("yolov3.weights", "yolov3.cfg")
    classes = []
    with open("coco.names", "r") as f:
        classes = [line.strip() for line in f.readlines()] 
    
    output_layers = [layer_name for layer_name in net.getUnconnectedOutLayersNames()]
    colors = np.random.uniform(0, 255, size=(len(classes), 3))
    return net, classes, colors, output_layers

def cargar_imagen(imagen)->any:
    """cargar_imagen
    Pre: Debe existir la imagen
    Post: Devuelve variables de tipo int
    """
    img = cv2.imread(imagen)
    img = cv2.resize(img,(600,400))
    height, width, channels = img.shape
    return img, height, width, channels

def detector_objetos(img, net, outputLayers):
    """detector_objetos
    Pre: Deben existir objetos en la imagen
    Post: Devuelve blob, outputs
    """

    blob = cv2.dnn.blobFromImage(img, scalefactor=0.00392, size=(320, 320), mean=(0, 0, 0), swapRB=True, crop=False)
    net.setInput(blob)
    outputs = net.forward(outputLayers)
    return blob, outputs

def dimencion_cajas(outputs, height, width)->list:
    """dimencion_cajas
    Pre: Recibe outputs, height, width
    Post: Devuleve boxes, confs, class_ids todas variables de tipo list
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

def recorte(boxes, confs, class_ids, classes, img)->None:
    """recorte
    Pre: La imagen debe tener un auto, y este debe estar comlpleto en la misma
    Post: Se crea una imagen con en recorte del auto en la que se ecuentra su patente
    """
    indexes = cv2.dnn.NMSBoxes(boxes, confs, 0.5, 0.4)
    font = cv2.FONT_HERSHEY_PLAIN
    try:
        #Busca en la imagen el auto principal al que se le saco foto (el de mayor tamaño)
        tam_max = boxes[indexes[0]][2]*boxes[indexes[0]][3]
        if tam_max<0:
            tam_max=tam_max*-1

        for i in range(len(boxes)):
            if i in indexes:
                x, y, w, h = boxes[i]
                tam = w*h

                if tam<0:
                    tam=tam*-1
                if tam > tam_max:
                    tam_max = w*h
                    if tam_max<0:
                        tam_max=tam_max*-1 

        for i in range(len(boxes)):
            if i in indexes:
                x, y, w, h = boxes[i]
                tam=w*h
                
                if tam<0:
                    tam = w*h*-1
                if tam==tam_max:
                    label = str(classes[class_ids[i]])
                    if label=="car" or label=="motorbike" or label=="truck" or label=="bus":
                        
                        #Recorta el auto principal
                        cv2.imwrite("Imagen.png",img[y:y+h,x:x+w])
    except:
        print("La imagen ingresada no es correcta")

def validacion(boxes, confs, class_ids, classes)->bool:
    """validacion
    Pre: Recibe por parametro boxes, confs, class_ids, classes.
    Post: Devuelve una variable de tipo bool.
    """
    indexes = cv2.dnn.NMSBoxes(boxes, confs, 0.5, 0.4)
    verificacion=False
    for i in range(len(boxes)):
        if i in indexes:
            label = str(classes[class_ids[i]])
            #Verifica que se en la imagen se encuentre un automovil
            if label == "car" or label == "motorbike" or label == "truck" or label == "bus":
                verificacion = True

    return verificacion

def detector(imagen)-> bool:
    """detector
    Pre: La imagen debe existir.
    Post: Devuelve una variable de tipo bool.
    """
    model, classes, colors, output_layers = cargar_yolo()
    image, height, width, channels = cargar_imagen(imagen)
    blob, outputs = detector_objetos(image, model, output_layers)
    boxes, confs, class_ids = dimencion_cajas(outputs, height, width)
    recorte(boxes, confs, class_ids, classes, image)
    verificacion = validacion(boxes, confs, class_ids, classes)

    return verificacion

def limpieza(Text:str)->str:
    """limpieza
    Pre: La patente tiene letras mayusculas y se encuentra en el parametro
    Post: Devuelve la patente
    """
    lista=list(Text)

    permitidos=["Q","W","E","R","T","Y","U","I","O","P","A","S","D","F","G","H","J","K","L","Ñ","Z","X","C","V","B","N","M","0","1","2","3","4","5","6","7","8","9"]

    patente:list=[]
    for i in lista:
        if i in permitidos:

            patente.append(i)

    patente="".join(patente)
    return patente


def patente(imagen:str)->str:
    """patente
    Pre: Recibe la ruta de la imagen
    Post: Retorna la patente tipo str
    """
    verificado = detector(imagen)

    if verificado == True:
        text = detector_placas("Imagen.png")
        borrar_pantalla()
        if text == "ERROR":
            patente = "No se encontro una placa"
        else:
            patente = limpieza(text)
    else:
        patente = "No se ha encontrado un auto en la imagen"

    return patente


def abrir_Imagen(imagen)->None:
    """abrir_Imagen
    Pre: Debe existir la imagen
    Post: No devuelve nada
    """

    img = cv2.imread(imagen,cv2.IMREAD_COLOR)
    img = cv2.resize(img, None, fx=0.4, fy=0.4)
    cv2.imshow('Auto.jpg',img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def haversine(coordenada1, coordenada2)-> float:
    """haversine
    Pre:
    Post:
    """
    rad=math.pi/180
    dlat=coordenada2[0] - coordenada1[0]
    dlon=coordenada2[1] - coordenada1[1]
    R=6372.795477598
    a=(math.sin(rad*dlat/2))**2 + math.cos(rad*coordenada1[0])*math.cos(rad*coordenada2[0])*(math.sin(rad*dlon/2))**2
    distancia=2*R*math.asin(math.sqrt(a))
    return distancia


def dentro_radio(coordenada1, coordenada2, radio) -> bool:
    """dentro_cuadrante
    Pre: Recibe las coordenadas de la denuncia, las coordenadas de los estadios y
    el tamaño del radio.
    Post: Devuelve true si las coordenadas de la denuncia estan dentro del radio 
    y false si no esta dentro.
    """
    if(haversine(coordenada1, coordenada2) <= radio):
        return True
    return False


def dentro_cuadrante(cuadrante, coordenada)->bool:
    """dentro_cuadrante
    Pre: Recibe las coordenadas del cuadrante y las coordenadas de la denuncia.
    Post: Devuelve true si las coordenadas de la denuncia estan dentro del cuadrante 
    y false si no esta dentro.
    """
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

def crear_mapa(centro_mapa, bombonera, monumental, cuadrante)-> map:
    """crear_mapa
    Pre: Recibe las coordenadas de los estadios del cuandrante y las del centro del mapa.
    Post: Devuelve un mapa
    """
    caba : map= folium.Map(location=centro_mapa, zoom_start=13)
    
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

def agregar_infraccion(caba, coordenadas, ruta_imagen)->None:
    """agregar_infraccion
    Pre:Recibe el mapa, las coordenadas y la ruta de la imagen de la denuncia.
    Post: Agrega un simbolo al mapa en las coordenadas que recibe por parametro simbolizando una denuncia.
    """
    isFile : bool= os.path.isfile(ruta_imagen)
    if(ruta_imagen == None or isFile == False):
        folium.Marker(location = coordenadas, icon=folium.Icon(color="red", icon = "exclamation-sign")).add_to(caba)
    else:
        folium.Marker(  location = coordenadas, popup = folium.Popup(f"""<h1>Infraccion</h1><br/>
                        <img src={ruta_imagen}  style="max-width:100%;max-height:100%">""", max_width=500), 
                        icon=folium.Icon(color="red", icon = "exclamation-sign")
                        ).add_to(caba)
        
def direccion_coordenadas(coordenadas)->dict:
    """direccion_coordenadas
    Pre:Recibe las coordenadas de la denuncia.
    Post: Devuelve un dict que segun las coordenadas recibidas
    tiene como llave la direccion, localidad, provincia, ciudad y pais 
    con su respectivo valor.
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

def crear_csv(registros)->None:
    """crear_csv
    Pre: Recibe los registros.
    Post:Crea un csv llamado registro con los headers de la lista headers
    y rellena las filas con los datos de los registros pasados por parametro.
    No devuelve nada.
    """
    headers: list = ['Timestamp','Telefono',
                    'Direccion de la infraccion',
                    'Localidad','Provincia',
                    'Patente','descripcion texto',
                    'descripcion audio']
    with open('registro.csv', 'w') as f:
        write = csv.writer(f)
        write.writerow(headers)
        write.writerows(registros)
        
def audio_a_texto(ruta_audio) -> str:
    """audio_a_texto
    Pre:Recibe una ruta de audio en formato .wav
    Post:Pasa el audio por filtros y devuelve el audio
    escrito como texto en formato str.
    """
    r = sr.Recognizer()
    with sr.AudioFile(ruta_audio) as source:
        r.adjust_for_ambient_noise(source)
        audio : str = r.listen(source)
        texto_audio : str = r.recognize_google(audio,language='es-AR')
    return texto_audio

def procesar_radio(denuncias,coordenadas_ciudad)->None:
    """procesar_radio
    Pre: Recibe las denuncias y el dict coordenadas_ciudad.
    Post: No devuelve nada.
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

    for i in range(len(denuncias)):
        coordenadas : list = [float(denuncias[i]['coord_latitud']),float(denuncias[i]['coord_long'])]
        if dentro_radio(coordenadas,coordenadas_ciudad['monumental'],1):
            print(f"El auto: {Patentes[i]} se encuentra a 1km de la monumental")
        elif dentro_radio(coordenadas,coordenadas_ciudad['bombonera'],1):
            print(f"El auto: {Patentes[i]} se encuentra a 1km de la bombonera")
           
def procesar_cuadrante(denuncias,coordenadas_ciudad)->None:
    """procesar_cuadrante
    Pre: Recibe las denuncias y el dict coordenadas_ciudad.
    Post: No devuelve nada.
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

    for i in range(len(denuncias)):
        coordenadas : list = [float(denuncias[i]['coord_latitud']),float(denuncias[i]['coord_long'])]
        if dentro_cuadrante(coordenadas_ciudad,coordenadas):
            print(F"El auto: {Patentes[i]} se encuentra en el cuadrante")

def grafico_xy(xy)->None:
    """grafico_xy
    Pre:Recibe el diccionario cantidad_de_denuncias.
    Post:Define las keys del diccionario como las variables en x
    y los valores como las variables en y, y genera un grafico con 
    esos datos. No devuelve nada.
    """
    gf.plot(xy.keys(), xy.values())
    gf.title('Cantidad de denuncias mensuales')
    gf.xlabel('Mes')
    gf.ylabel('Cantidad de denuncias')
    gf.xticks(rotation=90,fontsize=9)
    gf.show()
    
def contador_denuncias(denuncias)-> dict:
    """contador_denuncias.
    Pre: Recibe las denuncias.
    Post: Devuelve un diccionario con la cantidad de denuncias 
    separadas por mes.
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
    mes : int = 0
    for i in range(len(denuncias)):
        fecha : datetime = datetime.datetime.strptime(denuncias[i]['Timestamp'],'%Y-%m-%d %H:%M:%S')
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

def alertar_autos_robados(robados)->None:
    """alertar_autos_robados.
    Pre: Recibe un archivo csv.
    Post:Compara las patentes del archivo registro y si ecuentra alguna que
    tambien este en el csv pasado por parametro, manda una alerta, no devuelve nada.
    """
    Patente:list=[]
    with open(robados,'r') as P:
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

def busqueda_patente(coordenadas_ciudad)->None:
    """busqueda_patente.
    Pre:Recibe las coordenadas de los estadios y del centro
    de la ciudad en forma de diccionario y permite al usuario ingresar
    una patente en forma de str.
    Post:Muestra la patente agregada en el mapa, no devuelve nada.
    """
    print("Ingrese una patente: ")
    patente : str = input()

    Patentes_list:list=[]
    with open('registro.csv','r',newline='') as R:
        next(R)
        for linea in R:
            linea = linea.rstrip()
            linea = linea.split(',')
            Patentes_list.append(linea[5])

    if patente in Patentes_list:
        cont : int=0
        for i in Patentes_list:
            if i == patente:
                index: int=cont
            cont=cont+1
            
        with open('datos.csv','r',newline='') as D:
            next(D)
            cont : int=0
            for linea in D:
                linea = linea.rstrip()
                linea = linea.split(',')
                if cont == index:
                    ruta = linea[4]
                    cord1 = linea[2]
                    cord2 = linea[3]
                    coordenadas:list=[cord1,cord2]
                cont = cont+1
        abrir_Imagen(ruta)
        mapa = crear_mapa(coordenadas,coordenadas_ciudad['bombonera'],coordenadas_ciudad['monumental'],coordenadas_ciudad['cuadrante'])
        agregar_infraccion(mapa,coordenadas,ruta)
        mapa.save('Ubi_Auto.html')
        webbrowser.open_new_tab('Ubi_Auto.html')
        
    else:
        print("La Patente ingresada no fue registrada")

def localizacion_auto(centro_mapa,coordenadas)-> map:
    """Localizacion_Auto.
    Pre: Recibe el mapa y las coordenadas de la denuncia. 
    Post: Devuelve la ubicacion del auto denunciado en tipo de dato map.
    """
    ubi : map = folium.Map(location=centro_mapa, zoom_start=13)
    folium.Marker(location = coordenadas, popup = folium.Popup(f"""<h1>Auto Seleccionado</h1><br/>"""),
                  icon=folium.Icon(color="green", icon = "pushpin")).add_to(ubi)

    return ubi

def menu(denuncias,coordenadas_ciudad)-> None:
    """menu.
    Pre: Recibe la lista de denuncias y las coordenadas de los estadios
    y del centro de la ciudad en forma de diccionario, da una lista de opciones
    la cual el usuario puede elegir depende que elija el usuario llama a
    diferentes funciones.
    Post:No devuelve nada.
    """
    opcion: int = 0
    while not(opcion == 6):
        print(' 1. Mostrar denuncias realizadas a 1km de los estadios')
        print(' 2. Mostrar todas las infracciones dentro del centro de la ciudad')
        print(' 3. Autos robados')
        print(' 4. Ingresar una patente')
        print(' 5. Mostras mapa cantidad de denuncias recibidas')
        print(' 6. Salir')

        opcion=int(input("Que accion desea realizar?: "))
        if opcion < 1 and opcion > 6:
            opcion=int(input("Por favor ingrese un numero valido: "))
    
        if (opcion==1):
            procesar_radio(denuncias,coordenadas_ciudad)
            
        elif (opcion==2):
            procesar_cuadrante(denuncias,coordenadas_ciudad['cuadrante'])
            
        elif (opcion==3):
            alertar_autos_robados('Robados.txt')
            
        elif (opcion==4):
            busqueda_patente(coordenadas_ciudad)
                    
        elif (opcion==5):
            cantidad_de_denuncias = contador_denuncias(denuncias)
            grafico_xy(cantidad_de_denuncias)
        elif (opcion==6):
            print(' **** Saliendo del menu  ****')   
        else:
            print('No existe la opcion')

def formatear_datos_csv(denuncias,caba)->list[list]:
    """formatear_datos_csv
    Pre: Recibe las denuncias la cual debe ser una lista de diccionarios
    y el mapa de la ciudad.
    Post: Recorre las denuncias y devuelve los datos pedidos en una lista
    llamada registros, tambien llama a las funciones direccion_coordenadas 
    y speech_recognition_API para agregar esos datos a la lista"""
    registros: list[list] = []
    for i in range(len(denuncias)):
        formato_csv: list = []
        coordenadas : list = [float(denuncias[i]['coord_latitud']),float(denuncias[i]['coord_long'])]
        datos_coords = direccion_coordenadas(coordenadas)
        texto_audio = audio_a_texto((denuncias[i]['ruta_audio']).rstrip())
        
        formato_csv.append(denuncias[i]['Timestamp'])
        formato_csv.append(denuncias[i]['Telefono_celular'])
        formato_csv.append(datos_coords['direccion'])
        formato_csv.append(datos_coords['localidad'])
        formato_csv.append(datos_coords['provincia'])
        formato_csv.append(patente(denuncias[i]['ruta_foto']))
        formato_csv.append(denuncias[i]['descripcion_texto'])
        formato_csv.append(texto_audio)
        
        registros.append(formato_csv)
        
        agregar_infraccion(caba, coordenadas, denuncias[i]['ruta_foto'])
        
    return registros
            
def procesamiento_csv() -> list[dict]:
    """procesamiento csv.
    Pre: No recibe nada, lee el archivo denuncias.csv y lo recorre
    linea a linea.
    Post:Guarda los valores de cada linea con sus respectivas
    llaves en un diccionario llamdo denuncia, que luego es appendeado
    a una lista llamada denuncias, devuelve la list[dict] llamada denuncias. 
    """
    denuncias : list[dict] = []
    with open('denuncias.csv','r',newline='') as archivo:
        next(archivo)
        for linea in archivo:
            linea = linea.rstrip()
            linea = linea.split(',')
            denuncia = {
                "Timestamp":linea[0],
                "Telefono_celular":linea[1],
                "coord_latitud":linea[2],
                "coord_long":linea[3],
                "ruta_foto":linea[4],
                "descripcion_texto":linea[5],
                "ruta_audio":linea[6]
            }
            denuncias.append(denuncia)
    return denuncias

def main():
    """Main.
    Pre: No recibe nada
    Post: Llama a la funciones procesamiento_csv,
    crear_mapa,formatear_datos_csv, crear_csv y menu.
    """
    coordenadas_ciudad: dict = {
            'bombonera' : [-34.63561750108096, -58.364769713435194],
            'monumental': [-34.545272094172674, -58.449752491858995],
            'centro_mapa': [-34.60854928213016, -58.420043778191804], 
            'cuadrante': {
                'callao_rivadavia': [-34.60915405648046, -58.39196523234133],
                'callao_cordoba': [-34.59964035141302, -58.392944435644694],
                'alem_rivadavia': [-34.607710627889254, -58.370401504661324],
                'alem_cordoba': [-34.59836493767683, -58.370976016505566]
                }      
    }
    denuncias = procesamiento_csv()
    caba = crear_mapa(coordenadas_ciudad['centro_mapa'],coordenadas_ciudad['bombonera'],coordenadas_ciudad['monumental'],coordenadas_ciudad['cuadrante'])
    datos_csv = formatear_datos_csv(denuncias,caba)
    crear_csv(datos_csv)   
    menu(denuncias,coordenadas_ciudad)

main()
