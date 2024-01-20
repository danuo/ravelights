from dataclasses import InitVar, asdict, dataclass, field
from typing import TYPE_CHECKING, Any, Optional, TypeVar

if TYPE_CHECKING:
    from ravelights.configs.components import Keywords
    from ravelights.core.generator_super import Generator
    from ravelights.effects.effect_super import Effect


T = TypeVar("T")


class BlueprintNew:
    cls: type[T]

    def create_instance(self, kwargs: Optional[dict[str, Any]] = None) -> T:
        return self.cls(**asdict(self), **kwargs)


@dataclass
class BlueprintGenNew(BlueprintNew):
    cls: InitVar[type["Generator"]]
    name: str
    weight: float | int = 1.0
    keywords: list["Keywords"] = field(default_factory=list)
    version: Optional[int] = 0

    def __post_init__(self, cls):
        self.cls = cls

    # def create_instance(self, kwargs: Optional[dict[str, Any]] = None) -> "Generator":
    #     return create_instance(self, kwargs)


@dataclass
class BlueprintEffectNew(BlueprintNew):
    cls: InitVar[type["Effect"]]
    name: str

    def __post_init__(self, cls):
        self.cls = cls


def create_from_blueprint_new(blueprints, kwargs: Optional[dict[str, Any]] = None) -> Any:
    if kwargs is None:
        kwargs = dict()
    items = []
    for blueprint in blueprints:
        cls = blueprint.cls
        args = asdict(blueprint)
        del args["cls"]
        items.append(cls(**args, **kwargs))
    return items
