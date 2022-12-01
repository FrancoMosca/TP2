import cv2
import numpy as np
import argparse
import time
import imutils
import pytesseract
import os

def borrarPantalla():

    if os.name == "posix":
        os.system ("clear")
    elif os.name == "ce" or os.name == "nt" or os.name == "dos":
       os.system ("cls")

def Detector_Placas(Imagen)->str:
    """
    Precondiciones: Debe haber una patente en la imagen con la mejor calidad posible y sin rudio
    Postcondiciones: Se devuelve un string en el que se ecuentra la patente
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

        borrarPantalla()
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
        borrarPantalla()
        text="ERROR"

    return text

def Cargar_Yolo():
    """
    Precondiciones: Deben estar los 2 archivos yolov3.weights y yolov3.cfg
    """

    net = cv2.dnn.readNet("yolov3.weights", "yolov3.cfg")
    classes = []
    with open("coco.names", "r") as f:
        classes = [line.strip() for line in f.readlines()] 
    
    output_layers = [layer_name for layer_name in net.getUnconnectedOutLayersNames()]
    colors = np.random.uniform(0, 255, size=(len(classes), 3))
    return net, classes, colors, output_layers

def Cargar_Imagen(Imagen):
    """
    Precondiciones: Debe existir la imagen
    """
    img = cv2.imread(Imagen)
    img = cv2.resize(img,(600,400))
    height, width, channels = img.shape
    return img, height, width, channels

def Detector_Objetos(img, net, outputLayers):
    """
    Precondiciones: Deben existir objetos en la imagen
    """

    blob = cv2.dnn.blobFromImage(img, scalefactor=0.00392, size=(320, 320), mean=(0, 0, 0), swapRB=True, crop=False)
    net.setInput(blob)
    outputs = net.forward(outputLayers)
    return blob, outputs

def Dimencion_Cajas(outputs, height, width):

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

def Recorte(boxes, confs, class_ids, classes, img):
    """
    Precondiciones: La imagen debe tener un auto, y este debe estar comlpleto en la misma
    Postcondiciones: Se crea una imagen con en recorte del auto en la que se ecuentra su patente
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

def Validacion(boxes, confs, class_ids, classes)->bool:

    indexes = cv2.dnn.NMSBoxes(boxes, confs, 0.5, 0.4)
    Verificacion=False

    for i in range(len(boxes)):
        if i in indexes:

            label = str(classes[class_ids[i]])
            #Verifica que se en la imagen se encuentre un automovil
            if label == "car" or label == "motorbike" or label == "truck" or label == "bus":
                Verificacion = True

    return Verificacion

def Detector(Imagen):
    """
    Precondiciones: La imagen debe existir
    """

    model, classes, colors, output_layers = Cargar_Yolo()
    image, height, width, channels = Cargar_Imagen(Imagen)
    blob, outputs = Detector_Objetos(image, model, output_layers)
    boxes, confs, class_ids = Dimencion_Cajas(outputs, height, width)
    Recorte(boxes, confs, class_ids, classes, image)
    Verificacion = Validacion(boxes, confs, class_ids, classes)

    return Verificacion

def Limpieza(Text:str)->str:
    """
    Precondiciones: La patente tiene letras mayusculas y se encuentra en el parametro
    Postcondiciones: Devuelve la patente
    """
    Lista=list(Text)

    Permitidos=["Q","W","E","R","T","Y","U","I","O","P","A","S","D","F","G","H","J","K","L","Ñ","Z","X","C","V","B","N","M","0","1","2","3","4","5","6","7","8","9"]

    Patente:list=[]
    for i in Lista:
        if i in Permitidos:

            Patente.append(i)

    Patente="".join(Patente)
    return Patente


def Patente(Imagen:str)->str:
    """
    Precondicones:
    Postcondiciones
    """
    Verificado = Detector(Imagen)

    if Verificado == True:
        text = Detector_Placas("Imagen.png")
        borrarPantalla()
        if text == "ERROR":
            Patente = "No se encontro una placa"
        else:
            Patente = Limpieza(text)
    else:
        Patente = "No se ha encontrado un auto en la imagen"

    return Patente


def Abrir_Imagen(Imagen):
    """
    Precondiciones: Debe existir la imagen
    """

    img = cv2.imread(Imagen,cv2.IMREAD_COLOR)
    img = cv2.resize(img, None, fx=0.4, fy=0.4)
    cv2.imshow('Auto.jpg',img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
