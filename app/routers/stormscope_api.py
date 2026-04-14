from fastapi import HTTPException, Query, Response, status

from app.config import get_settings
from app.dependencies import AdminDep, AuthDep, SessionDep
from app.repositories.disaster_event import DisasterEventRepository
from app.repositories.saved_location import SavedLocationRepository
from app.repositories.user import UserRepository
from app.schemas.disaster import DisasterEventCreate, DisasterEventResponse, DisasterEventUpdate, DisasterImportResponse
from app.schemas.user import UserAdminUpdate, UserDeleteRequest, UserResponse, UserSelfUpdate
from app.schemas.watchlist import SavedLocationCreate, SavedLocationResponse, SavedLocationUpdate
from app.services.disaster_service import DisasterService
from app.services.user_service import UserAuthorizationError, UserConflictError, UserService, UserValidationError
from app.services.watchlist_service import WatchlistService
from app.services.weather_service import WeatherService
from . import api_router


@api_router.get("/auth/me", response_model=UserResponse)
async def auth_me(user: AuthDep):
    return user


def build_user_service(db: SessionDep) -> UserService:
    return UserService(
        user_repo=UserRepository(db),
        saved_location_repo=SavedLocationRepository(db),
        disaster_repo=DisasterEventRepository(db),
    )


@api_router.get("/users/me", response_model=UserResponse)
async def get_current_user_profile(user: AuthDep):
    return user


# PATCH fits this route because profile edits are partial; the client only sends changed fields instead of replacing the full user record as PUT would.
@api_router.patch("/users/me", response_model=UserResponse)
async def update_current_user_profile(payload: UserSelfUpdate, user: AuthDep, db: SessionDep):
    service = build_user_service(db)
    try:
        return service.update_current_user(user, payload)
    except UserValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except UserAuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except UserConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@api_router.delete("/users/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user_profile(
    payload: UserDeleteRequest,
    response: Response,
    user: AuthDep,
    db: SessionDep,
):
    service = build_user_service(db)
    try:
        service.delete_current_user(user, payload)
    except UserValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except UserAuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except UserConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    response.delete_cookie(
        key="access_token",
        httponly=True,
        samesite=get_settings().cookie_samesite,
        secure=get_settings().cookie_secure,
    )


@api_router.get("/users", response_model=list[UserResponse])
async def list_users(user: AdminDep, db: SessionDep):
    service = build_user_service(db)
    return service.get_all_users()


# PATCH fits this admin route because staff may update only one account field at a time, while PUT would imply submitting a complete replacement user payload.
@api_router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, payload: UserAdminUpdate, user: AdminDep, db: SessionDep):
    service = build_user_service(db)
    try:
        return service.update_user_as_admin(user, user_id, payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except UserValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except UserAuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except UserConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@api_router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, user: AdminDep, db: SessionDep):
    service = build_user_service(db)
    try:
        service.delete_user_as_admin(user, user_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except UserAuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except UserConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@api_router.get("/weather/search")
async def weather_search(q: str = Query(min_length=2)):
    service = WeatherService()
    try:
        return {"results": await service.search_city(q)}
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Weather search failed: {exc}")


@api_router.get("/weather/current")
async def weather_current(
    latitude: float,
    longitude: float,
    timezone: str = "auto",
):
    service = WeatherService()
    try:
        return await service.get_current_weather(latitude=latitude, longitude=longitude, timezone=timezone)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Current weather lookup failed: {exc}")


@api_router.get("/weather/forecast")
async def weather_forecast(
    latitude: float,
    longitude: float,
    timezone: str = "auto",
):
    service = WeatherService()
    try:
        return await service.get_forecast(latitude=latitude, longitude=longitude, timezone=timezone)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Forecast lookup failed: {exc}")


@api_router.get("/external/eonet/events")
async def eonet_events(limit: int = 10, scope: str = "global", include_wildfires: bool = True):
    service = WeatherService()
    try:
        return {
            "events": await service.get_live_eonet_events(
                limit=limit,
                caribbean_only=scope.lower() != "global",
                include_wildfires=include_wildfires,
            )
        }
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"EONET lookup failed: {exc}")


@api_router.get("/watchlist", response_model=list[SavedLocationResponse])
async def list_watchlist(user: AuthDep, db: SessionDep):
    service = WatchlistService(SavedLocationRepository(db))
    return service.list_locations(user)


@api_router.post("/watchlist", response_model=SavedLocationResponse, status_code=status.HTTP_201_CREATED)
async def create_watchlist_item(payload: SavedLocationCreate, user: AuthDep, db: SessionDep):
    service = WatchlistService(SavedLocationRepository(db))
    try:
        return service.add_location(user, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


# PATCH fits this watchlist route because nickname and priority are optional partial edits, not a full replacement of the saved location entry.
@api_router.patch("/watchlist/{location_id}", response_model=SavedLocationResponse)
async def update_watchlist_item(location_id: int, payload: SavedLocationUpdate, user: AuthDep, db: SessionDep):
    service = WatchlistService(SavedLocationRepository(db))
    try:
        return service.update_location(user, location_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@api_router.delete("/watchlist/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_watchlist_item(location_id: int, user: AuthDep, db: SessionDep):
    service = WatchlistService(SavedLocationRepository(db))
    try:
        service.delete_location(user, location_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@api_router.get("/disasters", response_model=list[DisasterEventResponse])
async def list_disasters(
    db: SessionDep,
    category: str | None = None,
    country: str | None = None,
    severity: str | None = None,
    include_live_nasa: bool = True,
):
    service = DisasterService(DisasterEventRepository(db))
    return await service.list_events(
        category=category,
        country=country,
        severity=severity,
        include_live_nasa=include_live_nasa,
    )


@api_router.get("/disasters/{event_id}", response_model=DisasterEventResponse)
async def get_disaster(event_id: int, db: SessionDep):
    service = DisasterService(DisasterEventRepository(db))
    try:
        return service.get_event(event_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@api_router.post("/admin/disasters", response_model=DisasterEventResponse, status_code=status.HTTP_201_CREATED)
async def create_disaster(payload: DisasterEventCreate, user: AdminDep, db: SessionDep):
    service = DisasterService(DisasterEventRepository(db))
    return service.create_event(user, payload)


# PATCH fits this disaster update route because admins often correct only a few event fields, while PUT would suggest replacing the entire disaster record.
@api_router.patch("/admin/disasters/{event_id}", response_model=DisasterEventResponse)
async def update_disaster(event_id: int, payload: DisasterEventUpdate, user: AdminDep, db: SessionDep):
    service = DisasterService(DisasterEventRepository(db))
    try:
        return service.update_event(event_id, payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@api_router.delete("/admin/disasters/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_disaster(event_id: int, user: AdminDep, db: SessionDep):
    service = DisasterService(DisasterEventRepository(db))
    try:
        service.delete_event(event_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@api_router.post("/admin/disasters/sync-nasa", response_model=DisasterImportResponse)
async def sync_nasa_disasters(
    user: AdminDep,
    db: SessionDep,
    limit: int = Query(default=250, ge=1, le=500),
    include_wildfires: bool = True,
):
    service = DisasterService(DisasterEventRepository(db))
    try:
        return await service.sync_nasa_feed(
            limit=limit,
            include_wildfires=include_wildfires,
            max_age_minutes=0,
            created_by=user.id,
            force=True,
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"NASA disaster sync failed: {exc}")
