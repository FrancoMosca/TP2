from geopy.geocoders import Nominatim
import folium 
from folium.plugins import MarkerCluster
import math
import webbrowser
import os

#https://www.youtube.com/watch?v=jFaa2vwU4-M
#https://getbootstrap.com/docs/3.3/components/
"""
localizador = Nominatim(user_agent="fede")
ubicacion = localizador.reverse("-34.60854928213016, -58.420043778191804")
print(f"dentro: {dentro_cuadrante(cuadrante, coord_cuadrante)}")
print(haversine(coord1, coord2))
print(dentro_radio(coord1, coord2, 1))
print(ubicacion.latitude, ubicacion.longitude)
print(ubicacion.address)
"""

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

def main():
    bombonera = [-34.63561750108096, -58.364769713435194]
    monumental = [-34.545272094172674, -58.449752491858995]
    centro_mapa = [-34.60854928213016, -58.420043778191804]
    cuadrante = {
        'callao_rivadavia': [-34.60915405648046, -58.39196523234133],
        'callao_cordoba': [-34.59964035141302, -58.392944435644694],
        'alem_rivadavia': [-34.607710627889254, -58.370401504661324],
        'alem_cordoba': [-34.59836493767683, -58.370976016505566]
    }
    
    caba = crear_mapa(centro_mapa, bombonera, monumental, cuadrante)
    agregar_infraccion(caba, centro_mapa, "373791.jpg")
    caba.save('index.html')
    webbrowser.open_new_tab('index.html')

main()