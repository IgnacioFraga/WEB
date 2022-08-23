# -*- coding: utf-8 -*-
"""
Created on Fri Aug  5 08:44:36 2022

@author: ifraga
"""


import streamlit as st
from PIL import Image




# Encabezados y titulos 
st.set_page_config(page_title="Datos de nutrientes", layout="wide") 
st.title("Datos de nutrientes disponibles en el C.O de A Coruña")

# Añade el logo del IEO
logo_IEO = 'C:/Users/ifraga/Desktop/03-DESARROLLOS/NUTRIENTES/WEB/DATOS/IMAGENES/logo-CSIC.jpg'
imagen   = Image.open(logo_IEO)
st.image(imagen)


