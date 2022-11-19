from geopy.geocoders import Nominatim
import folium
from folium.plugins import MarkerCluster
import math


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

def main():
    localizador = Nominatim(user_agent="fede")
    ubicacion = localizador.reverse("-34.60854928213016, -58.420043778191804")

    coord1 = [ubicacion.latitude, ubicacion.longitude]
    coord2 = [-34.61116343450093, -58.42190427416548]

    cuadrante = {
        'callao_rivadavia': [-34.60915405648046, -58.39196523234133],
        'callao_cordoba': [-34.59964035141302, -58.392944435644694],
        'alem_rivadavia': [-34.607710627889254, -58.370401504661324],
        'alem_cordoba': [-34.59836493767683, -58.370976016505566]
    }
    
    coord_cuadrante = [-34.69716797660035, -58.37993019820602]
    print(f"dentro: {dentro_cuadrante(cuadrante, coord_cuadrante)}")
    print(haversine(coord1, coord2))
    print(dentro_radio(coord1, coord2, 1))
    print(ubicacion.latitude, ubicacion.longitude)
    print(ubicacion.address)


main()