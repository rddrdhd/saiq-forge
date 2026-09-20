_DETECTORS = {}


def register(class_name, method):
    key = (class_name, method)

    def decorator(cls):
        _DETECTORS[key] = cls
        return cls
    return decorator


def get_detector(class_name, method):
    try:
        return _DETECTORS[(class_name, method)]
    except KeyError:
        raise KeyError(
            f"no detector registered for {class_name}.{method} "
            f"(known: {sorted(_DETECTORS)})"
        )
