# Source: Besoin en eau des cultures KARA1.xlsx - Données locales KARA (Togo)
# Calendrier: Avril → Mars (12 mois)

MOIS = ["Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre", "Janvier", "Février", "Mars"]
MOIS_ORDER = {m: i for i, m in enumerate(MOIS)}
JOURS_MOIS = [30, 31, 30, 31, 30, 31, 30, 31, 30, 31, 28, 31]

# ETP locale KARA (mm/jour) - données climatiques locales
ETP_KARA = [5.2, 5.0, 4.5, 4.0, 3.8, 4.2, 4.5, 4.8, 5.0, 5.3, 5.5, 5.4]

# Pluviométrie mensuelle KARA (mm/mois)
PLUIE_KARA = [50, 100, 122, 178, 288, 220, 105, 4, 1, 2, 8, 22]

# Kc mensuels par culture (Avril→Mars) - extraits du fichier Excel KARA1
KC_VALUES = {
    "Tomate": {
        "kc":  [0.45, 0.75, 1.15, 1.15, 1.15, 1.15, 0.90, 0.70, 0.45, 0.45, 0.45, 0.75],
        "z":   [0.30, 0.40, 0.50, 0.60, 0.70, 0.70, 0.70, 0.70, 0.30, 0.30, 0.30, 0.40],
    },
    "Piment": {
        "kc":  [0.35, 0.70, 1.05, 1.05, 1.05, 1.05, 0.95, 0.90, 0.35, 0.35, 0.35, 0.70],
        "z":   [0.25, 0.35, 0.45, 0.50, 0.60, 0.60, 0.60, 0.60, 0.25, 0.25, 0.25, 0.35],
    },
    "Oignon": {
        "kc":  [0.50, 0.70, 1.05, 1.05, 1.05, 0.85, 0.75, 0.50, 0.50, 0.50, 0.50, 0.70],
        "z":   [0.20, 0.25, 0.30, 0.30, 0.30, 0.30, 0.30, 0.25, 0.20, 0.20, 0.20, 0.25],
    },
    "Chou": {
        "kc":  [0.45, 0.70, 1.00, 1.05, 1.05, 0.95, 0.90, 0.45, 0.45, 0.45, 0.45, 0.70],
        "z":   [0.25, 0.35, 0.45, 0.50, 0.50, 0.50, 0.45, 0.25, 0.25, 0.25, 0.25, 0.35],
    },
    "Laitue": {
        "kc":  [0.70, 0.85, 1.00, 1.00, 1.00, 0.95, 0.70, 0.70, 0.70, 0.70, 0.70, 0.85],
        "z":   [0.15, 0.20, 0.25, 0.30, 0.30, 0.30, 0.20, 0.15, 0.15, 0.15, 0.15, 0.20],
    },
    "Carotte": {
        "kc":  [0.50, 0.70, 1.00, 1.05, 1.05, 1.00, 0.90, 0.50, 0.50, 0.50, 0.50, 0.70],
        "z":   [0.25, 0.35, 0.45, 0.55, 0.60, 0.60, 0.55, 0.25, 0.25, 0.25, 0.25, 0.35],
    },
    "Concombre": {
        "kc":  [0.40, 0.70, 1.00, 1.15, 1.15, 0.90, 0.85, 0.40, 0.40, 0.40, 0.40, 0.70],
        "z":   [0.20, 0.30, 0.35, 0.40, 0.40, 0.40, 0.35, 0.20, 0.20, 0.20, 0.20, 0.30],
    },
    "Aubergine": {
        "kc":  [0.45, 0.70, 1.00, 1.15, 1.15, 1.00, 0.85, 0.80, 0.45, 0.45, 0.45, 0.70],
        "z":   [0.30, 0.40, 0.50, 0.60, 0.70, 0.70, 0.70, 0.60, 0.30, 0.30, 0.30, 0.40],
    },
    "Gombo": {
        "kc":  [0.40, 0.65, 0.90, 1.00, 1.00, 0.95, 0.85, 0.40, 0.40, 0.40, 0.40, 0.65],
        "z":   [0.25, 0.35, 0.45, 0.55, 0.60, 0.60, 0.55, 0.25, 0.25, 0.25, 0.25, 0.35],
    },
    "Pastèque": {
        "kc":  [0.40, 0.60, 0.85, 1.00, 1.00, 0.95, 0.75, 0.40, 0.40, 0.40, 0.40, 0.60],
        "z":   [0.40, 0.60, 0.80, 1.00, 1.20, 1.20, 1.00, 0.40, 0.40, 0.40, 0.40, 0.60],
    },
}

SOIL_TYPES = {
    "Sableux":           {"RU": 60},
    "Sableux-Limoneux":  {"RU": 90},
    "Limoneux":          {"RU": 120},
    "Argilo-Limoneux":   {"RU": 150},
    "Argileux":          {"RU": 180},
}

# Mapping texture SoilGrids → clé SOIL_TYPES
TEXTURE_MAP = {
    "Sableux":          "Sableux",
    "Sableux-Limoneux": "Sableux-Limoneux",
    "Limoneux":         "Limoneux",
    "Argilo-Limoneux":  "Argilo-Limoneux",
    "Argileux":         "Argileux",
}

IRRIGATION_SYSTEMS = {
    "Goutte à goutte":  {"efficiency": 0.90},
    "Bande perforée":   {"efficiency": 0.75},
    "Aspersion":        {"efficiency": 0.75},
    "Gravitaire":       {"efficiency": 0.60},
}
