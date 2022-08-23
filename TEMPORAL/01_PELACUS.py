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
import numpy
import psycopg2

# Parámetros de la base de datos
base_datos = 'IEO_Coruna'
usuario    = 'postgres'
contrasena = 'IEO2022'
puerto     = '5432'

# Parámetros generales del estado de los procesos
# 0- No disponible 1- Pendiente de análisis 2-Analizado 3-Procesado primario 4-Procesado + CC
listado_estados = ['No disponible','Pendiente de análisis','Analizado','Procesado primario','Procesado secundario']
listado_colores = ['#CD5C5C','#F4A460','#87CEEB','#66CDAA','#2E8B57']






# Consulta a la base de datos las fechas de los distintos procesos

conn   = psycopg2.connect(database=base_datos, user=usuario, password=contrasena, port=puerto)
cursor = conn.cursor()

# Identificador del programa (PELACUS en este caso)
instruccion_sql = "SELECT id_programa FROM programas WHERE nombre_programa = 'PELACUS' ;"
cursor.execute(instruccion_sql)
id_pelacus =cursor.fetchone()[0]
conn.commit()

instruccion_sql = "SELECT * FROM estado_procesos WHERE nombre_programa = 'PELACUS' ;"
cursor.execute(instruccion_sql)
id_pelacus =cursor.fetchone()[0]
conn.commit() 

cursor.close()
conn.close()


# Carga la excel con los datos de disponibilidad
ruta_excel_pelacus  = 'C:/Users/ifraga/Desktop/03-DESARROLLOS/NUTRIENTES/WEB/DATOS/PELACUS.csv'
df_pelacus_estado   = pandas.read_csv(ruta_excel_pelacus,delimiter=';')
df_pelacus_estado["Fecha_control_calidad_secundario"] = pandas.to_datetime(df_pelacus_estado["Fecha_control_calidad_secundario"],format='%d/%m/%Y')
df_pelacus_estado["Fecha_procesado_laboratorio"] = pandas.to_datetime(df_pelacus_estado["Fecha_procesado_laboratorio"],format='%d/%m/%Y')
df_pelacus_estado["Fecha_analisis"] = pandas.to_datetime(df_pelacus_estado["Fecha_analisis"],format='%d/%m/%Y')
df_pelacus_estado["Fecha_finalizacion_campana"] = pandas.to_datetime(df_pelacus_estado["Fecha_finalizacion_campana"],format='%d/%m/%Y')





# Encabezados y titulos 
st.set_page_config(page_title="Datos de nutrientes", layout="wide") 
st.title("Campaña PELACUS")

# Bara de selección de fecha de consulta. 
num_semanas_intervalo = 12
t_actual            = datetime.date.today()
t_inicial           = t_actual-datetime.timedelta(weeks=num_semanas_intervalo) 

tiempo_consulta = st.sidebar.slider(
     "Selecciona fecha de consulta",
     min_value = t_inicial,
     max_value = t_actual,
     value     = t_actual,
     step      = datetime.timedelta(days=7),
     format="DD/MM/YYYY")
st.sidebar.write("Fecha consultada:", tiempo_consulta.strftime("%d-%m-%Y"))


# Asigna una fecha a los registros sin dato (suficientemente antigua)
tiempo_cero_ref            = datetime.date(2200,1,1)
end = pandas.to_datetime(tiempo_cero_ref)
df_pelacus_estado['Fecha_control_calidad_secundario'] = df_pelacus_estado['Fecha_control_calidad_secundario'].fillna(end)
df_pelacus_estado['Fecha_procesado_laboratorio'] = df_pelacus_estado['Fecha_procesado_laboratorio'].fillna(end)
df_pelacus_estado['Fecha_analisis'] = df_pelacus_estado['Fecha_analisis'].fillna(end)
df_pelacus_estado['Fecha_finalizacion_campana'] = df_pelacus_estado['Fecha_finalizacion_campana'].fillna(end)


## PROCESADO CORRESPONDIENTE A LA FECHA SELECCIONADA

# Determina el estado de los procesos 
df_pelacus_estado['ESTADO']    = ''
df_pelacus_estado['id_estado'] = 0

