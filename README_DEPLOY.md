# Analizador Gaussiano de Emisiones de Gases

Aplicación web Flask para analizar concentraciones de gases (CH4, CO2, H2O) usando el modelo de pluma gaussiana, con visualización satelital de mapas.

## Características

- 📊 Análisis de datos del analizador LI-7810
- 🗺️ Mapas satelitales con Mapbox
- 📈 Visualización de series temporales
- 🌹 Rosa de vientos
- 🎯 Estimación de ubicación de fuentes
- 📍 Integración con datos GPS (.gpx)

## Despliegue en Render.com

1. Crea una cuenta en [Render.com](https://render.com)
2. Conecta tu repositorio de GitHub
3. Crea un nuevo "Web Service"
4. Render detectará automáticamente la configuración
5. ¡Despliega!

## Variables de Entorno

En Render.com, configura:
- `MAPBOX_TOKEN`: Tu token de Mapbox (opcional pero recomendado para vista satelital)

## Uso Local

```bash
pip install -r requirements.txt
python codigo_HTML_Gausiana.py
```

Accede a `http://127.0.0.1:5000`

## Archivos Requeridos

- `.data`: Archivo del analizador LI-7810
- `.gpx`: Archivo de trackeo GPS

## Tecnologías

- Flask 3.0
- Plotly 5.18
- Pandas 2.1
- NumPy 1.26
- Scikit-learn 1.3
