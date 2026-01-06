import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from CoolProp.CoolProp import PropsSI
import matplotlib.ticker as ticker

# Configurazione pagina
st.set_page_config(page_title="Chiller Diagnostic Tool", layout="wide")

st.title("❄️ Analisi Professionale Chiller")
st.write("Diagnostica termodinamica avanzata per impianti di refrigerazione")

# --- SIDEBAR INPUT ---
with st.sidebar:
    st.header("⚙️ Dati Operativi")
    lista_gas = ["R134a", "R1234ze", "R513A", "R514A", "R410A", "R32", "R1233zd"]
    gas = st.selectbox("Refrigerante", lista_gas)
    
    p_evap = st.number_input("Pres. Evaporazione (kPaA)", value=371.5)
    p_cond = st.number_input("Pres. Condensazione (kPaA)", value=801.4)
    t_asp = st.number_input("Temp. Aspirazione Compressore (°C)", value=12.0)
    t_scarico = st.number_input("Temp. Scarico (°C)", value=55.1)
    subcool = st.number_input("Sottoraffreddamento (K)", value=8.7)
    t_acqua_out = st.number_input("Temp. Uscita Acqua Evap. (°C)", value=9.7)
    
    submit = st.button("ESEGUI ANALISI")

if submit:
    try:
        # --- CALCOLI TERMODINAMICI ---
        t_sat_evap = PropsSI('T', 'P', p_evap*1000, 'Q', 1, gas) - 273.15
        t_sat_cond = PropsSI('T', 'P', p_cond*1000, 'Q', 0, gas) - 273.15
        
        # Punti principali (kJ/kg)
        h1 = PropsSI('H', 'P', p_evap*1000, 'T', t_asp+273.15, gas)/1000 
        h2 = PropsSI('H', 'P', p_cond*1000, 'T', t_scarico+273.15, gas)/1000 
        s1 = PropsSI('S', 'P', p_evap*1000, 'T', t_asp+273.15, gas) 
        h2s = PropsSI('H', 'P', p_cond*1000, 'S', s1, gas)/1000 
        
        h4 = PropsSI('H', 'P', p_cond*1000, 'T', (t_sat_cond+273.15) - subcool, gas)/1000
        h5 = h4 
        
        # KPI Performance
        cop = (h1 - h5) / (h2 - h1)
        rend_isen = (h2s - h1) / (h2 - h1) * 100
        approach = t_acqua_out - t_sat_evap
        disch_sh = t_scarico - t_sat_cond

        # --- INTERFACCIA RISULTATI ---
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("COP", f"{cop:.2f}")
        m2.metric("Efficienza Isentropica", f"{rend_isen:.1f} %")
        m3.metric("Approach", f"{approach:.2f} K")
        m4.metric("Sottoraffreddamento", f"{subcool:.1f} K")

        # Diagnosi tecnica
        st.subheader("📋 Esito Diagnostica")
        if approach > 3.5: 
            st.error("❌ Efficienza evaporatore bassa. Possibile sporcamento scambiatore o scarsa portata acqua.")
        elif approach < 0.3:
            st.warning("⚠️ Valore approach sospetto. Verificare taratura sonde temperatura.")
        else:
            st.success("✅ Scambio termico all'evaporatore ottimale.")

        if subcool < 4.0: 
            st.error("❌ Sottoraffreddamento basso. Possibile scarsità di refrigerante nell'impianto.")
        elif subcool > 12.0:
            st.warning("⚠️ Sottoraffreddamento elevato. Possibile eccesso di carica o allagamento condensatore.")

        if disch_sh < 15.0: 
            st.error("🚨 ATTENZIONE: Surriscaldamento allo scarico pericoloso. Rischio di trascinamento liquido al compressore!")

        # --- GRAFICO AVANZATO ---
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Zone e Campana
        tc = PropsSI('Tcrit', gas)
        pc = PropsSI('Pcrit', gas)
        T_range = np.linspace(235, tc - 0.5, 100)
        h_liq = [PropsSI('H', 'T', t, 'Q', 0, gas)/1000 for t in T_range]
        h_vap = [PropsSI('H', 'T', t, 'Q', 1, gas)/1000 for t in T_range]
        p_range = [PropsSI('P', 'T', t, 'Q', 0, gas)/1000 for t in T_range]
        
        ax.fill_betweenx(p_range, 0, h_liq, color='skyblue', alpha=0.1, label='Zona Liquido')
        ax.fill_betweenx(p_range, h_liq, h_vap, color='lightgray', alpha=0.1, label='Saturazione')
        ax.fill_betweenx(p_range, h_vap, max(h_vap)+300, color='coral', alpha=0.1, label='Zona Vapore')

        # Linee di Titolo e Isentropiche
        for x in [0.2, 0.4, 0.6, 0.8]:
            h_x = [PropsSI('H', 'T', t, 'Q', x, gas)/1000 for t in T_range]
            ax.plot(h_x, p_range, 'k:', alpha=0.15, lw=0.8)

        # Ciclo
        p_ciclo = [p_evap, p_cond, p_cond, p_evap, p_evap]
        h_ciclo = [h1, h2, h4, h5, h1]
        ax.plot(h_ciclo, p_ciclo, 'bo-', lw=3, markersize=8, label="Ciclo Frigo")
        
        # Estetica assi
        ax.set_yscale('log')
        ax.yaxis.set_major_formatter(ticker.ScalarFormatter())
        ax.set_xlabel("Entalpia [kJ/kg]")
        ax.set_ylabel("Pressione [kPaA]")
        ax.grid(True, which="both", alpha=0.2)
        ax.legend(loc='upper left')
        
        st.pyplot(fig)

    except Exception as e:
        st.error(f"Errore tecnico: {e}. Verificare la coerenza dei dati (es. P alta > P bassa).")
        
