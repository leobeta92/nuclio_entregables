import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
import requests as rq
import lxml as lxml 
import re
from fuzzywuzzy import process

headers = {
    'User-Agent': 'Mozilla/5.0'
}

link_ctry = 'https://es.wikipedia.org/wiki/Campeonato_Europeo_de_Halterofilia'

def list_of_countries(link):
    link_info = rq.get(link, headers = headers)
    tables = pd.read_html(link_info.text, flavor= 'lxml')
    country_table = pd.DataFrame(tables[1]['País'])
    country_list = list(country_table['País'].transform(lambda x: re.split('\[',x)[0]).unique())
    country_list.append('AIN')
    country_list.sort()

    return country_list


country_list = list_of_countries(link_ctry)


def df_wiki_tables(link):
    link_info = rq.get(link, headers = headers)
    soup = BeautifulSoup(link_info.text, 'html.parser')

    year = re.findall(r'20\d{2}',soup.title.text)[0]

    tables = pd.read_html(link_info.text, flavor= 'lxml')
    tables_dict = {
        'masculino': format_tables(pd.DataFrame(tables[2]), 'Masculino', year),
        'femenino': format_tables(pd.DataFrame(tables[3]), 'Femenino', year),
        'medallas': pd.DataFrame(tables[4]),
        'paises': list(pd.DataFrame(tables[4])['País'].unique())
    }

    df_masc_fem = pd.concat([tables_dict['masculino'], tables_dict['femenino']], ignore_index= True)
    # masc_table = rename_tables(pd.DataFrame(tables[2]))
    # fem_table = rename_tables(pd.DataFrame(tables[3]))
    # return (masc_table, fem_table)
    return df_masc_fem

def rename_tables(table):
    return table.rename(columns= {
    'Evento': 'Eventos',
    'Unnamed: 1': "Oro",
    'Unnamed: 2': "Plata",
    'Unnamed: 3': "Bronce"
})

def format_tables(table, genero, year):
    table = rename_tables(table)
 
    table['Año'] = year
    table['Genero'] = genero

    return table
    

# Extrae la fecha y evento (modificando si lo requiere) de la columna "Eventos" y devuelve en un dicciónario.
def modificar_eventos(row):

    if bool(re.search('\+',row['Eventos'])):
        move_to_right_step1 = re.findall('[0-9]+\skg', row['Eventos'])
        move_to_right_step2 = re.split('\s', move_to_right_step1[0])
        move_to_right_step3 = move_to_right_step2[0] + "+ " + move_to_right_step2[1]
        evento = move_to_right_step3
    else:
        evento = re.findall('[0-9]+\skg', row['Eventos'])[0]

    fecha = row['Eventos'][row['Eventos'].find("(")+1:row['Eventos'].find(")")] 

    fecha_to_datetime = fechas_to_datetime(fecha, row['Año'])
        
    
    return {
        'evento': evento, 
        'fecha': fecha_to_datetime
    }


def fechas_to_datetime(fecha, anio):
    patron = r'^(0[1-9]|[12][0-9]|3[01]).(0[1-9]|1[0-2])'

    if pd.notnull(fecha) and re.fullmatch(patron, fecha):
        together = f'{fecha}.{anio}'
        # print(type(together))
        # new_date = pd.to_datetime(date_string, format='%d.%m', errors = 'coerce').strftime('%m-%d')
        new_date = pd.to_datetime(together, format='%d.%m.%Y', errors = 'coerce')

        return new_date
    else:
        return pd.NaT
    

"""
1. Separate name and country from results.
2. Approximate country from Step 1.
3. Remove country from Step 1.
4. Take out results and send to function.

"""
# Step 1
def get_name_country(value):
    if bool(re.findall(r'\[\d\]',value)):
        extract_name_country = re.sub(r'\[\d\]',' ',value)
        extract_name_country = re.match('^\w\D+\s',extract_name_country)[0]
    else:
        extract_name_country = re.match('^\w\D+\s',value)[0]
    
    trim_exact_name_country = re.split('[ \t]+$', extract_name_country)[0]

    if bool(re.findall('\[\d',trim_exact_name_country)):
        re.sub(r'\[\D', '', trim_exact_name_country)

    return trim_exact_name_country

