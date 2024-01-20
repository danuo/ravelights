from dataclasses import asdict, dataclass, field
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from ravelights.configs.components import Keywords
    from ravelights.core.generator_super import Generator
    from ravelights.effects.effect_super import Effect


@dataclass
class BlueprintGenNew:
    cls: type["Generator"]
    name: str
    weight: float | int = 1.0
    keywords: list["Keywords"] = field(default_factory=list)
    version: Optional[int] = 0


@dataclass
class BlueprintEffectNew:
    cls: type["Effect"]
    name: str


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
