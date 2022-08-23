# -*- coding: utf-8 -*-
"""
Created on Fri Aug  5 08:44:36 2022

@author: ifraga
"""


import streamlit as st
import pandas 
import matplotlib.pyplot as plt
import st_aggrid 
from io import BytesIO
import os
import datetime

# Carga la excel con los datos de disponibilidad
ruta_excel_pelacus  = 'C:/Users/ifraga/Desktop/03-DESARROLLOS/NUTRIENTES/WEB/DATOS/PELACUS.csv'
df_pelacus_numerico = pandas.read_csv(ruta_excel_pelacus,delimiter=';')
df_pelacus_estado   = pandas.read_csv(ruta_excel_pelacus,delimiter=';')







# Transforma los punteros a estados
# 1- No disponible 2-En proceso 3-Procesado 4-Procesado + CC
listado_estados = ['No disponible','En proceso','Procesado','Validado']
listado_colores = ['#F08080','#F4A460','#87CEEB','#2E8B57']
for idato in range (df_pelacus_estado.shape[0]):
    df_pelacus_estado['ESTADO'][idato] = listado_estados[df_pelacus_numerico['ESTADO'][idato]-1]

# Cuenta el numero de veces que se repite cada estado para sacar un gráfico pie-chart
num_valores = df_pelacus_estado['ESTADO'].value_counts()

explode_estados = (0, 0, 0, 0.2)  # "explode" el estado validado, para que se vea mejor
cm              = 1/2.54 # pulgadas a cm
fig, ax1 = plt.subplots(figsize=(8*cm, 8*cm))
ax1.pie(num_valores, explode=explode_estados, colors=listado_colores,labels=listado_estados, autopct='%1.1f%%', shadow=True, startangle=90)
ax1.axis('equal')  # Para representar el pie-chart como un circulo

# Genera un dataframe con los años en los que hay datos, entre los que se seleccionará la descarga
datos_disponibles = df_pelacus_numerico[df_pelacus_numerico['ESTADO'] >= 3]

# Define los estilos para la tabla y el gráfico
cellsytle_jscode = st_aggrid.shared.JsCode(
    """function(params) {
    if (params.value.includes('Validado')) 
    {return {'color': 'black', 'backgroundColor': 'SeaGreen'}} 

    if (params.value.includes('Procesado')) 
    {return {'color': 'black', 'backgroundColor': 'SkyBlue'}}   

    if (params.value.includes('En proceso')) 
    {return {'color': 'black', 'backgroundColor': 'SandyBrown'}}  
 
    if (params.value.includes('No disponible')) 
    {return {'color': 'black', 'backgroundColor': 'IndianRed '}}    
    };""")
    


########################################
### Muestra la informacion en la web ###
########################################

# Encabezados y titulos 
st.set_page_config(page_title="Datos de nutrientes", layout="wide") 
st.title("Datos de nutrientes disponibles en el C.O de A Coruña")

#Division en dos columnas, una para tabla otra para la imagen
col1, col2 = st.columns(2,gap="medium")

# Representacion de la tabla de estados
with col1:
    st.header("Listado de datos")
#    st_aggrid.AgGrid(df_pelacus_estado,width=800)
    gb = st_aggrid.grid_options_builder.GridOptionsBuilder.from_dataframe(df_pelacus_estado)
    gb.configure_column("ESTADO", cellStyle=cellsytle_jscode)

    gridOptions = gb.build()

    

    data = st_aggrid.AgGrid(
        df_pelacus_estado,
        gridOptions=gridOptions,
        enable_enterprise_modules=True,
        allow_unsafe_jscode=True
        )



with col2:
    
    # Representa el pie-chart con el estado de los procesos
    buf = BytesIO()
    fig.savefig(buf, format="png",bbox_inches='tight')
    st.image(buf)
    
    # Selecciona el año del que se quiere descargar datos
    seleccion = st.selectbox('Selecciona el año a descargar (entre los disponibles)',        
        datos_disponibles['ANO'])
    nombre_archivo = 'C:/Users/ifraga/Desktop/03-DESARROLLOS/NUTRIENTES/WEB/DATOS/' + str(seleccion) + '.csv'
     
    # Comprueba si el archivo está disponible. Si es así permite su descarga
    if os.path.isfile(nombre_archivo) == True:

        # Carga el archivo y conviertelo al formato necesario para exportarlo
        df_exporta  = pandas.read_csv(nombre_archivo,delimiter=';')
        csv_exporta = df_exporta.to_csv().encode('utf-8')

        st.download_button(
            label="DESCARGA LOS DATOS SELECCIONADOS",
            data=csv_exporta,
            file_name=nombre_archivo,
            mime='text/csv',
            help= 'Descarga un archivo .csv con los datos solicitados',
            )
    else:
        st.text('Error en la ruta al archivo solicitado. Contacte con el administrador')