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
import datetime
import numpy
import psycopg2
from sqlalchemy import create_engine

pandas.options.mode.chained_assignment = None

# Parámetros de la base de datos
base_datos = 'IEO_Coruna'
usuario    = 'postgres'
contrasena = 'IEO2022'
puerto     = '5432'

# Parámetros generales del estado de los procesos
# 0- No disponible 1- Pendiente de análisis 2-Analizado 3-Procesado primario 4-Procesado + CC
listado_estados = ['No disponible','Pendiente de análisis','Analizado, pendiente de procesado','Procesado primario','Procesado secundario']
listado_colores = ['#CD5C5C','#F4A460','#87CEEB','#66CDAA','#2E8B57']

directorio_temporal = 'C:/Users/ifraga/Desktop/03-DESARROLLOS/NUTRIENTES/WEB/DATOS'

programa            = 'PELACUS'


### Consulta a la base de datos las fechas de los distintos procesos

conn   = psycopg2.connect(database=base_datos, user=usuario, password=contrasena, port=puerto)
cursor = conn.cursor()

# Identificador del programa (PELACUS en este caso)
instruccion_sql = "SELECT id_programa FROM programas WHERE nombre_programa = 'PELACUS' ;"
cursor.execute(instruccion_sql)
id_programa =cursor.fetchone()[0]
conn.commit()
cursor.close()
conn.close()

# Recupera la información de la tabla como un dataframe
engine                   = create_engine('postgresql://postgres:' + contrasena + '@localhost:' + puerto + '/' + base_datos)
dbConnection             = engine.connect();
temporal_estado_procesos = pandas.read_sql_table('estado_procesos', con=dbConnection)
dbConnection.close();

# Extrae los datos disponibles del programa, sin identificador del programa o del registro
estado_procesos_programa = temporal_estado_procesos[temporal_estado_procesos['programa']==id_programa]
estado_procesos_programa = estado_procesos_programa.drop(['id_proceso','programa'], axis = 1)
estado_procesos_programa = estado_procesos_programa.fillna(numpy.nan).replace([numpy.nan], [None])




### Encabezados y titulos 
st.set_page_config(page_title="Datos de nutrientes", layout="wide") 
st.title("Campaña PELACUS")



## Bara de selección de fecha de consulta. 
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

#tiempo_consulta = datetime.date(2019,12,5)

### Determina el estado de cada proceso, en la fecha seleccionada
estado_procesos_programa['estado']    = ''
estado_procesos_programa['contacto']    = ''
estado_procesos_programa['id_estado'] = 0
for ianho in range(estado_procesos_programa.shape[0]):

    # Caso 4. Fecha de consulta posterior al control de calidad secundario.
    if estado_procesos_programa['fecha_procesado_secundario'][ianho] is False:
        
        if tiempo_consulta >= (estado_procesos_programa['fecha_procesado_secundario'][ianho]).date():  # is not None:      
            estado_procesos_programa['id_estado'][ianho] = 4 
            estado_procesos_programa['contacto'][ianho] = estado_procesos_programa['persona_contacto_procesado'][ianho]      
        
    else:
        # Caso 3. Fecha de consulta posterior al control de calidad primario pero anterior al secundario.
        if pandas.isnull(estado_procesos_programa['fecha_procesado_primario'][ianho]) is False:
            if tiempo_consulta >= (estado_procesos_programa['fecha_procesado_primario'][ianho]).date():  #estado_procesos_programa['fecha_procesado_primario'][ianho] is not None:     
                estado_procesos_programa['id_estado'][ianho] = 3
                estado_procesos_programa['contacto'][ianho] = estado_procesos_programa['persona_contacto_procesado'][ianho] 
            
        else:
            
            # Caso 2. Fecha de consulta posterior al análisis de laboratorio pero anterior a realizar el control de calidad primario.
            if pandas.isnull(estado_procesos_programa['fecha_analisis_laboratorio'][ianho]) is False:
                if tiempo_consulta >= (estado_procesos_programa['fecha_analisis_laboratorio'][ianho]).date():  # estado_procesos_programa['fecha_analisis_laboratorio'][ianho] is not None:     
                    estado_procesos_programa['id_estado'][ianho] = 2
                    estado_procesos_programa['contacto'][ianho] = estado_procesos_programa['persona_contacto_muestreo'][ianho] 
                    
            else:
                # Caso 1. Fecha de consulta posterior a terminar la campaña pero anterior al análisis en laboratorio, o análisis no disponible. 
                if pandas.isnull(estado_procesos_programa['fecha_final_muestreo'][ianho]) is False:
                    if tiempo_consulta >= (estado_procesos_programa['fecha_final_muestreo'][ianho]).date(): #estado_procesos_programa['fecha_final_muestreo'][ianho] is not None:
                        estado_procesos_programa['id_estado'][ianho] = 1 
                        estado_procesos_programa['contacto'][ianho] = estado_procesos_programa['persona_contacto_muestreo'][ianho]


    estado_procesos_programa['estado'][ianho] = listado_estados[estado_procesos_programa['id_estado'][ianho]]
                
    
    
    
