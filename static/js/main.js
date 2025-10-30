// Gaussian Emissions Analyzer - JavaScript Principal
// Versión 2.0 - Modularizado

$(document).ready(function() {
    console.log('🚀 Gaussian Emissions Analyzer v2.0 Inicializado');
    
    // Manejador del formulario de análisis
    $('#analysis-form').submit(function(e) {
        e.preventDefault();
        
        // Validar archivos
        const dataFileInput = document.getElementById('data-file');
        const gpxFileInput = document.getElementById('gpx-file');
        const gasType = document.getElementById('gas-type').value;
        
        if (!dataFileInput.files.length) {
            alert('Por favor selecciona el archivo de datos CSV');
            return;
        }
        
        if (!gpxFileInput.files.length) {
            alert('Por favor selecciona el archivo GPX');
            return;
        }
        
        // Preparar FormData
        const formData = new FormData();
        formData.append('dataFile', dataFileInput.files[0]);
        formData.append('gpxFile', gpxFileInput.files[0]);
        formData.append('gasType', gasType);
        
        // Mostrar spinner
        $('#loading-spinner').removeClass('d-none');
        $('#results-container').addClass('d-none');
        $('#plots-container').addClass('d-none');
        
        // Enviar solicitud AJAX
        $.ajax({
            url: '/upload',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                handleSuccess(response);
            },
            error: function(xhr, status, error) {
                handleError(xhr, status, error);
            }
        });
    });
});

// Función para manejar respuesta exitosa
function handleSuccess(response) {
    console.log('🚀 Respuesta recibida:', response);
    
    // Ocultar spinner
    $('#loading-spinner').addClass('d-none');
    
    if (response.error) {
        alert('Error: ' + response.error);
        if (response.trace) {
            console.error('Trace:', response.trace);
        }
        return;
    }
    
    // Mostrar resultados con animación
    console.log('✅ Mostrando resultados y botones de exportación...');
    $('#data-summary-card').removeClass('d-none');
    $('#results-container').removeClass('d-none');
    $('#plots-container').removeClass('d-none');
    
    // Mostrar botones de exportación
    document.getElementById('export-buttons-simple').style.display = 'block';
    console.log('✅ Botones de exportación ahora visibles');
    
    // Actualizar todas las secciones
    updateEmissionRate(response);
    updateStatistics(response);
    updateMetadata(response);
    updateDataSummary(response);
    createPlots(response);
}

// Función para formatear números con máximo 3 decimales
function formatNumber(num) {
    if (num === null || num === undefined || isNaN(num)) return '0.000';
    // Si el número es muy grande o muy pequeño, usar notación científica
    if (Math.abs(num) >= 1e6 || (Math.abs(num) < 0.001 && num !== 0)) {
        return num.toExponential(3);
    }
    // Para números normales, usar 3 decimales
    return num.toFixed(3);
}

// Actualizar tasa de emisión
function updateEmissionRate(response) {
    let qHtml = `
        <div class="stat-label">Tasa de Emisión (Q)</div>
        <div class="stat-value" style="color: #27ae60;">
            ${formatNumber(response.results.Q_hat_gps)} 
            <span style="font-size: 1.2rem; font-weight: 600; color: #2c3e50;">g/s</span>
        </div>
        <div style="font-size: 0.9rem; color: #7f8c8d; margin-top: -10px; margin-bottom: 15px;">
            ± ${formatNumber(response.results.Q_std_gps)} g/s (desviación estándar)
        </div>
        <hr style="margin: 15px 0;">
        <div class="stat-label">Tasa de Emisión (Q)</div>
        <div class="stat-value" style="color: #27ae60;">
            ${formatNumber(response.results.Q_hat_gph)} 
            <span style="font-size: 1.2rem; font-weight: 600; color: #2c3e50;">g/h</span>
        </div>
        <div style="font-size: 0.9rem; color: #7f8c8d; margin-top: -10px;">
            ± ${formatNumber(response.results.Q_std_gph)} g/h (desviación estándar)
        </div>
    `;
    
    if (response.results.error) {
        qHtml += `<div class="alert alert-warning mt-3 mb-0">
            <i class="fas fa-exclamation-triangle"></i> 
            <strong>No se pudo calcular:</strong><br>
            ${response.results.error}
        </div>`;
        
        // Información de debug
        if (response.results.debug_info) {
            qHtml += `<div class="alert alert-info mt-2 mb-0">
                <small>
                    <strong><i class="fas fa-info-circle"></i> Información de depuración:</strong><br>
                    • Puntos combinados: ${response.results.debug_info.merged_points}<br>
                    • Puntos filtrados: ${response.results.debug_info.filtered_points}<br>
                    • Concentración background: ${response.results.debug_info.background.toFixed(2)}<br>
                    • Rango de gas: ${response.results.debug_info.gas_range}
                </small>
            </div>`;
        }
        
        // Recomendaciones
        if (response.results.recommendations) {
            qHtml += buildRecommendationsHTML(response.results.recommendations);
        }
    }
    
    $('#q-value').html(qHtml);
}

