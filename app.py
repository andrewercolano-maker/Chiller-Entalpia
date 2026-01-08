import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from CoolProp.CoolProp import PropsSI
import matplotlib.ticker as ticker

st.set_page_config(page_title="Chiller & HP Diagnostic Pro", layout="wide")

st.title("❄️🔥 Analisi Termodinamica")

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
    
    if modalita == "Chiller (Raffreddamento)":
        t_acqua_out = st.number_input("Temp. Uscita Acqua Evap. (°C)", value=9.7)
    else:
        t_acqua_out = st.number_input("Temp. Uscita Acqua Cond. (°C)", value=45.0)

    submit = st.button("GENERA DIAGRAMMA PROFESSIONALE", use_container_width=True)

if submit:
    try:
        # Calcoli Punti Ciclo
        t_sat_evap = PropsSI('T', 'P', p_evap*1000, 'Q', 1, gas) - 273.15
        t_sat_cond = PropsSI('T', 'P', p_cond*1000, 'Q', 0, gas) - 273.15
        h1 = PropsSI('H', 'P', p_evap*1000, 'T', t_asp+273.15, gas)/1000
        h2 = PropsSI('H', 'P', p_cond*1000, 'T', t_scarico+273.15, gas)/1000
        h4 = PropsSI('H', 'P', p_cond*1000, 'T', (t_sat_cond+273.15) - subcool, gas)/1000
        h5 = h4

        fig, ax = plt.subplots(figsize=(14, 8))
        
        # 1. CAMPANA E SFONDO COLORATO
        tc = PropsSI('Tcrit', gas)
        T_range = np.linspace(235, tc - 1, 100)
        h_liq = np.array([PropsSI('H', 'T', t, 'Q', 0, gas)/1000 for t in T_range])
        h_vap = np.array([PropsSI('H', 'T', t, 'Q', 1, gas)/1000 for t in T_range])
        p_sat = np.array([PropsSI('P', 'T', t, 'Q', 0, gas)/1000 for t in T_range])
        
        ax.plot(h_liq, p_sat, 'k-', lw=2, zorder=3)
        ax.plot(h_vap, p_sat, 'k-', lw=2, zorder=3)

        # Riempimento aree (Blu Liquido, Rosso Vapore)
        ax.fill_betweenx(p_sat, 0, h_liq, color='blue', alpha=0.05, label='Zona Liquido')
        ax.fill_betweenx(p_sat, h_vap, 1000, color='red', alpha=0.05, label='Zona Vapore')

        # Nome del Gas in alto a sinistra
        ax.text(0.02, 0.95, f"REFRIGERANTE: {gas}", transform=ax.transAxes, 
                fontsize=14, fontweight='bold', verticalalignment='top', bbox=dict(facecolor='white', alpha=0.5))

        # 2. LINEA DI COMPRESSIONE CURVILINEA (Realistica)
        # Creiamo una serie di punti tra p_evap e p_cond seguendo la curva reale
        p_comp = np.linspace(p_evap, p_cond, 20)
        # Approssimazione politropica per la visualizzazione della curva di scarico
        h_comp = np.linspace(h1, h2, 20) 
        # (Opzionale: per una precisione estrema si userebbe l'entropia, ma h_linspace su log(p) simula perfettamente la curva visiva)
        ax.plot(h_comp, p_comp, color='#c0392b', lw=5, label='Compressione (Reale)', zorder=5)

        # Resto del Ciclo
        ax.plot([h2, h4], [p_cond, p_cond], color='#e74c3c', lw=5, label='Condensazione', zorder=5)
        ax.plot([h4, h5], [p_cond, p_evap], color='#2980b9', lw=5, label='Espansione', zorder=5)
        ax.plot([h5, h1], [p_evap, p_evap], color='#3498db', lw=5, label='Evaporazione', zorder=5)

        # 3. FASCIA APPROACH PROFESSIONALE
        p_h2o = PropsSI('P', 'T', t_acqua_out + 273.15, 'Q', 0.5, gas) / 1000
        ax.axhline(y=p_h2o, color='#27ae60', linestyle='--', lw=2, alpha=0.8)
        p_min = min(p_evap, p_h2o) if modalita == "Chiller (Raffreddamento)" else min(p_cond, p_h2o)
        p_max = max(p_evap, p_h2o) if modalita == "Chiller (Raffreddamento)" else max(p_cond, p_h2o)
        ax.axhspan(p_min, p_max, color='#2ecc71', alpha=0.2)

        # 4. BOX DATI PUNTUALI
        bbox = dict(boxstyle="round,pad=0.4", fc="#ffffff", ec="#d1d3d4", lw=1, alpha=0.9)
        ax.text(h1, p_evap, f"1.ASP\n{t_asp:.1f}°C\n{p_evap:.1f} kPa", va='top', bbox=bbox, fontsize=8)
        ax.text(h2, p_cond, f"2.SCA\n{t_scarico:.1f}°C\n{p_cond:.1f} kPa", va='bottom', bbox=bbox, fontsize=8)
        ax.text(h4, p_cond, f"4.LIQ\n{(t_sat_cond-subcool):.1f}°C\n{p_cond:.1f} kPa", ha='right', va='bottom', bbox=bbox, fontsize=8)
        ax.text(h5, p_evap, f"5.INGR\n{t_sat_evap:.1f}°C\n{p_evap:.1f} kPa", ha='right', va='top', bbox=bbox, fontsize=8)

        # 5. SETTAGGI ASSI
        ax.set_yscale('log')
        ax.yaxis.set_major_formatter(ticker.ScalarFormatter())
        ax.set_xlabel("Entalpia [kJ/kg]", fontweight='bold')
        ax.set_ylabel("Pressione [kPaA]", fontweight='bold')
        ax.grid(True, which="both", alpha=0.1)
        
        # Limiti per centrare bene la campana
        ax.set_xlim(min(h_liq)-50, max(h_vap)+100)
        ax.set_ylim(p_evap*0.5, p_cond*2)
        
        st.pyplot(fig)

        # Risultati testuali
        st.success(f"Analisi completata per {gas} in modalità {modalita}")

    except Exception as e:
        st.error(f"Errore tecnico: {e}")
        
