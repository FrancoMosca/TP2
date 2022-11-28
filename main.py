import funciones

def main():
    coordenadas_dict: dict = {
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
    datos = funciones.procesamiento_csv()
    caba = funciones.crear_mapa(coordenadas_dict['centro_mapa'],coordenadas_dict['bombonera'],coordenadas_dict['monumental'],coordenadas_dict['cuadrante'])
    datos_csv = funciones.formatear_datos_csv(datos,caba)
    funciones.crear_csv(datos_csv)   
    # caba.save('index.html')
    # funciones.webbrowser.open_new_tab('index.html')
    funciones.menu(datos,coordenadas_dict)

main()
