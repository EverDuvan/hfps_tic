# Gestión de Inventario TIC - HFPS

Este proyecto es una aplicación web desarrollada en **Django** para la gestión integral del inventario de equipos tecnológicos y periféricos en el **Hospital Francisco de Paula Santander (HFPS)**. El sistema permite controlar el ciclo de vida de los activos, desde su registro hasta la baja, incluyendo cronogramas de mantenimiento, generación de actas (PDF) y reportes.

##  Características Principales

### 1. Gestión de Inventario
*   **Equipos de Cómputo**: Registro detallado de PCs, Laptops, All-in-One, etc. Incluye especificaciones técnicas (RAM, Disco, Procesador, IP, MAC), estado operativo y asignación a áreas.
*   **Periféricos**: Inventario de teclados, mouse, monitores e impresoras, con posibilidad de vincularlos a equipos principales.
*   **Centros de Costos y Áreas**: Organización de la infraestructura por sedes, áreas funcionales y centros de costos para una mejor trazabilidad.

### 2. Mantenimiento
*   **Tipos de Mantenimiento**: Registro de mantenimientos Preventivos y Correctivos.
*   **Bitácora Detallada**: Control de actividades realizadas (limpieza, actualizaciones, hardware, optimización).
*   **Cronograma de Mantenimiento**: Visualización anual y mensual de mantenimientos programados para cada equipo.
*   **Actas Automáticas**: Generación automática de **Actas de Mantenimiento en PDF** listas para imprimir y firmar.

### 3. Entregas y Movimientos (Actas de Entrega)
*   Registro de movimientos de equipos entre áreas o responsables.
*   Asignación de responsables (Funcionarios/Técnicos).
*   Generación de **Actas de Entrega/Devolución en PDF** con listado de ítems y espacios para firma.

### 4. Reportes y Dashboard
*   **Dashboard Interactivo**: Vista general con estadísticas de equipos activos, mantenimientos recientes y gráficas de estado.
*   **Exportación a Excel**: Posibilidad de exportar listados de equipos, periféricos, mantenimientos y entregas para análisis externos.

##  Tecnologías Utilizadas

*   **Python**: Lenguaje de programación principal.
*   **Django**: Framework web de alto nivel.
*   **SQLite**: Base de datos por defecto (fácilmente escalable a PostgreSQL/MySQL).
*   **FPDF2**: Generación de documentos PDF (Actas).
*   **OpenPyXL**: Generación de reportes en Excel (.xlsx).
*   **Bootstrap**: Diseño responsivo y moderno (usado en templates).

## Instalación y Configuración

Siga estos pasos para configurar el proyecto en su entorno local.

### Prerrequisitos
*   Python 3.8 o superior.
*   pip (gestor de paquetes de Python).
*   Un entorno virtual (recomendado).

### Pasos

1.  **Clonar el repositorio:**
    ```bash
    git clone <URL_DEL_REPOSITORIO>
    cd hfps_tic
    ```

2.  **Crear y activar un entorno virtual:**
    ```bash
    # Linux/Mac
    python3 -m venv env
    source env/bin/activate

    # Windows
    python -m venv env
    env\Scripts\activate
    ```

3.  **Instalar dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Aplicar migraciones de base de datos:**
    ```bash
    python manage.py migrate
    ```

5.  **Crear un superusuario (Administrador):**
    ```bash
    python manage.py createsuperuser
    ```
    Siga las instrucciones en pantalla para asignar usuario y contraseña.

6.  **Iniciar el servidor de desarrollo:**
    ```bash
    python manage.py runserver
    ```

7.  **Acceder a la aplicación:**
    Abra su navegador y vaya a: `http://127.0.0.1:8000/`

## Uso del Sistema

1.  **Login**: Ingrese con las credenciales de superusuario o usuario técnico creado.
2.  **Dashboard**: Al ingresar, verá el resumen del estado actual del inventario.
3.  **Registros Básicos**:
    *   Vaya a *Centros de Costo* y *Áreas* para poblar la estructura organizacional.
    *   Vaya a *Equipos* para registrar las máquinas.
4.  **Mantenimientos**:
    *   Desde el detalle de un equipo, puede registrar un nuevo mantenimiento.
    *   Al guardar, el sistema generará automáticamente el PDF del acta.
    *   Puede ver el *Cronograma* para planificar actividades futuras.
5.  **Entregas**:
    *   Use la opción *Entregas* para registrar cambios de ubicación o responsable.

## 📂 Estructura del Proyecto

*   `hfps_tic/`: Configuración principal de Django (settings, urls).
*   `inventory/`: Aplicación principal.
    *   `models.py`: Definición de datos (Equipos, Mantenimientos, etc.).
    *   `views.py`: Lógica de negocio y controladores.
    *   `utils.py`: Funciones auxiliares para generar PDFs y Excel.
    *   `templates/`: Archivos HTML para la interfaz de usuario.

## 📄 Licencia

Este proyecto es propiedad de Ever Duvan Hernandez y está destinado para uso interno exclusivo del departamento de TIC.

ubuntu aws

ssh -i hfps_aws.pem ubuntu@34.207.116.83
