# Análisis Gaussiano de Gases Atmosféricos

Este proyecto permite analizar datos de concentraciones de gases (CH4, CO2, H2O) combinando información del analizador LI-7810 y datos GPS, aplicando un modelo de dispersión gaussiana para estimar tasas de emisión.

## Características

- **Soporte para múltiples gases**: CH4, CO2, y H2O
- **Zona horaria unificada**: Todos los datos se procesan en UTC-5 (America/Bogota)
- **Sincronización automática**: Combina datos del analizador con GPS mediante timestamps
- **Visualización avanzada**:
  - Mapa satelital con puntos de medición y mapa de calor
  - Serie temporal de concentraciones
  - Rosa de vientos
  - Estadísticas del modelo gaussiano

## Requisitos

- Python 3.9 o superior
- Archivos de entrada:
  - Archivo `.data` del analizador LI-7810 (ej: "7. Pozo Estación Gala s-n 1183.data")
  - Archivo `.gpx` del GPS (ej: "Track_TRACK ESTACION GALA_GPS 5290 del s-n 1183.gpx")

## Instalación

1. Instalar las dependencias:
```bash
pip install -r requirements.txt
```

## Uso

1. Ejecutar la aplicación:
```bash
python codigo_HTML_Gausiana.py
```

2. Abrir el navegador en: http://localhost:5000

3. En la interfaz web:
   - Seleccionar el tipo de gas a analizar (CH4, CO2, o H2O)
   - Cargar el archivo `.data` del analizador
   - Cargar el archivo `.gpx` del GPS
   - Hacer clic en "Analizar Datos"

## Resultados

La aplicación genera:

1. **Tasa de Emisión (Q)**: Estimación de la tasa de emisión en g/s y g/h con incertidumbre
2. **Estadísticas del Modelo**: R², número de puntos, clase de estabilidad
3. **Mapa Satelital**: Visualización de puntos de medición con mapa de calor de concentraciones
4. **Serie Temporal**: Evolución de las concentraciones en el tiempo
5. **Rosa de Vientos**: Dirección predominante del viento
6. **Resumen de Datos**: Estadísticas descriptivas de las mediciones

## Notas Técnicas

- **Zona Horaria**: Los archivos GPX están en UTC, los archivos .data en America/Bogota (UTC-5). La aplicación sincroniza automáticamente a UTC-5.
- **Tolerancia de Sincronización**: 5 segundos entre mediciones GPS y del analizador
- **Modelo Gaussiano**: Utiliza el modelo de pluma gaussiana con reflexión en el suelo
- **Conversión CH4**: El CH4 en el archivo .data viene en ppb y se convierte automáticamente a ppm
- **Estilo de Mapa**: El mapa usa imágenes satelitales de Mapbox (requiere conexión a internet)

## Estructura de Archivos

```
ECUACION GAUSIANA/
├── codigo_HTML_Gausiana.py    # Aplicación Flask principal
├── gaussian_ch4.py             # Modelo de dispersión gaussiana
├── requirements.txt            # Dependencias Python
├── templates/
│   └── index.html             # Interfaz web
├── uploads/                    # Carpeta temporal para archivos subidos
└── DATA ESTACION GALA/        # Datos de ejemplo
    ├── 7. Pozo Estación Gala s-n 1183.data
    └── Track_TRACK ESTACION GALA_GPS 5290 del s-n 1183.gpx
```

## Solución de Problemas

- **Error: "No se pudieron combinar los datos"**: Verificar que los timestamps de ambos archivos coincidan aproximadamente
- **Error de Mapbox**: Asegurarse de tener conexión a internet para cargar el mapa satelital
- **Valores de Q anómalos**: Revisar la calidad de los datos y la dirección del viento

## Desarrollado por

Análisis basado en modelo de dispersión gaussiana para estimación de emisiones de gases de efecto invernadero.
