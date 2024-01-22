from dataclasses import InitVar, asdict, dataclass, field
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from ravelights.configs.components import Keywords
    from ravelights.core.generator_super import Generator
    from ravelights.effects.effect_super import Effect


@dataclass
class BlueprintGen:
    cls: InitVar[type["Generator"]]
    name: str
    weight: float | int = 1.0
    keywords: list["Keywords"] = field(default_factory=list)
    version: Optional[int] = 0

    def __post_init__(self, cls):
        self.cls = cls

    def create_instance(self, kwargs: Optional[dict[str, Any]] = None) -> "Generator":
        return self.cls(**asdict(self), **kwargs)


@dataclass
class BlueprintEffect:
    cls: InitVar[type["Effect"]]
    name: str
    keywords: list["Keywords"] = field(default_factory=list)

    def __post_init__(self, cls):
        self.cls = cls

    def create_instance(self, kwargs: Optional[dict[str, Any]] = None) -> "Effect":
        return self.cls(**asdict(self), **kwargs)
