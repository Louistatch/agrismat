"""
Géolocalisation et informations de lieu.
- Géoloc par IP via ipapi.co (gratuit, sans permission, fonctionne partout)
- Reverse geocoding via Nominatim (OpenStreetMap)
- Altitude via Open-Meteo
"""
import requests


def get_ip_location():
    """
    Géolocalisation par adresse IP via ipapi.co.
    Retourne lat, lon, ville, pays — sans permission navigateur ni GPS hardware.
    """
    try:
        r = requests.get("https://ipapi.co/json/", timeout=8,
                         headers={"User-Agent": "AgriSmart/2.0"})
        r.raise_for_status()
        d = r.json()
        return {
            "lat":     float(d["latitude"]),
            "lon":     float(d["longitude"]),
            "city":    d.get("city", ""),
            "region":  d.get("region", ""),
            "country": d.get("country_name", ""),
            "ip":      d.get("ip", ""),
        }
    except Exception as e:
        print(f"IP geoloc: {e}")
        return None


def get_location_info(lat, lon):
    """
    Reverse geocoding + altitude pour des coordonnées données.
    """
    result = {
        "display":  f"{lat:.4f}N, {lon:.4f}E",
        "city":     "",
        "country":  "",
        "region":   "",
        "altitude": None,
    }

    # Nominatim reverse geocoding
    try:
        r = requests.get("https://nominatim.openstreetmap.org/reverse", params={
            "lat": lat, "lon": lon, "format": "json", "zoom": 10
        }, headers={"User-Agent": "AgriSmart/2.0"}, timeout=8)
        r.raise_for_status()
        addr = r.json().get("address", {})
        city    = (addr.get("city") or addr.get("town") or addr.get("village")
                   or addr.get("municipality") or addr.get("county") or "")
        region  = addr.get("state") or addr.get("region") or ""
        country = addr.get("country", "")
        result["city"]    = city
        result["region"]  = region
        result["country"] = country
        result["display"] = ", ".join(filter(None, [city, region, country]))
    except Exception as e:
        print(f"Nominatim: {e}")

    # Altitude via Open-Meteo
    try:
        r = requests.get("https://api.open-meteo.com/v1/forecast", params={
            "latitude": lat, "longitude": lon,
            "forecast_days": 1, "daily": "temperature_2m_max", "timezone": "auto"
        }, timeout=8)
        r.raise_for_status()
        result["altitude"] = r.json().get("elevation")
    except Exception as e:
        print(f"Elevation: {e}")

    return result
