"""Dungeons domain with lazy router loading.

Gameplay contracts can be imported by expeditions without eagerly importing
routes and creating a circular dependency back into expedition services.
"""

__all__ = ["router"]


def __getattr__(name: str):
    if name != "router":
        raise AttributeError(name)
    from app.dungeons.routes import router
    return router