// Construir HTML de recomendaciones
function buildRecommendationsHTML(rec) {
    return `
        <div class="alert alert-success mt-3 mb-0" style="background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);">
            <h6 class="mb-3"><i class="fas fa-lightbulb"></i> <strong>Recomendaciones para Mediciones Exitosas</strong></h6>
            
            <div class="mb-3">
                <strong><i class="fas fa-route"></i> En Campo (Durante la Medición):</strong>
                <ul class="mt-2 mb-0">
                    ${rec.field_recommendations.map(r => `<li style="font-size: 0.9rem;">${r}</li>`).join('')}
                </ul>
            </div>
            
            <div class="mb-3">
                <strong><i class="fas fa-check-circle"></i> Calidad de Datos:</strong>
                <ul class="mt-2 mb-0">
                    ${rec.data_quality.map(r => `<li style="font-size: 0.9rem;">${r}</li>`).join('')}
                </ul>
            </div>
            
            <div class="mb-0">
                <strong><i class="fas fa-cloud-sun"></i> Condiciones Óptimas:</strong>
                <ul class="mt-2 mb-0">
                    ${rec.optimal_conditions.map(r => `<li style="font-size: 0.9rem;">${r}</li>`).join('')}
                </ul>
            </div>
        </div>
    `;
}

// Actualizar estadísticas del modelo
function updateStatistics(response) {
    let statsHtml = `
        <div class="row text-center mb-3">
            <div class="col-4">
                <div class="stat-label">Coeficiente R²</div>
                <div class="stat-value" style="font-size: 1.5rem;">${response.results.R2.toFixed(3)}</div>
                <small style="color: #7f8c8d;">(ajuste del modelo)</small>
            </div>
            <div class="col-4">
                <div class="stat-label">Puntos Usados</div>
                <div class="stat-value" style="font-size: 1.5rem;">${response.results.n_points}</div>
                <small style="color: #7f8c8d;">(observaciones)</small>
            </div>
            <div class="col-4">
                <div class="stat-label">Clase Estabilidad</div>
                <div class="stat-value" style="font-size: 1.5rem;">${response.results.stability_used}</div>
                <small style="color: #7f8c8d;">(Pasquill-Gifford)</small>
            </div>
        </div>
    `;
    
    // Agregar métricas adicionales si están disponibles
    if (response.results.metrics) {
        statsHtml += buildAdditionalMetricsHTML(response.results.metrics, response.data_summary.gas_units);
    }
    
    // Mostrar advertencia según R²
    statsHtml += buildR2WarningHTML(response.results);
    
    $('#stats').html(statsHtml);
}

// Construir HTML de métricas adicionales
function buildAdditionalMetricsHTML(metrics, units) {
    return `
        <hr style="margin: 15px 0;">
        <h6 class="mb-2"><i class="fas fa-calculator"></i> Métricas de Ajuste Adicionales</h6>
        <div class="row text-center">
            <div class="col-3">
                <div class="stat-label">MAE</div>
                <div style="font-size: 1.2rem; font-weight: 600; color: #3498db;">${metrics.MAE.toFixed(2)}</div>
                <small style="color: #7f8c8d; font-size: 0.75rem;">${units}<br>(Error Abs. Medio)</small>
            </div>
            <div class="col-3">
                <div class="stat-label">RMSE</div>
                <div style="font-size: 1.2rem; font-weight: 600; color: #9b59b6;">${metrics.RMSE.toFixed(2)}</div>
                <small style="color: #7f8c8d; font-size: 0.75rem;">${units}<br>(Raíz ECM)</small>
            </div>
            <div class="col-3">
                <div class="stat-label">MSE</div>
                <div style="font-size: 1.2rem; font-weight: 600; color: #e67e22;">${metrics.MSE.toFixed(2)}</div>
                <small style="color: #7f8c8d; font-size: 0.75rem;">${units}²<br>(Error Cuad. Medio)</small>
            </div>
            <div class="col-3">
                <div class="stat-label">MAPE</div>
                <div style="font-size: 1.2rem; font-weight: 600; color: #16a085;">${metrics.MAPE.toFixed(2)}</div>
                <small style="color: #7f8c8d; font-size: 0.75rem;">%<br>(Error % Medio)</small>
            </div>
        </div>
    `;
}

