import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from CoolProp.CoolProp import PropsSI
import matplotlib.ticker as ticker

st.set_page_config(page_title="Chiller & HP Diagnostic Pro", layout="wide")

st.title("❄️🔥 Analisi Termodinamica Professionale")

# --- SIDEBAR: INPUT ---
with st.sidebar:
    st.header("⚙️ Configurazione")
    modalita = st.radio("Modalità", ["Chiller (Raffreddamento)", "Heat Pump (Riscaldamento)"])
    lista_gas = ["R134a", "R1234ze", "R410A", "R32", "R290", "R513A"]
    gas = st.selectbox("Refrigerante", lista_gas)
    
    p_evap = st.number_input("Pres. Evaporazione (kPaA)", value=371.5)
    p_cond = st.number_input("Pres. Condensazione (kPaA)", value=801.4)
    
    st.divider()
    t_sat_evap_base = PropsSI('T', 'P', p_evap*1000, 'Q', 1, gas) - 273.15
    t_asp = st.number_input("Temp. Aspirazione (°C)", value=t_sat_evap_base + 5)
    t_scarico = st.number_input("Temp. Scarico (°C)", value=55.1)
    subcool = st.number_input("Sottoraffreddamento (K)", value=8.7)
    
    t_sat_cond_base = PropsSI('T', 'P', p_cond*1000, 'Q', 0, gas) - 273.15
    if modalita == "Chiller (Raffreddamento)":
        t_acqua_out = st.number_input("Temp. Uscita Acqua Evap. (°C)", value=9.7)
    else:
        t_acqua_out = st.number_input("Temp. Uscita Acqua Cond. (°C)", value=45.0)

    submit = st.button("ESEGUI ANALISI", use_container_width=True)

