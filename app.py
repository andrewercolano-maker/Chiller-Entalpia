import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from CoolProp.CoolProp import PropsSI
import matplotlib.ticker as ticker

# Configurazione per smartphone
st.set_page_config(page_title="Chiller Diagnostic Pro", layout="centered")

st.title("❄️ Chiller Diagnostic Pro")

# --- MASCHERA DI INSERIMENTO DATI ---
with st.form("dati_chiller"):
    st.subheader("📝 Inserimento Dati di Campo")
    
    col1, col2 = st.columns(2)
    with col1:
        gas = st.selectbox("Refrigerante", ["R134a", "R1234ze", "R410A"])
        p_evap = st.number_input("Pres. Evaporazione (kPaA)", value=371.5, step=5.0)
        t_scarico = st.number_input("Temp. Scarico (°C)", value=55.1, step=0.5)
    
    with col2:
        st.write("") # Allineamento
        p_cond = st.number_input("Pres. Condensazione (kPaA)", value=801.4, step=5.0)
        subcool = st.number_input("Sottoraffreddamento (K)", value=8.7, step=0.1)
    
    t_acqua_out = st.number_input("Temp. Uscita Acqua Evaporatore (°C)", value=9.7, step=0.1)

    # TASTO DI CONFERMA
    submit_button = st.form_submit_button(label='AGGIORNA DIAGNOSI E GRAFICO')

# --- LOGICA CHE PARTE SOLO QUANDO PREMI IL TASTO ---
if submit_button:
    try:
        # 1. Calcoli Termodinamici
        t_sat_evap = PropsSI('T', 'P', p_evap*1000, 'Q', 1, gas) - 273.15
        t_sat_cond = PropsSI('T', 'P', p_cond*1000, 'Q', 0, gas) - 273.15
        approach = t_acqua_out - t_sat_evap
        
        # Diagnosi
        stato_ok = approach <= 3.5 and 4 <= subcool <= 12
        colore_ciclo = 'green' if stato_ok else 'red'

        # 2. Creazione del Grafico
        fig, ax = plt.subplots(figsize=(10, 7))
        
        # Disegno Campana di Saturazione
        P_vals = np.logspace(np.log10(PropsSI('Pmin', gas)), np.log10(PropsSI('P_critical', gas)), 100)
        h_liq = [PropsSI('H', 'P', p, 'Q', 0, gas)/1000 for p in P_vals]
        h_vap = [PropsSI('H', 'P', p, 'Q', 1, gas)/1000 for p in P_vals]
        ax.plot(h_liq, P_vals/1000, 'k-', alpha=0.3)
        ax.plot(h_vap, P_vals/1000, 'k-', alpha=0.3)

        # Calcolo Punti Ciclo
        h1 = PropsSI('H', 'P', p_evap*1000, 'Q', 1, gas)/1000
        h2 = PropsSI('H', 'P', p_cond*1000, 'T', t_scarico+273.15, gas)/1000
        h4 = PropsSI('H', 'P', p_cond*1000, 'T', (t_sat_cond+273.15) - subcool, gas)/1000
        h5 = h4 # Espansione isoentalpica

        # Disegno Segmenti Ciclo
        h_punti = [h1, h2, h4, h5, h1]
        p_punti = [p_evap, p_cond, p_cond, p_evap, p_evap]
        ax.plot(h_punti, p_punti, color=colore_ciclo, marker='o', lw=3, ms=8)

        # Formattazione Grafico
        ax.set_yscale('log')
        ax.yaxis.set_major_formatter(ticker.ScalarFormatter())
        ax.grid(True, which="both", alpha=0.2)
        ax.set_xlabel("Entalpia [kJ/kg]")
        ax.set_ylabel("Pressione [kPaA]")
        ax.set_title(f"Diagramma p-h {gas} - Stato Ciclo")

        # 3. Mostra Risultati nell'App
        if stato_ok:
            st.success(f"✅ SISTEMA OK - Approach: {approach:.1f}K | Sottoraffreddamento: {subcool}K")
        else:
            st.error(f"⚠️ ANOMALIA - Approach: {approach:.1f}K | Sottoraffreddamento: {subcool}K")
        
        # MOSTRA IL GRAFICO
        st.pyplot(fig)

    except Exception as e:
        st.error(f"Errore nei dati: {e}. Controlla che la pressione di alta sia maggiore di quella di bassa.")
else:
    st.info("Inserisci i dati e premi il tasto per generare l'analisi.")
    