// Construir HTML de advertencia R²
function buildR2WarningHTML(results) {
    if (results.warning && results.suggestions) {
        return `
            <div class="alert alert-warning mt-3 mb-0">
                <strong><i class="fas fa-exclamation-circle"></i> ${results.warning}</strong>
                <ul class="mt-2 mb-0">
                    ${results.suggestions.map(s => `<li style="font-size: 0.9rem;">${s}</li>`).join('')}
                </ul>
            </div>
        `;
    } else if (results.R2 >= 0.7) {
        return `
            <div class="alert alert-success mt-3 mb-0">
                <i class="fas fa-check-circle"></i> <strong>Excelente ajuste del modelo!</strong> 
                Los resultados son confiables.
            </div>
        `;
    } else if (results.R2 >= 0.5) {
        return `
            <div class="alert alert-info mt-3 mb-0">
                <i class="fas fa-info-circle"></i> <strong>Buen ajuste del modelo.</strong> 
                Los resultados son aceptables pero pueden mejorarse.
            </div>
        `;
    }
    return '';
}

// Actualizar metadatos del modelo
function updateMetadata(response) {
    if (!response.metadata) return;
    
    const meta = response.metadata;
    const metadataHtml = `
        <div class="row">
            <div class="col-md-6">
                <p style="margin-bottom: 10px;">
                    <i class="fas fa-code-branch" style="color: #3498db;"></i> 
                    <strong>Versión del Modelo:</strong> ${meta.model_version}
                </p>
                <p style="margin-bottom: 10px;">
                    <i class="fas fa-calculator" style="color: #9b59b6;"></i> 
                    <strong>Modelo:</strong> ${meta.model_name}
                </p>
                <p style="margin-bottom: 10px;">
                    <i class="fas fa-clock" style="color: #e67e22;"></i> 
                    <strong>Hora de Procesamiento:</strong><br>
                    <span style="font-size: 0.95rem;">${meta.processing_time} (${meta.timezone})</span>
                </p>
                <p style="margin-bottom: 10px;">
                    <i class="fas fa-cloud" style="color: #16a085;"></i> 
                    <strong>Clase de Estabilidad:</strong> ${meta.stability_class} (Pasquill-Gifford)
                </p>
            </div>
            <div class="col-md-6">
                <p style="margin-bottom: 10px;">
                    <i class="fas fa-wind" style="color: #2ecc71;"></i> 
                    <strong>Viento Estimado:</strong><br>
                    <span style="font-size: 0.95rem;">
                        Dirección: ${meta.wind_direction_deg.toFixed(1)}° | 
                        Velocidad: ${meta.wind_speed_ms.toFixed(2)} m/s
                    </span>
                </p>
                <p style="margin-bottom: 10px;">
                    <i class="fas fa-map-pin" style="color: #e74c3c;"></i> 
                    <strong>Fuente Estimada:</strong><br>
                    <span style="font-size: 0.9rem;">
                        Lat: ${meta.source_location.lat.toFixed(6)}°, 
                        Lon: ${meta.source_location.lon.toFixed(6)}°
                    </span>
                </p>
                <p style="margin-bottom: 10px;">
                    <i class="fas fa-layer-group" style="color: #f39c12;"></i> 
                    <strong>Concentración Background:</strong> ${meta.background_concentration.toFixed(2)} ${response.data_summary.gas_units}
                </p>
                <p style="margin-bottom: 0;">
                    <i class="fas fa-arrows-alt" style="color: #95a5a6;"></i> 
                    <strong>Dispersión Espacial:</strong> ${meta.max_spatial_dispersion_km.toFixed(3)} km
                </p>
            </div>
        </div>
    `;
    $('#metadata').html(metadataHtml);
}

