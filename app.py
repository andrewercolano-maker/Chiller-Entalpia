import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from CoolProp.CoolProp import PropsSI
import matplotlib.ticker as ticker

st.set_page_config(page_title="Trane-Style Diagnostic", layout="wide")

st.title("🛡️ Chiller Diagnostic Pro (Trane/Carrier Logic)")

# --- INPUT DATI ---
with st.sidebar:
    st.header("⚙️ Parametri di Campo")
    lista_gas = ["R134a", "R1234ze", "R513A", "R514A", "R410A", "R32"]
    gas = st.selectbox("Refrigerante", lista_gas)
    
    p_evap = st.number_input("Pres. Evaporazione (kPaA)", value=371.5)
    p_cond = st.number_input("Pres. Condensazione (kPaA)", value=801.4)
    t_scarico = st.number_input("Temp. Scarico (°C)", value=55.1)
    subcool = st.number_input("Sottoraffreddamento (K)", value=8.7)
    t_acqua_out = st.number_input("Temp. Uscita Acqua Evap. (°C)", value=9.7)
    
    submit = st.button("ANALIZZA CICLO")

if submit:
    try:
        # --- CALCOLI TERMODINAMICI ---
        t_sat_evap = PropsSI('T', 'P', p_evap*1000, 'Q', 1, gas) - 273.15
        t_sat_cond = PropsSI('T', 'P', p_cond*1000, 'Q', 0, gas) - 273.15
        approach = t_acqua_out - t_sat_evap
        discharge_sh = t_scarico - t_sat_cond
        
        # Punti Ciclo
        h1 = PropsSI('H', 'P', p_evap*1000, 'Q', 1, gas)/1000
        h2 = PropsSI('H', 'P', p_cond*1000, 'T', t_scarico+273.15, gas)/1000
        h4 = PropsSI('H', 'P', p_cond*1000, 'T', (t_sat_cond+273.15) - subcool, gas)/1000
        h5 = h4

        # --- DIAGNOSTICA AVANZATA ---
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Approach Evaporatore", f"{approach:.2f} K")
            if approach > 3.0: st.error("⚠️ ALTO: Possibile fouling o bassa portata")
            elif approach < 0.5: st.warning("🔍 SOSPETTO: Verificare taratura sensori")
            else: st.success("✅ OTTIMO: Scambio efficiente")

        with col2:
            st.metric("Sottoraffreddamento", f"{subcool:.1f} K")
            if subcool < 4.0: st.error("⚠️ BASSO: Scarsità di refrigerante")
            elif subcool > 12.0: st.warning("⚠️ ALTO: Eccesso di carica / Allagamento")
            else: st.success("✅ NORMALE: Carica corretta")

        with col3:
            st.metric("Surriscaldamento Scarico", f"{discharge_sh:.1f} K")
            if discharge_sh < 12.0: st.error("🚨 PERICOLO: Rischio ritorno liquido")
            else: st.success("✅ SICURO: Gas surriscaldato")

        # --- GRAFICO PROFESSIONALE ---
        fig, ax = plt.subplots(figsize=(10, 7))
        
        # Generazione Campana e Zone
        tc = PropsSI('Tcrit', gas)
        T_range = np.linspace(230, tc - 0.5, 100)
        h_liq = [PropsSI('H', 'T', t, 'Q', 0, gas)/1000 for t in T_range]
        h_vap = [PropsSI('H', 'T', t, 'Q', 1, gas)/1000 for t in T_range]
        p_range = [PropsSI('P', 'T', t, 'Q', 0, gas)/1000 for t in T_range]

        # Sfondi colorati per zone
        ax.fill_betweenx(p_range, 0, h_liq, color='lightblue', alpha=0.2, label='Liquido')
        ax.fill_betweenx(p_range, h_liq, h_vap, color='lightgray', alpha=0.1, label='Saturazione')
        ax.fill_betweenx(p_range, h_vap, max(h_vap)+200, color='pink', alpha=0.1, label='Vapore')

        # Linee Titolo e Isoterme
        ax.plot(h_liq, p_range, 'k-', lw=2)
        ax.plot(h_vap, p_range, 'k-', lw=2)
        
        # Ciclo
        ax.plot([h1, h2, h4, h5, h1], [p_evap, p_cond, p_cond, p_evap, p_evap], 
                'go-', lw=4, markersize=10, label="Ciclo Reale")

        ax.set_yscale('log')
        ax.yaxis.set_major_formatter(ticker.ScalarFormatter())
        ax.set_xlabel("Entalpia [kJ/kg]")
        ax.set_ylabel("Pressione [kPaA]")
        ax.grid(True, which="both", alpha=0.3)
        ax.legend()
        
        st.pyplot(fig)

    except Exception as e:
        st.error(f"Errore: {e}. Verifica la coerenza tra Pressioni e Temperature.")
        
