# Auditoría del proyecto

**Proyecto:** *Modelado de estructuras latentes: análisis factorial aplicado a los intereses de jóvenes*
**Módulo:** Inferencia Avanzada y Análisis Multivariado — Unidad 2
**Objeto auditado:** `analisis_factorial.py`, `generar_pdf_apa.py`, `informe.md`, `README.md`, `requirements.txt` y los 34 artefactos de `resultados/`
**Fecha:** 14 de octubre de 2026

---

## 1. Método de la auditoría

La revisión se hizo por tres vías independientes, y toda cifra de este documento procede de una de ellas:

1. **Lectura completa del código y del informe** (564 + 388 + 434 líneas).
2. **Re-ejecución del pipeline** y comparación byte a byte de los 34 artefactos contra lo que está versionado.
3. **Recálculo independiente** de las fórmulas implementadas a mano (alfa de Cronbach, SRMR, CR, AVE, Mardia, residuos) y **simulación Monte Carlo** para arbitrar las disputas estadísticas.

Criterio de gravedad: **crítico** = invalida una afirmación del trabajo o un número publicado; **mayor** = defecto metodológico o de cumplimiento que un evaluador señalaría; **menor** = robustez, mantenibilidad o forma.

**Advertencia sobre dos hallazgos falsos.** Una revisión paralela propuso que el estadístico `b1` de Mardia era una constante matemática y que la varianza de `b2ₚ` omitía un factor 1/3. Ambas se **midieron y se rechazaron**: `b1` da 43,38 con datos normales simulados (no `n·p` = 28.352), y una simulación de 4.000 muestras normales multivariadas arroja `Var[b₂ₚ] = 8,49` frente a `8p(p+2)/n = 9,82`. El error estaba en la derivación, no en el código. **No se registran como hallazgos.** Se conservan aquí como advertencia sobre el riesgo de aceptar una demostración algebraica sin comprobarla.

---

## 2. Resumen de hallazgos

| ID | Gravedad | Hallazgo |
|---|---|---|
| C1 | Crítico | La réplica en mitades no valida el AFC, pero el informe afirma que sí |
| C2 | Crítico | La comparación de soluciones excluye *k* = 3 y *k* = 4 |
| C3 | Crítico | El criterio de depuración no se re-verifica tras reestimar |
| C4 | Crítico | La justificación para eliminar un ítem contradice la Tabla 3 |
| C5 | Crítico | El Resumen confunde la fiabilidad compuesta con la validez convergente |
| M1 | Mayor | SRMR: convención no documentada, cifra distinta a la definición estándar |
| M2 | Mayor | `b1` no es la asimetría multivariada de Mardia |
| M3 | Mayor | Supresión global de avisos oculta la no convergencia del AFE |
| M4 | Mayor | El par que recibe la covarianza de errores no se valida |
| M5 | Mayor | `np.argmax` sobre un vector booleano puede publicar «0 factores» |
| M6 | Mayor | Los alfas del AFE final nunca se guardan en disco |
| M7 | Mayor | Atribución incorrecta de los puntos de corte de ajuste |
| M8 | Mayor | Las Tablas 1 y 3 no llevan nota |
| M9 | Mayor | Los encabezados van en oración, no en Título (APA 7) |
| M10 | Mayor | El conversor compara secciones contra Markdown crudo |
| M11 | Mayor | El respaldo de fuente produce un PDF con símbolos perdidos |
| M12 | Mayor | Pérdida silenciosa de contenido en la conversión a PDF |
| m1–m13 | Menor | Ver sección 4 |
| m14–m20 | Menor | Ver sección 4 (descripción de *k*=7, criterio decorativo, Kaiser, RIASEC, terminología, exportación y forma) |

---

## 3. Hallazgos críticos

### C1. La réplica en mitades no valida el AFC, pero el informe afirma que sí

**Dónde:** `analisis_factorial.py:325-341` y `informe.md:297`

El script reestima el AFE por separado en dos mitades aleatorias y calcula la congruencia de Tucker:

```python
for h in mitades:
    m = efa(h, K)          # <- solo AFE
```