# Step 2
def encontrar_similar(valor):

    resultado = process.extractOne(valor, country_list)
    valor_similar = resultado[0]
    probabilidad = resultado[1]
    if probabilidad < 90:
        return 'revisar'
    else:
        return valor_similar

# Step 3
def extrae_nombre(name_with_country, country):

    
    nombre_sin_pais = re.sub(r'\b' + re.escape(country) + r'\b', '', name_with_country)

    nombre_sin_espacios_trim = nombre_sin_pais.replace(r'\s+', ' ').strip()

    nombres_espacios_split = re.split('\s',nombre_sin_espacios_trim)

    nombre = nombres_espacios_split[0]
    apellido = " ".join(nombres_espacios_split[1:])
    
    return {
        'nombre': nombre,
        'apellido': apellido
    }

# Step 4
def get_results(value):
    remove_brackets = re.sub(r'\[\D\s\d|\[\d\]',' ',value)
    find_scores = re.findall('\d+',remove_brackets)

    resultado_1 = find_scores[0]
    resultado_2 = find_scores[1]
    resultado_total = find_scores[2]

    return {
        'arrancada': resultado_1,
        'dos_tiempos': resultado_2,
        'total' : resultado_total
    }



def extract_information(value):

    # Get Name/Country
    name_with_country = get_name_country(value)

    # Guess Country
    country = encontrar_similar(name_with_country)
    
    # Take out country from name.
    name_surname = extrae_nombre(name_with_country, country)
    
    # Grab results from the value.
    results = get_results(value)

    return {
        'pais': country,
        'nombre': name_surname['nombre'],
        'apellido': name_surname['apellido'],
        'arrancada': results['arrancada'],
        'dos_tiempos': results['dos_tiempos'],
        'total' : results['total']
    }

'''
1. Get table to have "eventos", "oro", "plata", "bronce", ("Año", "Género") <-- which are in the provided tables and not in the web scraping.
'''



# Hice todas estas funciónes, pero les ejecuté individualmente. Sería más eficiente usar una función para ejecutar estas 4.
'''
def encontrar_similar(valor, valores_validos):

    # Para simplificar el notebook, traté de poner el link adentro del utils.py archivo y que la función se ejecute sin que yo especifico el enlace. Pero este método se demoró muchisimo cada vez que ejecuté la función encontrar_similar. Casi 1.5 minutos, usando el enlace en el notebook. Dejo aquí el enlace para mostrar el trabajo.

    # country_list = list_of_countries()

    resultado = process.extractOne(valor, valores_validos)
    valor_similar = resultado[0]
    probabilidad = resultado[1]
    if probabilidad < 90:
        return 'revisar'
    else:
        return valor_similar

def get_results(value):
    remove_brackets = re.sub(r'\[\D\s\d|\[\d\]',' ',value)
    find_scores = re.findall('\d+',remove_brackets)

    resultado_1 = find_scores[0]
    resultado_2 = find_scores[1]
    resultado_total = find_scores[2]

    return {
        'arrancada': resultado_1,
        'dos_tiempos': resultado_2,
        'total' : resultado_total
    }

def get_name_country(value):
    if bool(re.findall(r'\[\d\]',value)):
        extract_name_country = re.sub(r'\[\d\]',' ',value)
        extract_name_country = re.match('^\w\D+\s',extract_name_country)[0]
    else:
        extract_name_country = re.match('^\w\D+\s',value)[0]
    
    trim_exact_name_country = re.split('[ \t]+$', extract_name_country)[0]

    return trim_exact_name_country


def extrae_nombre(row):

    # espana_example.apply(lambda row: re.sub(r'\b' + re.escape(row['país_corregido']) + r'\b', '', row['atleta']), axis=1)
    #     .str.replace(r'\s+', ' ', regex=True)   # collapse extra spaces
    #     .str.strip()

    nombre_sin_pais = re.sub(r'\b' + re.escape(row['país_corregido']) + r'\b', '', row['atleta'])

    nombre_sin_espacios_trim = nombre_sin_pais.replace(r'\s+', ' ').strip()

    nombres_espacios_split = re.split('\s',nombre_sin_espacios_trim)

    nombre = nombres_espacios_split[0]
    apellido = " ".join(nombres_espacios_split[1:])
    
    return {
        'nombre': nombre,
        'apellido': apellido
    }
'''