   import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from CoolProp.CoolProp import PropsSI
import matplotlib.ticker as ticker

st.set_page_config(page_title="Chiller & HP Diagnostic Pro", layout="wide")

st.title("❄️🔥 Analisi Termodinamica Professionale")

# --- SIDEBAR (TOTALMENTE INALTERATA) ---
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
        
        # Variabili metriche
        h3_sat_vap = PropsSI('H', 'P', p_cond*1000, 'Q', 1, gas)/1000
        h3_sat_liq = PropsSI('H', 'P', p_cond*1000, 'Q', 0, gas)/1000
        h5_sat_vap = PropsSI('H', 'P', p_evap*1000, 'Q', 1, gas)/1000
        x5 = PropsSI('Q', 'P', p_evap*1000, 'H', h5*1000, gas)
        sh_asp = t_asp - t_sat_evap_calc
        sh_sca = t_scarico - t_sat_cond_calc
        approach = abs(t_acqua_out - (t_sat_evap_calc if modalita == "Chiller (Raffreddamento)" else t_sat_cond_calc))

        # --- GRAFICO DI PRECISIONE ---
        fig, ax = plt.subplots(figsize=(14, 10))
        t_crit = PropsSI('Tcrit', gas)
        p_crit = PropsSI('Pcrit', gas) / 1000
        
        # Limiti Grafico per calcolo proiezioni
        h_min_lim = PropsSI('H', 'T', 253.15, 'Q', 0, gas)/1000 - 50
        p_min_lim = 40

        # 1. Campana e Zone Colorate
        T_range = np.linspace(233.15, t_crit - 0.1, 300)
        h_liq_c = [PropsSI('H', 'T', t, 'Q', 0, gas)/1000 for t in T_range]
        h_vap_c = [PropsSI('H', 'T', t, 'Q', 1, gas)/1000 for t in T_range]
        p_sat_c = [PropsSI('P', 'T', t, 'Q', 0, gas)/1000 for t in T_range]
        ax.plot(h_liq_c, p_sat_c, 'k-', lw=1.8, zorder=3)
        ax.plot(h_vap_c, p_sat_c, 'k-', lw=1.8, zorder=3)
        ax.fill_betweenx(p_sat_c, 0, h_liq_c, color='blue', alpha=0.03)
        ax.fill_betweenx(p_sat_c, h_vap_c, max(h_vap_c)+500, color='red', alpha=0.03)

        # 2. Fascia APPROCCIO (RIPRISTINATA)
        p_h2o = PropsSI('P', 'T', t_acqua_out + 273.15, 'Q', 0.5, gas) / 1000
        p_min_app, p_max_app = sorted([p_evap, p_h2o]) if modalita == "Chiller (Raffreddamento)" else sorted([p_cond, p_h2o])
        ax.axhspan(p_min_app, p_max_app, color='#2ecc71', alpha=0.15, zorder=1)
        ax.text((h1+h5)/2, (p_min_app*p_max_app)**0.5, f"APPROACH: {approach:.1f} K", 
                ha='center', va='center', fontweight='bold', color='#1e8449', fontsize=9,
                bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', boxstyle='round,pad=0.2'))

        # 3. Ciclo Frigorifero
        ax.plot([h1, h2], [p_evap, p_cond], color='#c0392b', lw=4, zorder=10) # Compressione
        ax.plot([h2, h4], [p_cond, p_cond], color='#e74c3c', lw=4, zorder=10) # Condensazione
        ax.plot([h4, h5], [p_cond, p_evap], color='#2980b9', lw=4, zorder=10) # Espansione
        ax.plot([h5, h1], [p_evap, p_evap], color='#3498db', lw=4, zorder=10) # Evaporazione

        # 4. PROIEZIONI AI PUNTI E QUOTATURE ASSI (TECNICO)
        # Stile linee proiezione: sottili, tratteggiate, grigie
        proj_style = dict(color='gray', linestyle='--', linewidth=0.7, alpha=0.6, zorder=2)
        text_style = dict(color='black', fontsize=8, fontweight='bold', bbox=dict(facecolor='white', alpha=0.6, edgecolor='none'))

        # Proiezioni Pressione (Asse Y)
        for p_val in [p_evap, p_cond]:
            ax.axhline(y=p_val, xmin=0, xmax=0.05, **proj_style)
            ax.text(h_min_lim + 2, p_val, f"{p_val:.1f} kPa", va='center', **text_style)

        # Proiezioni Entalpia (Asse X)
        for h_val in [h5, h4, h1, h2]:
            ax.axvline(x=h_val, ymin=0, ymax=0.05, **proj_style)
            ax.text(h_val, p_min_lim * 1.1, f"{h_val:.0f}", ha='center', **text_style)

        # 5. Etichette SH / SUBCOOL (RIPRISTINATE)
        l_style = dict(fontsize=8, fontweight='bold', color='#444444', ha='center', bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))
        ax.text((h2 + h3_sat_vap)/2, p_cond * 1.08, f"SH SCARICO: {sh_sca:.1f}K", **l_style)
        ax.text((h4 + h3_sat_liq)/2, p_cond * 1.08, f"SUBCOOL: {subcool:.1f}K", **l_style)
        ax.text((h1 + h5_sat_vap)/2, p_evap * 0.88, f"SH ASPIRAZIONE: {sh_asp:.1f}K", **l_style)

        # 6. Box Dati e Nome Gas (RIPRISTINATI)
        ax.text(0.02, 0.96, f"GAS: {gas}", transform=ax.transAxes, fontsize=12, fontweight='bold', bbox=dict(facecolor='white', alpha=0.8))
        b_style = dict(boxstyle="round,pad=0.3", fc="white", ec="#2c3e50", lw=0.8, alpha=0.9)
        ax.text(h1 + 10, p_evap * 0.7, f"1. ASP\n{t_asp:.1f}°C", bbox=b_style, fontsize=8)
        ax.text(h2 + 10, p_cond * 1.35, f"2. SCA\n{t_scarico:.1f}°C", bbox=b_style, fontsize=8)
        ax.text(h4 - 10, p_cond * 1.35, f"4. LIQ\n{(t_sat_cond_calc-subcool):.1f}°C", ha='right', bbox=b_style, fontsize=8)
        ax.text(h5 - 10, p_evap * 0.7, f"5. INGR\n{t_sat_evap_calc:.1f}°C", ha='right', bbox=b_style, fontsize=8)

        # Formattazione Assi LogP-h
        ax.set_yscale('log')
        ax.yaxis.set_major_formatter(ticker.ScalarFormatter())
        ax.grid(True, which="both", alpha=0.1, color='gray')
        ax.set_xlim(h_min_lim, PropsSI('H', 'T', t_crit-10, 'Q', 1, gas)/1000 + 200)
        ax.set_ylim(p_min_lim, p_crit * 1.5)
        ax.set_xlabel("Enthalpy [kJ/kg]", fontweight='bold')
        ax.set_ylabel("Pressure [kPa]", fontweight='bold')
        
        st.pyplot(fig)

        # Metriche Esterne (TOTALMENTE INALTERATE)
        st.divider()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Flash Gas", f"{x5*100:.1f} %")
        c2.metric("Sottoraffreddamento", f"{subcool:.1f} K")
        c3.metric("Surriscaldamento Asp.", f"{sh_asp:.1f} K")
        c4.metric(f"Approach", f"{approach:.1f} K")

    except Exception as e:
        st.error(f"Errore tecnico: {e}")
            
