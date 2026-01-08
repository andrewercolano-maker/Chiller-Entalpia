import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from CoolProp.CoolProp import PropsSI
import matplotlib.ticker as ticker

st.set_page_config(page_title="Chiller & HP Diagnostic Pro", layout="wide")

st.title("❄️🔥 Analisi Termodinamica con Fasi del Ciclo")

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

    submit = st.button("GENERA DIAGRAMMA AVANZATO", use_container_width=True)

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

        fig, ax = plt.subplots(figsize=(14, 8))
        
        # 1. CAMPANA E SFONDO
        tc = PropsSI('Tcrit', gas)
        T_range = np.linspace(235, tc - 1, 100)
        h_liq = np.array([PropsSI('H', 'T', t, 'Q', 0, gas)/1000 for t in T_range])
        h_vap = np.array([PropsSI('H', 'T', t, 'Q', 1, gas)/1000 for t in T_range])
        p_sat = np.array([PropsSI('P', 'T', t, 'Q', 0, gas)/1000 for t in T_range])
        
        ax.plot(h_liq, p_sat, 'k-', lw=2, zorder=3)
        ax.plot(h_vap, p_sat, 'k-', lw=2, zorder=3)
        ax.fill_betweenx(p_sat, 0, h_liq, color='blue', alpha=0.04)
        ax.fill_betweenx(p_sat, h_vap, 1000, color='red', alpha=0.04)

        ax.text(0.02, 0.96, f"GAS: {gas}", transform=ax.transAxes, fontsize=14, fontweight='bold', bbox=dict(facecolor='white', alpha=0.7))

        # 2. DISEGNO CICLO (Linee e Fasi)
        # Compressione Curvilinea
        p_comp = np.linspace(p_evap, p_cond, 20)
        h_comp = np.linspace(h1, h2, 20)
        ax.plot(h_comp, p_comp, color='#c0392b', lw=4, zorder=5)
        
        # Condensazione
        ax.plot([h2, h4], [p_cond, p_cond], color='#e74c3c', lw=4, zorder=5)
        # Espansione
        ax.plot([h4, h5], [p_cond, p_evap], color='#2980b9', lw=4, zorder=5)
        # Evaporazione
        ax.plot([h5, h1], [p_evap, p_evap], color='#3498db', lw=4, zorder=5)

        # 3. ETICHETTE DELLE FASI (Testi sul grafico)
        style_fasi = dict(fontsize=8, fontweight='bold', color='black', alpha=0.7, ha='center')
        
        # Surriscaldamento Scarico (Discharge Superheat)
        ax.text((h2 + h3_sat_vap)/2, p_cond*1.05, f"SURR. SCARICO\n{(t_scarico - t_sat_cond):.1f} K", **style_fasi)
        
        # Sottoraffreddamento (Subcooling)
        ax.text((h4 + h3_sat_liq)/2, p_cond*1.05, f"SOTTORAFFR.\n{subcool:.1f} K", **style_fasi)
        
        # Surriscaldamento Aspirazione (Suction Superheat)
        ax.text((h1 + h5_sat_vap)/2, p_evap*0.85, f"SURR. ASPIRAZIONE\n{(t_asp - t_sat_evap):.1f} K", **style_fasi)

        # 4. BOX DATI PUNTUALI (Distanziati dai vertici)
        bbox = dict(boxstyle="round,pad=0.4", fc="#ffffff", ec="#34495e", lw=1, alpha=0.9)
        
        # Punto 1: Aspirazione (Spostato in basso a destra)
        ax.annotate(f"1. ASP\n{t_asp:.1f}°C\n{p_evap:.1f} kPa", xy=(h1, p_evap), xytext=(20, -40), 
                    textcoords='offset points', bbox=bbox, arrowprops=dict(arrowstyle='->', color='gray'))
        
        # Punto 2: Scarico (Spostato in alto a destra)
        ax.annotate(f"2. SCA\n{t_scarico:.1f}°C\n{p_cond:.1f} kPa", xy=(h2, p_cond), xytext=(20, 30), 
                    textcoords='offset points', bbox=bbox, arrowprops=dict(arrowstyle='->', color='gray'))
        
        # Punto 4: Liquido (Spostato in alto a sinistra)
        ax.annotate(f"4. LIQ\n{(t_sat_cond-subcool):.1f}°C\n{p_cond:.1f} kPa", xy=(h4, p_cond), xytext=(-80, 30), 
                    textcoords='offset points', bbox=bbox, arrowprops=dict(arrowstyle='->', color='gray'))
        
        # Punto 5: Ingresso Evaporatore (Spostato in basso a sinistra)
        ax.annotate(f"5. INGR\n{t_sat_evap:.1f}°C\n{p_evap:.1f} kPa", xy=(h5, p_evap), xytext=(-80, -40), 
                    textcoords='offset points', bbox=bbox, arrowprops=dict(arrowstyle='->', color='gray'))

        # 5. FASCIA APPROACH
        p_h2o = PropsSI('P', 'T', t_acqua_out + 273.15, 'Q', 0.5, gas) / 1000
        ax.axhline(y=p_h2o, color='#27ae60', linestyle='--', lw=2, alpha=0.6)
        p_min = min(p_evap, p_h2o) if modalita == "Chiller (Raffreddamento)" else min(p_cond, p_h2o)
        p_max = max(p_evap, p_h2o) if modalita == "Chiller (Raffreddamento)" else max(p_cond, p_h2o)
        ax.axhspan(p_min, p_max, color='#2ecc71', alpha=0.15)

        # 6. SETTAGGI FINALI
        ax.set_yscale('log')
        ax.yaxis.set_major_formatter(ticker.ScalarFormatter())
        ax.set_xlabel("Entalpia [kJ/kg]", fontweight='bold')
        ax.set_ylabel("Pressione [kPaA]", fontweight='bold')
        ax.grid(True, which="both", alpha=0.1)
        
        ax.set_xlim(min(h_liq)-60, max(h_vap)+120)
        ax.set_ylim(p_evap*0.5, p_cond*2.2)
        
        st.pyplot(fig)

    except Exception as e:
        st.error(f"Errore: {e}")
        
