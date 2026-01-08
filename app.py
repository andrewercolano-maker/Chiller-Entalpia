import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from CoolProp.CoolProp import PropsSI
import matplotlib.ticker as ticker
from datetime import datetime

# Configurazione Pagina
st.set_page_config(page_title="Chiller & HP Diagnostic Pro", layout="wide")

st.title("❄️🔥 Diagnostica Professionale Ciclo Frigo")
st.markdown("---")

# --- SIDEBAR: INPUT DATI ---
with st.sidebar:
    st.header("⚙️ Configurazione Sistema")
    
    # 1. Selezione Modalità
    modalita = st.radio("Modalità di Funzionamento", ["Chiller (Raffreddamento)", "Heat Pump (Riscaldamento)"])
    
    # 2. Selezione Gas
    lista_gas = ["R134a", "R1234ze", "R513A", "R514A", "R410A", "R32", "R1233zd", "R290"]
    gas = st.selectbox("Refrigerante", lista_gas)
    
    st.divider()
    st.subheader("📊 Misure di Pressione")
    p_evap = st.number_input("Pres. Evaporazione (kPaA)", value=371.5)
    p_cond = st.number_input("Pres. Condensazione (kPaA)", value=801.4)
    
    st.divider()
    st.subheader("🌡️ Temperature Refrigerante")
    
    # Calcolo saturazioni per stime
    t_sat_evap_base = PropsSI('T', 'P', p_evap*1000, 'Q', 1, gas) - 273.15
    t_sat_cond_base = PropsSI('T', 'P', p_cond*1000, 'Q', 0, gas) - 273.15

    # Gestione Aspirazione
    manca_asp = st.checkbox("Asp. mancante (stima SH 5K)")
    if manca_asp:
        t_asp = t_sat_evap_base + 5.0
    else:
        t_asp = st.number_input("Temp. Aspirazione (°C)", value=12.0)

    # Gestione Scarico
    manca_scarico = st.checkbox("Sca. mancante (stima Eff. 70%)")
    if manca_scarico:
        try:
            s1_temp = PropsSI('S', 'P', p_evap*1000, 'T', t_asp+273.15, gas)
            h1_temp = PropsSI('H', 'P', p_evap*1000, 'T', t_asp+273.15, gas)
            h2s = PropsSI('H', 'P', p_cond*1000, 'S', s1_temp, gas)
            h2_real = h1_temp + (h2s - h1_temp) / 0.7
            t_scarico = PropsSI('T', 'P', p_cond*1000, 'H', h2_real, gas) - 273.15
        except: t_scarico = t_sat_cond_base + 15.0
    else:
        t_scarico = st.number_input("Temp. Scarico (°C)", value=55.1)

    # Sottoraffreddamento
    manca_sub = st.checkbox("Subcool mancante (stima 5K)")
    subcool = 5.0 if manca_sub else st.number_input("Sottoraffreddamento (K)", value=8.7)

    st.divider()
    st.subheader("💧 Circuito Idraulico")
    
    # Acqua in base alla modalità
    if modalita == "Chiller (Raffreddamento)":
        label_h2o = "Temp. Uscita Acqua Evap. (°C)"
        def_h2o = 9.7
        manca_h2o_label = "Dato Acqua mancante (stima App 2K)"
    else:
        label_h2o = "Temp. Uscita Acqua Cond. (°C)"
        def_h2o = 45.0
        manca_h2o_label = "Dato Acqua mancante (stima App 2K)"

    manca_h2o = st.checkbox(manca_h2o_label)
    if manca_h2o:
        t_acqua_out = (t_sat_evap_base + 2.0) if modalita == "Chiller (Raffreddamento)" else (t_sat_cond_base - 2.0)
    else:
        t_acqua_out = st.number_input(label_h2o, value=def_h2o)

    submit = st.button("ESEGUI ANALISI", use_container_width=True)

