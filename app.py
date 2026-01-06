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

        # --- BOX DATI ESTERNO ---
        st.info(f"**REPORT:** {ora_attuale} | **GAS:** {gas} | **P.Evap:** {p_evap} kPa | **P.Cond:** {p_cond} kPa")

        # --- FIGURA ---
        fig, ax = plt.subplots(figsize=(12, 7))
        
        # Campana di saturazione
        tc = PropsSI('Tcrit', gas)
        # Range di temperatura ampio per vedere la forma della campana
        T_plot = np.linspace(230, tc - 0.5, 100)
        h_liq = [PropsSI('H', 'T', t, 'Q', 0, gas)/1000 for t in T_plot]
        h_vap = [PropsSI('H', 'T', t, 'Q', 1, gas)/1000 for t in T_plot]
        p_plot = [PropsSI('P', 'T', t, 'Q', 0, gas)/1000 for t in T_plot]
        
        ax.plot(h_liq, p_plot, 'k-', lw=1.5, alpha=0.7)
        ax.plot(h_vap, p_plot, 'k-', lw=1.5, alpha=0.7)
        
        # Sfondi colorati molto tenui
        ax.fill_betweenx(p_plot, 100, h_liq, color='skyblue', alpha=0.04)
        ax.fill_betweenx(p_plot, h_liq, h_vap, color='lightgray', alpha=0.04)
        ax.fill_betweenx(p_plot, h_vap, max(h_vap)+400, color='coral', alpha=0.04)

        # --- DISEGNO CICLO ---
        # Compressione/Condensazione (ROSSO)
        ax.plot([h1, h2, h4], [p_evap, p_cond, p_cond], color='red', lw=4, marker='o', markersize=7)
        # Espansione/Evaporazione (BLU)
        ax.plot([h4, h5, h1], [p_cond, p_evap, p_evap], color='blue', lw=4, marker='o', markersize=7)

        # --- ZOOM BILANCIATO (VIA DI MEZZO) ---
        # Allarghiamo i margini per vedere la curva della campana a sinistra e a destra
        h_ciclo = [h1, h2, h4, h5]
        delta_h = max(h_ciclo) - min(h_ciclo)
        ax.set_xlim(min(h_ciclo) - delta_h*0.5, max(h_ciclo) + delta_h*0.5)
        
        p_ciclo = [p_evap, p_cond]
        ax.set_ylim(min(p_ciclo)*0.6, max(p_ciclo)*1.5)

        # --- ETICHETTE DATI ---
        ax.text(h1, p_evap, f" {t_asp}°C", color='darkblue', fontweight='bold', va='top')
        ax.text(h2, p_cond, f" {t_scarico}°C", color='darkred', fontweight='bold', va='bottom')
        ax.text(h4, p_cond, f"{(t_sat_cond-subcool):.1f}°C ", color='darkred', fontweight='bold', ha='right', va='bottom')
        ax.text(h5, p_evap, f"{t_sat_evap:.1f}°C ", color='darkblue', fontweight='bold', ha='right', va='top')

        ax.set_yscale('log')
        ax.yaxis.set_major_formatter(ticker.ScalarFormatter())
        ax.set_xlabel("Entalpia [kJ/kg]")
        ax.set_ylabel("Pressione [kPaA]")
        ax.grid(True, which="both", alpha=0.15)
        
        st.pyplot(fig)

        # --- ESITO ---
        esito_positivo = (approach <= 3.5) and (subcool >= 4.0 and subcool <= 12.0) and (disch_sh >= 15.0)
        if esito_positivo:
            st.success("### ESITO: POSITIVO")
        else:
            st.error("### ESITO: NEGATIVO")

    except Exception as e:
        st.error(f"Errore: {e}")
        
