from sqlmodel import Field, SQLModel

class WeatherLocationRequest(SQLModel):
    latitude: float
    longitude: float
    timezone: str = "auto"

class WeatherCurrentBatchRequest(SQLModel):
    locations: list[WeatherLocationRequest] = Field(default_factory=list)
