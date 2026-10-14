# -*- coding: utf-8 -*-
"""
Modelado de estructuras latentes: análisis factorial aplicado
Módulo: Inferencia Avanzada y Análisis Multivariado - Unidad 2

Datos: Young People Survey (Kaggle, Miroslav Sabo)
       https://www.kaggle.com/datasets/miroslavsabo/young-people-survey
       Archivos: responses.csv y columns.csv (en la carpeta ./datos)

Bloque analizado: 32 ítems de "Hobbies e intereses" (escala Likert 1 a 5).

Flujo:
  1. Preparación de datos y descriptivos
  2. AFE: KMO, Bartlett, número de factores (Kaiser, scree, análisis paralelo),
     extracción por máxima verosimilitud, rotación promax, depuración de ítems
     y re-estimación; fiabilidad (alfa de Cronbach) y réplica en dos mitades.
  3. AFC (semopy, sintaxis tipo lavaan): modelo M1, índices de ajuste
     (chi-cuadrado, CFI, TLI, RMSEA, SRMR), cargas estandarizadas, CR, AVE,
     Fornell-Larcker, residuos; modelo ajustado M2.

Requisitos:  pip install pandas numpy scipy matplotlib factor_analyzer semopy
Ejecución:   python analisis_factorial.py
Salidas:     carpeta ./resultados (tablas CSV, figuras PNG, resumen JSON)
"""

import json
import os
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

import factor_analyzer.factor_analyzer as _fa_mod
from factor_analyzer import FactorAnalyzer, calculate_bartlett_sphericity, calculate_kmo
import semopy

# AUDITORIA M3: la supresión global apagaba también el aviso de no convergencia de
# factor_analyzer ("Failed to converge") y las advertencias de varianzas Heywood de
# semopy. Se acota el filtro y la convergencia se verifica de forma explicita en efa().
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")

# ---------------------------------------------------------------------------
# Compatibilidad: factor_analyzer 0.5.x usa el argumento 'force_all_finite' de
# scikit-learn, renombrado a 'ensure_all_finite' en versiones recientes.
# ---------------------------------------------------------------------------
_orig_check_array = _fa_mod.check_array


def _check_array_compat(*args, **kwargs):
    if "force_all_finite" in kwargs:
        val = kwargs.pop("force_all_finite")
        try:
            return _orig_check_array(*args, ensure_all_finite=val, **kwargs)
        except TypeError:
            return _orig_check_array(*args, force_all_finite=val, **kwargs)
    return _orig_check_array(*args, **kwargs)


_fa_mod.check_array = _check_array_compat

SEED = 2026
BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "resultados")
os.makedirs(OUT, exist_ok=True)
resumen = {}

# Nombres seguros (sin espacios) y etiquetas para cada ítem
ETIQUETAS = {
    "History": ("Historia", "Historia"),
    "Psychology": ("Psicologia", "Psicología"),
    "Politics": ("Politica", "Política"),
    "Mathematics": ("Matematicas", "Matemáticas"),
    "Physics": ("Fisica", "Física"),
    "Internet": ("Internet", "Internet"),
    "PC": ("PC", "Computación (software/hardware)"),
    "Economy Management": ("Economia", "Economía y gestión"),
    "Biology": ("Biologia", "Biología"),
    "Chemistry": ("Quimica", "Química"),
    "Reading": ("LecturaPoesia", "Lectura de poesía"),
    "Geography": ("Geografia", "Geografía"),
    "Foreign languages": ("Idiomas", "Idiomas extranjeros"),
    "Medicine": ("Medicina", "Medicina"),
    "Law": ("Derecho", "Derecho"),
    "Cars": ("Autos", "Autos"),
    "Art exhibitions": ("Arte", "Arte (exposiciones)"),
    "Religion": ("Religion", "Religión"),
    "Countryside, outdoors": ("AireLibre", "Actividades al aire libre"),
    "Dancing": ("Baile", "Baile"),
    "Musical instruments": ("Instrumentos", "Tocar instrumentos musicales"),
    "Writing": ("EscrituraPoesia", "Escritura de poesía"),
    "Passive sport": ("DeporteOcio", "Deporte recreativo"),
    "Active sport": ("DeporteCompetitivo", "Deporte competitivo"),
    "Gardening": ("Jardineria", "Jardinería"),
    "Celebrities": ("Celebridades", "Vida de celebridades"),
    "Shopping": ("Compras", "Compras"),
    "Science and technology": ("CienciaTec", "Ciencia y tecnología"),
    "Theatre": ("Teatro", "Teatro"),
    "Fun with friends": ("Amigos", "Socializar con amigos"),
    "Adrenaline sports": ("Adrenalina", "Deportes de adrenalina"),
    "Pets": ("Mascotas", "Mascotas"),
}

