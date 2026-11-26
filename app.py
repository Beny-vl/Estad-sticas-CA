#Imports
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
from scipy import stats

# TITULO
st.set_page_config(page_title="STATS CA", layout="wide")

@st.cache_data
def cargar_datos():
    df = pd.read_csv('DATASET_1_Torneo.csv')
    clave_candidata = ['ID_JUGADOR', 'ID_EQUIPO', 'JORNADA', 'CATEGORIA']
    indx_ambiguas = df.duplicated(subset=clave_candidata, keep=False)
    df = df[~indx_ambiguas]
    df = df[df.groupby('ID_JUGADOR')['POSICION'].transform('nunique') == 1]
    return df

df = cargar_datos()

#Tabla que se muestra
tabla_Visible = df.groupby('ID_JUGADOR').agg(
    minutos_totales=('MINUTOS JUGADOS', 'sum'),
    numero_partidos=('JORNADA', 'count'),
    posicion=('POSICION', 'first'),
    categoria=('CATEGORIA', 'first'),
    ).reset_index()

# --- Menú lateral  ---
seccion = st.sidebar.radio(
    "Navegación",
    ["Inicio", "Stats Individuales", "Comparar Estadísticas"]
)

# ---------------------- Seccion stats indiviuales ------------------------

if seccion == "Stats Individuales":
    st.title("📊 Stats Individuales")

    col1, col2 = st.columns([2, 1])

    with col2:
      categoria_seleccionada = st.multiselect("Seleccionar Gategoría",
                                                options=sorted(df['CATEGORIA'].dropna().unique()))
      posicion_seleccionada = st.multiselect("Seleccionar Posición",
                                               options=sorted(df['POSICION'].dropna().unique()))

    if categoria_seleccionada:
      tabla_Visible = tabla_Visible[tabla_Visible['categoria'].isin(categoria_seleccionada)]
    if posicion_seleccionada:
      tabla_Visible = tabla_Visible[tabla_Visible['posicion'].isin(posicion_seleccionada)]

    with col1:
        jugador_seleccionado = st.selectbox(
            "🔍 Buscar o seleccionar jugador:",
            options=list(tabla_Visible['ID_JUGADOR'])
        )

        if jugador_seleccionado:
          tabla_jugadorSeleccionado = df[df['ID_JUGADOR']==jugador_seleccionado]
          jugador_minutos = tabla_jugadorSeleccionado['MINUTOS JUGADOS'].sum()
          jugador_jornadas = tabla_jugadorSeleccionado['JORNADA'].count()
          jugador_posicion = tabla_jugadorSeleccionado["POSICION"].iloc[0]
          jugador_categoria = tabla_jugadorSeleccionado['CATEGORIA'].iloc[0]

        with st.container(border=True):
          m1, m2, m3 = st.columns([2, 1, 1])
          m1.metric("Posición", jugador_posicion)
          m2.metric("Categoría", jugador_categoria)
          m3.metric("Año de Nacimiento", tabla_jugadorSeleccionado["AÑO_NAC"].iloc[0])

    st.dataframe(tabla_Visible, height=250, use_container_width=True)

    st.divider() # ----- LINEA SEPARADORA ------

    st.title(f"Mostrando estadísticas de - {jugador_seleccionado}")
    st.write("(DEBRP = Diferencia entre balones recuperados y perdidos. Positiva : Más recuperaciones en promedio, Negativa : Más perdidas en promedio)")

    if tabla_jugadorSeleccionado['DIFERENCIA ENTRE BALONES RECUPERADOS Y BALONES PERDIDOS'].sum() != 0:
      DEBRP = tabla_jugadorSeleccionado['DIFERENCIA ENTRE BALONES RECUPERADOS Y BALONES PERDIDOS'].sum()/jugador_jornadas
    else:
      DEBRP = 0

    if ( DEBRP <= 0 ):
      diferencia = "Negativa"
    else:
      diferencia = "Positiva"

    with st.container(border=True):
      m1, m2, m3, m4 = st.columns([2,1,1,1])
      m1.metric("Posición", jugador_posicion)
      m2.metric("Número de Partidos", jugador_jornadas)
      m3.metric("Minutos Jugados", jugador_minutos)
      m4.metric("DEBRP", diferencia)

    st.metric("Promedio de Minutos Jugados por partido: ", round(jugador_minutos / jugador_jornadas, 2))

    datos_pases = tabla_jugadorSeleccionado[['JORNADA', 'TOTAL PASES ACERTADOS', 'TOTAL PASES NO ACERTADOS']].sort_values('JORNADA')
    datos_pases = datos_pases.rename(columns={
    'TOTAL PASES ACERTADOS': 'Pases Acertados',
    'TOTAL PASES NO ACERTADOS': 'Pases Fallados'})

    datos_faltas = tabla_jugadorSeleccionado[['JORNADA', 'FALTAS RECIBIDAS', 'FALTAS COMETIDAS']].sort_values('JORNADA')
    datos_faltas = datos_faltas.rename(columns={
    'FALTAS COMETIDAS': 'Faltas Cometidas',
    'FALTAS RECIBIDAS': 'Faltas Recibidas'})

    st.write(f"**Comparación pases fallados y pases completados en {jugador_jornadas} partidos**")

    st.bar_chart(datos_pases, height=350, x='JORNADA', color=['#00CC96', '#EF553B'], stack=False)

    st.write(f"**Comparación faltas cometidas y faltas recibidas en {jugador_jornadas} partidos**")

    st.bar_chart(datos_faltas, height=350, x='JORNADA', color=['#00CC96', '#EF553B'], stack=False)

    m1, m2 = st.columns(2)
    m1.metric('Promedio de Faltas Cometidas: ', round(datos_faltas['Faltas Cometidas'].sum()/jugador_jornadas, 3))
    m2.metric('Promedio de Faltas Recibidas: ', round(datos_faltas['Faltas Recibidas'].sum()/jugador_jornadas, 3))

    # ------------------------ Tabs ofensiva y defensiva -----------------------

    tab_ofensiva, tab_defensiva = st.tabs(["🛡️ Stats Defensivas", "⚔️ Stats Ofensivas",])

    with tab_ofensiva:
      st.subheader(f"Rendimiento Defensivo - {jugador_seleccionado}")

      datos_1v1DEF = tabla_jugadorSeleccionado[['JORNADA', '1 VS 1 EXITOSOS DEFENSIVOS', '1VS1 NO EXITOSO DEFENSIVO']].sort_values('JORNADA')
      datos_1v1DEF = datos_1v1DEF.rename(columns={
      '1 VS 1 EXITOSOS DEFENSIVOS': '1 vs 1 Exitosos',
      '1VS1 NO EXITOSO DEFENSIVO': '1 vs 1 No Exitoso'})

      datos_DEBRP = tabla_jugadorSeleccionado[['JORNADA', 'BALONES RECUPERADOS', 'BALONES PERDIDOS TOTALES']].sort_values('JORNADA')
      datos_DEBRP = datos_DEBRP.rename(columns={
      'BALONES RECUPERADOS': 'Balones Recuperados',
      'BALONES PERDIDOS TOTALES': 'Balones Perdidos'})

      st.write(f"**Comparación 1 vs 1 Defensivos Exitosos y No Exitosos en {jugador_jornadas} partidos**")

      st.bar_chart(datos_1v1DEF, height=350, x='JORNADA', color=['#00CC96', '#EF553B'], stack=False)

      jugador_partidosCon1v1DEF = (tabla_jugadorSeleccionado['1 VS 1 DEFENSIVOS TOTALES'] >= 1).sum()

      st.write(f'Partidos donde se llevaron a cabo 1 vs 1 Defensivos: {jugador_partidosCon1v1DEF}')

      if (datos_1v1DEF['1 vs 1 Exitosos'].sum() != 0) :
        PDEF = round(datos_1v1DEF['1 vs 1 Exitosos'].sum()/tabla_jugadorSeleccionado['1 VS 1 OFENSIVOS TOTALES'].sum()*100, 2)
      else :
        PDEF = 0

      st.metric('Porcentaje de Éxito en 1 vs 1 Defensivos:', f'{PDEF}%', f'{int(PDEF)}%')

      st.divider() # ----- LINEA SEPARADORA ------

      st.write(f"**Diferencia entre Balones Recuperados y Balones Perdidos en {jugador_jornadas} partidos**")

      st.bar_chart(datos_DEBRP, height=350, x='JORNADA', color=['#00CC96', '#EF553B'], stack=False)

      st.metric('**Diferencia Promedio entre Balones Recuperados y Perdidos**', round(DEBRP, 3), int(DEBRP))

      st.divider() # ----- LINEA SEPARADORA ------

    with tab_defensiva:
      st.subheader(f"Rendimiento Ofensivo - {jugador_seleccionado}")

      datos_1v1OF = tabla_jugadorSeleccionado[['JORNADA', '1 VS 1 EXITOSOS OFENSIVOS', '1VS1 NO EXITOSO OFENSIVO']].sort_values('JORNADA')
      datos_1v1OF = datos_1v1OF.rename(columns={
      '1 VS 1 EXITOSOS OFENSIVOS': '1 vs 1 Exitosos',
      '1VS1 NO EXITOSO OFENSIVO': '1 vs 1 No Exitoso'})

      st.write(f"**Comparación 1 vs 1 Ofensivos Exitosos y No Exitosos en {jugador_jornadas} partidos**")

      st.bar_chart(datos_1v1OF, height=350, x='JORNADA', color=['#00CC96', '#EF553B'], stack=False)

      jugador_partidosCon1v1OF = (tabla_jugadorSeleccionado['1 VS 1 OFENSIVOS TOTALES'] >= 1).sum()

      st.write(f'Partidos donde se llevaron a cabo 1 vs 1 Ofensivos: {jugador_partidosCon1v1OF}')

      if (datos_1v1OF['1 vs 1 Exitosos'].sum() != 0) :
        POF = round(datos_1v1OF['1 vs 1 Exitosos'].sum()/tabla_jugadorSeleccionado['1 VS 1 OFENSIVOS TOTALES'].sum()*100, 2)
      else :
        POF = 0
      st.metric('Porcentaje de Éxito en 1 vs 1 Ofensivos:', f'{POF}%', f'{int(POF)}%')

      st.divider() # ----- LINEA SEPARADORA ------

      st.write(f"**Estadísticas de Goles, Asistencias y Centros en {jugador_jornadas} partidos**")

      m1, m2, m3 = st.columns(3)
      m1.metric('Promedio de Goles por Partido: ', round(tabla_jugadorSeleccionado['GOLES'].sum()/jugador_jornadas, 3))
      m2.metric('Promedio de Centros por Partido: ', round(tabla_jugadorSeleccionado['CENTROS TOTALES'].sum()/jugador_jornadas, 3))
      m3.metric('Promedio de Asistencias por Partido: ', round(tabla_jugadorSeleccionado['ASISTENCIAS'].sum()/jugador_jornadas, 3))

      datos_Goles = tabla_jugadorSeleccionado[['JORNADA', 'TIROS A GOL', 'GOLES']].sort_values('JORNADA')
      datos_Goles = datos_Goles.rename(columns={
      'TIROS A GOL': 'Tiros a Gol',
      'GOLES': 'Goles'})

      st.bar_chart(datos_Goles, height=350, x='JORNADA', color=['#EF553B', '#00CC96'], stack=False)

      st.divider() # ----- LINEA SEPARADORA ------

      st.write(f"**Estadísticas de Penales Acertados y Fallados en {jugador_jornadas} partidos**")

      datos_Penales = tabla_jugadorSeleccionado[['JORNADA', 'PENALES ANOTADOS', 'PENALES FALLADOS']].sort_values('JORNADA')
      datos_Penales = datos_Penales.rename(columns={
      'PENALES ANOTADOS': 'Penales Anotados',
      'PENALES FALLADOS': 'Penales Fallados'})

      m1, m2 = st.columns(2)
      penales_Tirados = datos_Penales['Penales Anotados'].sum() + datos_Penales['Penales Fallados'].sum()
      m1.metric(f"Penales tirados en {jugador_jornadas} partidos: ", penales_Tirados)
      pct_penales = round(datos_Penales['Penales Anotados'].sum() / penales_Tirados * 100, 2) if penales_Tirados > 0 else 0
      m2.metric('Porcentaje de Penales Acertados: ', f"{pct_penales}%")
      st.bar_chart(datos_Penales, height=350, x='JORNADA', color=['#00CC96', '#EF553B'], stack=False)

      st.divider() # ----- LINEA SEPARADORA ------

