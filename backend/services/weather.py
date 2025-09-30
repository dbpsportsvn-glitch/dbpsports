# File: backend/services/weather.py
import requests
import unicodedata
from functools import lru_cache
from datetime import datetime
from zoneinfo import ZoneInfo
from django.core.cache import cache
from typing import Union # <-- THÊM DÒNG NÀY ĐỂ TƯƠNG THÍCH PYTHON 3.9

# --- CÁC BIẾN CẤU HÌNH ---
TZ = ZoneInfo("Asia/Ho_Chi_Minh")
HEADERS = {"User-Agent": "DBPSports/1.0 (contact: dbpsportsvn@gmail.com)"}

# --- CÁC HÀM TIỆN ÍCH VÀ BẢN ĐỒ DỮ LIỆU ---

def _normalize(s: str) -> str:
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    return s.lower().strip()

ALIASES = {
    "sai gon": "tp. hồ chí minh", "ho chi minh": "tp. hồ chí minh",
    "hcm": "tp. hồ chí minh", "tphcm": "tp. hồ chí minh",
    "hn": "hà nội", "danang": "đà nẵng",
}

LOCATION_COORDINATES = {
    "điện biên phủ": {"lat": 21.39, "lon": 103.02},
    "hà nội": {"lat": 21.0285, "lon": 105.8542},
    "tp. hồ chí minh": {"lat": 10.7769, "lon": 106.7009},
    "đà nẵng": {"lat": 16.0545, "lon": 108.2022},
    'sơn la': {'lat': 21.32, 'lon': 103.92},
    'lai châu': {'lat': 22.4, 'lon': 103.46},
    'thái bình': {'lat': 20.45, 'lon': 106.33},
    'nam định': {'lat': 20.42, 'lon': 106.17},
    'hưng yên': {'lat': 20.65, 'lon': 106.05},
    'bình dương': {'lat': 11.18, 'lon': 106.65},
}

WMO_CODE_MAP = {
    0: ("Trời quang", "bi-sun-fill"), 1: ("Trời trong", "bi-sun"),
    2: ("Ít mây", "bi-cloud-sun"), 3: ("Nhiều mây", "bi-cloud"),
    45: ("Sương mù", "bi-cloud-haze2-fill"), 48: ("Sương mù ẩm", "bi-cloud-haze2"),
    51: ("Mưa phùn nhẹ", "bi-cloud-drizzle"), 53: ("Mưa phùn", "bi-cloud-drizzle"),
    55: ("Mưa phùn dày", "bi-cloud-drizzle-fill"),
    61: ("Mưa nhỏ", "bi-cloud-rain"), 63: ("Mưa vừa", "bi-cloud-rain"),
    65: ("Mưa to", "bi-cloud-rain-heavy-fill"),
    80: ("Mưa rào nhẹ", "bi-cloud-rain-heavy"), 81: ("Mưa rào", "bi-cloud-rain-heavy"),
    82: ("Mưa rào xối xả", "bi-cloud-rain-heavy-fill"),
    95: ("Dông", "bi-cloud-lightning-rain"),
}

# --- CÁC HÀM LẤY TỌA ĐỘ (GEOCODING) ---

@lru_cache(maxsize=256)
def geocode_open_meteo_vn(q: str):
    try:
        r = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": q, "count": 1, "language": "vi", "format": "json"},
            headers=HEADERS, timeout=8
        )
        r.raise_for_status()
        results = r.json().get("results", [])
        if not results: return None
        best = results[0]
        return {"lat": best["latitude"], "lon": best["longitude"], "matched": best.get("name")}
    except Exception:
        return None

# === SỬA LỖI TẠI DÒNG NÀY ===
def resolve_coords_vn(location_name: str, region: Union[str, None] = None):
    if not location_name: return None
    key = ALIASES.get(_normalize(location_name), _normalize(location_name))

    for k, coords in LOCATION_COORDINATES.items():
        if _normalize(k) in key or key in _normalize(k):
            return {"lat": coords["lat"], "lon": coords["lon"], "source": "static", "matched": k}

    om = geocode_open_meteo_vn(location_name)
    if om: return {**om, "source": "open-meteo"}

    if region == "MIEN_BAC": return {**LOCATION_COORDINATES["hà nội"], "source": "fallback", "matched": "hà nội"}
    if region == "MIEN_TRUNG": return {**LOCATION_COORDINATES["đà nẵng"], "source": "fallback", "matched": "đà nẵng"}
    if region == "MIEN_NAM": return {**LOCATION_COORDINATES["tp. hồ chí minh"], "source": "fallback", "matched": "tp. hồ chí minh"}
    
    return {**LOCATION_COORDINATES["điện biên phủ"], "source": "fallback", "matched": "điện biên phủ"}

# --- HÀM LẤY DỰ BÁO (CÓ CACHE) ---

def _cache_ttl(match_date: str) -> int:
    today = datetime.now(TZ).strftime("%Y-%m-%d")
    return 900 if match_date == today else 3600

def fetch_forecast_day(lat: float, lon: float, date_str: str):
    ck = f"weather:{lat:.4f}:{lon:.4f}:{date_str}"
    cached = cache.get(ck)
    if cached: return cached
    
    params = {
        "latitude": lat, "longitude": lon,
        "hourly": "temperature_2m,weathercode,precipitation_probability,wind_speed_10m,relative_humidity_2m",
        "timezone": "Asia/Ho_Chi_Minh",
        "start_date": date_str, "end_date": date_str,
    }
    r = requests.get("https://api.open-meteo.com/v1/forecast", params=params, headers=HEADERS, timeout=10)
    r.raise_for_status()
    data = r.json().get("hourly", {})
    cache.set(ck, data, timeout=_cache_ttl(date_str))
    return data

# === VÀ SỬA LỖI TẠI DÒNG NÀY ===
def get_weather_for_match(location_name: str, match_datetime: datetime, region: Union[str, None] = None):
    loc = resolve_coords_vn(location_name, region)
    if not loc: return None
    
    md = match_datetime.astimezone(TZ) if match_datetime.tzinfo else match_datetime.replace(tzinfo=TZ)
    date_str = md.strftime("%Y-%m-%d")
    hourly = fetch_forecast_day(loc["lat"], loc["lon"], date_str)
    times = hourly.get("time", [])
    if not times: return None

    target = md.replace(minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:00")
    try:
        idx = times.index(target)
    except ValueError:
        def _p(t): return datetime.fromisoformat(t).replace(tzinfo=TZ)
        diffs = [abs((_p(t) - md).total_seconds()) for t in times]
        idx = diffs.index(min(diffs))

    def _get(key):
        arr = hourly.get(key, [])
        return arr[idx] if idx < len(arr) else None

    temp = _get("temperature_2m")
    code = _get("weathercode")
    rain_prob = _get("precipitation_probability")
    wind = _get("wind_speed_10m")
    rh = _get("relative_humidity_2m")
    condition, icon = WMO_CODE_MAP.get(code, ("Không xác định", "bi-question-circle"))

    return {
        "temp": f"{round(temp)}°C" if temp is not None else "N/A",
        "condition": condition,
        "icon": icon,
        "rain_prob": f"{rain_prob}%" if rain_prob is not None else "N/A",
        "wind_kmh": f"{round(wind)} km/h" if wind is not None else "N/A",
        "humidity": f"{rh}%" if rh is not None else "N/A",
    }