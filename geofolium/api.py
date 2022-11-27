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

print(direccion_coordenadas([-34.60915405648046, -58.39196523234133]))
print("------------------------------------------------")
print(direccion_coordenadas([-34.607710627889254, -58.370401504661324]))
print("------------------------------------------------")
print(direccion_coordenadas([-34.85419234590419, -59.06527098733429]))
print("------------------------------------------------")
print(direccion_coordenadas([-43.838774500287386, -18.283261888554332]))
"""
#Pre: recibe dos coordenadas en froma de pares dentro de una lista
#Post: la funcion una la formula de haversine para devolver la distancia entro dos cordenadas contemplando una esfera
def haversine(coordenada1:list, coordenada2:list) -> float:
    rad:float = math.pi/180
    dlat:float = coordenada2[0] - coordenada1[0]
    dlon:float = coordenada2[1] - coordenada1[1]
    R:float = 6372.795477598
    a:float = (math.sin(rad*dlat/2))**2 + math.cos(rad*coordenada1[0])*math.cos(rad*coordenada2[0])*(math.sin(rad*dlon/2))**2
    distancia:float = 2*R*math.asin(math.sqrt(a))
    return distancia

#Pre: recibe dos coordenadas en froma de pares dentro de una lista
#Post: devuelve true si la distancia entre las coordenadas es menor al radiod dado
def dentro_radio(coordenada1:list, coordenada2:list, radio:float) -> bool:
    if(haversine(coordenada1, coordenada2) <= radio):
        return True
    return False

#Pre: recibe una coordendas y un diccionario de 4 coordenadas que generan un ciadrante ya hardcodeadas
#Post: devuelve true si la coordenada se encuentra dentro del cuadrante
def dentro_cuadrante(cuadrante:list, coordenada:list) -> bool:
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

#Pre: 3 coordenadas y el cuandrante, donde todas estan hardcodeadas    
#Post: la funcion crea un mapa atravez de folium se genera con c3ntro en buenos aires y marca en el mapa los puntos datos
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


#Pre: recibe el mapa, una coordenada y la ruta del archivo de imagen
#Post: la funcion crea una infraccion en el mapa marcandolo en rojo, que al clicker se ve un popup con la imagen dada, si la imgen no existe o se le da None no hay popup
def agregar_infraccion(caba, coordenadas:list, ruta_imagen:str):
    isFile:bool = os.path.isfile(ruta_imagen)
    if(ruta_imagen == None or isFile == False):
        folium.Marker(location = coordenadas, icon=folium.Icon(color="red", icon = "exclamation-sign")).add_to(caba)
    else:
        folium.Marker(  location = coordenadas, popup = folium.Popup(f"""<h1>Infraccion</h1><br/>
                        <img src={ruta_imagen}  style="max-width:100%;max-height:100%">""", max_width=500), 
                        icon=folium.Icon(color="red", icon = "exclamation-sign")
                        ).add_to(caba)

        
#Pre: la funcion recibe una coordenadas
#Post: la funcion devuele un dicionario con los datos de la direccion dada a partir de las coordenadas
def direccion_coordenadas(coordenadas:list) -> dict:
    coordenadas_str:str = str(coordenadas[0]) + ", " + str(coordenadas[1])
    mini_dict:dict = {}
    localizador = Nominatim(user_agent="fede")
    ubicacion = localizador.reverse(coordenadas_str)
    if(ubicacion == None):
        return(mini_dict)
  
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

    return(mini_dict)

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