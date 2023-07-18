from typing import TYPE_CHECKING, Annotated, AnyStr, Dict, Literal, Optional, TypeVar, Union

import numpy as np
import numpy.typing as npt

if TYPE_CHECKING:
    from ravelights.configs.components import BlueprintEffect, BlueprintGen, BlueprintPlace, BlueprintSel
    from ravelights.core.pixelmatrix import PixelMatrix
    from ravelights.core.settings import Settings

T_ALL = Union[str, float, int, bool]
T_JSON = Dict[str, T_ALL]
T_BLUEPRINTS = list["BlueprintGen"] | list["BlueprintEffect"] | list["BlueprintSel"] | list["BlueprintPlace"]

# todo: implement new types
ArrayNx1 = Annotated[npt.NDArray[np.float_], Literal["N", 1]]  # n, 1
ArrayLx1 = Annotated[npt.NDArray[np.float_], Literal["L", 1]]  # n_leds, 1
ArrayNx3 = Annotated[npt.NDArray[np.float_], Literal["N", 3]]  # n, 3
ArrayMxKx3 = Annotated[npt.NDArray[np.float_], Literal["M", "K", 3]]  # n_leds, n_lights, 3
Array = TypeVar("Array", ArrayNx1, ArrayLx1, ArrayNx3, ArrayMxKx3)
