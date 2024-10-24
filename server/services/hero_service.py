# server/services/hero_service.py

from typing import List, Optional
from server.models.dnd_hero import DnDHero
import uuid
import asyncio
from server.logger import logger


class HeroService:
    def __init__(self):

        # In-memory structure to store heroes
        self.heroes_db: List[DnDHero] = []

        # Lock to handle concurrent access
        self.lock = asyncio.Lock()

    async def create_hero(self, hero: DnDHero) -> DnDHero:
        async with self.lock:
            hero.id = str(uuid.uuid4())
            self.heroes_db.append(hero)
            logger.info(f"Hero '{hero.name}' created with ID: {hero.id}")
            return hero

    async def get_hero(self, hero_id: str) -> Optional[DnDHero]:
        async with self.lock:
            hero = next((h for h in self.heroes_db if h.id == hero_id), None)
            if hero:
                logger.info(f"Hero '{hero_id}' retrieved.")
            else:
                logger.warning(f"Hero '{hero_id}' not found.")
            return hero

    async def list_heroes(self) -> List[DnDHero]:
        async with self.lock:
            logger.info(f"Listing all heroes. Total count: {len(self.heroes_db)}")
            return self.heroes_db.copy()

    async def delete_hero(self, hero_id: str) -> bool:
        async with self.lock:
            hero = next((h for h in self.heroes_db if h.id == hero_id), None)
            if hero:
                self.heroes_db.remove(hero)
                logger.info(f"Hero '{hero_id}' deleted.")
                return True
            else:
                logger.warning(f"Hero '{hero_id}' not found for deletion.")
                return False

    async def query_heroes_fireball_low_ac(self) -> List[DnDHero]:
        async with self.lock:
            results = [
                hero for hero in self.heroes_db
                if "Fireball" in hero.spells and hero.armor_class < 20
            ]
            logger.info(f"Found {len(results)} heroes with Fireball and AC < 20.")
            return results
