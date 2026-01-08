import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from CoolProp.CoolProp import PropsSI
import matplotlib.ticker as ticker

st.set_page_config(page_title="Chiller & HP Diagnostic Pro", layout="wide")

st.title("❄️🔥 Analisi Termodinamica Avanzata (P-h)")

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
    manca_asp = st.checkbox("Asp. mancante")
    t_asp = (t_sat_evap_base + 5.0) if manca_asp else st.number_input("Temp. Aspirazione (°C)", value=12.0)

    manca_scarico = st.checkbox("Sca. mancante")
    if manca_scarico:
        # Calcolo scarico teorico isentropico (eff 0.7)
        s1 = PropsSI('S', 'P', p_evap*1000, 'T', t_asp+273.15, gas)
        h1_t = PropsSI('H', 'P', p_evap*1000, 'T', t_asp+273.15, gas)
        h2s = PropsSI('H', 'P', p_cond*1000, 'S', s1, gas)
        h2_real = h1_t + (h2s - h1_t) / 0.7
        t_scarico = PropsSI('T', 'P', p_cond*1000, 'H', h2_real, gas) - 273.15
    else:
        t_scarico = st.number_input("Temp. Scarico (°C)", value=55.1)

    subcool = st.number_input("Sottoraffreddamento (K)", value=8.7)
    
    t_sat_cond_base = PropsSI('T', 'P', p_cond*1000, 'Q', 0, gas) - 273.15
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
        
        # 1. CAMPANA E SFONDO
        tc = PropsSI('Tcrit', gas)
        T_range = np.linspace(235, tc - 1, 60)
        h_liq = [PropsSI('H', 'T', t, 'Q', 0, gas)/1000 for t in T_range]
        h_vap = [PropsSI('H', 'T', t, 'Q', 1, gas)/1000 for t in T_range]
        p_sat = [PropsSI('P', 'T', t, 'Q', 0, gas)/1000 for t in T_range]
        ax.plot(h_liq, p_sat, 'k-', lw=2, alpha=0.7)
        ax.plot(h_vap, p_sat, 'k-', lw=2, alpha=0.7)

        # ISOTERME (Verdi)
        for T_iso in range(-20, 121, 20):
            try:
                P_vals = np.logspace(np.log10(100), np.log10(4000), 30)
                H_vals = [PropsSI('H', 'P', p*1000, 'T', T_iso+273.15, gas)/1000 for p in P_vals]
                ax.plot(H_vals, P_vals, 'g-', lw=0.6, alpha=0.15)
            except: pass

        # ISOENTROPICHE (Grigie tratteggiate) - Fondamentali per il compressore
        s_base = PropsSI('S', 'P', p_evap*1000, 'T', t_asp+273.15, gas)
        for s_offset in np.linspace(-0.2, 0.4, 6):
            try:
                s_val = s_base + s_offset * 1000
                P_vals = np.logspace(np.log10(p_evap), np.log10(p_cond*1.5), 20)
                H_vals = [PropsSI('H', 'P', p*1000, 'S', s_val, gas)/1000 for p in P_vals]
                ax.plot(H_vals, P_vals, 'k:', lw=0.8, alpha=0.2)
            except: pass

        # 2. FASCIA APPROACH
        p_h2o = PropsSI('P', 'T', t_acqua_out + 273.15, 'Q', 0.5, gas) / 1000
        ax.axhline(y=p_h2o, color='#27ae60', linestyle='--', lw=2, alpha=0.8)
        p_min = min(p_evap, p_h2o) if modalita == "Chiller (Raffreddamento)" else min(p_cond, p_h2o)
        p_max = max(p_evap, p_h2o) if modalita == "Chiller (Raffreddamento)" else max(p_cond, p_h2o)
        ax.axhspan(p_min, p_max, color='#2ecc71', alpha=0.2)
        ax.text(ax.get_xlim()[0]+170, p_h2o, f" ACQUA OUT: {t_acqua_out}°C", color='#27ae60', fontweight='bold', fontsize=10)

        # 3. CICLO FRIGO
        ax.plot([h1, h2], [p_evap, p_cond], color='#c0392b', lw=5, label='Compressione')
        ax.plot([h2, h4], [p_cond, p_cond], color='#e74c3c', lw=5, label='Condensazione')
        ax.plot([h4, h5], [p_cond, p_evap], color='#2980b9', lw=5, label='Espansione')
        ax.plot([h5, h1], [p_evap, p_evap], color='#3498db', lw=5, label='Evaporazione')

        # Box Dati Professionale
        bbox = dict(boxstyle="round,pad=0.4", fc="#f8f9fa", ec="#d1d3d4", lw=1, alpha=0.95)
        ax.text(h1, p_evap, f"1.ASP\n{t_asp:.1f}°C\n{p_evap:.0f} kPa", va='top', bbox=bbox, fontsize=9, fontweight='bold')
        ax.text(h2, p_cond, f"2.SCA\n{t_scarico:.1f}°C\n{p_cond:.0f} kPa", va='bottom', bbox=bbox, fontsize=9, fontweight='bold')
        ax.text(h4, p_cond, f"4.LIQ\n{(t_sat_cond-subcool):.1f}°C\n{p_cond:.0f} kPa", ha='right', va='bottom', bbox=bbox, fontsize=9)
        ax.text(h5, p_evap, f"5.INGR\n{t_sat_evap:.1f}°C\n{p_evap:.0f} kPa", ha='right', va='top', bbox=bbox, fontsize=9)

        # 4. SETTAGGI FINALI
        ax.set_yscale('log')
        ax.yaxis.set_major_formatter(ticker.ScalarFormatter())
        ax.grid(True, which="both", alpha=0.15, linestyle='--')
        ax.set_xlabel("Entalpia [kJ/kg]", fontsize=12, fontweight='bold')
        ax.set_ylabel("Pressione [kPaA]", fontsize=12, fontweight='bold')
        
        # Limiti dinamici per centraggio
        h_vals = [h1, h2, h4, h5]
        ax.set_xlim(min(h_vals)-70, max(h_vals)+70)
        ax.set_ylim(p_evap*0.6, p_cond*1.6)
        
        st.pyplot(fig)

        # Analisi Efficienza
        st.subheader("📝 Analisi Tecnica")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Surriscaldamento:** {(t_asp - t_sat_evap):.1f} K")
            st.write(f"**Sottoraffreddamento:** {subcool:.1f} K")
        with col2:
            st.write(f"**Approach Scambiatore:** {abs(t_acqua_out - (t_sat_evap if modalita=='Chiller' else t_sat_cond)):.1f} K")
            st.write(f"**Qualità Punto 5 (Flash Gas):** {PropsSI('Q', 'P', p_evap*1000, 'H', h5*1000, gas)*100:.1f} %")

    except Exception as e:
        st.error(f"Errore nella generazione: {e}")
        
