"""Geographic utilities for tournament location handling."""

import math


def haversine_distance(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """Calculate the great-circle distance between two points in kilometers."""
    R = 6371  # Earth's radius in km

    lat1_r, lat2_r = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def same_continent(country1: str, country2: str) -> bool:
    """Check if two countries (ISO 3166-1 alpha-3) are on the same continent."""
    continent_map = {
        # Europe
        "FRA": "EU", "GBR": "EU", "ESP": "EU", "ITA": "EU", "DEU": "EU",
        "SRB": "EU", "SUI": "EU", "AUT": "EU", "NED": "EU", "BEL": "EU",
        "CZE": "EU", "POL": "EU", "GRE": "EU", "NOR": "EU", "SWE": "EU",
        "DEN": "EU", "FIN": "EU", "POR": "EU", "ROU": "EU", "CRO": "EU",
        "HUN": "EU", "BUL": "EU", "RUS": "EU", "UKR": "EU", "BLR": "EU",
        "GEO": "EU", "MON": "EU", "IRL": "EU",
        # North America
        "USA": "NA", "CAN": "NA", "MEX": "NA",
        # South America
        "ARG": "SA", "BRA": "SA", "CHI": "SA", "COL": "SA", "PER": "SA",
        "URU": "SA", "ECU": "SA", "VEN": "SA", "BOL": "SA",
        # Asia
        "JPN": "AS", "CHN": "AS", "KOR": "AS", "IND": "AS", "KAZ": "AS",
        "THA": "AS", "TPE": "AS", "UZB": "AS", "QAT": "AS", "UAE": "AS",
        "BRN": "AS", "KSA": "AS", "ISR": "AS",
        # Oceania
        "AUS": "OC", "NZL": "OC",
        # Africa
        "RSA": "AF", "TUN": "AF", "EGY": "AF", "MAR": "AF",
    }
    return continent_map.get(country1, "?") == continent_map.get(country2, "??")
