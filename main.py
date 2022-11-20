import funciones

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
    datos = funciones.procesamiento_csv()
    
    
    for i in range(len(datos)):
        coordenadas : list = [float(datos[i]['coord_latitud']),float(datos[i]['coord_long'])]
        datos_coords = funciones.direccion_coordenadas(coordenadas)
        texto_audio = funciones.speech_recognition_API(datos[i]['ruta_audio'])
        funciones.crear_csv(datos[i]['Timestamp'],datos[i]['Telefono_celular'],datos_coords['direccion'],datos_coords['localidad'],datos_coords['provincia'],datos[i]['descripcion_texto'],texto_audio)

    caba = funciones.crear_mapa(centro_mapa, bombonera, monumental, cuadrante)
    funciones.agregar_infraccion(caba, centro_mapa, "373791.jpg")
    caba.save('index.html')
    funciones.webbrowser.open_new_tab('index.html')

main()
