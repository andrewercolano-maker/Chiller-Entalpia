import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from CoolProp.CoolProp import PropsSI
import matplotlib.ticker as ticker
from datetime import datetime

st.set_page_config(page_title="Chiller Diagnostic Pro", layout="wide")

st.title("❄️ Diagnostica Ciclo Frigo Professionale")

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

        # --- CALCOLI TERMODINAMICI ---
        t_sat_evap = PropsSI('T', 'P', p_evap*1000, 'Q', 1, gas) - 273.15
        t_sat_cond = PropsSI('T', 'P', p_cond*1000, 'Q', 0, gas) - 273.15
        approach = t_acqua_out - t_sat_evap
        disch_sh = t_scarico - t_sat_cond

        h1 = PropsSI('H', 'P', p_evap*1000, 'T', t_asp+273.15, gas)/1000
        h2 = PropsSI('H', 'P', p_cond*1000, 'T', t_scarico+273.15, gas)/1000
        h4 = PropsSI('H', 'P', p_cond*1000, 'T', (t_sat_cond+273.15) - subcool, gas)/1000
        h5 = h4
        x5 = PropsSI('Q', 'P', p_evap*1000, 'H', h5*1000, gas)

        # --- REPORT ESTERNO ---
        st.info(f"**REPORT:** {ora_attuale} | **GAS:** {gas} | **APPROACH:** {approach:.1f} K | **FLASH GAS:** {x5*100:.1f}%")

        # --- GRAFICO ---
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Campana di saturazione
        tc = PropsSI('Tcrit', gas)
        pc = PropsSI('Pcrit', gas)
        T_plot = np.linspace(230, tc - 0.5, 100)
        h_liq = [PropsSI('H', 'T', t, 'Q', 0, gas)/1000 for t in T_plot]
        h_vap = [PropsSI('H', 'T', t, 'Q', 1, gas)/1000 for t in T_plot]
        p_plot = [PropsSI('P', 'T', t, 'Q', 0, gas)/1000 for t in T_plot]
        
        ax.plot(h_liq, p_plot, 'k-', lw=1.5, alpha=0.7)
        ax.plot(h_vap, p_plot, 'k-', lw=1.5, alpha=0.7)

        # Linee di Titolo (X) e Isoterme (T)
        for x in [0.2, 0.4, 0.6, 0.8]:
            h_x = [PropsSI('H', 'T', t, 'Q', x, gas)/1000 for t in T_plot]
            ax.plot(h_x, p_plot, 'k--', alpha=0.05, lw=0.5)

        # --- DISEGNO CICLO ---
        ax.plot([h1, h2, h4], [p_evap, p_cond, p_cond], color='red', lw=4, marker='o', markersize=8)
        ax.plot([h4, h5, h1], [p_cond, p_evap, p_evap], color='blue', lw=4, marker='o', markersize=8)

        # --- VISUALIZZAZIONE APPROACH ---
        h_mid = (h1 + h5) / 2
        ax.annotate('', xy=(h_mid, p_evap), xytext=(h_mid, p_evap*0.8),
                    arrowprops=dict(arrowstyle='<->', color='orange', lw=2))
        ax.text(h_mid, p_evap*0.75, f"App: {approach:.1f}K", color='orange', fontweight='bold', ha='center', fontsize=10)

        # --- ZOOM ---
        h_ciclo = [h1, h2, h4, h5]
        delta_h = max(h_ciclo) - min(h_ciclo)
        ax.set_xlim(min(h_ciclo) - delta_h*0.5, max(h_ciclo) + delta_h*0.5)
        ax.set_ylim(p_evap*0.6, p_cond*1.6)

        # --- ETICHETTE PUNTI ---
        ax.text(h1, p_evap, f" 1. Asp: {t_asp}°C\n {p_evap}kPa", color='darkblue', fontweight='bold', va='top', ha='left', fontsize=9)
        ax.text(h2, p_cond, f" 2. Sca: {t_scarico}°C\n {p_cond}kPa", color='darkred', fontweight='bold', va='bottom', ha='left', fontsize=9)
        t_liq_out = t_sat_cond - subcool
        ax.text(h4, p_cond, f"4. Liq Out: {t_liq_out:.1f}°C\n{p_cond}kPa ", color='darkred', fontweight='bold', ha='right', va='bottom', fontsize=9)
        ax.text(h5, p_evap, f"5. Ingresso: {t_sat_evap:.1f}°C\n{p_evap}kPa ", color='darkblue', fontweight='bold', ha='right', va='top', fontsize=9)

        ax.set_yscale('log')
        ax.yaxis.set_major_formatter(ticker.ScalarFormatter())
        ax.set_xlabel("Entalpia [kJ/kg]")
        ax.set_ylabel("Pressione [kPaA]")
        ax.grid(True, which="both", alpha=0.1)
        
        st.pyplot(fig)

        # --- ESITO ---
        esito_positivo = (approach <= 3.5) and (4.0 <= subcool <= 12.0) and (disch_sh >= 15.0)
        if esito_positivo:
            st.success("### ESITO: POSITIVO")
        else:
            st.error("### ESITO: NEGATIVO")

    except Exception as e:
        st.error(f"Errore: {e}")
            
