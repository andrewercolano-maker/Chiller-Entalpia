import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from CoolProp.CoolProp import PropsSI
import matplotlib.ticker as ticker
from datetime import datetime

st.set_page_config(page_title="Chiller Diagnostic Report", layout="wide")

st.title("❄️ Diagnostica Ciclo Frigo")

# --- SIDEBAR INPUT ---
with st.sidebar:
    st.header("⚙️ Dati di Campo")
    lista_gas = ["R134a", "R1234ze", "R513A", "R514A", "R410A", "R32", "R1233zd"]
    gas = st.selectbox("Refrigerante", lista_gas)
    
    p_evap = st.number_input("Pres. Evaporazione (kPaA)", value=371.5)
    p_cond = st.number_input("Pres. Condensazione (kPaA)", value=801.4)
    t_asp = st.number_input("Temp. Aspirazione Compressore (°C)", value=12.0)
    t_scarico = st.number_input("Temp. Scarico (°C)", value=55.1)
    subcool = st.number_input("Sottoraffreddamento (K)", value=8.7)
    t_acqua_out = st.number_input("Temp. Uscita Acqua Evap. (°C)", value=9.7)
    
    submit = st.button("ANALIZZA")

if submit:
    try:
        ora_attuale = datetime.now().strftime("%d/%m/%Y %H:%M")

        # --- CALCOLI ---
        t_sat_evap = PropsSI('T', 'P', p_evap*1000, 'Q', 1, gas) - 273.15
        t_sat_cond = PropsSI('T', 'P', p_cond*1000, 'Q', 0, gas) - 273.15
        approach = t_acqua_out - t_sat_evap
        disch_sh = t_scarico - t_sat_cond

        h1 = PropsSI('H', 'P', p_evap*1000, 'T', t_asp+273.15, gas)/1000
        h2 = PropsSI('H', 'P', p_cond*1000, 'T', t_scarico+273.15, gas)/1000
        h4 = PropsSI('H', 'P', p_cond*1000, 'T', (t_sat_cond+273.15) - subcool, gas)/1000
        h5 = h4

        # --- FIGURA ---
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Campana di saturazione
        tc = PropsSI('Tcrit', gas)
        # Generiamo la campana su un range più ampio per lo sfondo
        T_range = np.linspace(230, tc - 0.5, 100)
        h_liq = [PropsSI('H', 'T', t, 'Q', 0, gas)/1000 for t in T_range]
        h_vap = [PropsSI('H', 'T', t, 'Q', 1, gas)/1000 for t in T_range]
        p_range = [PropsSI('P', 'T', t, 'Q', 0, gas)/1000 for t in T_range]
        
        ax.plot(h_liq, p_range, 'k-', lw=1.5, alpha=0.6)
        ax.plot(h_vap, p_range, 'k-', lw=1.5, alpha=0.6)
        
        # Sfondi zone
        ax.fill_betweenx(p_range, 0, h_liq, color='skyblue', alpha=0.05)
        ax.fill_betweenx(p_range, h_liq, h_vap, color='lightgray', alpha=0.05)
        ax.fill_betweenx(p_range, h_vap, max(h_vap)+500, color='coral', alpha=0.05)

        # --- DISEGNO CICLO ---
        # Compressione/Condensazione (ROSSO)
        ax.plot([h1, h2], [p_evap, p_cond], color='red', lw=4, marker='o', markersize=8)
        ax.plot([h2, h4], [p_cond, p_cond], color='red', lw=4, marker='o', markersize=8, label='Alta Pressione (Scarico/Cond)')
        
        # Espansione/Evaporazione (BLU)
        ax.plot([h4, h5], [p_cond, p_evap], color='blue', lw=4, marker='o', markersize=8)
        ax.plot([h5, h1], [p_evap, p_evap], color='blue', lw=4, marker='o', markersize=8, label='Bassa Pressione (Evap/Asp)')

        # --- ZOOM DINAMICO ---
        # Calcoliamo i limiti basandoci sui punti del ciclo con un margine del 15%
        h_min, h_max = min([h1, h2, h4, h5]), max([h1, h2, h4, h5])
        p_min, p_max = min([p_evap, p_cond]), max([p_evap, p_cond])
        
        ax.set_xlim(h_min - (h_max-h_min)*0.2, h_max + (h_max-h_min)*0.2)
        ax.set_ylim(p_min * 0.7, p_max * 1.4) # Scala logaritmica: margine proporzionale

        # --- ETICHETTE DATI ---
        ax.text(h1, p_evap, f"  {t_asp}°C\n  {p_evap}kPa", color='darkblue', fontweight='bold', va='top')
        ax.text(h2, p_cond, f"  {t_scarico}°C\n  {p_cond}kPa", color='darkred', fontweight='bold', va='bottom')
        ax.text(h4, p_cond, f"{(t_sat_cond-subcool):.1f}°C  \n{p_cond}kPa  ", color='darkred', fontweight='bold', ha='right', va='bottom')
        ax.text(h5, p_evap, f"{t_sat_evap:.1f}°C  \n{p_evap}kPa  ", color='darkblue', fontweight='bold', ha='right', va='top')

        # --- INFO BOX ---
        testo_legenda = (
            f"DATA: {ora_attuale}\n"
            f"GAS: {gas}\n"
            f"P. Evap: {p_evap} kPa\n"
            f"P. Cond: {p_cond} kPa\n"
            f"T. Asp: {t_asp} °C\n"
            f"T. Scarico: {t_scarico} °C\n"
            f"Sottoraffr: {subcool} K\n"
            f"T. H2O Out: {t_acqua_out} °C"
        )
        ax.text(0.02, 0.96, testo_legenda, transform=ax.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.9, edgecolor='gray'),
                fontsize=9, family='monospace')

        ax.set_yscale('log')
        ax.yaxis.set_major_formatter(ticker.ScalarFormatter())
        ax.set_xlabel("Entalpia [kJ/kg]")
        ax.set_ylabel("Pressione [kPaA]")
        ax.grid(True, which="both", alpha=0.2)
        ax.legend(loc='lower right', fontsize='small')
        
        st.pyplot(fig)

        # --- ESITO ---
        esito_positivo = (approach <= 3.5) and (subcool >= 4.0 and subcool <= 12.0) and (disch_sh >= 15.0)
        if esito_positivo:
            st.success("### ESITO: POSITIVO")
        else:
            st.error("### ESITO: NEGATIVO")

    except Exception as e:
        st.error(f"Errore: {e}")
        
