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
    
    st.divider()
    
    # 1. ASPIRAZIONE
    t_sat_evap_calc = PropsSI('T', 'P', p_evap*1000, 'Q', 1, gas) - 273.15
    manca_asp = st.checkbox("Temp. Aspirazione mancante")
    if manca_asp:
        t_asp = t_sat_evap_calc + 5.0 # Stima 5K di surriscaldamento
        st.caption(f"Stimata (SH 5K): {t_asp:.1f}°C")
    else:
        t_asp = st.number_input("Temp. Aspirazione (°C)", value=12.0)

    # 2. SCARICO
    manca_scarico = st.checkbox("Temp. Scarico mancante")
    if manca_scarico:
        # Calcolo scarico teorico (Isentropico con efficienza 0.7)
        s1_temp = PropsSI('S', 'P', p_evap*1000, 'T', t_asp+273.15, gas)
        h1_temp = PropsSI('H', 'P', p_evap*1000, 'T', t_asp+273.15, gas)
        h2s = PropsSI('H', 'P', p_cond*1000, 'S', s1_temp, gas)
        h2_real = h1_temp + (h2s - h1_temp) / 0.7
        t_scarico = PropsSI('T', 'P', p_cond*1000, 'H', h2_real, gas) - 273.15
        st.caption(f"Stimata (Eff. 70%): {t_scarico:.1f}°C")
    else:
        t_scarico = st.number_input("Temp. Scarico (°C)", value=55.1)

    # 3. SOTTORAFFREDDAMENTO
    manca_subcool = st.checkbox("Sottoraffreddamento mancante")
    subcool = 5.0 if manca_subcool else st.number_input("Sottoraffreddamento (K)", value=8.7)
    if manca_subcool: st.caption("Usato standard: 5.0 K")

    # 4. ACQUA
    manca_acqua = st.checkbox("Temp. Acqua Out mancante")
    t_acqua_out = (t_sat_evap_calc + 2.0) if manca_acqua else st.number_input("Temp. Uscita Acqua (°C)", value=9.7)
    if manca_acqua: st.caption("Stimata (App: 2.0 K)")
    
    submit = st.button("ANALIZZA")

if submit:
    try:
        # --- CALCOLI ---
        t_sat_evap = PropsSI('T', 'P', p_evap*1000, 'Q', 1, gas) - 273.15
        t_sat_cond = PropsSI('T', 'P', p_cond*1000, 'Q', 0, gas) - 273.15
        approach = t_acqua_out - t_sat_evap
        disch_sh = t_scarico - t_sat_cond

        h1 = PropsSI('H', 'P', p_evap*1000, 'T', t_asp+273.15, gas)/1000
        h2 = PropsSI('H', 'P', p_cond*1000, 'T', t_scarico+273.15, gas)/1000
        h4 = PropsSI('H', 'P', p_cond*1000, 'T', (t_sat_cond+273.15) - subcool, gas)/1000
        h5 = h4
        x5 = PropsSI('Q', 'P', p_evap*1000, 'H', h5*1000, gas)

        # --- REPORT ---
        st.info(f"**REPORT ANALISI** | **GAS:** {gas} | **FLASH GAS:** {x5*100:.1f}% | **APPROACH:** {approach:.1f}K")

        # --- GRAFICO ---
        fig, ax = plt.subplots(figsize=(12, 8))
        tc = PropsSI('Tcrit', gas)
        T_plot = np.linspace(230, tc - 0.5, 100)
        h_liq = [PropsSI('H', 'T', t, 'Q', 0, gas)/1000 for t in T_plot]
        h_vap = [PropsSI('H', 'T', t, 'Q', 1, gas)/1000 for t in T_plot]
        p_plot = [PropsSI('P', 'T', t, 'Q', 0, gas)/1000 for t in T_plot]
        ax.plot(h_liq, p_plot, 'k-', lw=1.5, alpha=0.6)
        ax.plot(h_vap, p_plot, 'k-', lw=1.5, alpha=0.6)

        # Ciclo
        ax.plot([h1, h2, h4], [p_evap, p_cond, p_cond], color='red', lw=4, marker='o')
        ax.plot([h4, h5, h1], [p_cond, p_evap, p_evap], color='blue', lw=4, marker='o')

        # Approach e Zoom
        h_mid = (h1 + h5) / 2
        ax.annotate('', xy=(h_mid, p_evap), xytext=(h_mid, p_evap*0.8), arrowprops=dict(arrowstyle='<->', color='orange'))
        
        h_ciclo = [h1, h2, h4, h5]
        ax.set_xlim(min(h_ciclo) - 100, max(h_ciclo) + 100)
        ax.set_ylim(p_evap*0.5, p_cond*2)

        # Etichette
        ax.text(h1, p_evap, f" 1. Asp: {t_asp:.1f}°C", color='darkblue', fontweight='bold', va='top')
        ax.text(h2, p_cond, f" 2. Sca: {t_scarico:.1f}°C", color='darkred', fontweight='bold', va='bottom')
        ax.text(h4, p_cond, f"4. Liq: {(t_sat_cond-subcool):.1f}°C ", color='darkred', ha='right')
        ax.text(h5, p_evap, f"5. Ingr: {t_sat_evap:.1f}°C ", color='darkblue', ha='right', va='top')

        ax.set_yscale('log')
        ax.yaxis.set_major_formatter(ticker.ScalarFormatter())
        ax.grid(True, which="both", alpha=0.1)
        st.pyplot(fig)

        if manca_asp or manca_scarico or manca_subcool or manca_acqua:
            st.warning("⚠️ L'analisi contiene dati stimati. I risultati sono puramente indicativi.")
        else:
            st.success("✅ Analisi completata con dati reali.")

    except Exception as e:
        st.error(f"Errore nel calcolo: {e}")
        