prueba_tiempos = df_pelacus_estado
elimina_no_tiempos = prueba_tiempos.drop(columns='ANO')
#for idato in range (2):
for idato in range (df_pelacus_estado.shape[0]):
    vector_tiempos = [df_pelacus_estado["Fecha_finalizacion_campana"][idato],df_pelacus_estado["Fecha_analisis"][idato],df_pelacus_estado["Fecha_procesado_laboratorio"][idato],df_pelacus_estado["Fecha_control_calidad_secundario"][idato]]
    for icompara in range(len(vector_tiempos)):
        if tiempo_consulta >= vector_tiempos[icompara]:
            df_pelacus_estado['id_estado'][idato] = icompara +1
       
    df_pelacus_estado['ESTADO'][idato] = listado_estados[df_pelacus_estado['id_estado'][idato]]


# Cuenta el numero de veces que se repite cada estado para sacar un gráfico pie-chart
num_valores = numpy.zeros(5,dtype=int)
for ivalor in range(5):
    try:
        num_valores[ivalor] = df_pelacus_estado['id_estado'].value_counts()[ivalor]
    except:
        pass
porcentajes = numpy.round((100*(num_valores/numpy.sum(num_valores))),0)

# Construye el gráfico
cm              = 1/2.54 # pulgadas a cm
fig, ax1 = plt.subplots(figsize=(8*cm, 8*cm))
#ax1.pie(num_valores, explode=explode_estados, colors=listado_colores,labels=listado_estados, autopct='%1.1f%%', shadow=True, startangle=90)
patches, texts= ax1.pie(num_valores, colors=listado_colores,shadow=True, startangle=90,radius=1.2)
ax1.axis('equal')  # Para representar el pie-chart como un circulo

# Representa y ordena la leyenda
etiquetas_leyenda = ['{0} - {1:1.0f} %'.format(i,j) for i,j in zip(listado_estados, porcentajes)]
plt.legend(patches, etiquetas_leyenda, loc='lower left', bbox_to_anchor=(-0.1, 1.),fontsize=8)

# Genera un subset del dataframe con los años en los que hay datos, entre los que se seleccionará la fecha a descargar
datos_disponibles = df_pelacus_estado.loc[df_pelacus_estado['id_estado'] >= 3]

# Genera un dataframe con las columnas que se quieran mostrar en la web
datos_visor = df_pelacus_estado.drop(columns=['Fecha_finalizacion_campana','Fecha_analisis','Fecha_procesado_laboratorio','Fecha_control_calidad_secundario','id_estado'])



# # Define los estilos para la tabla y el gráfico
# texto_estilo = '"""function(params) {' + '\n'
# for iestado in range(len(listado_estados)):
#     texto_estilo = texto_estilo + "if (params.value.includes('" + listado_estados[iestado] + "'))" + '\n'
#     texto_estilo = texto_estilo + "{return {'color': 'black', 'backgroundColor': '" + listado_colores[iestado] + "'}}" + '\n'
# texto_estilo = texto_estilo + '};"""'

cellsytle_jscode = st_aggrid.shared.JsCode(
"""function(params) {
if (params.value.includes('No disponible'))
{return {'color': 'black', 'backgroundColor': '#CD5C5C'}}
if (params.value.includes('Pendiente de análisis'))
{return {'color': 'black', 'backgroundColor': '#F4A460'}}
if (params.value.includes('Analizado'))
{return {'color': 'black', 'backgroundColor': '#87CEEB'}}
if (params.value.includes('Procesado primario'))
{return {'color': 'black', 'backgroundColor': '#66CDAA'}}
if (params.value.includes('Procesado secundario'))
{return {'color': 'black', 'backgroundColor': '#2E8B57'}}
};""")

    
#listado_estados = ['No disponible','Pendiente de análisis','Analizado','Procesado primario','Procesado secundario']
#listado_colores = ['#CD5C5C','#F4A460','#87CEEB','#66CDAA','#2E8B57']


########################################
### Muestra la informacion en la web ###
########################################



#Division en dos columnas, una para tabla otra para la imagen
col1, col2 = st.columns(2,gap="medium")

# Representacion de la tabla de estados
with col1:
    st.header("Listado de datos")
#    st_aggrid.AgGrid(df_pelacus_estado,width=800)
    gb = st_aggrid.grid_options_builder.GridOptionsBuilder.from_dataframe(datos_visor)
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