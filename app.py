import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from CoolProp.CoolProp import PropsSI
import matplotlib.ticker as ticker

st.set_page_config(page_title="Chiller & HP Diagnostic Pro", layout="wide")

st.title("❄️🔥 Analisi Termodinamica Professionale")

# --- SIDEBAR: INPUT CON REGOLE DI STIMA ---
with st.sidebar:
    st.header("⚙️ Configurazione")
    modalita = st.radio("Modalità di Funzionamento", ["Chiller (Raffreddamento)", "Heat Pump (Riscaldamento)"])
    
    lista_gas = ["R134a", "R1234ze", "R513A", "R514A", "R410A", "R32", "R1233zd", "R290"]
    gas = st.selectbox("Refrigerante", lista_gas)
    
    st.divider()
    p_evap = st.number_input("Pres. Evaporazione (kPaA)", value=371.5)
    p_cond = st.number_input("Pres. Condensazione (kPaA)", value=801.4)
    
    st.divider()
    # Logica Saturazioni per stime (Verificata per miscele)
    t_sat_evap_calc = PropsSI('T', 'P', p_evap*1000, 'Q', 1, gas) - 273.15
    t_sat_cond_calc = PropsSI('T', 'P', p_cond*1000, 'Q', 0, gas) - 273.15

    # 1. ASPIRAZIONE
    manca_asp = st.checkbox("Temp. Aspirazione mancante")
    t_asp = (t_sat_evap_calc + 5.0) if manca_asp else st.number_input("Temp. Aspirazione (°C)", value=12.0)

    # 2. SCARICO
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

    # 3. SOTTORAFFREDDAMENTO
    manca_subcool = st.checkbox("Sottoraffreddamento mancante")
    subcool = 5.0 if manca_subcool else st.number_input("Sottoraffreddamento (K)", value=8.7)

    # 4. ACQUA
    if modalita == "Chiller (Raffreddamento)":
        label_h2o, def_h2o = "Temp. Uscita Acqua Evap. (°C)", 9.7
    else:
        label_h2o, def_h2o = "Temp. Uscita Acqua Cond. (°C)", 45.0
    
    manca_h2o = st.checkbox("Dato Acqua mancante")
    if manca_h2o:
        t_acqua_out = (t_sat_evap_calc + 2.0) if modalita == "Chiller (Raffreddamento)" else (t_sat_cond_calc - 2.0)
    else:
        t_acqua_out = st.number_input(label_h2o, value=def_h2o)

    submit = st.button("ESEGUI ANALISI", use_container_width=True)

