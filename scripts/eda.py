import pandas as pd

# 1. Definir las rutas de los archivos (ahora sin el .gz)
# Asegúrate de que los archivos .csv estén en la misma carpeta que tu script
ruta_listings = '../data/malaga/listings.csv'
ruta_calendar = '../data/malaga/calendar.csv'

print("⏳ Cargando los datasets completos (esto puede tardar unos segundos)...")

# 2. Leer los archivos CSV normales
# Quitamos compression='gzip', pero mantenemos low_memory=False
df_listings = pd.read_csv(ruta_listings, low_memory=False)
df_calendar = pd.read_csv(ruta_calendar, low_memory=False)

print("✅ ¡Archivos cargados con éxito!\n")

# 3. Exploración inicial de LISTINGS (Viviendas)
print("="*50)
print(" 🏠 ANÁLISIS DE LISTINGS (Viviendas)")
print("="*50)
print(f"Total de viviendas: {df_listings.shape[0]}")
print(f"Total de columnas (variables): {df_listings.shape[1]}")
print("\nTipos de datos y valores nulos:")
df_listings.info()

# Mostrar las 5 primeras filas de listings
display(df_listings.head())  # Si no usas Jupyter Notebook, cambia 'display' por 'print'

# 4. Exploración inicial de CALENDAR (Disponibilidad y precios diarios)
print("\n" + "="*50)
print(" 📅 ANÁLISIS DE CALENDAR (Disponibilidad 365 días)")
print("="*50)
print(f"Total de registros diarios: {df_calendar.shape[0]}")
print(f"Total de columnas: {df_calendar.shape[1]}")
print("\nTipos de datos y valores nulos:")
df_calendar.info()

# Mostrar las 5 primeras filas de calendar
display(df_calendar.head())