if submit:
    try:
        # Calcoli Punti Ciclo
        t_sat_evap = PropsSI('T', 'P', p_evap*1000, 'Q', 1, gas) - 273.15
        t_sat_cond = PropsSI('T', 'P', p_cond*1000, 'Q', 0, gas) - 273.15
        h1 = PropsSI('H', 'P', p_evap*1000, 'T', t_asp+273.15, gas)/1000
        h2 = PropsSI('H', 'P', p_cond*1000, 'T', t_scarico+273.15, gas)/1000
        h4 = PropsSI('H', 'P', p_cond*1000, 'T', (t_sat_cond+273.15) - subcool, gas)/1000
        h3_sat_vap = PropsSI('H', 'P', p_cond*1000, 'Q', 1, gas)/1000
        h3_sat_liq = PropsSI('H', 'P', p_cond*1000, 'Q', 0, gas)/1000
        h5_sat_vap = PropsSI('H', 'P', p_evap*1000, 'Q', 1, gas)/1000
        h5 = h4
        
        x5 = PropsSI('Q', 'P', p_evap*1000, 'H', h5*1000, gas)
        sh_asp = t_asp - t_sat_evap
        sh_sca = t_scarico - t_sat_cond
        approach = abs(t_acqua_out - (t_sat_evap if modalita == "Chiller (Raffreddamento)" else t_sat_cond))

        # --- GRAFICO ---
        fig, ax = plt.subplots(figsize=(14, 9)) # Leggermente più alto per le scritte
        tc = PropsSI('Tcrit', gas)
        T_range = np.linspace(235, tc - 1, 100)
        h_liq = np.array([PropsSI('H', 'T', t, 'Q', 0, gas)/1000 for t in T_range])
        h_vap = np.array([PropsSI('H', 'T', t, 'Q', 1, gas)/1000 for t in T_range])
        p_sat = np.array([PropsSI('P', 'T', t, 'Q', 0, gas)/1000 for t in T_range])
        
        ax.plot(h_liq, p_sat, 'k-', lw=2, alpha=0.6)
        ax.plot(h_vap, p_sat, 'k-', lw=2, alpha=0.6)
        ax.fill_betweenx(p_sat, 0, h_liq, color='blue', alpha=0.03)
        ax.fill_betweenx(p_sat, h_vap, h_vap.max()+200, color='red', alpha=0.03)

        # Intestazione Gas
        ax.text(0.02, 0.96, f"GAS: {gas}", transform=ax.transAxes, fontsize=12, fontweight='bold', 
                bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))

        # Ciclo
        p_comp = np.linspace(p_evap, p_cond, 20)
        h_comp = np.linspace(h1, h2, 20)
        ax.plot(h_comp, p_comp, color='#c0392b', lw=4, zorder=5)
        ax.plot([h2, h4], [p_cond, p_cond], color='#e74c3c', lw=4, zorder=5)
        ax.plot([h4, h5], [p_cond, p_evap], color='#2980b9', lw=4, zorder=5)
        ax.plot([h5, h1], [p_evap, p_evap], color='#3498db', lw=4, zorder=5)

        # ETICHETTE FASI (Posizionate per non interferire)
        f_style = dict(fontsize=9, fontweight='bold', color='#444444', ha='center', va='center')
        
        # Surriscaldamento Scarico (Sopra il tratto vapore surriscaldato)
        ax.text((h2 + h3_sat_vap)/2, p_cond * 1.15, f"SH SCARICO: {sh_sca:.1f}K", **f_style)
        
        # Sottoraffreddamento (Sopra il tratto liquido)
        ax.text((h4 + h3_sat_liq)/2, p_cond * 1.15, f"SUBCOOL: {subcool:.1f}K", **f_style)
        
        # Surriscaldamento Aspirazione (Sotto la linea di evaporazione)
        ax.text((h1 + h5_sat_vap)/2, p_evap * 0.75, f"SH ASPIRAZIONE: {sh_asp:.1f}K", **f_style)

        # BOX DATI PUNTUALI (Spostati all'esterno del ciclo)
        b_style = dict(boxstyle="round,pad=0.3", fc="white", ec="#2c3e50", lw=0.8, alpha=0.9, fontsize=8)
        
        ax.text(h1 + 15, p_evap * 0.85, f"1. ASPIRAZIONE\n{t_asp:.1f}°C / {p_evap:.1f} kPa", **b_style)
        ax.text(h2 + 15, p_cond * 1.25, f"2. SCARICO\n{t_scarico:.1f}°C / {p_cond:.1f} kPa", **b_style)
        ax.text(h4 - 15, p_cond * 1.25, f"4. LIQUIDO\n{(t_sat_cond-subcool):.1f}°C / {p_cond:.1f} kPa", ha='right', **b_style)
        ax.text(h5 - 15, p_evap * 0.85, f"5. INGRESSO\n{t_sat_evap:.1f}°C / {p_evap:.1f} kPa", ha='right', **b_style)

        # FASCIA APPROACH
        p_h2o = PropsSI('P', 'T', t_acqua_out + 273.15, 'Q', 0.5, gas) / 1000
        ax.axhline(y=p_h2o, color='#27ae60', linestyle='--', lw=1.5, alpha=0.6)
        p_min, p_max = sorted([p_evap, p_h2o]) if modalita == "Chiller (Raffreddamento)" else sorted([p_cond, p_h2o])
        ax.axhspan(p_min, p_max, color='#2ecc71', alpha=0.2)
        
        # Testo Approach (Centrato orizzontalmente nel grafico)
        ax.text((min(h_liq) + max(h_vap))/2, (p_min * p_max)**0.5, f"APPROACH: {approach:.1f} K", 
                color='#1e8449', fontweight='bold', fontsize=10, ha='center', va='center',
                bbox=dict(facecolor='white', alpha=0.6, edgecolor='none', boxstyle='round,pad=0.2'))

        # SETTAGGI FINALI
        ax.set_yscale('log')
        ax.yaxis.set_major_formatter(ticker.ScalarFormatter())
        ax.set_xlabel("Entalpia [kJ/kg]", fontweight='bold')
        ax.set_ylabel("Pressione [kPaA]", fontweight='bold')
        ax.grid(True, which="both", alpha=0.05)
        
        # Margini ampi per evitare sovrapposizioni con i bordi
        ax.set_xlim(min(h_liq)-80, max(h_vap)+150)
        ax.set_ylim(p_evap*0.5, p_cond*3.0) 
        
        st.pyplot(fig)

        # RISULTATI ESTERNI
        st.divider()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Flash Gas", f"{x5*100:.1f} %")
        c2.metric("Sottoraffreddamento", f"{subcool:.1f} K")
        c3.metric("Surriscaldamento Asp.", f"{sh_asp:.1f} K")
        c4.metric(f"Approach ({modalita.split()[0]})", f"{approach:.1f} K")

    except Exception as e:
        st.error(f"Errore: {e}")
        
