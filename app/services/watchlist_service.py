from app.models.user import User
from app.repositories.saved_location import SavedLocationRepository
from app.schemas.watchlist import SavedLocationCreate, SavedLocationUpdate


class WatchlistService:
    def __init__(self, repo: SavedLocationRepository):
        self.repo = repo

    def list_locations(self, user: User):
        return self.repo.list_for_user(user.id)

    def add_location(self, user: User, payload: SavedLocationCreate):
        duplicate = self.repo.find_duplicate(user.id, payload.city_name, payload.country_name)
        if duplicate:
            raise ValueError("This city is already saved in your watchlist")
        return self.repo.create(user.id, payload)

    def update_location(self, user: User, location_id: int, payload: SavedLocationUpdate):
        location = self.repo.get_for_user(location_id, user.id)
        if not location:
            raise ValueError("Saved location not found")
        return self.repo.update(location, payload)

    def delete_location(self, user: User, location_id: int):
        location = self.repo.get_for_user(location_id, user.id)
        if not location:
            raise ValueError("Saved location not found")
        self.repo.delete(location)
