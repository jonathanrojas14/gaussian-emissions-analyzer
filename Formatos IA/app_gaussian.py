import os
from flask import Flask, render_template, request, jsonify
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from gaussian_ch4 import preprocess_and_invert
import json

app = Flask(__name__)

# Asegurarse de que existe el directorio para subir archivos
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    
    if file and file.filename.endswith('.csv'):
        # Leer el CSV
        df = pd.read_csv(file)
        
        try:
            # Normalizar nombres de columnas (eliminar espacios extras y convertir a minúsculas)
            df.columns = df.columns.str.strip()
            
            # Las columnas ya vienen correctamente nombradas, solo validar
            # Si no existen, intentar mapearlas
            required_columns = {
                'lat': ['lat', 'latitude', 'latitud'],
                'lon': ['lon', 'longitude', 'longitud'],
                'z_m': ['z_m', 'z', 'altura', 'height'],
                'ch4_ppm': ['ch4_ppm', 'ch4', 'metano'],
                'background_ppm': ['background_ppm', 'background', 'fondo'],
                'wind_speed_ms': ['wind_speed_ms', 'wind_speed', 'velocidad_viento'],
                'wind_dir_from_deg': ['wind_dir_from_deg', 'wind_dir', 'direccion_viento'],
                'stability': ['stability', 'estabilidad'],
                'source_lat': ['source_lat', 'lat_fuente'],
                'source_lon': ['source_lon', 'lon_fuente'],
                'source_height_m': ['source_height_m', 'altura_fuente'],
                'Q_true_gps': ['Q_true_gps', 'q_true']
            }
            
            # Intentar mapear columnas si no coinciden exactamente
            column_mapping = {}
            for target_col, possible_names in required_columns.items():
                if target_col not in df.columns:
                    for possible_name in possible_names:
                        if possible_name in df.columns:
                            column_mapping[possible_name] = target_col
                            break
            
            if column_mapping:
                df.rename(columns=column_mapping, inplace=True)
            
            # Procesar los datos usando el modelo gaussiano
            results = preprocess_and_invert(df)
            
            # Crear gráficas
            # 1. Mapa de dispersión con concentraciones de CH4
            fig_scatter = px.scatter_mapbox(df, 
                                   lat='lat', 
                                   lon='lon', 
                                   color='ch4_ppm',
                                   size='ch4_ppm',
                                   hover_data=['ch4_ppm', 'wind_speed_ms'],
                                   color_continuous_scale='Jet',
                                   title='Mapa de Concentraciones de CH4',
                                   zoom=14)
            fig_scatter.update_layout(
                mapbox_style="open-street-map",
                height=500,
                margin={"r":0,"t":30,"l":0,"b":0}
            )
            
            # 2. Gráfica 2D alternativa si mapbox falla
            # Asegurar que tenemos datos válidos
            df_valid = df[df['ch4_ppm'].notna() & df['lat'].notna() & df['lon'].notna()].copy()
            
            # Calcular rango de valores para mejor visualización
            ch4_min = df_valid['ch4_ppm'].min()
            ch4_max = df_valid['ch4_ppm'].max()
            
            print(f"Puntos válidos: {len(df_valid)}")
            print(f"CH4 rango: {ch4_min:.4f} - {ch4_max:.4f} ppm")
            print(f"Lat rango: {df_valid['lat'].min():.6f} - {df_valid['lat'].max():.6f}")
            print(f"Lon rango: {df_valid['lon'].min():.6f} - {df_valid['lon'].max():.6f}")
            
            fig_scatter_2d = px.scatter(df_valid, 
                                   x='lon', 
                                   y='lat', 
                                   color='ch4_ppm',
                                   hover_data={'ch4_ppm': ':.4f', 'wind_speed_ms': ':.2f', 'lat': ':.6f', 'lon': ':.6f'},
                                   color_continuous_scale='Jet',
                                   range_color=[ch4_min, ch4_max],
                                   title='Mapa de Concentraciones de CH4',
                                   labels={'lon': 'Longitud', 'lat': 'Latitud', 'ch4_ppm': 'CH4 (ppm)'})
            
            fig_scatter_2d.update_traces(
                marker=dict(
                    size=15,  # Aumentar tamaño
                    line=dict(width=2, color='white'),
                    opacity=0.9
                )
            )
            
            fig_scatter_2d.update_layout(
                height=500,
                showlegend=True,
                coloraxis_colorbar=dict(
                    title="CH4 (ppm)",
                    tickformat=".4f"
                ),
                xaxis=dict(title='Longitud', tickformat='.6f'),
                yaxis=dict(title='Latitud', scaleanchor="x", scaleratio=1, tickformat='.6f')
            )
            
            # 3. Rosa de vientos mejorada
            if 'wind_dir_from_deg' in df.columns:
                # Agrupar direcciones y contar frecuencias
                wind_data = df[df['wind_dir_from_deg'].notna()].copy()
                wind_counts = wind_data['wind_dir_from_deg'].value_counts().sort_index()
                
                print(f"Direcciones de viento únicas: {wind_counts.index.tolist()}")
                print(f"Frecuencias: {wind_counts.values.tolist()}")
                
                # Crear rosa de vientos con barras polares
                wind_rose = go.Figure()
                
                wind_rose.add_trace(go.Barpolar(
                    r=wind_counts.values,
                    theta=wind_counts.index,
                    name='Frecuencia',
                    marker=dict(
                        color=wind_counts.values,
                        colorscale='Viridis',
                        showscale=True,
                        colorbar=dict(title="Frecuencia"),
                        line=dict(color='white', width=2)
                    ),
                    opacity=0.9,
                    width=30  # Barras más anchas
                ))
                
                wind_rose.update_layout(
                    title=f'Rosa de Vientos (Total: {len(wind_data)} mediciones)',
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            showticklabels=True,
                            tickfont=dict(size=12),
                            range=[0, max(wind_counts.values) * 1.2]
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
            else:
                # Rosa de vientos placeholder
                wind_rose = go.Figure()
                wind_rose.update_layout(title='Rosa de Vientos - No hay datos disponibles')
            
            # 4. Serie temporal de CH4
            if 'ch4_ppm' in df.columns:
                ch4_valid = df[df['ch4_ppm'].notna()].copy()
                fig_timeseries = go.Figure()
                fig_timeseries.add_trace(go.Scatter(
                    x=list(range(len(ch4_valid))),
                    y=ch4_valid['ch4_ppm'].values,
                    mode='lines+markers',
                    name='CH4',
                    line=dict(color='green', width=2),
                    marker=dict(size=6, color='darkgreen', line=dict(width=1, color='white'))
                ))
                fig_timeseries.update_layout(
                    title='Serie Temporal de Concentraciones CH4',
                    xaxis_title='Índice de Muestra',
                    yaxis_title='CH4 (ppm)',
                    yaxis=dict(tickformat='.4f'),
                    height=400,
                    showlegend=False,
                    hovermode='x unified'
                )
            else:
                fig_timeseries = go.Figure()
                fig_timeseries.update_layout(title='Serie Temporal - No disponible')
            
            # Preparar respuesta
            response_data = {
                'results': results,
                'scatter_plot': json.loads(fig_scatter.to_json()),
                'scatter_plot_2d': json.loads(fig_scatter_2d.to_json()),
                'wind_rose': json.loads(wind_rose.to_json()),
                'timeseries': json.loads(fig_timeseries.to_json()),
                'data_summary': {
                    'total_points': len(df),
                    'ch4_mean': float(df['ch4_ppm'].mean()) if 'ch4_ppm' in df.columns else 0,
                    'ch4_max': float(df['ch4_ppm'].max()) if 'ch4_ppm' in df.columns else 0,
                    'ch4_min': float(df['ch4_ppm'].min()) if 'ch4_ppm' in df.columns else 0
                },
                'success': True
            }
            
            return jsonify(response_data)
            
        except Exception as e:
            return jsonify({'error': str(e), 'columns': list(df.columns) if 'df' in locals() else []})
    
    return jsonify({'error': 'Invalid file type'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)