# --- LOGICA DI CALCOLO E GRAFICO ---
if submit:
    try:
        # Punti Saturazione
        t_sat_evap = PropsSI('T', 'P', p_evap*1000, 'Q', 1, gas) - 273.15
        t_sat_cond = PropsSI('T', 'P', p_cond*1000, 'Q', 0, gas) - 273.15
        
        # Calcolo Approach
        if modalita == "Chiller (Raffreddamento)":
            approach = t_acqua_out - t_sat_evap
            nome_app = "Approach Evaporatore"
        else:
            approach = t_sat_cond - t_acqua_out
            nome_app = "Approach Condensatore"

        # Entalpie Punti Ciclo (kJ/kg)
        h1 = PropsSI('H', 'P', p_evap*1000, 'T', t_asp+273.15, gas)/1000
        h2 = PropsSI('H', 'P', p_cond*1000, 'T', t_scarico+273.15, gas)/1000
        h4 = PropsSI('H', 'P', p_cond*1000, 'T', (t_sat_cond+273.15) - subcool, gas)/1000
        h5 = h4 # Espansione isoentalpica
        
        # Qualità del vapore (Flash Gas)
        x5 = PropsSI('Q', 'P', p_evap*1000, 'H', h5*1000, gas)

        # Visualizzazione Risultati
        c1, c2, c3 = st.columns(3)
        c1.metric("Flash Gas", f"{x5*100:.1f} %")
        c2.metric(nome_app, f"{approach:.1f} K")
        c3.metric("Sottoraffreddamento", f"{subcool:.1f} K")

        if manca_asp or manca_scarico or manca_sub or manca_h2o:
            st.warning("⚠️ Nota: L'analisi utilizza uno o più valori stimati (dati mancanti).")

        # --- GENERAZIONE GRAFICO PROFESSIONALE ---
        fig, ax = plt.subplots(figsize=(12, 7))
        
        # Campana di saturazione
        tc = PropsSI('Tcrit', gas)
        T_range = np.linspace(230, tc - 0.5, 100)
        h_liq = [PropsSI('H', 'T', t, 'Q', 0, gas)/1000 for t in T_range]
        h_vap = [PropsSI('H', 'T', t, 'Q', 1, gas)/1000 for t in T_range]
        p_sat = [PropsSI('P', 'T', t, 'Q', 0, gas)/1000 for t in T_range]
        ax.plot(h_liq, p_sat, 'k-', lw=1.2, alpha=0.4)
        ax.plot(h_vap, p_sat, 'k-', lw=1.2, alpha=0.4)

        # Linee di Titolo (X) sottili
        for x_val in [0.2, 0.4, 0.6, 0.8]:
            h_x = [PropsSI('H', 'T', t, 'Q', x_val, gas)/1000 for t in T_range]
            ax.plot(h_x, p_sat, 'k--', lw=0.5, alpha=0.1)

        # FASCIA PROFESSIONALE APPROACH (Area Verde)
        try:
            # Calcoliamo la pressione equivalente alla temp acqua per posizionarla sull'asse Y
            p_h2o_virtual = PropsSI('P', 'T', t_acqua_out + 273.15, 'Q', 0.5, gas) / 1000
            ax.axhline(y=p_h2o_virtual, color='#27ae60', linestyle='--', lw=1.5, alpha=0.6)
            
            p_start = min(p_evap, p_h2o_virtual) if modalita == "Chiller (Raffreddamento)" else min(p_cond, p_h2o_virtual)
            p_end = max(p_evap, p_h2o_virtual) if modalita == "Chiller (Raffreddamento)" else max(p_cond, p_h2o_virtual)
            ax.axhspan(p_start, p_end, color='#2ecc71', alpha=0.15, label=f'Area Approach ({approach:.1f}K)')
            ax.text(ax.get_xlim()[0], p_h2o_virtual, f"  Acqua Out: {t_acqua_out}°C", color='#27ae60', fontweight='bold', va='bottom', fontsize=8)
        except: pass

        # Ciclo Frigo
        ax.plot([h1, h2, h4], [p_evap, p_cond, p_cond], color='#c0392b', lw=3, marker='o', markersize=5, label='Lato Alta')
        ax.plot([h4, h5, h1], [p_cond, p_evap, p_evap], color='#2980b9', lw=3, marker='o', markersize=5, label='Lato Bassa')

        # Etichette Punti con Box
        bbox_props = dict(boxstyle="round,pad=0.3", fc="white", ec="gray", lw=0.5, alpha=0.8)
        ax.text(h1, p_evap, f" 1.ASP\n {t_asp:.1f}°C", va='top', bbox=bbox_props, fontsize=8)
        ax.text(h2, p_cond, f" 2.SCA\n {t_scarico:.1f}°C", va='bottom', bbox=bbox_props, fontsize=8)
        ax.text(h4, p_cond, f" 4.LIQ\n {(t_sat_cond-subcool):.1f}°C", ha='right', va='bottom', bbox=bbox_props, fontsize=8)

        # Zoom e Formattazione
        ax.set_yscale('log')
        ax.yaxis.set_major_formatter(ticker.ScalarFormatter())
        ax.set_xlabel("Entalpia [kJ/kg]")
        ax.set_ylabel("Pressione [kPaA]")
        ax.grid(True, which="both", alpha=0.1, linestyle=':')
        ax.legend(loc='upper right', fontsize='x-small')
        
        h_all = [h1, h2, h4, h5]
        ax.set_xlim(min(h_all)-80, max(h_all)+80)
        ax.set_ylim(p_evap*0.6, p_cond*1.8)

        st.pyplot(fig)

        # Esito Diagnostico
        st.subheader("📋 Esito Diagnosi")
        if approach > 4.0:
            st.error(f"❌ Scambio termico inefficiente. {nome_app} troppo alto ({approach:.1f}K). Controllare pulizia scambiatori o portata acqua.")
        elif subcool < 3.0:
            st.warning("⚠️ Sottoraffreddamento basso. Possibile scarsa carica di refrigerante o problemi al condensatore.")
        else:
            st.success("✅ Il ciclo rientra nei parametri di efficienza standard.")

    except Exception as e:
        st.error(f"Errore nel calcolo termodinamico: {e}. Verifica che le pressioni siano corrette per il gas selezionato.")

