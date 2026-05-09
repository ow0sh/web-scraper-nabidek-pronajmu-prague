import functools
import operator
import os
from dataclasses import dataclass
from pathlib import Path

import environ
from dotenv import load_dotenv

from disposition import Disposition

load_dotenv(".env")

app_env = os.getenv("APP_ENV")
if app_env:
    load_dotenv(".env." + app_env, override=True)

load_dotenv(".env.local", override=True)

_str_to_disposition_map = {
    "1+kk": Disposition.FLAT_1KK,
    "1+1": Disposition.FLAT_1,
    "2+kk": Disposition.FLAT_2KK,
    "2+1": Disposition.FLAT_2,
    "3+kk": Disposition.FLAT_3KK,
    "3+1": Disposition.FLAT_3,
    "4+kk": Disposition.FLAT_4KK,
    "4+1": Disposition.FLAT_4,
    "5++": Disposition.FLAT_5_UP,
    "others": Disposition.FLAT_OTHERS
}


@dataclass(frozen=True)
class LocationConfig:
    name: str
    search_label: str
    city_label: str
    center_lat: str
    center_lng: str
    south: str
    west: str
    north: str
    east: str
    idnes_slug: str
    realcity_slug: str
    remax_region_query: str
    bezrealitky_region_osm_id: str


_supported_locations = {
    "prague": LocationConfig(
        name="Prague",
        search_label="Praha, Česko",
        city_label="Praha",
        center_lat="50.0874654",
        center_lng="14.4212535",
        south="49.9419006",
        west="14.2244355",
        north="50.1774302",
        east="14.7067867",
        idnes_slug="praha",
        realcity_slug="hlavni-mesto-praha-1",
        remax_region_query="regions%5B19%5D=on",
        bezrealitky_region_osm_id="R435514",
    ),
    "praha": None,
    "plzen": LocationConfig(
        name="Plzen",
        search_label="Plzeň, Česko",
        city_label="Plzeň",
        center_lat="49.7477415",
        center_lng="13.3775249",
        south="49.6776013",
        west="13.2679878",
        north="49.8057641",
        east="13.4758418",
        idnes_slug="plzen",
        realcity_slug="plzen-2605",
        remax_region_query="regions%5B43%5D%5B3405%5D=on",
        bezrealitky_region_osm_id="R438344",
    ),
    "plzeň": None,
}

_supported_locations["praha"] = _supported_locations["prague"]
_supported_locations["plzeň"] = _supported_locations["plzen"]


def optional_int_converter(raw_value: str | int | None) -> int | None:
    if raw_value is None:
        return None

    value = str(raw_value).strip()
    if not value:
        return None

    return int(value)


def dispositions_converter(raw_disps: str):
    return functools.reduce(operator.or_, map(lambda d: _str_to_disposition_map[d], raw_disps.split(",")), Disposition.NONE)


def location_converter(raw_location: str) -> LocationConfig:
    location_key = raw_location.strip().lower()
    try:
        return _supported_locations[location_key]
    except KeyError as exc:
        supported = ", ".join(sorted({key for key, value in _supported_locations.items() if value is not None}))
        raise ValueError(f"Unsupported CITY '{raw_location}'. Supported values: {supported}") from exc


@environ.config(prefix="")
class Config:
    debug: bool = environ.bool_var()
    found_offers_file: Path = environ.var(converter=Path)
    refresh_interval_daytime_minutes: int = environ.var(converter=int)
    refresh_interval_nighttime_minutes: int = environ.var(converter=int)
    dispositions: Disposition = environ.var(converter=dispositions_converter)
    city: LocationConfig = environ.var(default="prague", converter=location_converter)
    min_price: int | None = environ.var(default=None, converter=optional_int_converter)
    max_price: int | None = environ.var(default=None, converter=optional_int_converter)

    @environ.config()
    class Telegram:
        bot_token = environ.var()
        chat_id = environ.var()

    telegram: Telegram = environ.group(Telegram)

config: Config = Config.from_environ()
