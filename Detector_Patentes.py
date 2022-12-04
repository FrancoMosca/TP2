import cv2
import numpy as np
import argparse
import time
import imutils
import pytesseract
import os

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