# Ítems "marcadores" para nombrar los factores que entrega el AFE
MARCADORES = {
    "Biologia": "CienciasVida",
    "Teatro": "ArteCultura",
    "Fisica": "CienciasExactas",
    "Politica": "CienciasSociales",
    "Adrenalina": "DeporteRiesgo",
    "Compras": "Consumo",
}
NOMBRE_FACTOR = {
    "ArteCultura": "Arte y cultura",
    "CienciasVida": "Ciencias de la vida",
    "CienciasExactas": "Ciencias exactas y tecnología",
    "CienciasSociales": "Ciencias sociales y humanidades",
    "DeporteRiesgo": "Deporte y riesgo",
    "Consumo": "Consumo y estilo de vida",
}
ORDEN_FACTORES = list(NOMBRE_FACTOR)


def guardar(df, nombre):
    df.to_csv(os.path.join(OUT, nombre), encoding="utf-8-sig")


def efa(data, k, rotacion="promax"):
    """AFE por ML. AUDITORIA M3: se comprueba explicitamente que el optimizador
    convergio; antes el aviso de factor_analyzer quedaba silenciado."""
    modelo = FactorAnalyzer(n_factors=k, rotation=rotacion, method="ml")
    with warnings.catch_warnings(record=True) as avisos:
        warnings.simplefilter("always")
        modelo.fit(data)
    for w in avisos:
        if "converge" in str(w.message).lower():
            raise RuntimeError(f"El AFE con k={k} no convergio: {w.message}")
    return modelo


def nombrar_factores(cargas):
    """Renombra columnas F1..Fk según el factor donde carga cada marcador."""
    mapa = {}
    for item, nombre in MARCADORES.items():
        if item in cargas.index:
            col = cargas.loc[item].abs().idxmax()
            mapa[col] = nombre
    cargas = cargas.rename(columns=mapa)
    return cargas[[c for c in ORDEN_FACTORES if c in cargas.columns]
                  + [c for c in cargas.columns if c not in ORDEN_FACTORES]], mapa


def alfa_cronbach(d):
    k = d.shape[1]
    return k / (k - 1) * (1 - d.var(ddof=1).sum() / d.sum(axis=1).var(ddof=1))


# ===========================================================================
# 1. DATOS
# ===========================================================================
DATOS = os.path.join(BASE, "datos")
if not os.path.exists(os.path.join(DATOS, "responses.csv")):
    DATOS = BASE  # alternativa: los CSV junto al script
raw = pd.read_csv(os.path.join(DATOS, "responses.csv"))
cols = list(raw.columns)
# AUDITORIA m11: el assert desaparecia con `python -O` y cols.index() lanzaba un
# ValueError poco informativo justo cuando lo que se busca es diagnosticar un renombrado.
faltan = {"History", "Pets"} - set(cols)
if faltan:
    raise SystemExit(f"Faltan columnas en responses.csv (¿renombradas?): {sorted(faltan)}")
items_orig = cols[cols.index("History"): cols.index("Pets") + 1]
if len(items_orig) != 32:
    raise SystemExit(f"Se esperaban 32 items entre History y Pets; se hallaron "
                     f"{len(items_orig)}: {items_orig}")

datos = raw[items_orig].rename(columns={k: v[0] for k, v in ETIQUETAS.items()})
etiqueta = {v[0]: v[1] for v in ETIQUETAS.values()}
n_total = len(datos)
X = datos.dropna().astype(float)
n = len(X)
resumen["datos"] = {"n_total": n_total, "n_completos": n, "n_excluidos": n_total - n,
                    "n_items": X.shape[1]}

desc = pd.DataFrame({
    "item": [etiqueta[c] for c in X.columns],
    "media": X.mean().round(2).values,
    "de": X.std().round(2).values,
    "asimetria": X.skew().round(2).values,
    "curtosis": X.kurt().round(2).values,
    "faltantes": datos.isna().sum().values,
}, index=X.columns)
guardar(desc, "01_descriptivos.csv")

# Normalidad multivariada (Mardia), relevante para la estimación ML
Z = X.values - X.values.mean(axis=0)
S_inv = np.linalg.inv(np.cov(Z, rowvar=False, bias=True))
D = Z @ S_inv @ Z.T
p = X.shape[1]
# AUDITORIA M2: la asimetria multivariada de Mardia es b1p = (1/n^2) * sum_i d_i^3,
# es decir la diagonal de D (d_i^2) elevada a 3/2. Sumar (D**3).sum() recorre ademas
# los n^2 elementos fuera de la diagonal, que llevan signo y se cancelan parcialmente.
b1 = (np.diag(D) ** 1.5).sum() / n ** 2
b2 = np.mean(np.diag(D) ** 2)
z_asim = b1 / np.sqrt(2 * p * (p + 1) / (6 * n))
# La varianza de b2p bajo H0 es 8p(p+2)/n (verificada por simulacion: Var=8.49 frente
# a 9.82 teorico; la variante con /3 queda descartada).
z_kurt = (b2 - p * (p + 2)) / np.sqrt(8 * p * (p + 2) / n)
resumen["mardia"] = {"asimetria_b1p": round(b1, 4), "z_asimetria": round(z_asim, 2),
                     "curtosis_b2p": round(b2, 2),
                     "curtosis_esperada": p * (p + 2), "z_curtosis": round(z_kurt, 2),
                     "p_curtosis": float(2 * (1 - stats.norm.cdf(abs(z_kurt))))}

