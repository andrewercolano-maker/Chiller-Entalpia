        # --- AGGIUNTA LINEA ACQUA PER VISUALIZZARE APPROACH ---
        # Calcoliamo l'entalpia media per posizionare la linea dell'acqua sotto l'evaporatore
        h_mid = (h1 + h5) / 2
        p_acqua = p_evap * 0.85 # La posizioniamo graficamente un po' sotto per chiarezza
        
        # Disegniamo una freccia o una linea che rappresenta la T dell'acqua
        ax.annotate('', xy=(h_mid, p_evap), xytext=(h_mid, p_evap*0.7),
                    arrowprops=dict(arrowstyle='<->', color='orange', lw=1.5))
        ax.text(h_mid, p_evap*0.75, f" Approach: {approach:.1f}K", color='orange', fontweight='bold', ha='center')
        
        # Linea dell'acqua in uscita (riferimento termico)
        ax.axhline(y=PropsSI('P', 'T', t_acqua_out+273.15, 'Q', 1, gas)/1000, 
                   color='orange', linestyle=':', alpha=0.4, label='T. Acqua Out')
