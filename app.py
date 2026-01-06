import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from CoolProp.CoolProp import PropsSI
import matplotlib.ticker as ticker

st.set_page_config(page_title="Chiller Diagnostic Pro", layout="centered")

st.title("❄️ Chiller Diagnostic Pro")

# --- INPUT DATI ---
with st.form("dati_chiller"):
    col1, col2 = st.columns(2)
    with col1:
        gas = "R134a" # Fissato per stabilità
        p_evap = st.number_input("Pres. Evaporazione (kPaA)", value=371.5, step=5.0)
        t_scarico = st.number_input("Temp. Scarico (°C)", value=55.1, step=0.5)
    with col2:
        p_cond = st.number_input("Pres. Condensazione (kPaA)", value=801.4, step=5.0)
        subcool = st.number_input("Sottoraffreddamento (K)", value=8.7, step=0.1)
    
    t_acqua_out = st.number_input("Temp. Uscita Acqua Evap. (°C)", value=9.7)
    submit = st.form_submit_button("AGGIORNA GRAFICO")

if submit:
    try:
        # Calcoli base
        t_sat_evap = PropsSI('T', 'P', p_evap*1000, 'Q', 1, gas) - 273.15
        t_sat_cond = PropsSI('T', 'P', p_cond*1000, 'Q', 0, gas) - 273.15
        approach = t_acqua_out - t_sat_evap
        
        # Check sicurezza per il grafico (Surriscaldamento minimo)
        t_scarico_calc = max(t_scarico, t_sat_cond + 1.0)

        # Punti Entalpia
        h1 = PropsSI('H', 'P', p_evap*1000, 'Q', 1, gas)/1000
        h2 = PropsSI('H', 'P', p_cond*1000, 'T', t_scarico_calc+273.15, gas)/1000
        h4 = PropsSI('H', 'P', p_cond*1000, 'T', (t_sat_cond+273.15) - subcool, gas)/1000
        h5 = h4

        # Creazione Grafico
        fig, ax = plt.subplots(figsize=(8, 6))
        
        # Campana
        P_campana = np.logspace(np.log10(PropsSI('Pmin', gas)), np.log10(PropsSI('P_critical', gas)), 50)
        h_liq = [PropsSI('H', 'P', p, 'Q', 0, gas)/1000 for p in P_campana]
        h_vap = [PropsSI('H', 'P', p, 'Q', 1, gas)/1000 for p in P_campana]
        ax.plot(h_liq, P_campana/1000, 'k--', alpha=0.3)
        ax.plot(h_vap, P_campana/1000, 'k--', alpha=0.3)

        # Ciclo
        colore = 'green' if (approach <= 3.5 and 4 <= subcool <= 12) else 'red'
        ax.plot([h1, h2, h4, h5, h1], [p_evap, p_cond, p_cond, p_evap, p_evap], color=colore, marker='o', lw=2)

        ax.set_yscale('log')
        ax.yaxis.set_major_formatter(ticker.ScalarFormatter())
        ax.set_xlabel("Entalpia [kJ/kg]")
        ax.set_ylabel("Pressione [kPaA]")
        
        # Output
        if colore == 'green':
            st.success(f"✅ CICLO OK - Approach: {approach:.1f}K")
        else:
            st.error(f"⚠️ ANOMALIA - Approach: {approach:.1f}K")
            
        st.pyplot(fig) # MOSTRA IL GRAFICO

    except Exception as e:
        st.warning(f"Dati non validi per il calcolo: {e}")
        