# ===========================================================================
# 2. ANÁLISIS FACTORIAL EXPLORATORIO
# ===========================================================================
# 2.1 Factibilidad
chi2_b, p_b = calculate_bartlett_sphericity(X)
kmo_items, kmo_total = calculate_kmo(X)
resumen["factibilidad"] = {"kmo": round(kmo_total, 3),
                           "bartlett_chi2": round(chi2_b, 2),
                           "bartlett_gl": p * (p - 1) // 2,
                           "bartlett_p": float(p_b),
                           "det_R": float(np.linalg.det(X.corr().values))}
msa = pd.DataFrame({"item": [etiqueta[c] for c in X.columns], "MSA": np.round(kmo_items, 3)},
                   index=X.columns)
guardar(msa, "02_kmo_por_item.csv")

# 2.2 Número de factores: Kaiser, scree y análisis paralelo (Horn)
eig = np.sort(np.linalg.eigvalsh(X.corr().values))[::-1]
rng = np.random.default_rng(SEED)
sim = np.array([np.sort(np.linalg.eigvalsh(np.corrcoef(rng.normal(size=X.shape), rowvar=False)))[::-1]
                for _ in range(500)])
pa95 = np.percentile(sim, 95, axis=0)
n_kaiser = int((eig > 1).sum())
# AUDITORIA M5: np.argmax sobre un vector booleano devuelve 0 sin aviso si ningun
# autovalor cae bajo la linea paralela, lo que publicaba "0 factores" en el JSON y la figura.
_corte = np.flatnonzero(eig < pa95)
if _corte.size == 0:
    raise SystemExit("Ningun autovalor cae bajo el percentil 95 de la linea paralela.")
n_paralelo = int(_corte[0])
resumen["n_factores"] = {"kaiser": n_kaiser, "paralelo": n_paralelo,
                         "autovalores": np.round(eig[:10], 3).tolist(),
                         "paralelo_p95": np.round(pa95[:10], 3).tolist()}
guardar(pd.DataFrame({"autovalor": eig, "paralelo_p95": pa95,
                      "var_explicada_%": 100 * eig / p},
                     index=range(1, p + 1)), "03_autovalores.csv")

fig, ax = plt.subplots(figsize=(7.5, 4.2))
ax.plot(range(1, p + 1), eig, "o-", color="#1b3a5c", label="Datos observados")
ax.plot(range(1, p + 1), pa95, "s--", color="#e0a020", ms=4, label="Análisis paralelo (p95)")
ax.axhline(1, color="grey", lw=0.8, ls=":", label="Criterio de Kaiser (λ = 1)")
ax.axvline(n_paralelo, color="#b03030", lw=0.8, ls="--")
ax.annotate(f"{n_paralelo} factores", (n_paralelo + 0.3, eig[0] * 0.8), color="#b03030")
ax.set_xlabel("Número de factor")
ax.set_ylabel("Autovalor")
# (Sin título interno: en APA el título va sobre la figura, en el informe)
ax.legend(frameon=False)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig1_scree_paralelo.png"), dpi=200, bbox_inches="tight")
plt.close(fig)

# Comparación de soluciones alternativas (AUDITORIA C2: se amplía de 5,6,7 a 3-7; con
# CFI y TLI por debajo de 0.90 corresponde contrastar tambien soluciones con MENOS factores,
# que era el hueco de la version anterior).
comp = []
for k in (3, 4, 5, 6, 7):
    m = efa(X, k)
    Lk = pd.DataFrame(m.loadings_, index=X.columns, columns=[f"F{i+1}" for i in range(k)])
    ak = Lk.abs()
    p_k = ak.max(axis=1)
    c_k = ak.apply(lambda r: r.sort_values().iloc[-2], axis=1)
    ret_k = (p_k >= .40) & (c_k < .35)
    tam = ak[ret_k].idxmax(axis=1).value_counts()
    comp.append({"k": k, "var_acumulada_%": round(100 * m.get_factor_variance()[2][-1], 1),
                 "items_carga_>=.40": int((p_k >= .40).sum()),
                 "items_retenidos": int(ret_k.sum()),
                 "factores_con_<3_items": int((tam < 3).sum())})
guardar(pd.DataFrame(comp).set_index("k"), "04_comparacion_k.csv")
resumen["comparacion_k"] = comp

K = 6
# 2.3 AFE inicial con los 32 ítems (ML + promax)
efa1 = efa(X, K)
L1 = pd.DataFrame(efa1.loadings_, index=X.columns, columns=[f"F{i+1}" for i in range(K)])
L1, _ = nombrar_factores(L1)
L1["h2"] = efa1.get_communalities()
guardar(L1.round(3), "05_cargas_afe_inicial_32.csv")
var1 = efa1.get_factor_variance()
resumen["afe_inicial"] = {"var_acumulada_%": round(100 * var1[2][-1], 1)}