if submit:
    try:
        # Calcoli Punti Ciclo
        h1 = PropsSI('H', 'P', p_evap*1000, 'T', t_asp+273.15, gas)/1000
        h2 = PropsSI('H', 'P', p_cond*1000, 'T', t_scarico+273.15, gas)/1000
        h4 = PropsSI('H', 'P', p_cond*1000, 'T', (t_sat_cond_calc+273.15) - subcool, gas)/1000
        h5 = h4
        
        # Punti di saturazione per etichette fasi
        h3_sat_vap = PropsSI('H', 'P', p_cond*1000, 'Q', 1, gas)/1000
        h3_sat_liq = PropsSI('H', 'P', p_cond*1000, 'Q', 0, gas)/1000
        h5_sat_vap = PropsSI('H', 'P', p_evap*1000, 'Q', 1, gas)/1000
        
        # Valori per metriche
        x5 = PropsSI('Q', 'P', p_evap*1000, 'H', h5*1000, gas)
        sh_asp = t_asp - t_sat_evap_calc
        sh_sca = t_scarico - t_sat_cond_calc
        approach = abs(t_acqua_out - (t_sat_evap_calc if modalita == "Chiller (Raffreddamento)" else t_sat_cond_calc))

        # --- GRAFICO ---
        fig, ax = plt.subplots(figsize=(14, 10))
        tc = PropsSI('Tcrit', gas)
        T_range = np.linspace(235, tc - 1, 100)
        h_liq = np.array([PropsSI('H', 'T', t, 'Q', 0, gas)/1000 for t in T_range])
        h_vap = np.array([PropsSI('H', 'T', t, 'Q', 1, gas)/1000 for t in T_range])
        p_sat = np.array([PropsSI('P', 'T', t, 'Q', 0, gas)/1000 for t in T_range])
        
        ax.plot(h_liq, p_sat, 'k-', lw=2, alpha=0.6)
        ax.plot(h_vap, p_sat, 'k-', lw=2, alpha=0.6)
        ax.fill_betweenx(p_sat, 0, h_liq, color='blue', alpha=0.03)
        ax.fill_betweenx(p_sat, h_vap, h_vap.max()+200, color='red', alpha=0.03)

        ax.text(0.02, 0.96, f"GAS: {gas}", transform=ax.transAxes, fontsize=12, fontweight='bold', bbox=dict(facecolor='white', alpha=0.8))

        # Ciclo Curvilineo (Isoentropica approssimata)
        p_comp = np.linspace(p_evap, p_cond, 20)
        h_comp = np.linspace(h1, h2, 20)
        ax.plot(h_comp, p_comp, color='#c0392b', lw=4, zorder=5)
        ax.plot([h2, h4], [p_cond, p_cond], color='#e74c3c', lw=4, zorder=5)
        ax.plot([h4, h5], [p_cond, p_evap], color='#2980b9', lw=4, zorder=5)
        ax.plot([h5, h1], [p_evap, p_evap], color='#3498db', lw=4, zorder=5)

        # FASI CICLO
        f_style = dict(fontsize=9, fontweight='bold', color='#444444', ha='center')
        ax.text((h2 + h3_sat_vap)/2, p_cond * 1.18, f"SH SCARICO: {sh_sca:.1f}K", **f_style)
        ax.text((h4 + h3_sat_liq)/2, p_cond * 1.18, f"SUBCOOL: {subcool:.1f}K", **f_style)
        ax.text((h1 + h5_sat_vap)/2, p_evap * 0.72, f"SH ASPIRAZIONE: {sh_asp:.1f}K", **f_style)

        # BOX DATI (Verificati per non generare errori FancyBboxPatch)
        b_style = dict(boxstyle="round,pad=0.3", fc="white", ec="#2c3e50", lw=0.8, alpha=0.9)
        
        ax.text(h1 + 20, p_evap * 0.85, f"1. ASPIRAZIONE\n{t_asp:.1f}°C / {p_evap:.1f} kPa", bbox=b_style, fontsize=8)
        ax.text(h2 + 20, p_cond * 1.30, f"2. SCARICO\n{t_scarico:.1f}°C / {p_cond:.1f} kPa", bbox=b_style, fontsize=8)
        ax.text(h4 - 20, p_cond * 1.30, f"4. LIQUIDO\n{(t_sat_cond_calc-subcool):.1f}°C / {p_cond:.1f} kPa", ha='right', bbox=b_style, fontsize=8)
        ax.text(h5 - 20, p_evap * 0.85, f"5. INGRESSO\n{t_sat_evap_calc:.1f}°C / {p_evap:.1f} kPa", ha='right', bbox=b_style, fontsize=8)

        # APPROACH
        p_h2o = PropsSI('P', 'T', t_acqua_out + 273.15, 'Q', 0.5, gas) / 1000
        ax.axhline(y=p_h2o, color='#27ae60', linestyle='--', lw=1.5, alpha=0.6)
        p_min, p_max = sorted([p_evap, p_h2o]) if modalita == "Chiller (Raffreddamento)" else sorted([p_cond, p_h2o])
        ax.axhspan(p_min, p_max, color='#2ecc71', alpha=0.2)
        
        h_center = (min(h_liq) + max(h_vap))/2
        ax.text(h_center, (p_min * p_max)**0.5, f"APPROACH: {approach:.1f} K", 
                color='#1e8449', fontweight='bold', fontsize=10, ha='center', va='center',
                bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.2'))

        # SETTAGGI ASSI
        ax.set_yscale('log')
        ax.yaxis.set_major_formatter(ticker.ScalarFormatter())
        ax.grid(True, which="both", alpha=0.05)
        
        # Margini ampi per la massima leggibilità
        ax.set_xlim(min(h_liq)-80, max(h_vap)+180)
        ax.set_ylim(p_evap*0.4, p_cond*4.5) 
        
        st.pyplot(fig)

        # --- RISULTATI ESTERNI (METRICHE) ---
        st.divider()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Flash Gas", f"{x5*100:.1f} %")
        c2.metric("Sottoraffreddamento", f"{subcool:.1f} K")
        c3.metric("Surriscaldamento Asp.", f"{sh_asp:.1f} K")
        c4.metric(f"Approach ({modalita.split()[0]})", f"{approach:.1f} K")

    except Exception as e:
        st.error(f"Errore tecnico: {e}")
        
