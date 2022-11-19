from geopy.geocoders import Nominatim
import folium
from folium.plugins import MarkerCluster
import math

import pandas as pd
from IPython.display import display
import webbrowser

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
    bombonera = [-34.63561750108096, -58.364769713435194]
    monumental = [-34.545272094172674, -58.449752491858995]

    cuadrante = {
        'callao_rivadavia': [-34.60915405648046, -58.39196523234133],
        'callao_cordoba': [-34.59964035141302, -58.392944435644694],
        'alem_rivadavia': [-34.607710627889254, -58.370401504661324],
        'alem_cordoba': [-34.59836493767683, -58.370976016505566]
    }
    
    coord_cuadrante = [-34.69716797660035, -58.37993019820602]
    """
    print(f"dentro: {dentro_cuadrante(cuadrante, coord_cuadrante)}")
    print(haversine(coord1, coord2))
    print(dentro_radio(coord1, coord2, 1))
    print(ubicacion.latitude, ubicacion.longitude)
    print(ubicacion.address)
    """

    franchises = pd.read_csv('locali.csv')
    #view the dataset
    print(franchises.head())
    center = [-34.60854928213016, -58.420043778191804]
    caba = folium.Map(location=center, zoom_start=15)
    folium.Circle(location = bombonera, radius = 1000, color = "red", fill = True).add_to(caba)
    folium.Circle(location = monumental, radius = 1000, color = "red", fill = True).add_to(caba)
    
    for index, franchise in franchises.iterrows():
        location = [franchise['latitude'], franchise['longitude']]
        folium.Marker(location, popup = f"Name:{franchise['name']}\n" , color ="red", icon=folium.Icon(color="green")).add_to(caba)

    # save map to html file
    caba.save('index.html')
    webbrowser.open_new_tab('index.html')


main()

