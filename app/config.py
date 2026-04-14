from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_uri: str = "sqlite:///database.db"
    secret_key: str = "YouShouldChangeThisSecretKeyToSomethingLongAndRandom"
    env: str = "development"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expires: int = 60 * 24
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    db_pool_size: int = 10
    db_additional_overflow: int = 10
    db_pool_timeout: int = 10
    db_pool_recycle: int = 1800
    weather_cache_ttl_seconds: int = 60
    weather_stale_ttl_seconds: int = 1800
    weather_search_cache_ttl_seconds: int = 1800
    weather_upstream_min_interval_ms: int = 300
    weather_current_snapshot_ttl_seconds: int = 3600
    weather_current_snapshot_stale_ttl_seconds: int = 86400
    weather_forecast_snapshot_ttl_seconds: int = 10800
    weather_forecast_snapshot_stale_ttl_seconds: int = 86400
    weather_game_csv_path: str = "gameinfo.csv"
    open_meteo_geocoding_url: str = "https://geocoding-api.open-meteo.com/v1/search"
    open_meteo_forecast_url: str = "https://api.open-meteo.com/v1/forecast"
    met_no_locationforecast_url: str = "https://api.met.no/weatherapi/locationforecast/2.0/compact"
    met_no_user_agent: str = "StormScope/1.0 (student weather dashboard)"
    nasa_eonet_url: str = "https://eonet.gsfc.nasa.gov/api/v3/events"
    caribbean_lat_min: float = 5.0
    caribbean_lat_max: float = 30.0
    caribbean_lon_min: float = -90.0
    caribbean_lon_max: float = -55.0
    seeded_user_username: str = "bob"
    seeded_user_email: str = "bob@example.com"
    seeded_user_password: str = "bobpass"
    seeded_admin_username: str = "stormadmin"
    seeded_admin_email: str = "stormadmin@example.com"
    seeded_admin_password: str = "adminpass"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def is_production(self) -> bool:
        return self.env.lower() == "production"

    @property
    def cookie_secure(self) -> bool:
        return self.is_production

    @property
    def cookie_samesite(self) -> str:
        return "none" if self.is_production else "lax"


@lru_cache
def get_settings() -> Settings:
    return Settings()