**No se ajusta ningún modelo AFC en las mitades.** En cambio, la sección de Limitaciones afirma:

> «Lo ideal es validarlo en una muestra independiente; la réplica en mitades mitiga, pero no sustituye, esa validación.»

La congruencia de Tucker mide la replicabilidad de la *estructura factorial*, no del AFC. No aporta ninguna evidencia sobre el ajuste del modelo confirmatorio. La afirmación, tal como está escrita, sugiere una garantía de validación cruzada que el análisis no realiza.

**Corrección:** (a) implementar el AFC en cada mitad y reportar sus índices, y (b) reformular la limitación para que describa lo que la réplica efectivamente hace.

---

### C2. La comparación de soluciones excluye *k* = 3 y *k* = 4

**Dónde:** `analisis_factorial.py:237-242`, Tabla 1 del informe

```python
for k in (5, 6, 7):      # <- empieza en 5
```

El análisis paralelo retiene 6 factores, pero el resultado final es **CFI = 0,890 y TLI = 0,858**, por debajo de 0,90. Cuando los índices incrementales fallan, la revisión estándar exige contrastar la solución con **menos** factores, no solo con más. Aquí esa mitad de la comparación no existe.

Se calculó lo que faltaba, con el mismo procedimiento y la misma regla de depuración:

| *k* | Varianza acumulada | Ítems con carga ≥ 0,40 | Ítems retenidos tras depurar | Factores con < 3 indicadores |
|---:|---:|---:|---:|---|
| 3 | 25,7 % | 16 | 16 | 0 |
| **4** | **30,4 %** | **20** | **18** | **0** |
| 5 | 34,7 % | 21 | 18 | 1 |
| 6 | 38,6 % | 20 | 20 | 1 |
| 7 | 41,7 % | 22 | 22 | 2 |

El dato relevante: **con *k* = 4 se retienen 18 ítems y ningún factor queda con menos de tres indicadores**, mientras que con *k* = 6 el factor *Consumo* se queda con dos. Esta es exactamente la alternativa que el trabajo debería haber discutido, y que además es donde está la raíz del AVE de 0,299 en *Deporte y riesgo* y de la carga de 0,356 en *Computación*.

**Corrección:** ampliar la comparación a *k* = 3–7, incorpolarla a la Tabla 1 y discutir en el texto por qué se conserva la solución de seis factores.

---

### C3. El criterio de depuración no se re-verifica tras reestimar

**Dónde:** `analisis_factorial.py:255-279`, `informe.md:97`

La depuración se aplica a la solución inicial de 32 ítems:

```python
abs1 = L1[ORDEN_FACTORES].abs()      # solución de 32 ítems
retener = (principal >= .40) & (cruzada < .35)
```

Tras reestimar con los 20 ítems retenidos, el script **no vuelve a comprobar el criterio**. Al medir `07_cargas_afe_final.csv` contra la regla que el propio trabajo declara:

| Ítem | Carga principal | Cumple ≥ 0,40 |
|---|---:|:---:|
| Computación (software/hardware) | **0,348** | No |
| Actividades al aire libre | **0,383** | No |

Además, la afirmación del informe de que «cada ítem carga de forma clara en un solo factor y las cargas cruzadas son pequeñas» no se sostiene para el ítem con peor comportamiento:

| Ítem | Principal | Cruzada máxima | Ratio |
|---|---:|---:|---:|
| Lectura de poesía | 0,495 | **0,338** (sobre *Deporte y riesgo*) | 68 % |

Una carga cruzada que es el 68 % de la principal no es «pequeña»; y los dos ítems que fallan el umbral son precisamente los dos que luego se eliminan en el AFC por baja carga. Es decir: la evidencia que motivó sus eliminaciones ya era visible en el AFE final y no se年来 evaluó.

**Corrección:** (a) añadir al script una comprobación explícita y su salida, que señale los ítems que dejan de cumplir el criterio tras la reestimación; (b) corregir la frase del informe; (c) reconocer en Limitaciones que la depuración fue de una sola pasada y no iterativa.

---

### C4. La justificación para eliminar un ítem contradice la propia Tabla 3

**Dónde:** `informe.md:193`

