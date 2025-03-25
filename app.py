import pandas as pd
import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

# Nombre del archivo Excel
excel_filename = "REPORTE-PRODUCTOS-PQUA-SimplifiCA-1-DE-JUNIO-DE-2024.xlsx"

# Función para obtener todas las palabras únicas de la columna 10 de cada hoja del archivo Excel
def obtener_palabras_columna_10(filename):
    palabras_encontradas = []

    # Cargar el archivo Excel
    xls = pd.ExcelFile(filename)

    # Iterar sobre cada hoja del archivo Excel
    for sheet_name in xls.sheet_names:
        # Leer la hoja del Excel sin encabezados
        df = pd.read_excel(xls, sheet_name=sheet_name, header=None)

        # Verificar si hay al menos 11 columnas para acceder a la columna número 10 (índice 9 en Python)
        if 9 < len(df.columns):
            # Obtener valores únicos de la columna número 10 (índice 9 en Python)
            valores_columna_10 = df.iloc[:, 9].dropna().astype(str).unique().tolist()

            # Agregar los valores únicos encontrados a la lista
            palabras_encontradas.extend(valores_columna_10)

    # Eliminar duplicados y ordenar la lista de palabras encontradas
    palabras_encontradas = sorted(set(palabras_encontradas))

    return palabras_encontradas

# Función para filtrar y obtener las filas que contienen palabras seleccionadas en la columna 10
def filtrar_y_obtener_tabla(filename, palabras_seleccionadas):
    filas_seleccionadas = []
    xls = pd.ExcelFile(filename)
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name, header=None, dtype=str)  # Leer sin encabezados y mantener como str
        if 9 < len(df.columns):  # Asegurar que hay al menos 10 columnas para acceder a la columna número 10
            for index, row in df.iterrows():
                for palabra in palabras_seleccionadas:
                    if palabra.lower() in str(row.iloc[9]).lower():  # Buscar en la columna 10 (índice 9 en Python)
                        filas_seleccionadas.append(row)
    if filas_seleccionadas:
        df_resultado = pd.concat(filas_seleccionadas, axis=1).T
        # Renombrar columnas según los encabezados requeridos
        df_resultado.columns = [
            "NOMBRE EMPRESA", "DIRECCIÓN", "TELEFONO", "CORREO ELECTRÓNICO", 
            "DOCUMENTO", "NOMBRE PRODUCTO", "INGREDIENTE ACTIVO", "CONCENTRACIÓN", 
            "TIPO DE FORMULACIÓN", "CLASE DE PRODUCTO", "NÚMERO DE REGISTRO", "FECHA DE REGISTRO"
        ]
        # Convertir la columna TELEFONO de nuevo a str si es necesario
        df_resultado["TELEFONO"] = df_resultado["TELEFONO"].astype(str)
        return df_resultado
    else:
        return pd.DataFrame()

# Función para obtener el enlace que contiene una palabra en una página web
def obtener_enlace_palabra(url, palabra):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        enlaces = soup.find_all('a', href=True)
        for enlace in enlaces:
            enlace_absoluto = urljoin(url, enlace['href'])
            if palabra.lower() in enlace.text.lower():
                return enlace_absoluto
        st.warning(f"No se encontró la palabra '{palabra}' en ningún enlace de la página.")
    else:
        st.error("Error al obtener la página web")
    return None

# Función para limpiar el valor y eliminar los símbolos "<" y ">"
def clean_value(value):
    value = value.strip()
    value = re.sub(r'[<>]', '', value)
    return value

# Función para extraer los valores específicos de una página web
def extraer_valores(soup):
    valores = {
        "Solubility - In water at 20 °C (mg l⁻¹)": None,
        "DT₅₀ (typical)": None,
        "Koc (mL g⁻¹)": None
    }

    # Buscar "Solubility - In water at 20 °C (mg l⁻¹)"
    for th in soup.find_all("th", class_="rowhead"):
        if "Solubility - In water at 20 °C (mg l⁻¹)" in th.text.strip():
            td_element = th.find_next("td", class_="data3")
            if td_element:
                valores["Solubility - In water at 20 °C (mg l⁻¹)"] = clean_value(td_element.text.strip())
            break

    # Buscar "DT₅₀ (typical)" y "Koc (mL g⁻¹)"
    for th in soup.find_all("th", class_="rowhead_split"):
        row_header_text = th.text.strip()
        data3_td = th.find_next("td", class_="data3")
        if "DT₅₀ (typical)" in row_header_text:
            if data3_td:
                valores["DT₅₀ (typical)"] = clean_value(data3_td.text.strip())
    # Buscar "Koc (mL g⁻¹)"
    for th in soup.find_all("th", class_="rowhead_split"):
        row_header_text = th.text.strip()
        data3_td = th.find_next("td", class_="data3")
        if "Koc (mL g⁻¹)" in row_header_text:
            if data3_td:
                valores["Koc (mL g⁻¹)"] = clean_value(data3_td.text.strip())
            break

    return valores

