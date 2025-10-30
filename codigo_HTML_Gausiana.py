import os
from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from gaussian_ch4 import preprocess_and_invert
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import pytz
from sklearn.metrics import pairwise_distances

app = Flask(__name__)

# Asegurarse de que existe el directorio para subir archivos
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Zona horaria UTC-5
UTC_MINUS_5 = pytz.timezone('America/Bogota')

def parse_gpx_file(gpx_file):
    """Parse GPX file and extract trackpoints with timestamps"""
    tree = ET.parse(gpx_file)
    root = tree.getroot()
    
    # Namespace para GPX
    ns = {'gpx': 'http://www.topografix.com/GPX/1/1'}
    
    trackpoints = []
    for trkpt in root.findall('.//gpx:trkpt', ns):
        lat = float(trkpt.get('lat'))
        lon = float(trkpt.get('lon'))
        
        ele_elem = trkpt.find('gpx:ele', ns)
        ele = float(ele_elem.text) if ele_elem is not None else 0.0
        
        time_elem = trkpt.find('gpx:time', ns)
        if time_elem is not None:
            # Parse ISO format timestamp and convert to UTC-5
            timestamp = datetime.fromisoformat(time_elem.text.replace('Z', '+00:00'))
            timestamp = timestamp.astimezone(UTC_MINUS_5)
            
            trackpoints.append({
                'lat': lat,
                'lon': lon,
                'elevation': ele,
                'timestamp': timestamp
            })
    
    return pd.DataFrame(trackpoints)

def parse_data_file(data_file, gas_type='CH4'):
    """Parse .data file from LI-7810 analyzer"""
    # Leer el archivo buscando la línea que empieza con DATAH (header)
    with open(data_file, 'r') as f:
        lines = f.readlines()
    
    # Encontrar índice del header
    header_idx = None
    for i, line in enumerate(lines):
        if line.startswith('DATAH'):
            header_idx = i
            break
    
    if header_idx is None:
        raise ValueError("No se encontró el header DATAH en el archivo")
    
    # Leer columnas del header
    header_line = lines[header_idx].strip().split('\t')
    header_cols = [col.strip() for col in header_line]
    
    # Leer datos
    data_rows = []
    for line in lines[header_idx + 2:]:  # Saltar DATAH y DATAU
        if line.startswith('DATA\t'):
            row = line.strip().split('\t')
            data_rows.append(row[1:])  # Quitar 'DATA' del inicio
    
    # Crear DataFrame
    df = pd.DataFrame(data_rows, columns=header_cols[1:])
    
    # Convertir columnas numéricas
    numeric_cols = ['SECONDS', 'H2O', 'CO2', 'CH4']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Combinar DATE y TIME para crear timestamp
    df['timestamp'] = pd.to_datetime(df['DATE'] + ' ' + df['TIME'], errors='coerce')
    
    # Convertir a UTC-5 (el archivo dice America/Bogota que es UTC-5)
    df['timestamp'] = df['timestamp'].dt.tz_localize(UTC_MINUS_5)
    
    # Seleccionar columna de gas
    gas_column_map = {
        'CH4': 'CH4',  # ppb (lo mantendremos en ppb)
        'CO2': 'CO2',  # ppm
        'H2O': 'H2O'   # ppm
    }
    
    if gas_type not in gas_column_map:
        raise ValueError(f"Tipo de gas no válido: {gas_type}")
    
    gas_col = gas_column_map[gas_type]
    
    # Mantener las unidades originales
    df['gas_concentration'] = df[gas_col]
    df['gas_type'] = gas_type
    
    # Guardar las unidades
    if gas_type == 'CH4':
        df['gas_units'] = 'ppb'
    else:
        df['gas_units'] = 'ppm'
    
    # Debug: imprimir algunos valores
    print(f"\n=== DEBUG: Parseo de archivo .data para {gas_type} ===")
    print(f"Total de filas antes de dropna: {len(df)}")
    print(f"Valores no nulos de {gas_col}: {df[gas_col].notna().sum()}")
    print(f"Primeros 10 valores de {gas_col}:")
    print(df[gas_col].head(10))
    print("="*50)
    
    result_df = df[['timestamp', 'gas_concentration', 'gas_type', 'gas_units']].dropna()
    print(f"Total de filas después de dropna: {len(result_df)}")
    if len(result_df) > 0:
        print(f"Primeros 5 valores gas_concentration: {result_df['gas_concentration'].head().tolist()}")
    
    return result_df