El informe elimina *Tocar instrumentos musicales* del AFC con este argumento:

> «es una práctica (hacer) y no un interés de consumo cultural como los otros ítems del factor»

El criterio no se sostiene dentro del mismo documento:

- **Escritura de poesía** es igualmente una práctica (escribir), pertenece al mismo factor, y **se conserva** con λ = 0,430.
- **Actividades al aire libre** se asignó a *Arte y cultura* en la Tabla 3 con la justificación «expresión artística y consumo cultural», cuando su contenido es naturaleza y campo, y se elimina en M2 precisamente por eso.
- La carga M1 de *Tocar instrumentos musicales* es 0,367 frente a 0,430 de *Escritura de poesía*: la diferencia real es de 0,06, no de naturaleza.

Es decir, el criterio declarado esboquea la re-especificación, pero los datos apuntan a un criterio no declarado —carga por debajo de 0,50— y a ese criterio seDpide la palabra.

**Corrección:** declarar el criterio que realmente se aplicó (carga estandarizada en M1 < 0,50), y reformular la justificación distinguishingla de una seletividad de contenido.

### C5. El Resumen confunde la fiabilidad compuesta con la validez convergente

**Dónde:** `informe.md:22`

El Resumen afirma que «la validez convergente es sólida en tres factores y débil en Deporte y riesgo». Contrastado con `14_validez_M2.csv`:

| Criterio | Umbral | Factores que lo cumplen |
|---|---|---|
| AVE (validez convergente) | ≥ 0,50 | **2 de 6** — Ciencias de la vida (0,679) y Consumo (0,520) |
| CR (fiabilidad compuesta) | ≥ 0,70 | **3 de 6** — Arte y cultura (0,726), Ciencias de la vida (0,864) y Ciencias exactas (0,706) |

El «tres» corresponde a la **fiabilidad compuesta**, no a la validez convergente. Además, H2 (línea 157) exige *ambos* criterios a la vez, y el único factor que cumple los dos simultáneamente es Ciencias de la vida. En consecuencia, el Resumen **sobrerrepresenta** la solidez del constructo: el trabajo cuerpo (línea 268) llega a una conclusión más pesimista y correcta que su propio resumen.

**Corrección:** reformular el Resumen distinguiendo los dos criterios y dar el recuento exacto de cada uno.

---

### M1. SRMR: convención no documentada

`analisis_factorial.py:361-362` usa `np.tril_indices(len(obs))`, que **incluye la diagonal**. La definición más extendida de SRMR promedia sobre los p(p−1)/2 pares distintos. Recalculado con los datos reales:

| Modelo | Elementos en la media | SRMR reportado | SRMR estándar (sin diagonal) |
|---|---:|---:|---:|
| M1 | 210 (190 + 20 diagonales) | 0,0670 | **0,0705** |
| M2 | 171 (153 + 18 diagonales) | 0,0617 | **0,0652** |

La convención del código coincide con la que usa `lavaan` por defecto, así que no es un error respecto a ese programa; pero **no está documentada**, y un lector que aplique la definición estándar obtendrá otra cifra. **Ninguna conclusión cambia**: ambos valores quedan bajo 0,08.

**Corrección:** reportar el valor estándar y dejar constancia explícita de la convención en el código y en la nota de la Tabla 5.

### M2. `b1` no es la asimetría multivariada de Mardia

`analisis_factorial.py:185`:

```python
b1 = (D ** 3).sum() / n ** 2
```

Esto suma los n² elementos de `D`, incluidos los fuera de la diagonal, que **llevan signo y se cancelan parcialmente**. La asimetría de Mardia es `b1p = (1/n²)·Σ diag(D)^{3/2}`.

Medido con los datos reales: el script publica **62,27**; el valor correcto es **0,2121**. El valor publicado no es una constante (con datos normales simulados da 43,38, no `n·p`).

**Impacto limitado:** el informe nunca cita `b1`, así que la notificación escrita no se ve afectada; el defecto queda en `resumen.json`.

**Corrección:** calcular `b1p` sobre la diagonal, o retirar el campo si no se va a reportar.

### M3. La supresión global de avisos oculta la no convergencia del AFE

