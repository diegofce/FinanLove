import uuid
from dataclasses import dataclass

from app.application.ports import CategoryRepository
from app.domain.planning import Category


@dataclass(frozen=True)
class CreateCategoryCommand:
    owner_id: uuid.UUID
    name: str


class CreateCategory:
    def __init__(self, repository: CategoryRepository) -> None:
        self.repository = repository

    async def execute(self, command: CreateCategoryCommand) -> Category:
        return await self.repository.add(Category(uuid.uuid4(), **command.__dict__))


class ListCategories:
    def __init__(self, repository: CategoryRepository) -> None:
        self.repository = repository

    async def execute(self, owner_id: uuid.UUID) -> list[Category]:
        return await self.repository.list_by_owner(owner_id)