# Función principal de la aplicación Streamlit
def main():
    st.title("Análisis Toxicológico de Ingredientes Activos")

    # Obtener las palabras únicas de la columna 10 y almacenar en st.session_state
    if 'palabras_columna_10' not in st.session_state:
        st.session_state.palabras_columna_10 = obtener_palabras_columna_10(excel_filename)

    # Componente multiselect para seleccionar palabras de la columna 10
    filtro_seleccionado = st.multiselect(
        "Selecciona palabras para filtrar:",
        options=st.session_state.palabras_columna_10,
        key="filtro_multiselect"
    )

    # Mostrar las palabras seleccionadas
    st.write("Palabras seleccionadas:")
    st.write(filtro_seleccionado)

    # Botón para realizar el filtrado y generar la nueva tabla
    if st.button("Filtrar y generar tabla"):
        if filtro_seleccionado:
            df_filtrado = filtrar_y_obtener_tabla(excel_filename, filtro_seleccionado)
            if not df_filtrado.empty:
                st.write("Tabla filtrada:")
                st.dataframe(df_filtrado)

                # Obtener y mostrar las palabras únicas de la columna "INGREDIENTE ACTIVO" de la tabla filtrada
                ingredientes_activos_unicos = df_filtrado["INGREDIENTE ACTIVO"].drop_duplicates().tolist()
                st.write("Ingredientes activos únicos en la tabla filtrada:")
                st.write(ingredientes_activos_unicos)

                # Actualizar la lista all_products con las palabras únicas de la tabla filtrada
                st.session_state.all_products = ingredientes_activos_unicos

    # Mostrar el multiselect para seleccionar uno o más ingredientes activos
    if 'all_products' not in st.session_state:
        st.session_state.all_products = []
    palabras = st.multiselect("Seleccione uno o más ingredientes activos:", st.session_state.all_products)

    # Diccionario para almacenar dosis para cada ingrediente activo
    dosis_dict = {}

    if palabras:
        st.subheader("Ingrese las dosis para cada ingrediente activo seleccionado:")

        # Crear un formulario para ingresar dosis por cada ingrediente seleccionado
        with st.form(key='dosis_form'):
            for palabra in palabras:
                if palabra != "Selecciona un I.A":
                    dosis_dict[palabra] = st.number_input(f"Dosis para {palabra}:", min_value=0.0, format="%f")
            submit_button = st.form_submit_button(label='Buscar')

        # Botón para iniciar la búsqueda
        if submit_button:
            resultados = []
            valores_extraidos = []  # Para almacenar los valores extraídos

            for palabra, dosis in dosis_dict.items():
                if palabra != "Selecciona un I.A":
                    # Obtener el enlace que contiene la palabra
                    url_base = "https://sitem.herts.ac.uk/aeru/ppdb/en/atoz.htm"
                    enlace_palabra = obtener_enlace_palabra(url_base, palabra)

                    if enlace_palabra:
                        st.success(f"Se encontró el enlace que contiene la palabra '{palabra}': {enlace_palabra}")

                        # Realizar la solicitud GET al enlace encontrado
                        response = requests.get(enlace_palabra)

                        if response.status_code == 200:
                            soup = BeautifulSoup(response.content, "html.parser")

                            # Extraer valores específicos
                            valores = extraer_valores(soup)
                            valores["Ingrediente activo"] = palabra
                            valores["Dosis ingresada"] = dosis

                            # Buscar información para "Mammals - Acute oral LD₅₀ (mg kg⁻¹)"
                            th_elements = soup.find_all("th", class_="rowhead")
                            mammal_value = None
                            for th in th_elements:
                                if "Mammals - Acute oral LD₅₀ (mg kg⁻¹)" in th.text.strip():
                                    td_element = th.find_next("td", class_="data3")
                                    if td_element:
                                        mammal_value = clean_value(td_element.text.strip())
                                    break

                            # Buscar información para "Contact acute LD₅₀ (worst case from 24, 48 and 72 hour values - μg bee⁻¹)"
                            th_elements = soup.find_all("th", class_="rowhead_split")
                            bee_value = None
                            for th in th_elements:
                                if "Contact acute LD₅₀ (worst case from 24, 48 and 72 hour values - μg bee⁻¹)" in th.text.strip():
                                    td_row_header = th.find_next("td", class_="row_header")
                                    if td_row_header:
                                        td_data3 = td_row_header.find_next("td", class_="data3")
                                        if td_data3:
                                            bee_value = clean_value(td_data3.text.strip())
                                    break

                            if mammal_value and bee_value:
                                try:
                                    # Calcular las UTm y UTi
                                    utm = dosis / float(mammal_value)
                                    uti = dosis / float(bee_value)

                                    # Almacenar los resultados
                                    resultados.append({
                                        "Ingrediente activo": palabra,
                                        "Mammals - Acute oral LD₅₀ (mg kg⁻¹)": mammal_value,
                                        "Contact acute LD₅₀ (μg bee⁻¹)": bee_value,
                                        "Dosis ingresada": dosis,
                                        "UTm (Unidades Toxicológicas para mamíferos)": utm,
                                        "UTi (Unidades Toxicológicas para insectos)": uti
                                    })

                                    # Almacenar los valores extraídos
                                    valores_extraidos.append(valores)
                                except ValueError:
                                    st.warning(f"Error al convertir valores para '{palabra}'. Verifique los datos.")
                            else:
                                st.warning(f"No se encontraron los valores necesarios en la página para '{palabra}'.")

                        else:
                            st.error(f"No se pudo acceder al enlace: {response.status_code}")

                    else:
                        st.warning(f"No se encontró ningún enlace que contenga la palabra '{palabra}'.")

            # Mostrar los resultados en una tabla
            if resultados:
                st.subheader("Resultados del Análisis Toxicológico:")
                df_resultados = pd.DataFrame(resultados)
                st.dataframe(df_resultados)

                # Mostrar valores extraídos
                st.subheader("Valores de Solubilidad, DT50 y Koc:")
                df_valores = pd.DataFrame(valores_extraidos)
                st.dataframe(df_valores)

if __name__ == "__main__":
    main()