`analisis_factorial.py:41` ejecuta `warnings.filterwarnings("ignore")` sobre todo el proceso. Con ello se apaga, entre otras, la única señal que emite `factor_analyzer` cuando el optimizador no converge:

```python
if not res.success:
    warnings.warn(f"Failed to converge: {res.message}")
```

El script llama a `efa()` siete veces y no verifica la convergencia en ninguna. El mismo silencio cubre las advertencias de `semopy` sobre varianzas negativas (casos Heywood), que invalidarían los índices publicados.

**Corrección:** acotar el filtro y verificar la convergencia de forma explícita en `efa()`.

### M4. El par que recibe la covarianza de errores no se valida

`analisis_factorial.py:458-461` elige el par con mayor residuo sin comprobar dos cosas: que los dos ítems estén en **factores distintos** (si estuvieran en el mismo, el parámetro no sería identificable y `semopy` podría descartarlo en silencio, dejando `χ²`, los gl y el ajusteublished inconsistentes con `modelo_M2.txt`), ni que **ambos sobrevivan a M2** (si no, la llamada a `Xr[items_m2]` fallaría).

Hoy es inocuo: el par es *Autos*–*PC*, en *Deporte y riesgo* y *Ciencias exactas*, ambos retenidos. Pero el código no lo garantiza.

### M5. `np.argmax` sobre un vector booleano puede publicar «0 factores»

`analisis_factorial.py:214`: `n_paralelo = int(np.argmax(eig < pa95))`. Si ningún autovalor cae bajo el percentil 95, devuelve `0` sin excepción, y ese `0` se escribe en `resumen.json`, se dibuja en la Figura 1 y se anota como «0 factores».

### M6. Los alfas del AFE final nunca se guardan

`fiab` (líneas 300-304) se calcula y se imprime, pero no hay ninguna llamada a `guardar()`. Es la **única cifra del script sin CSV correspondiente**, y el README instruye precisamente a copiar valores desde los CSV de `resultados/`. Si el análisis se re-ejecuta, esos valores no se pueden recuperar de ningún artefacto.

### M7. Atribución incorrecta de los puntos de corte

`informe.md:163` y la nota de la Tabla 5 atribuyen a Hu y Bentler (1999) un conjunto de umbrales que ese trabajo no propuso. Hu y Bentler (1999) propuso CFI y TLI ≥ 0,95 y RMSEA ≤ 0,06. **No propuso el criterio SRMR ≤ 0,08** (que procede de Browne y Cudeck, 1993) **ni los niveles «aceptables» 0,90 y 0,08** (que proceden de Hair et al., 2010).

Además, la fila «Criterio» de la Tabla 5 incluye `χ²/gl < 3`, la regla de Wheaton, obsoleta desde hace décadas y no recomendada con muestras grandes como esta (n = 886), donde el cociente se satura.