def merge_gps_and_gas_data(gps_df, gas_df):
    """Merge GPS and gas analyzer data by matching timestamps"""
    # Asegurarse de que ambos timestamps estén en UTC-5
    gps_df['timestamp'] = pd.to_datetime(gps_df['timestamp'])
    gas_df['timestamp'] = pd.to_datetime(gas_df['timestamp'])
    
    # Merge asof (nearest timestamp matching)
    merged_df = pd.merge_asof(
        gps_df.sort_values('timestamp'),
        gas_df.sort_values('timestamp'),
        on='timestamp',
        direction='nearest',
        tolerance=pd.Timedelta('5s')  # Tolerancia de 5 segundos
    )
    
    return merged_df.dropna()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    import sys
    
    # Escribir a archivo de log
    with open('debug_log.txt', 'w', encoding='utf-8') as f:
        f.write("="*60 + "\n")
        f.write("=== INICIO DE PROCESAMIENTO DE ARCHIVOS ===\n")
        f.write("="*60 + "\n")
    
    print("\n" + "="*60, flush=True)
    sys.stdout.flush()
    print("=== INICIO DE PROCESAMIENTO DE ARCHIVOS ===", flush=True)
    sys.stdout.flush()
    print("="*60, flush=True)
    sys.stdout.flush()
    
    # Verificar que se hayan subido los archivos necesarios
    if 'dataFile' not in request.files or 'gpxFile' not in request.files:
        return jsonify({'error': 'Se requieren ambos archivos: .data y .gpx'})
    
    data_file = request.files['dataFile']
    gpx_file = request.files['gpxFile']
    gas_type = request.form.get('gasType', 'CH4')
    
    with open('debug_log.txt', 'a', encoding='utf-8') as f:
        f.write(f"Archivo .data: {data_file.filename}\n")
        f.write(f"Archivo .gpx: {gpx_file.filename}\n")
        f.write(f"Tipo de gas: {gas_type}\n")
    
    print(f"Archivo .data: {data_file.filename}", flush=True)
    print(f"Archivo .gpx: {gpx_file.filename}", flush=True)
    print(f"Tipo de gas: {gas_type}", flush=True)
    sys.stdout.flush()
    
    if data_file.filename == '' or gpx_file.filename == '':
        return jsonify({'error': 'Archivos no seleccionados'})
    
    try:
        # Guardar archivos temporalmente
        data_path = os.path.join(app.config['UPLOAD_FOLDER'], data_file.filename)
        gpx_path = os.path.join(app.config['UPLOAD_FOLDER'], gpx_file.filename)
        data_file.save(data_path)
        gpx_file.save(gpx_path)
        
        print("Archivos guardados temporalmente")
        
        # Parsear archivos
        gps_df = parse_gpx_file(gpx_path)
        print(f"GPS DataFrame: {len(gps_df)} puntos")
        
        gas_df = parse_data_file(data_path, gas_type)
        print(f"Gas DataFrame: {len(gas_df)} puntos")
        print(f"Primeros valores de gas: {gas_df['gas_concentration'].head().tolist()}")
        
        with open('debug_log.txt', 'a', encoding='utf-8') as f:
            f.write(f"GPS DataFrame: {len(gps_df)} puntos\n")
            f.write(f"Gas DataFrame: {len(gas_df)} puntos\n")
            f.write(f"Primeros valores de gas: {gas_df['gas_concentration'].head().tolist()}\n")
        
        # Combinar datos
        merged_df = merge_gps_and_gas_data(gps_df, gas_df)
        
        print(f"Merged DataFrame: {len(merged_df)} puntos")
        print(f"Primeros valores de gas en merged: {merged_df['gas_concentration'].head().tolist()}")
        
        with open('debug_log.txt', 'a', encoding='utf-8') as f:
            f.write(f"Merged DataFrame: {len(merged_df)} puntos\n")
            f.write(f"Primeros valores de gas en merged: {merged_df['gas_concentration'].head().tolist()}\n")
        
        if len(merged_df) == 0:
            return jsonify({'error': 'No se pudieron combinar los datos GPS y del analizador'})
        
        # Preparar datos para análisis gaussiano - VERSIÓN MEJORADA V2
        
        # 1. BACKGROUND DINÁMICO: usar percentil 10 (más robusto que percentil 5)
        background_default = merged_df['gas_concentration'].quantile(0.10)
        
        # 2. UBICACIÓN DE LA FUENTE: usar el punto de MÁXIMA concentración
        max_conc_idx = merged_df['gas_concentration'].idxmax()
        source_lat = merged_df.loc[max_conc_idx, 'lat']
        source_lon = merged_df.loc[max_conc_idx, 'lon']
        
        # 3. ESTIMACIÓN DE DIRECCIÓN DEL VIENTO: calcular vector desde centroide a máxima concentración
        centroid_lat = merged_df['lat'].mean()
        centroid_lon = merged_df['lon'].mean()
        
        # Vector de centroide a fuente
        dlat = source_lat - centroid_lat
        dlon = source_lon - centroid_lon
        
        # Convertir a ángulo meteorológico (desde donde viene el viento)
        # El ángulo va desde el centroide (donde está la mayoría de puntos) hacia la fuente
        bearing_towards_source = (np.degrees(np.arctan2(dlon, dlat)) + 360) % 360
        # El viento viene desde la dirección opuesta
        wind_dir_estimated = (bearing_towards_source + 180) % 360
        
        # 4. VELOCIDAD DEL VIENTO: estimar desde rango de distancias
        from sklearn.metrics import pairwise_distances
        coords = merged_df[['lat', 'lon']].values
        distances = pairwise_distances(coords)
        max_distance_km = np.max(distances) * 111  # Aproximación: 1° ≈ 111 km
        # A mayor dispersión, mayor velocidad (heurística simple)
        wind_speed_estimated = np.clip(1.0 + max_distance_km * 5, 1.0, 8.0)
        
        print(f"\n=== PARÁMETROS ESTIMADOS DEL MODELO ===")
        print(f"Background: {background_default:.2f}")
        print(f"Fuente en: lat={source_lat:.6f}, lon={source_lon:.6f}")
        print(f"Centroide en: lat={centroid_lat:.6f}, lon={centroid_lon:.6f}")
        print(f"Dirección del viento estimada: {wind_dir_estimated:.1f}°")
        print(f"Velocidad del viento estimada: {wind_speed_estimated:.2f} m/s")
        print(f"Dispersión espacial máxima: {max_distance_km:.3f} km")
        print("="*40)
        
        with open('debug_log.txt', 'a', encoding='utf-8') as f:
            f.write(f"\n=== PARÁMETROS ESTIMADOS ===\n")
            f.write(f"Background: {background_default:.2f}\n")
            f.write(f"Fuente: ({source_lat:.6f}, {source_lon:.6f})\n")
            f.write(f"Viento: {wind_dir_estimated:.1f}° @ {wind_speed_estimated:.2f} m/s\n")
        
        # Crear DataFrame compatible con gaussian_ch4
        df = pd.DataFrame({
            'lat': merged_df['lat'],
            'lon': merged_df['lon'],
            'z_m': merged_df['elevation'],
            'ch4_ppm': merged_df['gas_concentration'],  # Usamos esta columna independiente del gas
            'gas_concentration': merged_df['gas_concentration'],  # Mantener también esta columna
            'background_ppm': background_default,
            'wind_speed_ms': wind_speed_estimated,
            'wind_dir_from_deg': wind_dir_estimated,
            'stability': 'D',  # Estabilidad neutral
            'source_lat': source_lat,
            'source_lon': source_lon,
            'source_height_m': 2.0,
            'Q_true_gps': 0.0
        })
        
        # APLICAR FILTROS ESTADÍSTICOS SUAVIZADOS para mejorar el modelo
        # Filtro 1: Eliminar datos sin gradiente apreciable (menos agresivo)
        # Usar 20% sobre background en lugar de valor fijo
        threshold = background_default * 1.001  # Solo 0.1% sobre background
        df = df[df['ch4_ppm'] > threshold]
        
        # Filtro 2: Eliminar datos con viento MUY bajo (más permisivo)
        df = df[df['wind_speed_ms'] > 0.3]
        
        print(f"Datos después de aplicar filtros estadísticos: {len(df)} puntos")
        with open('debug_log.txt', 'a', encoding='utf-8') as f:
            f.write(f"Datos después de filtros estadísticos: {len(df)} puntos\n")
        
        # Procesar los datos usando el modelo gaussiano - BÚSQUEDA OPTIMIZADA V2
        try:
            # Probar múltiples combinaciones de estabilidad y sector
            best_results = None
            best_r2 = -999999
            error_msg = ""
            
            # Clases de estabilidad a probar (ordenadas por probabilidad)
            stability_classes = ['D', 'C', 'B', 'E', 'A']
            # Sectores MÁS AMPLIOS para capturar más puntos
            sector_widths = [180.0, 150.0, 120.0, 90.0]
            
            print(f"\n=== BÚSQUEDA DE MEJOR CONFIGURACIÓN ===")
            
            for stability in stability_classes:
                for sector_width in sector_widths:
                    try:
                        # Actualizar estabilidad en el DataFrame
                        df['stability'] = stability
                        
                        from gaussian_ch4 import preprocess_and_invert
                        temp_results = preprocess_and_invert(df, 
                                                            stability_override=stability,
                                                            wind_sector_half_width_deg=sector_width)
                        
                        if temp_results['n_points'] >= 10:  # Requerir al menos 10 puntos
                            r2 = temp_results['R2']
                            print(f"Estabilidad={stability}, Sector={sector_width}° → R²={r2:.3f}, n={temp_results['n_points']}, Q={temp_results['Q_hat_gph']:.1f} g/h")
                            
                            # Guardar si es mejor que el anterior Y tiene R² >= -0.5
                            if r2 > best_r2 and r2 >= -0.5:
                                best_r2 = r2
                                best_results = temp_results
                                
                    except Exception as e:
                        error_msg = str(e)
                        continue
            
            print("="*40)
            
            if best_results is not None:
                results = best_results
                print(f"\n*** MEJOR RESULTADO: R²={results['R2']:.3f}, Estabilidad={results['stability_used']} ***\n")
            else:
                # Si no funciona, usar valores por defecto sin modelo gaussiano
                results = {
                    "Q_hat_gps": 0.0,
                    "Q_std_gps": 0.0,
                    "Q_hat_gph": 0.0,
                    "Q_std_gph": 0.0,
                    "R2": 0.0,
                    "n_points": len(df),
                    "stability_used": "D",
                    "error": f"No se pudo calcular: {error_msg}"
                }
        except Exception as e:
            results = {
                "Q_hat_gps": 0.0,
                "Q_std_gps": 0.0,
                "Q_hat_gph": 0.0,
                "Q_std_gph": 0.0,
                "R2": 0.0,
                "n_points": len(df),
                "stability_used": "D",
                "error": f"Error en análisis: {str(e)}"
            }
        
        # Crear gráficas
        # 1. Mapa satelital 3D con puntos y mapa de calor
        # Calcular centro del mapa
        center_lat = df['lat'].mean()
        center_lon = df['lon'].mean()
        
        # Determinar unidades del gas
        gas_units = 'ppb' if gas_type == 'CH4' else 'ppm'
        
        # Crear mapa con plotly usando mapbox SATELITAL
        # IMPORTANTE: Convertir a listas para evitar codificación binaria
        lat_list = df['lat'].tolist()
        lon_list = df['lon'].tolist()
        concentration_list = df['gas_concentration'].tolist()
        elevation_list = df['z_m'].tolist()
        
        fig_heatmap = go.Figure()
        
        # Agregar mapa de calor (densidad) primero (abajo) - más transparente para ver el satélite
        fig_heatmap.add_trace(go.Densitymapbox(
            lat=lat_list,
            lon=lon_list,
            z=concentration_list,
            radius=30,
            colorscale=[
                [0, 'rgba(0,255,0,0.0)'],      # Transparente total (bajo - no contamina el mapa)
                [0.3, 'rgba(255,255,0,0.3)'],  # Amarillo muy transparente
                [0.6, 'rgba(255,165,0,0.5)'],  # Naranja semi-transparente
                [1, 'rgba(255,0,0,0.7)']       # Rojo (alto)
            ],
            showscale=False,
            hoverinfo='skip',
            name='Densidad',
            opacity=0.5,
            zmin=min(concentration_list),
            zmax=max(concentration_list)
        ))
        
        # Agregar puntos de medición encima con elevación en hover
        fig_heatmap.add_trace(go.Scattermapbox(
            lat=lat_list,
            lon=lon_list,
            mode='markers',
            marker=dict(
                size=8,
                color=concentration_list,
                colorscale='Jet',
                cmin=min(concentration_list),
                cmax=max(concentration_list),
                showscale=True,
                colorbar=dict(
                    title=dict(
                        text=f"{gas_type}<br>({gas_units})",
                        font=dict(size=12)
                    ),
                    x=1.02,
                    thickness=15,
                    len=0.7
                ),
                opacity=0.9
            ),
            text=[f"<b>{gas_type}:</b> {val:.1f} {gas_units}<br><b>Elevación:</b> {elev:.1f} m<br><b>Lat:</b> {lat:.6f}<br><b>Lon:</b> {lon:.6f}" 
                  for val, elev, lat, lon in zip(concentration_list, elevation_list, lat_list, lon_list)],
            hoverinfo='text',
            name='Puntos de medición',
            hovertemplate='%{text}<extra></extra>'
        ))
        
        # Token de Mapbox (reemplazar con tu token para vista satelital)
        # Obtén uno gratis en: https://account.mapbox.com/access-tokens/
        MAPBOX_TOKEN = "pk.eyJ1IjoidGF0YW4xNCIsImEiOiJjbWhhc3VwOHQxbnhtMm1wdXo2YzI1dnZkIn0.3bHCUGk_o-Ly8zZlKvskBw"
        
        # Elegir estilo de mapa según si hay token
        if MAPBOX_TOKEN:
            mapbox_style = 'satellite-streets'  # Vista satelital real
            mapbox_accesstoken = MAPBOX_TOKEN
        else:
            mapbox_style = 'open-street-map'  # Vista OpenStreetMap
            mapbox_accesstoken = None
        
        fig_heatmap.update_layout(
            mapbox=dict(
                style=mapbox_style,
                accesstoken=mapbox_accesstoken,
                center=dict(lat=center_lat, lon=center_lon),
                zoom=17,
                pitch=0,
                bearing=0
            ),
            title=dict(
                text=f'🗺️ Mapa de Concentraciones de {gas_type}' + (' (Satelital)' if MAPBOX_TOKEN else ''),
                font=dict(size=16, color='#2c3e50'),
                x=0.5,
                xanchor='center'
            ),
            height=650,
            margin={"r":0,"t":50,"l":0,"b":0},
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor="rgba(255,255,255,0.9)",
                bordercolor="Black",
                borderwidth=1
            ),
            hovermode='closest'
        )
        
        # 2. Rosa de vientos (usando dirección de viento real o asumida)
        wind_rose = go.Figure()
        
        # Crear datos para la rosa de vientos
        wind_directions = [wind_dir_estimated]
        wind_frequencies = [len(df)]
        
        wind_rose.add_trace(go.Barpolar(
            r=wind_frequencies,
            theta=wind_directions,
            name='Frecuencia',
            marker=dict(
                color=wind_frequencies,
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Frecuencia"),
                line=dict(color='white', width=2)
            ),
            opacity=0.9,
            width=30
        ))
        
        wind_rose.update_layout(
            title=f'Rosa de Vientos (Total: {len(df)} mediciones)',
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    showticklabels=True,
                    tickfont=dict(size=12),
                    range=[0, max(wind_frequencies) * 1.2]
                ),
                angularaxis=dict(
                    direction="clockwise",
                    rotation=90,
                    tickmode='array',
                    tickvals=[0, 45, 90, 135, 180, 225, 270, 315],
                    ticktext=['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'],
                    tickfont=dict(size=14, color='black')
                )
            ),
            height=500,
            showlegend=False
        )
        
        # 3. Serie temporal de concentraciones
        # IMPORTANTE: Convertir explícitamente a listas Python para evitar codificación binaria
        timestamps_list = merged_df['timestamp'].tolist()
        concentrations_list = merged_df['gas_concentration'].tolist()
        
        fig_timeseries = go.Figure()
        fig_timeseries.add_trace(go.Scatter(
            x=timestamps_list,
            y=concentrations_list,
            mode='lines+markers',
            name=gas_type,
            line=dict(color='green', width=2),
            marker=dict(size=4, color='darkgreen'),
            hovertemplate=f'<b>Tiempo:</b> %{{x}}<br><b>{gas_type}:</b> %{{y:.1f}} {gas_units}<extra></extra>'
        ))
        fig_timeseries.update_layout(
            title=f'Serie Temporal de Concentraciones {gas_type}',
            xaxis_title='Tiempo (UTC-5)',
            yaxis_title=f'{gas_type} ({gas_units})',
            height=400,
            showlegend=True,
            hovermode='closest'
        )
        
        # Imprimir algunos valores para debug
        print(f"\n=== DEBUG: Valores de {gas_type} ===")
        valores_lista = merged_df['gas_concentration'].head().tolist()
        print(f"Primeros 5 valores: {valores_lista}")
        print(f"Últimos 5 valores: {merged_df['gas_concentration'].tail().tolist()}")
        print(f"Min: {merged_df['gas_concentration'].min()}, Max: {merged_df['gas_concentration'].max()}")
        print(f"Media: {merged_df['gas_concentration'].mean()}")
        print("="*40)
        
        with open('debug_log.txt', 'a', encoding='utf-8') as f:
            f.write(f"\n=== DEBUG: Valores de {gas_type} ===\n")
            f.write(f"Primeros 5 valores: {valores_lista}\n")
            f.write(f"Min: {merged_df['gas_concentration'].min()}, Max: {merged_df['gas_concentration'].max()}\n")
            f.write(f"Media: {merged_df['gas_concentration'].mean()}\n")
        
        # Convertir a JSON y verificar datos
        timeseries_json = json.loads(fig_timeseries.to_json())
        print(f"\n=== DEBUG: Datos en JSON de timeseries ===")
        y_data = timeseries_json['data'][0]['y']
        print(f"Tipo de y_data: {type(y_data)}")
        
        with open('debug_log.txt', 'a', encoding='utf-8') as f:
            f.write(f"\n=== DEBUG: JSON timeseries ===\n")
            f.write(f"Tipo de y_data: {type(y_data)}\n")
            if isinstance(y_data, list):
                f.write(f"Primeros 5 valores Y en JSON: {y_data[:5]}\n")
                f.write(f"Últimos 5 valores Y en JSON: {y_data[-5:]}\n")
            else:
                f.write(f"y_data no es lista: {y_data}\n")
        print(f"Primeros 5 valores Y en JSON: {list(y_data)[:5] if hasattr(y_data, '__iter__') else y_data}")
        print(f"Total de puntos en JSON: {len(y_data) if hasattr(y_data, '__len__') else 'N/A'}")
        print("="*40)
        
        # Preparar respuesta
        response_data = {
            'results': results,
            'heatmap': json.loads(fig_heatmap.to_json()),
            'wind_rose': json.loads(wind_rose.to_json()),
            'timeseries': timeseries_json,
            'data_summary': {
                'total_points': len(merged_df),
                'gas_mean': float(merged_df['gas_concentration'].mean()),
                'gas_max': float(merged_df['gas_concentration'].max()),
                'gas_min': float(merged_df['gas_concentration'].min()),
                'gas_type': gas_type,
                'gas_units': gas_units,
                'time_range': f"{merged_df['timestamp'].min()} - {merged_df['timestamp'].max()}"
            },
            'success': True
        }
        
        # Limpiar archivos temporales
        try:
            if os.path.exists(data_path):
                os.remove(data_path)
            if os.path.exists(gpx_path):
                os.remove(gpx_path)
        except Exception as cleanup_error:
            print(f"Error al limpiar archivos temporales: {cleanup_error}")
        
        return jsonify(response_data)
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"\n❌ ERROR: {str(e)}")
        print(error_trace)
        
        # Intentar limpiar archivos en caso de error
        try:
            if 'data_path' in locals() and os.path.exists(data_path):
                os.remove(data_path)
            if 'gpx_path' in locals() and os.path.exists(gpx_path):
                os.remove(gpx_path)
        except:
            pass
            
        return jsonify({'error': str(e), 'trace': error_trace})

if __name__ == '__main__':
    # Para producción (Render.com) se usa el puerto de la variable de entorno
    port = int(os.environ.get('PORT', 5000))
    # Usar host 0.0.0.0 para aceptar conexiones externas
    app.run(host='0.0.0.0', port=port, debug=False)
