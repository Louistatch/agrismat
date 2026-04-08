import requests
from datetime import datetime, timedelta

def _fetch_open_meteo(lat, lon, start_date, end_date, endpoint):
    """Appel générique Open-Meteo avec plage de dates."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": ["et0_fao_evapotranspiration", "precipitation_sum"],
        "timezone": "auto",
        "start_date": start_date,
        "end_date": end_date,
    }
    response = requests.get(endpoint, params=params, timeout=15)
    response.raise_for_status()
    return response.json()

def get_weather(lat, lon, days=7):
    """
    Récupère ET0 et précipitations sur `days` jours.
    - Passé/présent  → Open-Meteo Archive (ERA5)
    - Futur (≤16j)   → Open-Meteo Forecast
    Pour les horizons longs, on répète le dernier cycle annuel connu.
    """
    today = datetime.now().date()
    results = []

    # 1. Données historiques : de (today - days) à hier via Archive
    hist_start = today - timedelta(days=days)
    hist_end   = today - timedelta(days=1)

    try:
        data = _fetch_open_meteo(
            lat, lon,
            hist_start.strftime("%Y-%m-%d"),
            hist_end.strftime("%Y-%m-%d"),
            "https://archive-api.open-meteo.com/v1/archive"
        )
        daily = data["daily"]
        for i in range(len(daily["time"])):
            et0   = daily["et0_fao_evapotranspiration"][i] or 0.0
            precip = daily["precipitation_sum"][i] or 0.0
            results.append({"date": daily["time"][i], "et0": et0, "precip": precip})
    except Exception as e:
        print(f"Erreur Open-Meteo Archive: {e}")

    # 2. Prévisions courtes (max 16 jours) pour les jours à venir
    try:
        data = _fetch_open_meteo(
            lat, lon,
            today.strftime("%Y-%m-%d"),
            (today + timedelta(days=15)).strftime("%Y-%m-%d"),
            "https://api.open-meteo.com/v1/forecast"
        )
        daily = data["daily"]
        for i in range(len(daily["time"])):
            et0    = daily["et0_fao_evapotranspiration"][i] or 0.0
            precip = daily["precipitation_sum"][i] or 0.0
            results.append({"date": daily["time"][i], "et0": et0, "precip": precip})
    except Exception as e:
        print(f"Erreur Open-Meteo Forecast: {e}")

    if not results:
        # Fallback synthétique si les deux APIs échouent
        print("Fallback: données synthétiques utilisées.")
        for i in range(days):
            d = today - timedelta(days=days - i)
            results.append({"date": d.strftime("%Y-%m-%d"), "et0": 5.0, "precip": 1.0})
        return results

    # 3. Si on a besoin de plus de jours que disponibles, on boucle sur l'historique
    if len(results) < days:
        base = results.copy()
        base_len = len(base)
        last_date = datetime.strptime(results[-1]["date"], "%Y-%m-%d").date()
        while len(results) < days:
            idx = (len(results) - len(base)) % base_len
            next_date = last_date + timedelta(days=len(results) - len(base) + 1)
            results.append({
                "date": next_date.strftime("%Y-%m-%d"),
                "et0": base[idx]["et0"],
                "precip": base[idx]["precip"]
            })

    return results[:days]
