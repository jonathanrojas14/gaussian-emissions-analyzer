# 🚀 GUÍA COMPLETA: Desplegar en Render.com
## (Solo copiar y pegar - No necesitas saber programar)

---

## ✅ ARCHIVOS NECESARIOS (Ya están listos en tu carpeta):

1. ✓ codigo_HTML_Gausiana.py
2. ✓ gaussian_ch4.py  
3. ✓ requirements.txt
4. ✓ Procfile
5. ✓ templates/index.html

---

## 📝 PASO 1: CREAR CUENTA EN GITHUB (5 minutos)

1. Abre tu navegador y ve a: **https://github.com/signup**

2. Llena el formulario:
   - Email: tu_email@gmail.com
   - Contraseña: (elige una segura)
   - Username: (elige uno único, ejemplo: tatan14)

3. Verifica tu email

4. ¡Listo! Ya tienes cuenta en GitHub

---

## 📁 PASO 2: CREAR REPOSITORIO EN GITHUB (3 minutos)

1. Una vez dentro de GitHub, click en el botón verde **"New"** (arriba a la izquierda)
   O ve directamente a: **https://github.com/new**

2. Llena el formulario:
   - **Repository name**: `gaussian-emissions-analyzer`
   - **Description**: `Analizador de emisiones de gases con modelo gaussiano`
   - **Public** (seleccionado)
   - ❌ NO marques "Add a README file"
   - ❌ NO agregues .gitignore
   - ❌ NO agregues licencia

3. Click en **"Create repository"**

4. Verás una página con comandos. IGNÓRALA por ahora.

---

## 📤 PASO 3: SUBIR ARCHIVOS A GITHUB (10 minutos)

### Método 1: Subir uno por uno (MÁS FÁCIL)

1. En la página de tu repositorio, busca el link que dice:
   **"uploading an existing file"** (texto azul)
   
2. Click en ese link

3. Arrastra los siguientes archivos desde tu carpeta:
   ```
   C:\Users\Usuario\Desktop\ECUACION GAUSIANA\
   ```
   
   Archivos a subir:
   - codigo_HTML_Gausiana.py
   - gaussian_ch4.py
   - requirements.txt
   - Procfile
   - .gitignore

4. En el cuadro de mensaje abajo, escribe: "Add main files"

5. Click en **"Commit changes"**

6. IMPORTANTE: Ahora sube la carpeta templates:
   - Click en **"Add file"** → **"Upload files"**
   - Crea una carpeta llamada "templates" haciendo:
     * Click en el campo donde dice "Name your file..."
     * Escribe: `templates/index.html`
     * Luego pega el contenido del archivo index.html
   
7. Commit con mensaje: "Add templates"

---

## 🌐 PASO 4: CREAR CUENTA EN RENDER.COM (3 minutos)

1. Ve a: **https://render.com/register**

2. Click en **"Sign up with GitHub"** (botón morado)

3. Autoriza a Render para acceder a tu cuenta de GitHub

4. ¡Listo! Cuenta creada

---

## 🚀 PASO 5: DESPLEGAR LA APLICACIÓN (5 minutos)

1. En Render.com, click en **"New +"** (arriba a la derecha)

2. Selecciona **"Web Service"**

3. Busca tu repositorio: `gaussian-emissions-analyzer`
   - Si no aparece, click en "Configure account" y da acceso

4. Click en **"Connect"** al lado de tu repositorio

5. Configura el servicio:

   **Name**: `gaussian-analyzer`
   
   **Region**: `Oregon (US West)`
   
   **Branch**: `main`
   
   **Root Directory**: (déjalo vacío)
   
   **Environment**: `Python 3`
   
   **Build Command**: 
   ```
   pip install -r requirements.txt
   ```
   
   **Start Command**:
   ```
   gunicorn codigo_HTML_Gausiana:app
   ```
   
   **Instance Type**: `Free`

6. Click en **"Advanced"** para agregar variables de entorno

7. Click en **"Add Environment Variable"**:
   - **Key**: `MAPBOX_TOKEN`
   - **Value**: `pk.eyJ1IjoidGF0YW4xNCIsImEiOiJjbWhhc3VwOHQxbnhtMm1wdXo2YzI1dnZkIn0.3bHCUGk_o-Ly8zZlKvskBw`

8. Click en **"Create Web Service"**

---

## ⏳ PASO 6: ESPERAR EL DESPLIEGUE (3-5 minutos)

1. Verás un log con el progreso del despliegue

2. Espera a que aparezca: ✅ **"Your service is live"**

3. Tu URL será algo como:
   ```
   https://gaussian-analyzer.onrender.com
   ```

4. ¡LISTO! Copia esa URL y compártela con quien quieras

---

## 🎯 RESUMEN RÁPIDO:

1. ✅ Crear cuenta GitHub → https://github.com/signup
2. ✅ Crear repositorio → https://github.com/new
3. ✅ Subir archivos → Drag & drop
4. ✅ Crear cuenta Render → https://render.com/register
5. ✅ Desplegar → New + → Web Service

**Tiempo total: ~25 minutos**

---

## ❓ PROBLEMAS COMUNES:

### "Build failed"
- Verifica que subiste todos los archivos
- Verifica que requirements.txt esté correcto

### "Application error"
- Agrega la variable de entorno MAPBOX_TOKEN
- Verifica que el Start Command sea: `gunicorn codigo_HTML_Gausiana:app`

### "No me aparece mi repositorio en Render"
- Ve a Settings → Configure account en Render
- Da acceso a tu repositorio específico

---

## 📞 ¿NECESITAS AYUDA?

Si algo no funciona:
1. Copia el mensaje de error exacto
2. Pégalo y pídeme ayuda
3. Te diré exactamente qué hacer

---

## 🎉 ¡DISFRUTA TU APLICACIÓN EN LA NUBE!

Una vez desplegada, podrás:
- Acceder desde cualquier dispositivo
- Compartir el link con colegas
- Subir archivos .data y .gpx
- Ver mapas satelitales en tiempo real
- Analizar emisiones de CH4, CO2 y H2O

---

**Nota**: El plan gratuito de Render puede tomar 30-60 segundos en "despertar" 
si la app no se ha usado en un rato. ¡Es normal!
