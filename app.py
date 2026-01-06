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
        # Orario analisi
        ora_attuale = datetime.now().strftime("%d/%m/%Y %H:%M")

        # --- CALCOLI ---
        t_sat_evap = PropsSI('T', 'P', p_evap*1000, 'Q', 1, gas) - 273.15
        t_sat_cond = PropsSI('T', 'P', p_cond*1000, 'Q', 0, gas) - 273.15
        approach = t_acqua_out - t_sat_evap
        disch_sh = t_scarico - t_sat_cond

        # Punti Ciclo (Entalpia kJ/kg)
        h1 = PropsSI('H', 'P', p_evap*1000, 'T', t_asp+273.15, gas)/1000
        h2 = PropsSI('H', 'P', p_cond*1000, 'T', t_scarico+273.15, gas)/1000
        h4 = PropsSI('H', 'P', p_cond*1000, 'T', (t_sat_cond+273.15) - subcool, gas)/1000
        h5 = h4

        # --- GRAFICO ---
        fig, ax = plt.subplots(figsize=(12, 9))
        
        # Campana e Zone
        tc = PropsSI('Tcrit', gas)
        T_range = np.linspace(235, tc - 0.5, 100)
        h_liq = [PropsSI('H', 'T', t, 'Q', 0, gas)/1000 for t in T_range]
        h_vap = [PropsSI('H', 'T', t, 'Q', 1, gas)/1000 for t in T_range]
        p_range = [PropsSI('P', 'T', t, 'Q', 0, gas)/1000 for t in T_range]
        
        ax.fill_betweenx(p_range, 0, h_liq, color='skyblue', alpha=0.1)
        ax.fill_betweenx(p_range, h_liq, h_vap, color='lightgray', alpha=0.1)
        ax.fill_betweenx(p_range, h_vap, max(h_vap)+400, color='coral', alpha=0.1)

        # Linee di riferimento (Titolo e Isoterme)
        for x in np.arange(0.2, 1.0, 0.2):
            h_x = [PropsSI('H', 'T', t, 'Q', x, gas)/1000 for t in T_range]
            ax.plot(h_x, p_range, 'k:', alpha=0.1, lw=0.7)

        # --- DISEGNO CICLO CON COLORI RICHIESTI ---
        # 1. Compressione (1->2) ROSSA
        ax.plot([h1, h2], [p_evap, p_cond], color='red', lw=4, marker='o', markersize=8, label='Compressione/Condensazione')
        # 2. Condensazione (2->4) ROSSA
        ax.plot([h2, h4], [p_cond, p_cond], color='red', lw=4, marker='o', markersize=8)
        # 3. Espansione (4->5) BLU
        ax.plot([h4, h5], [p_cond, p_evap], color='blue', lw=4, marker='o', markersize=8, label='Espansione/Evaporazione')
        # 4. Evaporazione (5->1) BLU
        ax.plot([h5, h1], [p_evap, p_evap], color='blue', lw=4, marker='o', markersize=8)

        # --- ETICHETTE DATI SUI PUNTI ---
        ax.text(h1, p_evap, f"  {t_asp}°C\n  {p_evap}kPa", color='darkblue', fontweight='bold', va='bottom')
        ax.text(h2, p_cond, f"  {t_scarico}°C\n  {p_cond}kPa", color='darkred', fontweight='bold', va='bottom')
        ax.text(h4, p_cond, f"{(t_sat_cond-subcool):.1f}°C  \n{p_cond}kPa  ", color='darkred', fontweight='bold', ha='right', va='top')
        ax.text(h5, p_evap, f"{t_sat_evap:.1f}°C  \n{p_evap}kPa  ", color='darkblue', fontweight='bold', ha='right', va='top')

        # --- LEGENDA DATI INSERITI ---
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
        # Posiziona la legenda in un box nell'angolo
        ax.text(0.02, 0.98, testo_legenda, transform=ax.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8, edgecolor='gray'),
                fontsize=10, family='monospace')

        ax.set_yscale('log')
        ax.yaxis.set_major_formatter(ticker.ScalarFormatter())
        ax.set_xlabel("Entalpia [kJ/kg]")
        ax.set_ylabel("Pressione [kPaA]")
        ax.grid(True, which="both", alpha=0.1)
        ax.legend(loc='lower right')
        
        st.pyplot(fig)

        # --- ESITO SECCO ---
        esito_positivo = (approach <= 3.5) and (subcool >= 4.0 and subcool <= 12.0) and (disch_sh >= 15.0)
        
        if esito_positivo:
            st.success("### ESITO: POSITIVO")
        else:
            st.error("### ESITO: NEGATIVO")

    except Exception as e:
        st.error(f"Errore: {e}")
        
