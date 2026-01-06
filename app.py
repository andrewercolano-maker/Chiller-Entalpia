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
        gas = "R134a"
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
        
        # Correzione automatica per evitare crash grafici
        t_scarico_calc = max(t_scarico, t_sat_cond + 1.0)

        # Creazione punti ciclo
        h1 = PropsSI('H', 'P', p_evap*1000, 'Q', 1, gas)/1000
        h2 = PropsSI('H', 'P', p_cond*1000, 'T', t_scarico_calc+273.15, gas)/1000
        h4 = PropsSI('H', 'P', p_cond*1000, 'T', (t_sat_cond+273.15) - subcool, gas)/1000
        h5 = h4

        # Disegno Grafico
        fig, ax = plt.subplots(figsize=(8, 6))
        
        # DISEGNO CAMPANA (METODO STABILE SENZA PMIN)
        tc = PropsSI('Tcrit', gas)
        pc = PropsSI('Pcrit', gas)
        T_vals = np.linspace(230, tc - 0.1, 50) # Range di temperatura fisso
        h_liq = [PropsSI('H', 'T', t, 'Q', 0, gas)/1000 for t in T_vals]
        h_vap = [PropsSI('H', 'T', t, 'Q', 1, gas)/1000 for t in T_vals]
        p_vals = [PropsSI('P', 'T', t, 'Q', 0, gas)/1000 for t in T_vals]
        
        ax.plot(h_liq, p_vals, 'k--', alpha=0.3)
        ax.plot(h_vap, p_vals, 'k--', alpha=0.3)

        # DISEGNO CICLO
        stato_ok = approach <= 3.5 and 4 <= subcool <= 12
        colore = 'green' if stato_ok else 'red'
        ax.plot([h1, h2, h4, h5, h1], [p_evap, p_cond, p_cond, p_evap, p_evap], 
                color=colore, marker='o', lw=2, label="Ciclo Frigo")

        ax.set_yscale('log')
        ax.yaxis.set_major_formatter(ticker.ScalarFormatter())
        ax.set_xlabel("Entalpia [kJ/kg]")
        ax.set_ylabel("Pressione [kPaA]")
        ax.grid(True, which="both", alpha=0.2)
        
        # Risultati testuali
        if stato_ok:
            st.success(f"✅ CICLO OK - Approach: {approach:.1f}K")
        else:
            st.error(f"⚠️ ANOMALIA - Approach: {approach:.1f}K")
            
        st.pyplot(fig) # Questo mostrerà il grafico

    except Exception as e:
        st.warning(f"Errore tecnico: {e}")
        
