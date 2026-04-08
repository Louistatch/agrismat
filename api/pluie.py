"""
Données agroclimatiques via NASA POWER Climatology (normales 30 ans).
Calcul ETP Penman-Monteith FAO-56 depuis T, RH, Vent, Rayonnement.
"""
import requests
import math

_NASA_MONTHS = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']
_JOURS_MOIS  = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

def _penman_monteith(tmax, tmin, tmean, rh, ws, rs):
    """ETP Penman-Monteith FAO-56 (mm/jour)."""
    es    = 0.6108 * math.exp(17.27 * tmean / (tmean + 237.3))
    ea    = es * rh / 100.0
    delta = 4098 * es / (tmean + 237.3) ** 2
    gamma = 0.0665
    rns   = 0.77 * rs
    sigma = 4.903e-9
    rnl   = (sigma * ((tmax+273.16)**4 + (tmin+273.16)**4) / 2
             * (0.34 - 0.14 * math.sqrt(max(ea, 0)))
             * (1.35 * rs / max(0.75*rs + 0.1, 0.01) - 0.35))
    rn    = rns - rnl
    eto   = (0.408*delta*(rn) + gamma*(900/(tmean+273))*ws*(es-ea)) / \
            (delta + gamma*(1 + 0.34*ws))
    return max(0.0, round(eto, 2))

def get_climate(lat, lon):
    """
    Normales climatiques mensuelles via NASA POWER Climatology.
    Retourne ETP (mm/j), précipitations (mm/mois), température (°C)
    pour les 12 mois Jan→Déc.
    """
    try:
        r = requests.get(
            "https://power.larc.nasa.gov/api/temporal/climatology/point",
            params={
                "latitude":   lat,
                "longitude":  lon,
                "parameters": "T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,RH2M,WS2M,ALLSKY_SFC_SW_DWN",
                "format":     "JSON",
                "community":  "ag",
            },
            timeout=20,
        )
        r.raise_for_status()
        d = r.json()["properties"]["parameter"]

        etp_list   = []
        pluie_list = []
        temp_list  = []

        for i, m in enumerate(_NASA_MONTHS):
            eto   = _penman_monteith(
                d["T2M_MAX"][m], d["T2M_MIN"][m], d["T2M"][m],
                d["RH2M"][m], d["WS2M"][m], d["ALLSKY_SFC_SW_DWN"][m]
            )
            pluie = round(d["PRECTOTCORR"][m] * _JOURS_MOIS[i], 1)
            etp_list.append(eto)
            pluie_list.append(pluie)
            temp_list.append(round(d["T2M"][m], 1))

        return {
            "source":          "NASA POWER Climatology (30 ans)",
            "etp_mensuelle":   etp_list,       # mm/j, index 0=Jan
            "pluie_mensuelle": pluie_list,     # mm/mois, index 0=Jan
            "temp_mensuelle":  temp_list,
            "total_precip":    round(sum(pluie_list), 0),
            "avg_temp":        round(sum(temp_list) / 12, 1),
        }

    except Exception as e:
        print(f"NASA POWER: {e}")
        # Fallback KARA
        return {
            "source":          "Défaut (KARA)",
            "etp_mensuelle":   [5.3,5.5,5.4,5.2,5.0,4.5,4.0,3.8,4.2,4.5,4.8,5.0],
            "pluie_mensuelle": [2,8,22,50,100,122,178,288,220,105,4,1],
            "temp_mensuelle":  [24.9,27.7,29.1,28.3,27.2,25.9,24.7,24.3,24.7,25.3,25.6,24.5],
            "total_precip":    1100,
            "avg_temp":        26.0,
        }
