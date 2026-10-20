from dataclasses import dataclass, field


@dataclass(slots=True)
class Entity:
    id: int | None = field(default=None, init=True)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Entity) or type(self) is not type(other):
            return False
        if self.id is None or other.id is None:
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash((type(self), self.id))