# ----------------- Seccion Comparar Estadísticas --------------------

elif seccion == 'Comparar Estadísticas':
  st.title("Comparar Estadísticas por Posición")
  st.write('En esta sección se comparan los indicadores ajustados por tiempo de juego entre distintas posiciones, permitiendo evaluar el impacto del criterio mínimo de minutos en la estabilidad de las métricas.')

  m1, m2 = st.columns([2, 1])

  with m2:
    categoria = st.selectbox("Seleccionar Gategoría",
                                            options=sorted(df['CATEGORIA'].dropna().unique()), index=3)
    min_minutos = st.radio("Mínimo de Minutos Jugados",
                                            options=['Sin Mínimo', 180, 360], index=1)

  with m1:
    with st.container(border=True):
      sub_m1, sub_m2 = st.columns(2)
      sub_m1.metric('Categoría Seleccionada: ', categoria)
      sub_m2.metric('Mínimo de Minutos', min_minutos)
    st.write('Exigir un mínimo de 180 o 360 minutos acumulados reduce la influencia de participaciones muy breves que pueden presentar mayor variabilidad y distorsionar los promedios por cada 90 minutos.')

  st.divider() # ----- LINEA SEPARADORA ------

  # PROCESAMIENTO Y AGREGACIÓN POR JUGADOR (UNIDAD DE ANÁLISIS)

  # Filtramos primero por la categoría elegida
  df_cat = df[df['CATEGORIA'] == categoria].copy()

  # Agrupamos por jugador para que cada futbolista cuente una sola vez
  jugadores_cat = df_cat.groupby('ID_JUGADOR').agg(
      posicion=('POSICION', 'first'),
      minutos_totales=('MINUTOS JUGADOS', 'sum'),
      balones_recuperados=('BALONES RECUPERADOS', 'sum'),
      pases_acertados=('TOTAL PASES ACERTADOS', 'sum'),
      pases_totales=('PASES TOTALES', 'sum')
  ).reset_index()

  # Aplicamos el filtro de mínimo de minutos si no es 'Sin Mínimo'
  if min_minutos != 'Sin Mínimo':
    jugadores_cat = jugadores_cat[jugadores_cat['minutos_totales'] >= min_minutos].copy()

  # Calculamos las tasas individuales (R_i y Q_i del notebook)
  jugadores_cat['tasa_recuperaciones_90'] = (90 * jugadores_cat['balones_recuperados']) / jugadores_cat['minutos_totales']
  jugadores_cat['proporcion_pases'] = (jugadores_cat['pases_acertados'] / jugadores_cat['pases_totales'].replace(0, np.nan)) * 100

  # Selector múltiple de posiciones dentro de la categoría
  posiciones_disp = sorted(jugadores_cat['posicion'].dropna().unique())
  posiciones_defecto = [p for p in ['Defensa Central', 'Volante Defensivo', 'Delantero'] if p in posiciones_disp]

  posiciones_sel = st.multiselect(
      "Selecciona una o más posiciones para comparar:",
      options=posiciones_disp,
      default=posiciones_defecto if posiciones_defecto else posiciones_disp[:3]
  )

  # Validación por si el usuario borra todas las posiciones
  if not posiciones_sel:
    st.warning("⚠️ Por favor, selecciona al menos una posición en el menú superior para visualizar la comparación.")
  else:
    # Filtramos el dataframe final con las posiciones elegidas
    datos_comp = jugadores_cat[jugadores_cat['posicion'].isin(posiciones_sel)].copy()


    # TARJETAS DE RESUMEN (KPIs) Y TAMAÑO DE MUESTRA (n)

    st.subheader("Resumen Descriptivo por Posición")

    # Calculamos las métricas agrupadas por posición
    resumen = datos_comp.groupby('posicion').agg(
        n_jugadores=('ID_JUGADOR', 'count'),
        media_rec_90=('tasa_recuperaciones_90', 'mean'),
        desv_rec_90=('tasa_recuperaciones_90', 'std'),
        mediana_min=('minutos_totales', 'median'),
        pases_acert_sum=('pases_acertados', 'sum'),
        pases_tot_sum=('pases_totales', 'sum')
    ).reset_index()

    # Proporción combinada de pases acertados (q_g del modelo binomial)
    resumen['prop_pases_comb'] = (resumen['pases_acert_sum'] / resumen['pases_tot_sum']) * 100

    # Columna dinámica por cada posición seleccionada (máximo 4 por fila para que se vea limpio)
    cols_kpi = st.columns(len(posiciones_sel))

    for idx, pos in enumerate(posiciones_sel):
      fila = resumen[resumen['posicion'] == pos]
      with cols_kpi[idx]:
        with st.container(border=True):
          st.markdown(f"#### {pos}")
          if not fila.empty:
            r = fila.iloc[0]
            st.metric("Recuperaciones / 90 min (Media)", f"{r['media_rec_90']:.2f}", f"± {r['desv_rec_90']:.2f} DE")
            st.metric("Efectividad de Pases", f"{r['prop_pases_comb']:.1f}%")
            st.caption(f"👥 **Muestra:** {int(r['n_jugadores'])} jugadores | ⏱️ **Mediana:** {int(r['mediana_min'])} min")
          else:
            st.info("Sin jugadores con este filtro.")

    st.write('DE : Desviación Estandar')

    st.divider() # ----- LINEA SEPARADORA ------


    # GRÁFICAS DE DISPERSIÓN E INCERTIDUMBRE

    st.subheader("Distribución y Estabilidad de las Tasas de Recuperación")

    graf1, graf2 = st.columns(2)

    with graf1:
      st.write("**Distribución por Posición (Diagrama de Caja)**")
      # Boxplot mostrando mediana, cuartiles y valores atípicos (outliers)
      fig_box = px.box(
          datos_comp,
          x='posicion',
          y='tasa_recuperaciones_90',
          color='posicion',
          points="all", # Muestra todos los jugadores individuales al lado de la caja
          hover_data=['ID_JUGADOR', 'minutos_totales', 'balones_recuperados'],
          labels={
              'posicion': 'Posición',
              'tasa_recuperaciones_90': 'Recuperaciones por cada 90 min',
              'ID_JUGADOR': 'Jugador',
              'minutos_totales': 'Minutos Totales',
              'balones_recuperados': 'Balones Recuperados'
          }
      )
      fig_box.update_layout(showlegend=False, height=420)
      st.plotly_chart(fig_box, use_container_width=True)
      st.caption("Cada punto representa un jugador único. La caja muestra el 50% central de los datos (IQR) y la línea horizontal la mediana.")

    with graf2:
      st.write("**Tasas Individuales vs. Minutos Acumulados**")
      # Scatter plot para evidenciar cómo se estabiliza la tasa a mayor exposición
      fig_scatter = px.scatter(
          datos_comp,
          x='minutos_totales',
          y='tasa_recuperaciones_90',
          color='posicion',
          hover_data=['ID_JUGADOR', 'balones_recuperados'],
          labels={
              'minutos_totales': 'Minutos Acumulados en el Torneo',
              'tasa_recuperaciones_90': 'Recuperaciones por cada 90 min',
              'posicion': 'Posición',
              'ID_JUGADOR': 'Jugador',
              'balones_recuperados': 'Balones Recuperados'
          }
      )
      # Líneas verticales de referencia para 180 y 360 minutos
      fig_scatter.add_vline(x=180, line_dash="dash", line_color="gray", annotation_text="180 min")
      fig_scatter.add_vline(x=360, line_dash="dot", line_color="gray", annotation_text="360 min")
      fig_scatter.update_layout(height=420, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
      st.plotly_chart(fig_scatter, use_container_width=True)
      st.caption("Con pocos minutos (<180) las tasas tienen mayor dispersión y tienden a estabilizarse conforme aumenta el tiempo mínimo de juego.")

  st.divider() # ----- LINEA SEPARADORA ------

  if not posiciones_sel:
    st.warning("⚠️ Por favor, selecciona al menos una posición en el menú superior para visualizar la comparación.")
  else:

    # SIMULADOR DE PROBABILIDADES (MODELOS DISCRETOS - SECCIÓN 3)

    st.subheader("Simulador de Probabilidades por Posición (Modelos Discretos)")
    st.write(
        "Estima la probabilidad de que un jugador representativo de cada posición alcance "
        "cierto rendimiento en un partido de 90 minutos, utilizando las tasas combinadas de la cohorte filtrada."
    )

    sim_izq, sim_der = st.columns(2)

    # 1. MODELO POISSON: BALONES RECUPERADOS EN 90 MINUTOS

    with sim_izq:
      with st.container(border=True):
        st.markdown("#### 🛡️ Recuperaciones en 90 min (Poisson)")

        # Slider interactivo para que el usuario elija el umbral 'b' (Paso 3.15 del notebook)
        umbral_rec = st.slider(
            "Umbral mínimo de balones recuperados (b):",
            min_value=1,
            max_value=20,
            value=7, # Valor intermedio cercano a los umbrales exploratorios (8 para DC, 7 para VD)
            help="Calcula P(B ≥ b) asumiendo un partido completo de 90 minutos."
        )

        # Calculamos la tasa combinada (lambda_g = 90 * sum(B_i) / sum(M_i)) por posición
        poisson_df = datos_comp.groupby('posicion').agg(
            rec_totales=('balones_recuperados', 'sum'),
            min_totales=('minutos_totales', 'sum')
        ).reset_index()

        poisson_df['lambda_g'] = (90 * poisson_df['rec_totales']) / poisson_df['min_totales']
        # P(B >= umbral) = 1 - P(B <= umbral - 1) = stats.poisson.sf(umbral - 1, lambda_g)
        poisson_df['prob_exito'] = stats.poisson.sf(umbral_rec - 1, poisson_df['lambda_g']) * 100

        # Mostramos los resultados dinámicos por cada posición seleccionada
        cols_p = st.columns(len(posiciones_sel))
        for idx, pos in enumerate(posiciones_sel):
          fila_p = poisson_df[poisson_df['posicion'] == pos]
          with cols_p[idx]:
            if not fila_p.empty:
              rp = fila_p.iloc[0]
              st.metric(
                  label=pos,
                  value=f"{rp['prob_exito']:.1f}%",
                  delta=f"λ = {rp['lambda_g']:.2f} esp.",
                  delta_color="off"
              )

        st.caption(
            f"Probabilidad estimada de lograr **al menos {umbral_rec} recuperaciones** en 90 min. "
            "Nota: En defensas y volantes existe sobredispersión (varianza > media), por lo que este valor es una referencia base."
        )

    # 2. MODELO BINOMIAL: PASES ACERTADOS EN 20 INTENTOS

    with sim_der:
      with st.container(border=True):
        st.markdown("#### 🎯 Efectividad en 20 Pases (Binomial)")

        # Slider interactivo para los pases acertados en n=20 intentos (Paso 3.11 del notebook)
        umbral_pases = st.slider(
            "Mínimo de pases acertados en 20 intentos:",
            min_value=8,
            max_value=20,
            value=15, # Valor exacto usado en la guía y el notebook: P(X_g >= 16)
            help="Calcula P(X ≥ k) para n = 20 intentos usando la proporción combinada de aciertos (q_g)."
        )

        n_intentos = 20
        # Reutilizamos 'resumen' calculado en el Bloque A (donde ya tenemos pases_acert_sum y pases_tot_sum)
        resumen['q_g'] = resumen['pases_acert_sum'] / resumen['pases_tot_sum']
        resumen['esperanza_pases'] = n_intentos * resumen['q_g']
        # P(X >= umbral) = stats.binom.sf(umbral - 1, n=20, p=q_g)
        resumen['prob_pases'] = stats.binom.sf(umbral_pases - 1, n_intentos, resumen['q_g']) * 100

        # Mostramos los resultados dinámicos por cada posición seleccionada
        cols_b = st.columns(len(posiciones_sel))
        for idx, pos in enumerate(posiciones_sel):
          fila_b = resumen[resumen['posicion'] == pos]
          with cols_b[idx]:
            if not fila_b.empty:
              rb = fila_b.iloc[0]
              st.metric(
                  label=pos,
                  value=f"{rb['prob_pases']:.1f}%",
                  delta=f"E[X] = {rb['esperanza_pases']:.1f} pases",
                  delta_color="off"
              )

        st.caption(
            f"Probabilidad estimada de acertar **al menos {umbral_pases} de 20 pases** consecutivos "
            "bajo independencia y probabilidad constante por posición."
        )

# ---------------------------- Sección Inicio ------------------------

elif seccion == "Inicio":
  st.title("⚽ Portal de Análisis Estadístico | Reto Cruz Azul")
  st.write(
      "Bienvenido a la plataforma interactiva de exploración y comparación de rendimiento por posición. "
      "Esta herramienta complementa el informe de investigación estadística, permitiendo visualizar "
      "indicadores ajustados por tiempo de juego (cada 90 minutos) a partir de la base del torneo."
  )

  st.divider() # ----- LINEA SEPARADORA ------

  # RESUMEN DE AUDITORÍA Y POBLACIÓN DE ESTUDIO

  st.subheader("Panorama General de la Base de Datos")
  st.write(
      "Para garantizar comparaciones válidas, cada futbolista representa una única unidad de análisis "
      "(agregando sus minutos y acciones de todas las jornadas jugadas) tras excluir registros ambiguos "
      "y jugadores con múltiples posiciones registradas."
  )

  # Calculamos métricas rápidas
  total_registros = len(df)
  total_jugadores = df['ID_JUGADOR'].nunique()
  total_categorias = df['CATEGORIA'].nunique()
  total_posiciones = df['POSICION'].nunique()

  c1, c2, c3, c4 = st.columns(4)
  with c1:
    with st.container(border=True):
      st.metric("Registros Válidos", f"{total_registros:,}")
  with c2:
    with st.container(border=True):
      st.metric("Jugadores Únicos", f"{total_jugadores:,}")
  with c3:
    with st.container(border=True):
      st.metric("Categorías", total_categorias)
  with c4:
    with st.container(border=True):
      st.metric("Posiciones", total_posiciones)

  st.divider() # ----- LINEA SEPARADORA ------

  # GUÍA DE NAVEGACIÓN DEL PORTAL

  st.subheader("¿Qué puedes explorar en este portal?")

  nav1, nav2 = st.columns(2)

  with nav1:
    with st.container(border=True):
      st.markdown("#### 📊 Stats Individuales")
      st.write(
          "Consulta el desglose jornada por jornada de cualquier jugador filtrado por categoría y posición. "
          "Incluye métricas de pases acertados vs. fallados, duelos 1 vs. 1 defensivos y ofensivos, "
          "diferencia de balones recuperados/perdidos y efectividad de tiro."
      )

  with nav2:
    with st.container(border=True):
      st.markdown("#### ⚖️ Comparar Estadísticas")
      st.write(
          "Evalúa diferencias entre posiciones (ej. Defensa Central, Volante Defensivo y Delantero en U19). "
          "Permite aplicar filtros de exposición mínima (180 vs. 360 minutos), analizar la dispersión "
          "con diagramas de caja y simular probabilidades mediante modelos Poisson y Binomial."
      )

  # Aviso de alcance requerido por la guía del reto
  st.info(
      "ℹ️ **Nota sobre el alcance de los datos:** Este portal utiliza el archivo sintético proporcionado "
      "para fines académicos y de enseñanza. Los resultados sirven como propuesta metodológica de reporte "
      "y no deben utilizarse para evaluar ni tomar decisiones sobre futbolistas reales."
  )
