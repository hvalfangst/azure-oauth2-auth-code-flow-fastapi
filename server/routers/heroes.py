# server/routers/heroes.py

from http.client import HTTPException
from typing import List
from fastapi import APIRouter
from fastapi import HTTPException
from server.models.dnd_hero import DnDHero
from server.services.hero_service import HeroService

router = APIRouter()
hero_service = HeroService()


# POST: Create a new Hero
@router.post("/heroes/", response_model=DnDHero)
async def create_hero(hero: DnDHero):
    return await hero_service.create_hero(hero)


# GET: Retrieve a hero by ID
@router.get("/heroes/{hero_id}", response_model=DnDHero)
async def read_hero(hero_id: str):
    hero = await hero_service.get_hero(hero_id)
    if hero:
        return hero
    else:
        raise HTTPException(status_code=404, detail="Hero not found")


# GET: Retrieve all heroes
@router.get("/heroes/", response_model=List[DnDHero])
async def read_heroes():
    return await hero_service.list_heroes()


# DELETE: Delete a hero by ID
@router.delete("/heroes/{hero_id}", response_model=dict)
async def delete_hero(hero_id: str):
    success = await hero_service.delete_hero(hero_id)
    if success:
        return {"message": f"Hero with id '{hero_id}' deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Hero not found")


# GET: Custom query to retrieve heroes with Fireball spell and AC < 20
@router.get("/heroes-fireball-low-ac", response_model=List[DnDHero])
async def get_fireball_heroes_with_low_ac():
    return await hero_service.query_heroes_fireball_low_ac()
