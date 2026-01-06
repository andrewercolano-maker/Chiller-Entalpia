import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from CoolProp.CoolProp import PropsSI
import matplotlib.ticker as ticker

# Configurazione pagina per smartphone
st.set_page_config(page_title="Chiller Diagnostic Pro", layout="centered")

st.title("❄️ Chiller Diagnostic Pro")
st.write("Inserisci i dati del circuito per aggiornare il grafico e la diagnosi.")

# --- SEZIONE INPUT DATI ---
# Usiamo gli 'expander' per tenere l'interfaccia pulita sul telefono
with st.expander("📝 INSERIMENTO DATI CIRCUITO", expanded=True):
    col1, col2 = st.columns(2)
    
    with col1:
        gas = st.selectbox("Refrigerante", ["R134a", "R1234ze", "R410A"])
        p_evap = st.number_input("Pres. Evaporazione (kPaA)", value=371.5, step=5.0, help="Pressione di bassa assoluta")
        t_scarico = st.number_input("Temp. Scarico (°C)", value=55.1, step=0.5)
        
    with col2:
        st.write("") # Spazio vuoto
        p_cond = st.number_input("Pres. Condensazione (kPaA)", value=801.4, step=5.0, help="Pressione di alta assoluta")
        subcool = st.number_input("Sottoraffreddamento (K)", value=8.7, step=0.1)

with st.expander("💧 DATI ACQUA (Per Approach)"):
    t_acqua_out = st.number_input("Temp. Uscita Acqua Evaporatore (°C)", value=9.7, step=0.1)

# --- LOGICA DI CALCOLO E DIAGNOSI ---
try:
    # Calcolo temperature di saturazione
    t_sat_evap = PropsSI('T', 'P', p_evap*1000, 'Q', 1, gas) - 273.15
    t_sat_cond = PropsSI('T', 'P', p_cond*1000, 'Q', 0, gas) - 273.15
    
    # Calcolo Approach
    approach = t_acqua_out - t_sat_evap
    
    # Logica Semaforo
    stato_ok = True
    errori = []
    
    if approach > 3.5:
        stato_ok = False
        errori.append(f"APPROACH ALTO ({approach:.1f}K)")
    if subcool < 4 or subcool > 12:
        stato_ok = False
        errori.append(f"SOTTORAFFREDDAMENTO FUORI RANGE ({subcool}K)")

    # --- VISUALIZZAZIONE RISULTATI ---
    if stato_ok:
        st.success("✅ CICLO FUNZIONANTE CORRETTAMENTE")
    else:
        st.error(f"⚠️ ATTENZIONE: {', '.join(errori)}")

    # --- GENERAZIONE GRAFICO ---
    fig, ax = plt.subplots(figsize=(10, 7))
    
    # Colore dinamico
    color = 'g' if stato_ok else 'r'
    
    # Sfondo tecnico (Campana)
    P_vals = np.logspace(np.log10(PropsSI('Pmin', gas)), np.log10(PropsSI('P_critical', gas)), 100)
    ax.plot([PropsSI('H', 'P', p, 'Q', 0, gas)/1000 for p in P_vals], P_vals/1000, 'k-', alpha=0.2)
    ax.plot([PropsSI('H', 'P', p, 'Q', 1, gas)/1000 for p in P_vals], P_vals/1000, 'k-', alpha=0.2)
    
    # Punti Ciclo
    h1 = PropsSI('H', 'P', p_evap*1000, 'Q', 1, gas)/1000
    h2 = PropsSI('H', 'P', p_cond*1000, 'T', t_scarico+273.15, gas)/1000
    h4 = PropsSI('H', 'P', p_cond*1000, 'T', (t_sat_cond+273.15) - subcool, gas)/1000
    
    ax.plot([h1, h2, h4, h4, h1], [p_evap, p_cond, p_cond, p_evap, p_evap], color + 'o-', lw=3)
    
    ax.set_yscale('log')
    ax.yaxis.set_major_formatter(ticker.ScalarFormatter())
    ax.grid(True, which="both", alpha=0.1)
    ax.set_xlabel("Entalpia [kJ/kg]")
    ax.set_ylabel("Pressione [kPaA]")
    
    st.pyplot(fig)

except Exception as e:
    st.warning("Errore nei dati inseriti. Verifica che le pressioni siano coerenti.")

