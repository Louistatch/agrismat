"""
Calcul des propriétés hydrauliques du sol via ROSETTA (USDA-ARS).
L'utilisateur sélectionne la texture manuellement.
ROSETTA prédit FC et WP via le modèle van Genuchten (version 3).
RU = (FC - WP) * 1000 mm/m
"""
from rosetta import rosetta as _rosetta

# Propriétés typiques par texture USDA (sand%, silt%, clay%, bd g/cm³)
TEXTURE_PARAMS = {
    "Sableux":           (75.0, 17.0,  8.0, 1.55),
    "Sableux-Limoneux":  (60.0, 28.0, 12.0, 1.45),
    "Limoneux":          (42.0, 36.0, 22.0, 1.30),
    "Argilo-Limoneux":   (32.0, 38.0, 30.0, 1.20),
    "Argileux":          (20.0, 38.0, 42.0, 1.10),
}

def _van_genuchten_theta(thr, ths, alpha, n, h_kpa):
    """Teneur en eau volumique à une pression h (kPa) via van Genuchten."""
    h_cm = h_kpa * 10.2   # kPa → cm H2O
    m    = 1.0 - 1.0 / n
    return thr + (ths - thr) / (1.0 + (alpha * h_cm) ** n) ** m

def get_soil(texture="Limoneux", **kwargs):
    """
    Calcule les propriétés hydrauliques du sol via ROSETTA v3.
    Entrée  : texture (str) — clé de TEXTURE_PARAMS
    Sortie  : dict avec RU, RFU, FC, WP, texture, source
    """
    sand, silt, clay, bd = TEXTURE_PARAMS.get(texture, TEXTURE_PARAMS["Limoneux"])

    mean, std, codes = _rosetta(3, [[sand, silt, clay, bd]])

    thr   = mean[0][0]   # theta_r
    ths   = mean[0][1]   # theta_s
    alpha = mean[0][2]   # alpha (1/cm)
    n     = mean[0][3]   # n

    fc  = _van_genuchten_theta(thr, ths, alpha, n, 33.0)    # 33 kPa = capacité au champ
    wp  = _van_genuchten_theta(thr, ths, alpha, n, 1500.0)  # 1500 kPa = point flétrissement
    ru  = round((fc - wp) * 1000)
    rfu = round(ru * 2 / 3)

    return {
        "source":   "ROSETTA v3 (USDA-ARS · van Genuchten)",
        "texture":  texture,
        "sand_pct": round(sand, 1),
        "silt_pct": round(silt, 1),
        "clay_pct": round(clay, 1),
        "bdod":     round(bd, 2),
        "fc_pct":   round(fc * 100, 1),
        "wp_pct":   round(wp * 100, 1),
        "RU":       ru,
        "RFU":      rfu,
    }
