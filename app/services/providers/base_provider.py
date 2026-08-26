from abc import ABC, abstractmethod
from typing import List, Optional
from app.schemas.weather import CurrentWeatherResponse, ForecastResponse
from app.schemas.location import LocationSearchResult


class BaseWeatherProvider(ABC):
    """
    Abstract interface for all upstream weather data providers.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier string."""
        pass

    @abstractmethod
    async def get_current_weather(self, lat: float, lon: float) -> Optional[CurrentWeatherResponse]:
        """Fetch current weather conditions."""
        pass

    @abstractmethod
    async def get_forecast(
        self, lat: float, lon: float, hourly_steps: int = 24, daily_steps: int = 7
    ) -> Optional[ForecastResponse]:
        """Fetch hourly and daily forecasts."""
        pass

    @abstractmethod
    async def search_locations(self, query: str) -> List[LocationSearchResult]:
        """Search global locations with typeahead autocomplete."""
        pass
