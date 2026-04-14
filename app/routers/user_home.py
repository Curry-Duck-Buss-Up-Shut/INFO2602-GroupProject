from fastapi import Request
from fastapi.responses import HTMLResponse

from app.dependencies.auth import AuthDep
from . import router, templates


def render_stormscope_page(request: Request, user, template_name: str):
    return templates.TemplateResponse(
        request=request,
        name=template_name,
        context={
            "user": user,
            "is_admin": user.role == "admin",
        },
    )


@router.get("/app", response_class=HTMLResponse)
async def user_home_view(
    request: Request,
    user: AuthDep,
):
    return render_stormscope_page(request, user, "app.html")


@router.get("/app/explorer", response_class=HTMLResponse)
async def explorer_view(
    request: Request,
    user: AuthDep,
):
    return render_stormscope_page(request, user, "explorer.html")


@router.get("/app/game", response_class=HTMLResponse)
async def weather_game_view(
    request: Request,
    user: AuthDep,
):
    return render_stormscope_page(request, user, "weather-game.html")


@router.get("/app/profile", response_class=HTMLResponse)
async def profile_view(
    request: Request,
    user: AuthDep,
):
    return render_stormscope_page(request, user, "profile.html")


@router.get("/app/timeline", response_class=HTMLResponse)
async def timeline_view(
    request: Request,
    user: AuthDep,
):
    return render_stormscope_page(request, user, "timeline.html")
