import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from CoolProp.CoolProp import PropsSI
import matplotlib.ticker as ticker

st.set_page_config(page_title="Chiller & HP Diagnostic Pro", layout="wide")

st.title("❄️🔥 Analisi Termodinamica Professionale")

# --- SIDEBAR (INALTERATA) ---
with st.sidebar:
    st.header("⚙️ Configurazione")
    modalita = st.radio("Modalità di Funzionamento", ["Chiller (Raffreddamento)", "Heat Pump (Riscaldamento)"])
    lista_gas = ["R134a", "R1234ze", "R513A", "R514A", "R410A", "R32", "R1233zd", "R290"]
    gas = st.selectbox("Refrigerante", lista_gas)
    
    st.divider()
    p_evap = st.number_input("Pres. Evaporazione (kPaA)", value=371.5)
    p_cond = st.number_input("Pres. Condensazione (kPaA)", value=801.4)
    
    st.divider()
    t_sat_evap_calc = PropsSI('T', 'P', p_evap*1000, 'Q', 1, gas) - 273.15
    t_sat_cond_calc = PropsSI('T', 'P', p_cond*1000, 'Q', 0, gas) - 273.15

    manca_asp = st.checkbox("Temp. Aspirazione mancante")
    t_asp = (t_sat_evap_calc + 5.0) if manca_asp else st.number_input("Temp. Aspirazione (°C)", value=12.0)

    manca_scarico = st.checkbox("Temp. Scarico mancante")
    if manca_scarico:
        try:
            s1_temp = PropsSI('S', 'P', p_evap*1000, 'T', t_asp+273.15, gas)
            h1_temp = PropsSI('H', 'P', p_evap*1000, 'T', t_asp+273.15, gas)
            h2s = PropsSI('H', 'P', p_cond*1000, 'S', s1_temp, gas)
            h2_real = h1_temp + (h2s - h1_temp) / 0.7
            t_scarico = PropsSI('T', 'P', p_cond*1000, 'H', h2_real, gas) - 273.15
        except: t_scarico = t_sat_cond_calc + 15.0
    else:
        t_scarico = st.number_input("Temp. Scarico (°C)", value=55.1)

    manca_subcool = st.checkbox("Sottoraffreddamento mancante")
    subcool = 5.0 if manca_subcool else st.number_input("Sottoraffreddamento (K)", value=8.7)

    manca_h2o = st.checkbox("Dato Acqua mancante")
    if manca_h2o:
        t_acqua_out = (t_sat_evap_calc + 2.0) if modalita == "Chiller (Raffreddamento)" else (t_sat_cond_calc - 2.0)
    else:
        t_acqua_out = st.number_input("Temp. Uscita Acqua (°C)", value=9.7)

    submit = st.button("ESEGUI ANALISI", use_container_width=True)

if submit:
    try:
        # Calcoli Punti Ciclo
        h1 = PropsSI('H', 'P', p_evap*1000, 'T', t_asp+273.15, gas)/1000
        h2 = PropsSI('H', 'P', p_cond*1000, 'T', t_scarico+273.15, gas)/1000
        h4 = PropsSI('H', 'P', p_cond*1000, 'T', (t_sat_cond_calc+273.15) - subcool, gas)/1000
        h5 = h4
        x5 = PropsSI('Q', 'P', p_evap*1000, 'H', h5*1000, gas)
        sh_asp = t_asp - t_sat_evap_calc
        approach = abs(t_acqua_out - (t_sat_evap_calc if modalita == "Chiller (Raffreddamento)" else t_sat_cond_calc))

        # --- GRAFICO CON CAMPANA REALE (CORRETTO) ---
        fig, ax = plt.subplots(figsize=(14, 9))
        
        t_crit = PropsSI('Tcrit', gas)
        p_crit = PropsSI('Pcrit', gas) / 1000
        
        # 1. Generazione Campana Arrotondata
        T_range = np.linspace(233.15, t_crit - 0.1, 300) 
        h_liq = np.array([PropsSI('H', 'T', t, 'Q', 0, gas)/1000 for t in T_range])
        h_vap = np.array([PropsSI('H', 'T', t, 'Q', 1, gas)/1000 for t in T_range])
        p_sat = np.array([PropsSI('P', 'T', t, 'Q', 0, gas)/1000 for t in T_range])
        
        ax.plot(h_liq, p_sat, color='#2c3e50', lw=2, zorder=3)
        ax.plot(h_vap, p_sat, color='#2c3e50', lw=2, zorder=3)

        # 2. Aggiunta Isoterme (MODIFICATO: Calcolo stabile H = f(P,T))
        p_iso_range = np.logspace(np.log10(50), np.log10(p_crit*1.5), 50)
        for temp in range(-20, int(t_crit)+40, 20):
            T_kelvin = temp + 273.15
            h_iso = []
            for p in p_iso_range:
                try:
                    h_val = PropsSI('H', 'T', T_kelvin, 'P', p*1000, gas)/1000
                    h_iso.append(h_val)
                except:
                    h_iso.append(np.nan)
            ax.plot(h_iso, p_iso_range, color='gray', lw=0.5, alpha=0.3)

        # 3. Disegno Ciclo
        ax.plot(np.linspace(h1, h2, 20), np.linspace(p_evap, p_cond, 20), color='#c0392b', lw=4, zorder=10)
        ax.plot([h2, h4], [p_cond, p_cond], color='#e74c3c', lw=4, zorder=10)
        ax.plot([h4, h5], [p_cond, p_evap], color='#2980b9', lw=4, zorder=10)
        ax.plot([h5, h1], [p_evap, p_evap], color='#3498db', lw=4, zorder=10)

        # Box Dati
        b_style = dict(boxstyle="round,pad=0.3", fc="white", ec="#2c3e50", lw=0.8, alpha=0.9)
        ax.text(h1 + 10, p_evap * 0.8, f"1. ASP\n{t_asp:.1f}°C", bbox=b_style, fontsize=8)
        ax.text(h2 + 10, p_cond * 1.2, f"2. SCA\n{t_scarico:.1f}°C", bbox=b_style, fontsize=8)
        ax.text(h4 - 10, p_cond * 1.2, f"4. LIQ\n{(t_sat_cond_calc-subcool):.1f}°C", ha='right', bbox=b_style, fontsize=8)
        ax.text(h5 - 10, p_evap * 0.8, f"5. INGR\n{t_sat_evap_calc:.1f}°C", ha='right', bbox=b_style, fontsize=8)

        # Formattazione Assi
        ax.set_yscale('log')
        ax.yaxis.set_major_formatter(ticker.ScalarFormatter())
        ax.grid(True, which="both", alpha=0.1, color='gray')
        
        # Limiti dinamici basati sul gas per Aspect Ratio reale
        h_min_plot = PropsSI('H', 'T', 253.15, 'Q', 0, gas)/1000 - 50
        h_max_plot = PropsSI('H', 'T', t_crit-10, 'Q', 1, gas)/1000 + 150
        ax.set_xlim(h_min_plot, h_max_plot)
        ax.set_ylim(50, p_crit * 1.5) 
        
        st.pyplot(fig)

        # Metriche
        st.divider()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Flash Gas", f"{x5*100:.1f} %")
        c2.metric("Sottoraffreddamento", f"{subcool:.1f} K")
        c3.metric("Surriscaldamento Asp.", f"{sh_asp:.1f} K")
        c4.metric(f"Approach", f"{approach:.1f} K")

    except Exception as e:
        st.error(f"Errore tecnico: {e}")
        