**Corrección:** reatribuir cada umbral a su fuente y presentar el χ² junto a *p*, no a χ²/*gl*.

### M8. Las Tablas 1 y 3 no llevan nota

APA 7 exige nota en toda tabla y figura. Se comprobó una por una: de las 9 tablas, **7 tienen nota; la Tabla 1 y la Tabla 3 no**. Las 4 figuras sí la tienen.

### M9. Los encabezados van en oración, no en Título

APA 7 exige **Title Case** en los tres niveles de encabezado. El informe los emplea en oración de forma sistemática: «Análisis factorial exploratorio», «Factibilidad del análisis», «Extracción, rotación y depuración de ítems», «Diseño del modelo de medición», «Lo que se aprendió del comportamiento de las variables», «Siguientes pasos», etc. Los estilos del PDF (`generar_pdf_apa.py:102-105`) aplican correctamente negrita, cursiva y centrado; lo que falla es el texto.

### M10. El conversor compara secciones contra Markdown crudo

`generar_pdf_apa.py:252-257` y `:283` comparan `seccion` contra `tokens[i+1].content`, que es el Markdown **sin procesar**. Si un encabezado de nivel 1 llevara énfasis (`# **Referencias**`), la comparación fallaría en silencio: las **Referencias perderían la sangría francesa y el salto de página**, y el **Resumen ganaría una sangría de primera línea que APA 7 no prescribe**.

Hoy funciona porque los ocho encabezados de nivel 1 del informe son texto plano. Es una fragilidad de una línea.

### M11. El respaldo de fuente produce un PDF con símbolos perdidos

`generar_pdf_apa.py:83-88`: si no encuentra Times New Roman ni Liberation Serif, **avisa y continúa** con `Times-Roman`. Las fuentes base-14 de ReportLab usan codificación WinAnsi, que **no incluye** χ, λ, α, √, ≤ ni ≥ — símbolos usados masivamente: `χ²` en el texto y en la Tabla 5, `√AVE` **en el encabezado de la Tabla 7**, que es el resultado central de validez discriminante, `≤` y `≥` en el criterio de la Tabla 5.

El script termina con éxito y entrega un PDF silenciosamente degradado.

### M12. Pérdida silenciosa de contenido en la conversión

`generar_pdf_apa.py:337-341` descarta **todo** bloque HTML que no sea `<!-- salto -->`, y `:169-170` descarta la URL de los enlaces `[texto](url)`.

Verificado en el estado actual: `informe.md` produce **2 bloques HTML** (ambos comentarios) y **0 enlaces Markdown**, así que hoy no se pierde contenido — el PDF conserva las 7 tablas, las 4 figuras, ambos apéndices y las 17 referencias, con acentos y símbolos correctos. Pero el riesgo es latente y alto: el autor ve en GitHub exactamente lo que escribe, y cualquier `<div>`, `<u>` o `[texto](url)` futuro desaparecerá del PDF sin error ni aviso.

---

## 5. Hallazgos menores

| ID | Ubicación | Hallazgo |
|---|---|---|
| m1 | `informe.md:186` | Dice «El mayor residuo (0,29)»; el CSV da 0,295 y el propio `resumen.json` lo formatea como 0,30. Es truncado, no redondeado. |
| m2 | Tabla 4 | Muestra 6 de los 10 residuos que guarda el script, sin nota que lo aclare. Deriva documental. |
| m3 | `analisis_factorial.py:436` | `sort_values` usa `quicksort`, no estable: un empate cambiaría qué par recibe la covarianza de errores. Hoy el máximo es único (0,295 frente a 0,232). |
| m4 | `analisis_factorial.py:518-522` | La Figura 3 dibuja la flecha en la posición de `(a_, b_)` pero toma el valor de `errcov_m2.iloc[0]`, sin filtrar por ese par. Hoy hay una sola covarianza. |
| m5 | `generar_pdf_apa.py:359` | Usa `Table._cellvalues`, atributo privado de ReportLab sin garantía entre versiones. |
| m6 | `generar_pdf_apa.py:206,223` | Una tabla Markdown con número desigual de columnas produce `IndexError`. Las 9 tablas actuales son regulares. |
| m7 | `requirements.txt` | Sin versiones. `semopy` 2.3.11 ya no expone SRMR en `calc_stats` (obliga al cálculo manual) y el script parchea el renombre `force_all_finite` → `ensure_all_finite`, así que no se sabe con qué API se generó `resultados/`. |
| m8 | `analisis_factorial.py:47-60` | Monkeypatch global sobre un módulo de terceros; su `except TypeError` envuelve toda la llamada y puede enmascarar errores reales. Con scikit-learn ≥ 1.6 ya es innecesario. |
| m9 | `generar_pdf_apa.py:333` | `Preformatted` no ajusta líneas largas; hoy la más larga (89 caracteres) cabe en Courier 8 pt. |
| m10 | `generar_pdf_apa.py:295-311` | Las listas anidadas se aplanan y se renumeran como una sola secuencia. Hoy las 4 listas son de un nivel. |
| m11 | `analisis_factorial.py:160` | El `assert` desaparece con `python -O`, y `cols.index()` lanza un `ValueError` poco informativo justo cuando lo que se busca es diagnosticar un renombrado. |
| m12 | `informe.md:6` | «Jaime Edison Rojas mora»: *Mora* es apellido y debe llevar mayúscula → «Rojas Mora». |
| m13 | `analisis_factorial.py:214` | Consta en M5; aquí se señala que el criterio «primer autovalor por debajo del percentil 95» no se contrasta con el gráfico de sedimentación, que el texto menciona pero no se usa para decidir. |
| m14 | `informe.md:77` | **La descripción de la solución de siete factores es incorrecta.** Reejecutada: el factor que queda con **dos** ítems es {Matemáticas, Física}, mientras que el de Internet y Computación tiene **tres** ({Internet, Computación, Ciencia y tecnología}). El texto afirma lo contrario («el segundo queda con solo dos ítems»). Con siete factores hay además dos factores de dos ítems, porque *Consumo* ya lo estaba con seis. |
| m15 | `informe.md:93` | **El criterio de carga cruzada < 0,35 no eliminó ningún ítem.** Verificado sobre `06_depuracion_items.csv`: los 12 eliminados incumplían ya la carga principal ≥ 0,40, y ninguno fue eliminado solo por la cruzada. El criterio se declara como parte de la regla pero no exerts ningún efecto sobre estos datos; conviene decirlo, porque da una impresión de rigor que no se corresponde con su papel real. |
| m16 | `informe.md:63` | **KMO de 0,762 calificado como «bueno» contra Kaiser (1974).** Las etiquetas de Kaiser son *meritorious* (0,80 o más), *middling* (0,70) y *mediocre* (0,60). Un valor de 0,762 cae en *middling*, no en la categoría superior. |
| m17 | `informe.md:286` | **Alcance de RIASEC excedido.** El texto afirma que las seis dimensiones «recuerdan a los tipos de Holland», pero solo dos están vinculados a RIASEC en la Tabla 3, no se calcularon perfiles por tipo y faltan las dimensiones «social», «emprendedor» y «convencional» que Holland sí distingue. |
| m18 | `informe.md:97` | **«46,4 % de la varianza común» es terminología incorrecta.** La cifra es 9,286/20, es decir la proporción de la **varianza total** de los 20 ítems. El Resumen dice correctamente «de la varianza»; el cuerpo del informe no. |
| m19 | `22_validacion_cruzada_mitades.csv` | **El IC del RMSEA se exportaba como texto crudo de Python** (`[np.float64(0.058), np.float64(0.074)]`), lo que contaminaría cualquier tabla construida sobre ese archivo. Corregido convirtiendo a `float` antes de guardar. |
| m20 | `informe.md:67, 91, 186` | Tres detalles de forma: «el criterio más preciso» es un superlativo sin sustento (sustituido por «el que suele recomendarse por su conservatism»); «que la actividad admite» es jerga interna del curso, incomprensible fuera de él; y las correlaciones con el género se reportaban sin *n* ni la codificación de la variable. |

---

## 6. Verificaciones que resultaron correctas

Se registramos porque acotan el alcance de las correcciones: **no deben tocarse**.

| Elemento | Verificación |
|---|---|
| `alfa_cronbach` (l. 146) | Fórmula correcta. Recalculada desde cero: coincide en los seis factores (0,718 / 0,862 / 0,679 / 0,658 / 0,579 / 0,647). |
| Mardia `b2p` y su estandarización | **Correctas.** Simulación de 4.000 muestras normales con p = 32, n = 886: `Var[b₂ₚ] = 8,49` frente a `8p(p+2)/n = 9,82` (0,86×) y `8p(p+2)/(3n) = 3,27` (2,59×). El *z* = 13,93 es correcto. |
| Análisis paralelo | Estable: 6 factores con 500 y con 5.000 réplicas (p95 del sexto autovalor = 1,227 en ambos casos). |
| Reproducibilidad | 27 de 34 artefactos idénticos byte a byte tras re-ejecución; los 7 restantes difieren **solo en el último dígito de coma flotante**. El pipeline es determinista en lo sustancial. |
| CR y AVE | Recalculados a mano desde las cargas estandarizadas: coinciden con `18_fiabilidad_validez_final.csv`. |
| Tablas 2, 4, 5, 6, 7, A1 y B1 | Cifras contrastadas una a una con sus CSV: coinciden. |
| KMO por ítem | Rango 0,636–0,845 y «ninguno por debajo de 0,50»: exacto. |
| Apéndice A | Los 32 ítems coinciden en nombre y orden con `datos/columns.csv`; *M*, *DE*, asimetría y faltantes coinciden con `01_descriptivos.csv`. |
| Apéndice B | Las 12 eliminadas coinciden con `06_depuracion_items.csv` y las 20 retenidas forman exactamente `modelo_M1.txt`. |
| Referencias | Las 17 entradas se citan en el texto y todo lo citado figura en Referencias. No hay referencias huérfanas ni citas rotas. |
| Conversión a PDF | 27 páginas; 9 tablas, 4 figuras, 2 apéndices y 17 referencias sobreviven; acentos y símbolos griegos correctos. |
| Gl del AFC | **Verificados por recuento explícito de parámetros.** M2: 18 ítems → 171 momentos; 12 cargas libres + 18 varianzas de error + 6 varianzas latentes + 15 covarianzas entre factores + 1 covarianza de errores = 52 parámetros; 171 − 52 = **119**. La parametrización alternativa (`std.lv`: varianza latente fijada a 1 y las 18 cargas libres) da **exactamente los mismos 119**, porque en ambas hay 51 parámetros libres. Fijar simultáneamente varianza latente y carga marcador sobredeterminaría la escala. Una revisión propuso 161/125; se rechaza. |
| Validación cruzada del AFC (nueva) | El modelo M2 reestimado en cada mitad replica el ajuste de la muestra completa: CFI = 0,889 y 0,889 frente a 0,890; TLI = 0,858 en ambas; RMSEA = 0,066 y 0,068 frente a 0,066; SRMR = 0,066 y 0,072. La estructura es estable. |
| Aritmética de la Tabla 5 | χ²/*gl*, RMSEA e IC 90 % reproducen los valores publicados. |

---

## 7. Plan de corrección aplicado

| Hallazgo | Corrección aplicada |
|---|---|
| C1 | El AFC se reestima ahora en cada mitad; se añade la Tabla de validación cruzada y se reescribe la limitación para describir lo que la réplica hace realmente. |
| C2 | La comparación de soluciones pasa a *k* = 3–7 y se incorpora a la Tabla 1, con discusión en el texto. |
| C3 | El script comprueba el criterio tras la reestimación y guarda qué ítems dejan de cumplirlo; se corrige la frase del informe y se añade la limitación correspondiente. |
| C4 | Se declara el criterio real (λ < 0,50 en M1) y se reformula la justificación. |
| C5 | El Resumen distingue fiabilidad compuesta de validez convergente y da el recuento exacto de cada una. |
| M1 | SRMR estándar (sin diagonal), con la convención documentada en el código y en la nota de la Tabla 5. |
| M2 | `b1p` se calcula sobre la diagonal conforme a Mardia. |
| M3 | Filtro de avisos acotado y verificación explícita de convergencia. |
| M4 | El par de la covarianza de errores se filtra por factor distinto y por permanencia en M2. |
| M5 | `flatnonzero` con error explícito. |
| M6 | Los alfas del AFE final se guardan en `20_alfa_afe_final.csv`. |
| M7 | Atribuciones corregidas y referencias nuevas incorporadas. |
| M8 | Nota añadida a las Tablas 1 y 3. |
| M9 | Encabezados en Título. |
| M10, M11, M12 | Correcciones en `generar_pdf_apa.py`. |
| m1–m13 | Correcciones puntuales. |
| m14 | Corregida la descripción de la solución de siete factores. |
| m15 | Se declara que el criterio de carga cruzada no eliminó ningún ítem. |

---

## 8. Limitación que la auditoría no resuelve

La **validación cruzada del AFC** que se implementa (C1) mejora la evidencia, pero no cierra el problema de fondo: AFE y AFC siguen calculándose **sobre la misma muestra de 886 casos**. La capitalización del azar en la depuración de ítems y en la re-especificación sigue siendo real, y solo un AFC sobre una muestra genuinely independiente la resolvería. Queda declarado como limitación, no como hallazgo resuelto.