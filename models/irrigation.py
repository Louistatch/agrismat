import pandas as pd
from utils.kc_values import KC_VALUES, IRRIGATION_SYSTEMS, MOIS, JOURS_MOIS

# Mapping mois français (Avr→Mars) → index Jan-based (0=Jan)
_MOIS_TO_JAN_IDX = {
    "Avril": 3, "Mai": 4, "Juin": 5, "Juillet": 6,
    "Août": 7, "Septembre": 8, "Octobre": 9, "Novembre": 10,
    "Décembre": 11, "Janvier": 0, "Février": 1, "Mars": 2
}

def pluie_efficace(p_mm):
    """Pluies efficaces USDA SCS (mensuel)."""
    return (0.85 * p_mm + 3) if p_mm > 17 else 0.0


def compute_monthly_needs(crop_name, area_ha, soil_data, system_name, climate_data):
    """
    Calcule les besoins en eau mensuels avec données sol et climat dynamiques.

    soil_data    : dict retourné par api/sol.get_soil()  → contient 'RU'
    climate_data : dict retourné par api/pluie.get_climate() → contient
                   'etp_mensuelle' (mm/j, Jan=0) et 'pluie_mensuelle' (mm/mois, Jan=0)
    """
    efficiency = IRRIGATION_SYSTEMS[system_name]["efficiency"]
    ru_m       = soil_data["RU"]          # mm/m (calculé par pédotransfert)
    crop       = KC_VALUES[crop_name]

    etp_jan   = climate_data["etp_mensuelle"]    # list 12 valeurs, index 0=Jan
    pluie_jan = climate_data["pluie_mensuelle"]  # list 12 valeurs, index 0=Jan

    rows = []
    for i, mois in enumerate(MOIS):
        jan_idx  = _MOIS_TO_JAN_IDX[mois]
        nb_jours = JOURS_MOIS[i]
        etp      = etp_jan[jan_idx]
        pluie    = pluie_jan[jan_idx]
        kc       = crop["kc"][i]
        z        = crop["z"][i]

        etm          = etp * kc * nb_jours      # mm/mois
        peff         = pluie_efficace(pluie)    # mm/mois
        ru           = ru_m * z                 # mm
        rfu          = (2 / 3) * ru             # mm
        bilan        = (peff + rfu) - etm
        besoin_net   = max(0, -bilan)
        besoin_brut  = besoin_net / efficiency
        volume_ha    = besoin_brut * 10         # m³/ha/mois
        volume_total = volume_ha * area_ha      # m³/mois

        rows.append({
            "mois":         mois,
            "mois_order":   i,
            "nb_jours":     nb_jours,
            "etp":          round(etp, 2),
            "kc":           kc,
            "z":            z,
            "etm":          round(etm, 1),
            "pluie":        round(pluie, 1),
            "peff":         round(peff, 1),
            "ru":           round(ru, 1),
            "rfu":          round(rfu, 1),
            "bilan":        round(bilan, 1),
            "besoin_net":   round(besoin_net, 1),
            "besoin_brut":  round(besoin_brut, 1),
            "volume_ha":    round(volume_ha, 1),
            "volume_total": round(volume_total, 1),
        })

    return pd.DataFrame(rows)