# 2.4 Depuración: carga principal >= .40 y ninguna carga cruzada >= .35
abs1 = L1[ORDEN_FACTORES].abs()
principal = abs1.max(axis=1)
cruzada = abs1.apply(lambda r: r.sort_values().iloc[-2], axis=1)
retener = (principal >= .40) & (cruzada < .35)
depuracion = pd.DataFrame({
    "item": [etiqueta[c] for c in L1.index],
    "factor": abs1.idxmax(axis=1).map(NOMBRE_FACTOR),
    "carga_principal": principal.round(2),
    "carga_cruzada_max": cruzada.round(2),
    "h2": L1["h2"].round(2),
    "decision": np.where(retener, "Se retiene", "Se elimina"),
})
guardar(depuracion, "06_depuracion_items.csv")
items_ret = list(L1.index[retener])
resumen["depuracion"] = {"retenidos": len(items_ret),
                         "eliminados": [etiqueta[c] for c in L1.index[~retener]]}

# 2.5 AFE final con los ítems retenidos
Xr = X[items_ret]
efa2 = efa(Xr, K)
L2 = pd.DataFrame(efa2.loadings_, index=items_ret, columns=[f"F{i+1}" for i in range(K)])
L2, mapa2 = nombrar_factores(L2)
L2["h2"] = efa2.get_communalities()
guardar(L2.round(3), "07_cargas_afe_final.csv")

# AUDITORIA C3: la depuracion se aplico a la solucion de 32 items, pero tras reestimar con
# los 20 items el criterio deja de cumplirse para algunos. Se comprueba y se deja constancia.
_a2 = L2[ORDEN_FACTORES].abs()
_p2 = _a2.max(axis=1)
_c2 = _a2.apply(lambda r: r.sort_values().iloc[-2], axis=1)
guardar(pd.DataFrame({"item": [etiqueta[c] for c in _p2.index],
                      "carga_principal": _p2.round(3).values,
                      "carga_cruzada_max": _c2.round(3).values,
                      "cumple_criterio": (_p2 >= .40).values}),
        "20_items_fuera_de_criterio.csv")
resumen["reverificacion_criterio"] = {
    "items_que_ya_no_cumplen": [etiqueta[c] for c in _p2[_p2 < .40].index],
    "cruzada_maxima": round(float(_c2.max()), 3),
    "item_cruzada_maxima": etiqueta[_c2.idxmax()]}
print("Reverificacion del criterio tras reestimar: items por debajo de 0.40 ->",
      [etiqueta[c] for c in _p2[_p2 < .40].index])
var2 = efa2.get_factor_variance()
orden_cols = [f"F{i+1}" for i in range(K)]
var_tab = pd.DataFrame(np.array(var2), index=["SS cargas", "Prop. varianza", "Prop. acumulada"],
                       columns=[mapa2.get(c, c) for c in orden_cols])
var_tab = var_tab.loc[["SS cargas", "Prop. varianza"], ORDEN_FACTORES]
var_tab["Total"] = [var_tab.loc["SS cargas"].sum(), var_tab.loc["Prop. varianza"].sum()]
guardar(var_tab.round(3), "08_varianza_afe_final.csv")
phi = pd.DataFrame(efa2.phi_, index=[mapa2.get(c, c) for c in orden_cols],
                   columns=[mapa2.get(c, c) for c in orden_cols]).loc[ORDEN_FACTORES, ORDEN_FACTORES]
guardar(phi.round(3), "09_correlaciones_factores_afe.csv")
kmo_r = calculate_kmo(Xr)[1]
resumen["afe_final"] = {"n_items": len(items_ret), "kmo": round(kmo_r, 3),
                        "var_acumulada_%": round(100 * var2[2][-1], 1)}

# Asignación de ítems a factores (modelo de medición)
asignacion = L2[ORDEN_FACTORES].abs().idxmax(axis=1)
modelo_medicion = {f: [i for i in items_ret if asignacion[i] == f] for f in ORDEN_FACTORES}
resumen["modelo_medicion"] = modelo_medicion

# Fiabilidad por factor
fiab = pd.DataFrame({
    "factor": [NOMBRE_FACTOR[f] for f in ORDEN_FACTORES],
    "n_items": [len(modelo_medicion[f]) for f in ORDEN_FACTORES],
    "alfa": [round(alfa_cronbach(Xr[modelo_medicion[f]]), 3) for f in ORDEN_FACTORES],
}, index=ORDEN_FACTORES)
# AUDITORIA M6: estos alfas se imprimian pero nunca se guardaban, y eran la unica cifra
# del script sin CSV correspondiente (el README indica copiar valores desde resultados/).
guardar(fiab, "21_alfa_afe_final.csv")