# Cuenta el numero de veces que se repite cada estado para sacar un gráfico pie-chart
num_valores = numpy.zeros(5,dtype=int)
for ivalor in range(5):
    try:
        num_valores[ivalor] = estado_procesos_programa['id_estado'].value_counts()[ivalor]
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
datos_disponibles = estado_procesos_programa.loc[estado_procesos_programa['id_estado'] >= 3]

# Genera un dataframe con las columnas que se quieran mostrar en la web
datos_visor = estado_procesos_programa.drop(columns=['nombre_programa','fecha_final_muestreo','fecha_analisis_laboratorio','fecha_procesado_primario','fecha_procesado_secundario','id_estado','persona_contacto_muestreo','persona_contacto_procesado'])


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

   

########################################
### Muestra la informacion en la web ###
########################################



#Division en dos columnas, una para tabla otra para la imagen
col1, col2 = st.columns(2,gap="medium")

# Representacion de la tabla de estados
with col1:
    st.header("Listado de datos")
    gb = st_aggrid.grid_options_builder.GridOptionsBuilder.from_dataframe(datos_visor)
    gb.configure_column("estado", cellStyle=cellsytle_jscode)

    gridOptions = gb.build()
    
    data = st_aggrid.AgGrid(
        datos_visor,
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
        datos_disponibles['año'])


    anho_consulta         = seleccion #☺datos_disponibles['año'][0]
    fecha_inicio_consulta = datetime.date(anho_consulta,1,1)
    fecha_final_consulta  = datetime.date(anho_consulta+1,1,1)

    
    # Primero recupera los registros correspondientes al periodo evaluado y al año consultado
    conn   = psycopg2.connect(database=base_datos, user=usuario, password=contrasena, port=puerto)
    cursor = conn.cursor()
    instruccion_sql = "SELECT id_muestreo FROM muestreos_discretos INNER JOIN estaciones ON muestreos_discretos.estacion = estaciones.id_estacion WHERE estaciones.programa = %s AND muestreos_discretos.fecha_muestreo >= %s AND muestreos_discretos.fecha_muestreo < %s;"
    cursor.execute(instruccion_sql,(id_programa,fecha_inicio_consulta,fecha_final_consulta))
    #registros_consulta =cursor.fetchall()
    registros_consulta = [r[0] for r in cursor.fetchall()]
    conn.commit()
    cursor.close()
    conn.close()
    
    indices_dataframe         = numpy.arange(0,len(registros_consulta),1,dtype=int)
    
    # A continuacion recupera las tablas de datos biogeoquimicos y físicos
    engine                       = create_engine('postgresql://postgres:' + contrasena + '@localhost:' + puerto + '/' + base_datos)
    dbConnection                 = engine.connect();
    temporal_estaciones          = pandas.read_sql_table('estaciones', con=dbConnection)
    temporal_muestreos           = pandas.read_sql_table('muestreos_discretos', con=dbConnection)
    temporal_datos_biogeoquimica = pandas.read_sql_table('datos_discretos_biogeoquimica', con=dbConnection)
    temporal_datos_fisica        = pandas.read_sql_table('datos_discretos_fisica', con=dbConnection)
    dbConnection.close(); 
  
    # Compón dataframes con los registros que interesan y elimina el temporal, para reducir la memoria ocupada
    # En cada dataframe hay que re-definir el indice del registro para luego poder juntar los 3 dataframes 
    datos_biogeoquimicos            = temporal_datos_biogeoquimica[temporal_datos_biogeoquimica['muestreo'].isin(registros_consulta)]
    datos_biogeoquimicos['id_temp'] = indices_dataframe
    datos_biogeoquimicos.set_index('id_temp',drop=True,append=False,inplace=True)
    del(temporal_datos_biogeoquimica)
    datos_biogeoquimicos = datos_biogeoquimicos.drop(columns=['id_disc_biogeoquim','muestreo'])
    
    datos_fisicos = temporal_datos_fisica[temporal_datos_fisica['muestreo'].isin(registros_consulta)]
    datos_fisicos['id_temp'] = indices_dataframe
    datos_fisicos.set_index('id_temp',drop=True,append=False,inplace=True) 
    del(temporal_datos_fisica)
    datos_fisicos = datos_fisicos.drop(columns=['id_disc_fisica','muestreo'])
    
    datos_muestreo = temporal_muestreos[temporal_muestreos['id_muestreo'].isin(registros_consulta)]
    datos_muestreo['id_temp'] = indices_dataframe
    datos_muestreo.set_index('id_temp',drop=True,append=False,inplace=True)      
    datos_muestreo = datos_muestreo.drop(columns=['id_muestreo','configuracion_perfilador','configuracion_superficie'])
    datos_muestreo['fecha_muestreo'] = pandas.to_datetime(datos_muestreo['fecha_muestreo']).dt.date
    datos_muestreo['hora_muestreo'] = datos_muestreo['hora_muestreo'].apply(lambda x: x.replace(tzinfo=None))   
    del(temporal_muestreos)
    
    
    
    # Añade las coordenadas de cada muestreo, a partir de la estación asociada
    datos_muestreo['latitud']  = numpy.zeros(datos_muestreo.shape[0])
    datos_muestreo['longitud'] = numpy.zeros(datos_muestreo.shape[0])    
    for iregistro in range(datos_muestreo.shape[0]):
        datos_muestreo['latitud'][iregistro] = temporal_estaciones['latitud'][temporal_estaciones['id_estacion']==datos_muestreo['estacion'][iregistro]]
        datos_muestreo['longitud'][iregistro] = temporal_estaciones['longitud'][temporal_estaciones['id_estacion']==datos_muestreo['estacion'][iregistro]]  
    del(temporal_estaciones)
    datos_muestreo = datos_muestreo.drop(columns=['estacion'])
    
    # Une los dataframes resultantes
    datos_compuesto = pandas.concat([datos_muestreo, datos_fisicos, datos_biogeoquimicos], axis=1, join='inner')
     
    # Reemplaza los NaN por None
    datos_compuesto = datos_compuesto.replace({numpy.nan:None})
    
    
     
    ## Botón para exportar los resultados
    nombre_archivo =  programa + str(anho_consulta) + '.xlsx'

    output = BytesIO()
    writer = pandas.ExcelWriter(output, engine='xlsxwriter')
    datos_compuesto.to_excel(writer, index=False, sheet_name='DATOS')
    workbook = writer.book
    worksheet = writer.sheets['DATOS']
    writer.save()
    datos_exporta = output.getvalue()

    st.download_button(
        label="DESCARGA LOS DATOS SELECCIONADOS",
        data=datos_exporta,
        file_name=nombre_archivo,
        help= 'Descarga un archivo .csv con los datos solicitados',
        mime="application/vnd.ms-excel"
    )


