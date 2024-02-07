from dataclasses import asdict, dataclass, field
from typing import TYPE_CHECKING, Any, Generic, Optional, TypeVar

if TYPE_CHECKING:
    from ravelights.configs.components import Keyword
    from ravelights.core.generator_super import Dimmer, Pattern, Thinner, Vfilter
    from ravelights.effects.effect_super import Effect


T = TypeVar("T", "Pattern", "Vfilter", "Dimmer", "Thinner")


@dataclass
class BlueprintGen(Generic[T]):
    cls: type[T]
    name: str
    weight: float | int = 1.0
    keywords: list["Keyword"] = field(default_factory=list)
    version: Optional[int] = 0

    def create_instance(self, kwargs: Optional[dict[str, Any]] = None) -> T:
        attributes = asdict(self)
        del attributes["cls"]
        instance: T = self.cls(**attributes, **kwargs)  # type: ignore[arg-type]
        return instance


@dataclass
class BlueprintEffect:
    cls: type["Effect"]
    name: str
    keywords: list["Keyword"] = field(default_factory=list)

    def create_instance(self, kwargs: Optional[dict[str, Any]] = None) -> "Effect":
        attributes = asdict(self)
        del attributes["cls"]
        return self.cls(**attributes, **kwargs)  # type: ignore[arg-type]