// Actualizar resumen de datos
function updateDataSummary(response) {
    if (!response.data_summary) return;
    
    const units = response.data_summary.gas_units || 'ppm';
    const gasIcon = response.data_summary.gas_type === 'CH4' ? '🔥' : 
                    response.data_summary.gas_type === 'CO2' ? '🌫️' : '💧';
    
    // Actualizar unidades en los títulos de gráficos
    $('#map-units').html(`Distribución espacial de ${response.data_summary.gas_type} (${units})`);
    $('#timeseries-units').html(`Variación de ${response.data_summary.gas_type} en el tiempo (${units})`);
    
    $('#data-summary').html(`
        <div class="row">
            <div class="col-md-6">
                <p style="margin-bottom: 12px;">
                    <i class="fas fa-flask text-primary"></i> <strong>Gas Analizado:</strong> 
                    ${gasIcon} <span style="font-size: 1.1rem; font-weight: 600;">${response.data_summary.gas_type}</span>
                </p>
                <p style="margin-bottom: 12px;">
                    <i class="fas fa-chart-line text-success"></i> <strong>Concentración Promedio:</strong><br>
                    <span style="font-size: 1.3rem; font-weight: 600; color: #27ae60;">${response.data_summary.gas_mean.toFixed(2)}</span>
                    <span style="font-size: 1.1rem; font-weight: 600; color: #2c3e50;"> ${units}</span>
                </p>
                <p style="margin-bottom: 12px;">
                    <i class="fas fa-arrow-up text-danger"></i> <strong>Concentración Máxima:</strong><br>
                    <span style="font-size: 1.2rem; font-weight: 600; color: #e74c3c;">${response.data_summary.gas_max.toFixed(2)}</span>
                    <span style="font-size: 1rem; font-weight: 600; color: #2c3e50;"> ${units}</span>
                </p>
            </div>
            <div class="col-md-6">
                <p style="margin-bottom: 12px;">
                    <i class="fas fa-arrow-down text-info"></i> <strong>Concentración Mínima:</strong><br>
                    <span style="font-size: 1.2rem; font-weight: 600; color: #3498db;">${response.data_summary.gas_min.toFixed(2)}</span>
                    <span style="font-size: 1rem; font-weight: 600; color: #2c3e50;"> ${units}</span>
                </p>
                <p style="margin-bottom: 12px;">
                    <i class="fas fa-map-marker-alt text-warning"></i> <strong>Total de Puntos GPS:</strong> 
                    <span style="font-size: 1.2rem; font-weight: 600; color: #f39c12;">${response.data_summary.total_points}</span>
                </p>
                <p style="margin-bottom: 0;">
                    <i class="fas fa-clock text-secondary"></i> <strong>Período de Medición:</strong><br>
                    <small style="font-size: 0.85rem; color: #7f8c8d;">${response.data_summary.time_range}</small>
                </p>
            </div>
        </div>
    `);
}

// Crear gráficas
function createPlots(response) {
    try {
        // Crear gráfico de observado vs modelado si está disponible
        if (response.obs_vs_pred) {
            console.log('Creando gráfico observado vs modelado...');
            $('#obs-vs-pred-container').removeClass('d-none');
            Plotly.newPlot('obs-vs-pred-plot', response.obs_vs_pred.data, response.obs_vs_pred.layout, {responsive: true});
        }
        
        console.log('Creando mapa interactivo...');
        
        // Configuración para el mapa interactivo con responsividad
        const heatmapConfig = {
            responsive: true,
            displayModeBar: true,
            modeBarButtonsToAdd: ['toggleHover'],
            displaylogo: false,
            scrollZoom: true
        };
        
        // Ajustar altura según el tamaño de la pantalla
        if (response.heatmap.layout) {
            if (window.innerWidth < 768) {
                response.heatmap.layout.height = 400;
            } else if (window.innerWidth < 992) {
                response.heatmap.layout.height = 500;
            }
        }
        
        Plotly.newPlot('heatmap-plot', response.heatmap.data, response.heatmap.layout, heatmapConfig);
        
        console.log('Creando rosa de vientos...');
        
        // Ajustar altura de rosa de vientos
        if (response.wind_rose.layout && window.innerWidth < 768) {
            response.wind_rose.layout.height = 350;
        }
        
        Plotly.newPlot('wind-rose', response.wind_rose.data, response.wind_rose.layout, {responsive: true});
        
        console.log('Creando serie temporal...');
        
        // Ajustar altura de serie temporal
        if (response.timeseries.layout && window.innerWidth < 768) {
            response.timeseries.layout.height = 300;
        }
        
        Plotly.newPlot('timeseries-plot', response.timeseries.data, response.timeseries.layout, {responsive: true});
        
        // Hacer que las gráficas se redimensionen cuando cambie el tamaño de ventana
        window.addEventListener('resize', function() {
            if (response.obs_vs_pred) {
                Plotly.Plots.resize('obs-vs-pred-plot');
            }
            Plotly.Plots.resize('heatmap-plot');
            Plotly.Plots.resize('wind-rose');
            Plotly.Plots.resize('timeseries-plot');
        });
        
        console.log('✅ Todas las gráficas creadas exitosamente');
    } catch(e) {
        console.error('Error al crear gráficas:', e);
        alert('Error al crear las gráficas: ' + e.message);
    }
}

// Función para manejar errores
function handleError(xhr, status, error) {
    $('#loading-spinner').addClass('d-none');
    console.error('Error AJAX:', {xhr: xhr, status: status, error: error});
    console.error('Respuesta:', xhr.responseText);
    alert('Error en el servidor: ' + error + '\nEstado: ' + status);
}