# Mapa de calor de cargas
fig, ax = plt.subplots(figsize=(7.5, 7))
orden_items = [i for f in ORDEN_FACTORES for i in modelo_medicion[f]]
M = L2.loc[orden_items, ORDEN_FACTORES].values
im = ax.imshow(M, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
ax.set_xticks(range(K))
ax.set_xticklabels([NOMBRE_FACTOR[f] for f in ORDEN_FACTORES], fontsize=7.5, rotation=35, ha="right")
ax.set_yticks(range(len(orden_items)))
ax.set_yticklabels([etiqueta[i] for i in orden_items], fontsize=8)
for r in range(M.shape[0]):
    for c in range(M.shape[1]):
        ax.text(c, r, f"{M[r, c]:.2f}", ha="center", va="center", fontsize=6.5,
                color="white" if abs(M[r, c]) > .5 else "black")
fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02, label="Carga factorial")
# (Sin título interno: en APA el título va sobre la figura, en el informe)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig2_cargas_afe.png"), dpi=200, bbox_inches="tight")
plt.close(fig)

# 2.6 Estabilidad: réplica del AFE final en dos mitades aleatorias (congruencia de Tucker)
idx = np.random.default_rng(SEED).permutation(n)
mitades = [Xr.iloc[idx[: n // 2]], Xr.iloc[idx[n // 2:]]]
cargas_m = []
for h in mitades:
    m = efa(h, K)
    Lh = pd.DataFrame(m.loadings_, index=items_ret, columns=[f"F{i+1}" for i in range(K)])
    Lh, _ = nombrar_factores(Lh)
    cargas_m.append(Lh)
congr = {}
for f in ORDEN_FACTORES:
    if f in cargas_m[0].columns and f in cargas_m[1].columns:
        a, b = cargas_m[0][f].values, cargas_m[1][f].values
        congr[f] = round(abs(a @ b) / np.sqrt((a @ a) * (b @ b)), 3)
    else:
        congr[f] = None
resumen["congruencia_mitades"] = congr

# ===========================================================================
# 3. ANÁLISIS FACTORIAL CONFIRMATORIO (semopy, estimación ML)
# ===========================================================================
def sintaxis(modelo, extra=""):
    lineas = [f"{f} =~ " + " + ".join(its) for f, its in modelo.items()]
    return "\n".join(lineas) + ("\n" + extra if extra else "")


def ajustar_afc(desc_modelo, data):
    m = semopy.Model(desc_modelo)
    m.fit(data, obj="MLW")
    st = semopy.calc_stats(m).T.iloc[:, 0]
    # SRMR: residuo cuadrático medio estandarizado
    obs = m.vars["observed"]
    S = data[obs].cov().values * (len(data) - 1) / len(data)
    Sigma = m.calc_sigma()[0]
    d = np.sqrt(np.diag(S))
    Rres = (S - Sigma) / np.outer(d, d)
    # AUDITORIA M1: SRMR = RMS de los residuales estandarizados sobre los p(p-1)/2 pares
    # distintos (definicion estandar, la de Hu y Bentler, 1999). La version anterior
    # usaba np.tril_indices, que ademas de esos pares incluye la diagonal, y por tanto
    # reportaba una cifra menor (M1: 0.067 vs 0.071; M2: 0.062 vs 0.065). Ninguna
    # conclusion cambia, ambas quedan bajo 0.08; se adoptan los valores estandar.
    tri = np.triu_indices(len(obs), 1)
    srmr = float(np.sqrt(np.mean(Rres[tri] ** 2)))
    chi2, gl = float(st["chi2"]), float(st["DoF"])
    nn = len(data)

    # IC 90 % del RMSEA (método del parámetro de no centralidad)
    def lam(target):
        # Cota superior por la formula del limite superior real del IC; con la anterior
        # (10*chi2) un modelo bien ajustado y muchos gl truncaría rmsea_hi en silencio.
        lo, hi = 0.0, (np.sqrt(chi2) + 1.645 * np.sqrt(2 * gl)) ** 2 + 1.0
        if stats.ncx2.cdf(chi2, gl, 1e-9) < target:
            return 0.0
        for _ in range(200):
            mid = (lo + hi) / 2
            if stats.ncx2.cdf(chi2, gl, mid) > target:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2
    rmsea_lo = np.sqrt(lam(0.95) / (gl * (nn - 1)))
    rmsea_hi = np.sqrt(lam(0.05) / (gl * (nn - 1)))
    ajuste = {"chi2": round(chi2, 2), "gl": int(gl), "p": float(st["chi2 p-value"]),
              "chi2_gl": round(chi2 / gl, 2), "CFI": round(float(st["CFI"]), 3),
              "TLI": round(float(st["TLI"]), 3), "RMSEA": round(float(st["RMSEA"]), 3),
              "RMSEA_IC90": [round(rmsea_lo, 3), round(rmsea_hi, 3)],
              "SRMR": round(srmr, 3)}
    # Modelo nulo (independencia): su RMSEA indica cuánto margen tienen CFI/TLI.
    # El argumento se sustenta en Kenny (s. f.); si se cita en el informe, debe
    # incorporarse a la lista de Referencias (AUDITORIA M7: cita colgante).
    R_ = data[obs].corr().values
    pp = len(obs)
    chi2_nulo = (nn - 1) * (-np.log(np.linalg.det(R_)))
    gl_nulo = pp * (pp - 1) / 2
    ajuste["RMSEA_nulo"] = round(float(np.sqrt(max(chi2_nulo - gl_nulo, 0) / (gl_nulo * (nn - 1)))), 3)
    ajuste["r_media_abs"] = round(float(np.abs(R_[np.triu_indices(pp, 1)]).mean()), 3)
    Rres_df = pd.DataFrame(Rres, index=obs, columns=obs)
    return m, ajuste, Rres_df


def tablas_afc(m, modelo):
    est = m.inspect(std_est=True)
    cargas = est[est["op"] == "~"].copy()          # semopy: indicador ~ factor
    cargas = cargas.rename(columns={"lval": "item", "rval": "factor"})
    cargas = cargas[["factor", "item", "Estimate", "Std. Err", "z-value", "p-value", "Est. Std"]]
    cargas["R2"] = cargas["Est. Std"].astype(float) ** 2
    cov = est[(est["op"] == "~~") & (est["lval"] != est["rval"])]
    lat = list(modelo)
    corr = pd.DataFrame(np.eye(len(lat)), index=lat, columns=lat)
    for _, r in cov.iterrows():
        if r["lval"] in lat and r["rval"] in lat:
            corr.loc[r["lval"], r["rval"]] = corr.loc[r["rval"], r["lval"]] = float(r["Est. Std"])
    err_cov = cov[~cov["lval"].isin(lat)][["lval", "rval", "Estimate", "Est. Std", "p-value"]]
    validez = []
    for f in lat:
        lam_ = cargas.loc[cargas["factor"] == f, "Est. Std"].astype(float).values
        cr = lam_.sum() ** 2 / (lam_.sum() ** 2 + (1 - lam_ ** 2).sum())
        ave = np.mean(lam_ ** 2)
        max_r = corr.loc[f].drop(f).abs().max()
        validez.append({"factor": f, "n_items": len(lam_), "CR": round(cr, 3), "AVE": round(ave, 3),
                        "raiz_AVE": round(np.sqrt(ave), 3), "max_corr": round(max_r, 3),
                        "Fornell_Larcker": "Cumple" if np.sqrt(ave) > max_r else "No cumple"})
    return cargas, corr, pd.DataFrame(validez).set_index("factor"), err_cov


# 3.1 Modelo M1: estructura derivada del AFE
desc_m1 = sintaxis(modelo_medicion)
with open(os.path.join(OUT, "modelo_M1.txt"), "w", encoding="utf-8") as fh:
    fh.write(desc_m1)
m1, ajuste_m1, res_m1 = ajustar_afc(desc_m1, Xr)
cargas_m1, corr_m1, val_m1, _ = tablas_afc(m1, modelo_medicion)
guardar(cargas_m1.round(3), "10_cargas_afc_M1.csv")
guardar(val_m1, "11_validez_M1.csv")
resumen["afc_M1"] = ajuste_m1

# Residuos estandarizados más grandes (posibles fuentes de desajuste)
tri = np.triu_indices(len(res_m1), 1)
pares = pd.DataFrame({"item_1": res_m1.index[tri[0]], "item_2": res_m1.columns[tri[1]],
                      "residuo": res_m1.values[tri]})
pares["abs"] = pares["residuo"].abs()
# AUDITORIA m3: quicksort no es estable; un empate cambiaria que par recibe la covarianza
# de errores y, en cascada, todo el ajuste de M2. mergesort garantiza el orden.
top_res = (pares.sort_values("abs", ascending=False, kind="mergesort")
           .head(10).drop(columns="abs"))
guardar(top_res.round(3).reset_index(drop=True), "12_residuos_M1.csv")

# 3.2 Modelo M2 (ajustado). Re-especificaciones, cada una con justificación teórica:
#   a) Se eliminan los indicadores con carga estandarizada < .40 en M1, salvo que
#      su factor quede con menos de 3 indicadores (requisito de identificación
#      recomendado por Kline, 2023).
#   b) Se libera la covarianza de errores del par con el mayor residuo de M1
#      (Computación ~~ Autos): ambos reflejan un interés técnico-mecánico común
#      que no explican sus factores (y que se asocia al género, ver tabla 19).
modelo_m2 = {f: list(its) for f, its in modelo_medicion.items()}
cambios = []
for _, r in cargas_m1.iterrows():
    lam_ = float(r["Est. Std"])
    f, it = r["factor"], r["item"]
    if lam_ < .40:
        if len(modelo_m2[f]) > 3:
            modelo_m2[f].remove(it)
            cambios.append(f"Se elimina '{etiqueta[it]}' (carga M1 = {lam_:.2f})")
        else:
            cambios.append(f"Se conserva '{etiqueta[it]}' (carga M1 = {lam_:.2f}) para mantener "
                           f"3 indicadores en '{NOMBRE_FACTOR[f]}'")
# AUDITORIA M4: se eligen los dos items con mayor residuo de correccion, pero solo si
# pertenecen a factores DISTINTOS y ambos sobreviven a M2. Sin esas dos comprobaciones el
# parametro seria no identificable (mismo factor) o haria fallar el ajuste (item eliminado).
factor_de = {it: f for f, its in modelo_m2.items() for it in its}
candidatos = [r for _, r in top_res.iterrows()
              if factor_de.get(r["item_1"]) != factor_de.get(r["item_2"])
              and r["item_1"] in factor_de and r["item_2"] in factor_de]
if not candidatos:
    raise SystemExit("No hay ningun par de items de factores distintos que reciba la "
                     "covarianza de errores; revisar los residuos de M1.")
a_, b_ = candidatos[0]["item_1"], candidatos[0]["item_2"]
extra = f"{b_} ~~ {a_}"
cambios.append(f"Covarianza de errores {etiqueta[b_]} ~~ {etiqueta[a_]} "
               f"(residuo M1 = {candidatos[0]['residuo']:.3f})")
desc_m2 = sintaxis(modelo_m2, extra)
with open(os.path.join(OUT, "modelo_M2.txt"), "w", encoding="utf-8") as fh:
    fh.write(desc_m2)
items_m2 = sum(modelo_m2.values(), [])
m2, ajuste_m2, res_m2 = ajustar_afc(desc_m2, Xr[items_m2])
cargas_m2, corr_m2, val_m2, errcov_m2 = tablas_afc(m2, modelo_m2)
guardar(cargas_m2.round(3), "13_cargas_afc_M2.csv")
guardar(val_m2, "14_validez_M2.csv")
guardar(corr_m2.round(3), "15_correlaciones_factores_M2.csv")
guardar(errcov_m2.round(3), "16_covarianza_errores_M2.csv")
resumen["afc_M2"] = ajuste_m2
resumen["afc_M2_cambios"] = cambios
resumen["afc_M2_covarianza_errores"] = errcov_m2.round(3).to_dict(orient="records")

comparacion = pd.DataFrame([dict(modelo="M1", items=len(items_ret), **{k: v for k, v in ajuste_m1.items() if k not in ("RMSEA_IC90", "AIC", "BIC")}),
                            dict(modelo="M2", items=len(items_m2), **{k: v for k, v in ajuste_m2.items() if k not in ("RMSEA_IC90", "AIC", "BIC")})]).set_index("modelo")
guardar(comparacion, "17_comparacion_ajuste.csv")

# Asociación de los ítems con el género (para interpretar los residuos)
genero = raw.loc[Xr.index, "Gender"].map({"female": 0, "male": 1})
r_gen = Xr[items_m2].corrwith(genero).round(3)
guardar(pd.DataFrame({"item": [etiqueta[i] for i in r_gen.index], "r_hombre": r_gen.values},
                     index=r_gen.index).sort_values("r_hombre"), "19_correlacion_genero.csv")
resumen["genero_n_validos"] = int(genero.notna().sum())

# ---------------------------------------------------------------------------
# 3.4 AUDITORIA C1: validacion cruzada del AFC en las dos mitades.
# La replica en mitades anterior solo reestimaba el AFE (congruencia de Tucker), de modo
# que no aportaba ninguna evidencia sobre el ajuste del AFC. Aqui se ajusta el modelo M2
# por separado en cada mitad y se comparan sus indices con los de la muestra completa.
# ---------------------------------------------------------------------------
val_cruzada = []
for nombre, h in zip(("Mitad 1", "Mitad 2"), mitades):
    try:
        _, aj_h, _ = ajustar_afc(desc_m2, h[items_m2])
        val_cruzada.append(dict(muestra=nombre, items=len(items_m2), n=len(h), **aj_h))
    except Exception as exc:                       # noqa: BLE001
        val_cruzada.append(dict(muestra=nombre, items=len(items_m2), n=len(h),
                                error=f"{type(exc).__name__}: {exc}"))
# El IC del RMSEA sale como lista de np.float64 y se volcaba al CSV como el repr
# "[np.float64(0.058), np.float64(0.074)]"; se convierten a float nativo.
for r in val_cruzada:
    if isinstance(r.get("RMSEA_IC90"), (list, tuple)):
        r["RMSEA_IC90"] = [round(float(x), 3) for x in r["RMSEA_IC90"]]
guardar(pd.DataFrame([dict(muestra="Muestra completa", items=len(items_m2), n=n,
                           **{k: v for k, v in ajuste_m2.items() if k != "RMSEA_IC90"})]
                      + [{k: v for k, v in r.items()} for r in val_cruzada])
        .set_index("muestra"), "22_validacion_cruzada_mitades.csv")
resumen["validacion_cruzada"] = val_cruzada
print("\nValidacion cruzada del AFC en dos mitades:")
for r in val_cruzada:
    print("  ", r)

# Fiabilidad final (alfa) junto con CR y AVE del modelo M2
fiab_m2 = val_m2.copy()
fiab_m2["alfa"] = [round(alfa_cronbach(Xr[modelo_m2[f]]), 3) for f in fiab_m2.index]
guardar(fiab_m2, "18_fiabilidad_validez_final.csv")

# 3.3 Diagrama del modelo M2 (cargas estandarizadas)
fig, ax = plt.subplots(figsize=(11, 6.2))
ax.axis("off")
n_it = len(items_m2)
x_items = np.linspace(0.03, 0.97, n_it)
pos_item = dict(zip(items_m2, x_items))
pos_fac = {f: np.mean([pos_item[i] for i in modelo_m2[f]]) for f in ORDEN_FACTORES}
colores = ["#1b3a5c", "#2e7d6b", "#b05a1f", "#6a3d9a", "#a8323e", "#5f6b2a"]
for c, f in zip(colores, ORDEN_FACTORES):
    xf = pos_fac[f]
    ax.add_patch(matplotlib.patches.Ellipse((xf, 0.8), 0.115, 0.13, fc="white", ec=c, lw=1.6))
    ax.text(xf, 0.8, NOMBRE_FACTOR[f].replace(" y ", "\ny "), ha="center", va="center",
            fontsize=6.6, color=c, weight="bold")
    for it in modelo_m2[f]:
        lam_ = float(cargas_m2.loc[cargas_m2["item"] == it, "Est. Std"].iloc[0])
        ax.annotate("", xy=(pos_item[it], 0.27), xytext=(xf, 0.735),
                    arrowprops=dict(arrowstyle="->", color=c, lw=0.6 + 1.6 * lam_))
        ax.text(pos_item[it] + (xf - pos_item[it]) * 0.2, 0.37 + 0.33 * 0.2, f"{lam_:.2f}",
                fontsize=6, ha="center", color=c,
                bbox=dict(fc="white", ec="none", pad=0.3))
for it in items_m2:
    ax.add_patch(matplotlib.patches.Rectangle((pos_item[it] - 0.021, 0.12), 0.042, 0.15, fc="#f2f2f2",
                                              ec="#555", lw=0.6))
    ax.text(pos_item[it], 0.195, etiqueta[it].split(" (")[0], rotation=90, ha="center", va="center",
            fontsize=5.6)
if extra:
    xa, xb = pos_item[a_], pos_item[b_]
    ax.annotate("", xy=(xa, 0.11), xytext=(xb, 0.11),
                arrowprops=dict(arrowstyle="<->", connectionstyle="arc3,rad=0.25", color="grey", lw=0.8))
    _par = errcov_m2[((errcov_m2["lval"] == a_) & (errcov_m2["rval"] == b_)) |
                 ((errcov_m2["lval"] == b_) & (errcov_m2["rval"] == a_))]
    if len(_par):
        r_ = float(_par["Est. Std"].iloc[0])
        ax.text((xa + xb) / 2, 0.035, f"r(e) = {r_:.2f}", ha="center", fontsize=6, color="grey")
ax.set_xlim(-0.01, 1.03)
ax.set_ylim(-0.06, 0.92)
# (Sin título interno: en APA el título va sobre la figura, en el informe)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig3_diagrama_afc.png"), dpi=220, bbox_inches="tight")
plt.close(fig)

# Mapa de calor de correlaciones entre factores (M2)
fig, ax = plt.subplots(figsize=(6, 5))
C = corr_m2.loc[ORDEN_FACTORES, ORDEN_FACTORES].values
im = ax.imshow(C, cmap="RdBu_r", vmin=-1, vmax=1)
lbl = [NOMBRE_FACTOR[f] for f in ORDEN_FACTORES]
ax.set_xticks(range(K))
ax.set_xticklabels(lbl, rotation=40, ha="right", fontsize=7.5)
ax.set_yticks(range(K))
ax.set_yticklabels(lbl, fontsize=7.5)
for r in range(K):
    for c in range(K):
        ax.text(c, r, f"{C[r, c]:.2f}", ha="center", va="center", fontsize=7.5,
                color="white" if abs(C[r, c]) > .5 else "black")
fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
# (Sin título interno: en APA el título va sobre la figura, en el informe)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig4_correlaciones_factores.png"), dpi=200, bbox_inches="tight")
plt.close(fig)

with open(os.path.join(OUT, "resumen.json"), "w", encoding="utf-8") as fh:
    json.dump(resumen, fh, ensure_ascii=False, indent=2, default=float)

# ---------------------------------------------------------------------------
print("=" * 70)
print(f"Casos completos: {n} de {n_total}   |   Ítems: {p}")
print(f"KMO = {kmo_total:.3f}   Bartlett: chi2({p*(p-1)//2}) = {chi2_b:.1f}, p = {p_b:.2e}")
print(f"Kaiser: {n_kaiser} factores   |   Análisis paralelo: {n_paralelo} factores")
print(f"Ítems retenidos tras depuración: {len(items_ret)}")
print("\nFiabilidad (alfa) AFE final:\n", fiab.to_string())
print("\nCongruencia de Tucker entre mitades:", congr)
print("\nAjuste M1:", ajuste_m1)
print("Ajuste M2:", ajuste_m2)
print("Cambios M2:", cambios)
print("\nValidez M2:\n", fiab_m2.to_string())
print(f"\nResultados guardados en: {OUT}")
