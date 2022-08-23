# -*- coding: utf-8 -*-
"""
Created on Fri Aug  5 08:44:36 2022

@author: ifraga
"""



import pandas 
import sys
pandas.options.mode.chained_assignment = None

# Define las rutas de los directorios
dir_base = 'C:/Users/ifraga/Desktop/03-DESARROLLOS/NUTRIENTES/WEB'
sys.path.append(dir_base)

# Carga el modulo con las funciones comunes
import FUNCIONES_AUXILIARES

# Carga los parámetros de la base de datos y de estilo
archivo_parametros = dir_base + '/DATOS/DATOS_GENERALES.xlsx'
xls                = pandas.ExcelFile(archivo_parametros)
df_base_datos      = pandas.read_excel(xls, 'BASE_DATOS')
df_estilos         = pandas.read_excel(xls, 'ESTILOS')

# Parámetros de la base de datos
base_datos = df_base_datos['nombre'][0]
usuario    = df_base_datos['usuario'][0]
contrasena = df_base_datos['contrasena'][0]
puerto     = str(df_base_datos['puerto'][0])

# Estilos
listado_estados = df_estilos['Estado']
listado_colores = df_estilos['Color']


# Llama a la funcion que construye la página
FUNCIONES_AUXILIARES.pagina_programa('RADIAL CORUNA',listado_estados,listado_colores,base_datos,usuario,contrasena,puerto)




