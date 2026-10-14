# Análisis factorial aplicado: intereses de jóvenes

Actividad sumativa de la Unidad 2 del módulo **Inferencia Avanzada y Análisis Multivariado**: análisis factorial exploratorio (AFE) y confirmatorio (AFC) en Python sobre la encuesta *Young People Survey* (Kaggle).

📄 **El informe está en [`informe.md`](informe.md)**. Se puede leer y editar directamente en GitHub, y con un comando se convierte en PDF con formato APA 7.

## Contenido del repositorio

| Archivo / carpeta | Qué es |
|---|---|
| `informe.md` | El informe técnico (texto editable). Usa las figuras de `resultados/`. |
| `AUDITORIA.md` | Auditoría del proyecto: hallazgos, verificación numérica y correcciones aplicadas. |
| `analisis_factorial.py` | Todo el análisis: KMO, Bartlett, análisis paralelo, AFE, AFC, fiabilidad y validez. Genera `resultados/`. |
| `generar_pdf_apa.py` | Convierte `informe.md` en `Informe_APA.pdf` con formato APA 7. |
| `datos/` | `responses.csv` (datos) y `columns.csv` (diccionario de variables) de Kaggle. |
| `resultados/` | Tablas (CSV), figuras (PNG), sintaxis de los modelos y `resumen.json`. Se regenera con el script. |
| `Informe_APA.pdf` | Versión en PDF lista para entregar. |
| `requirements.txt` | Librerías necesarias. |

## Cómo usarlo

```bash
pip install -r requirements.txt
python analisis_factorial.py     # 1. corre el análisis y genera resultados/
python generar_pdf_apa.py        # 2. genera Informe_APA.pdf desde informe.md
```

> Si `pip install semopy` falla al compilar, descarga el código fuente e instálalo con
> `pip install --use-pep517 semopy`.

## Cómo editar el informe en equipo

1. Abran `informe.md` en GitHub y usen el lápiz ✏️ para editar (o clonen el repositorio y editen en VS Code).
2. Hagan cambios pequeños y describan qué cambiaron en el mensaje del *commit*. Si trabajan en paralelo, cada persona puede usar su propia rama y abrir un *pull request*.
3. Después de editar, generen el PDF con `python generar_pdf_apa.py` y súbanlo también.

### Convenciones del Markdown (para que el PDF salga en APA)

| Para… | Escriba en `informe.md` |
|---|---|
| Datos de la portada | Edite el bloque inicial entre las líneas `---` (título, autores, institución, curso, docente, fecha). |
| Encabezado nivel 1 / 2 / 3 | `# Título`, `## Título`, `### Título` |
| Tabla | `**Tabla 1**`, en la línea siguiente `*Título en cursiva*`, luego la tabla y `*Nota.* texto` |
| Figura | `**Figura 1**`, `*Título en cursiva*`, `![descripción](resultados/archivo.png)`, `*Nota.* texto` |
| Salto de página en el PDF | `<!-- salto -->` (en GitHub no se ve) |
| Símbolos estadísticos | En cursiva: `*p*`, `*n*`, `*r*`; los griegos van normales: χ², λ, α |

Las secciones **Referencias** y **Apéndice…** empiezan automáticamente en una página nueva, y las referencias se escriben una por párrafo (el PDF les pone sangría francesa).

### ¿Y si cambia el análisis?

Las figuras se actualizan solas: `informe.md` las lee desde `resultados/`, así que basta con volver a correr `analisis_factorial.py`. Las cifras del texto y de las tablas sí están escritas a mano en `informe.md`; si cambian el análisis, copien los nuevos valores desde los CSV de `resultados/` (los nombres de los archivos indican qué tabla contienen).

## Datos

Sabo, M. (s. f.). *Young People Survey* [Conjunto de datos]. Kaggle. https://www.kaggle.com/datasets/miroslavsabo/young-people-survey
