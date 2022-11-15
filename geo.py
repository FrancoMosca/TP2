from geopy.geocoders import Nominatim
import folium
from folium.plugins import MarkerCluster
import math

def cuadrado(numero:float) -> float:
    return(numero * numero) 



def haversine(coordenada1, coordenada2):
    rad=math.pi/180
    dlat=coordenada2[0] - coordenada1[0]
    dlon=coordenada2[1] - coordenada1[1]
    R=6372.795477598
    a=(math.sin(rad*dlat/2))**2 + math.cos(rad*coordenada1[0])*math.cos(rad*coordenada2[0])*(math.sin(rad*dlon/2))**2
    distancia=2*R*math.asin(math.sqrt(a))
    return distancia

def dentro_radio(coordenada1, coordenada2, radio) -> bool:
    if(haversine(coordenada1, coordenada2) <= radio):
        return True
    return False

def main():
    localizador = Nominatim(user_agent="fede")
    ubicacion = localizador.reverse("-34.60854928213016, -58.420043778191804")

    coord1 = [ubicacion.latitude, ubicacion.longitude]
    coord2 = [-34.61116343450093, -58.42190427416548]



    print(haversine(coord1, coord2))
    print(dentro_radio(coord1, coord2, 1))

    print(ubicacion.latitude, ubicacion.longitude)
    print(ubicacion)


main()