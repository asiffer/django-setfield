import inspect
import logging
from functools import wraps
from typing import Callable


from .fields import SetField

log = logging.getLogger(__file__)
log.setLevel(logging.DEBUG)
# create console handler and set level to debug
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
# create formatter
formatter = logging.Formatter("[%(levelname)s] %(message)s")
# add formatter to ch
handler.setFormatter(formatter)
# add ch to logger
log.addHandler(handler)


def method_call_to_str(obj: object, fun: Callable, *args, **kwargs):
    args_list = list(map(str, args[1:]))
    kwargs_list = list(map(lambda item: f"{item[0]}={item[1]}", kwargs.items()))
    full_args = ", ".join(args_list + kwargs_list)
    return f"{obj}.{fun.__name__}({full_args})"


def hook_method(fun: Callable) -> Callable:
    @wraps(fun)
    def hook(*args, **kwargs):
        if len(args) <= 0:
            return fun(*args, **kwargs)
        obj = args[0]
        if not hasattr(obj, "__hook_level__"):
            return fun(*args, **kwargs)
        obj.__hook_level__ += 1

        prefix = " │   " * obj.__hook_level__
        log.debug(f"{prefix} ┌ {method_call_to_str(obj, fun, *args[1:], **kwargs)}")
        result = fun(*args, **kwargs)
        log.debug(f"{prefix} └ {result}")
        obj.__hook_level__ -= 1
        return result

    return hook


def hook_class(cls: type) -> type:
    """Decorator to hook all public methods of a class
    This is for debug purpose.
    """

    HookedClass = type(f"Debug{cls.__name__}", (cls,), {"__hook_level__": -1})
    HookedClass.__module__ = cls.__module__

    for method_name, method in inspect.getmembers(HookedClass, inspect.isfunction):
        if method_name.startswith("_") and method_name not in [
            "__init__",
            "__set__",
            "__setattr__",
        ]:
            continue
        setattr(HookedClass, method_name, hook_method(method))

    return HookedClass


DebugSetField = hook_class(SetField)
