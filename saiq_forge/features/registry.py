_EXTRACTORS = {}


def register(modality):
    def decorator(cls):
        _EXTRACTORS[modality] = cls
        return cls
    return decorator


def get_extractor(modality):
    try:
        return _EXTRACTORS[modality]
    except KeyError:
        raise KeyError(
            f"no feature extractor registered for modality {modality!r} "
            f"(known: {sorted(_EXTRACTORS)})"
        )


def available_modalities():
    return set(_EXTRACTORS)
