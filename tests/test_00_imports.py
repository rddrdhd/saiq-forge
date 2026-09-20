def test_imports_succeed():
    import saiq_forge.cli  # noqa: F401
    import saiq_forge.config.loader  # noqa: F401
    import saiq_forge.config.validate  # noqa: F401
    import saiq_forge.detectors.statistical  # noqa: F401
    import saiq_forge.features.behavioral  # noqa: F401
    import saiq_forge.features.temporal  # noqa: F401
    import saiq_forge.features.windowing  # noqa: F401
    import saiq_forge.io.captures  # noqa: F401
    import saiq_forge.io.schema  # noqa: F401
    import saiq_forge.pipeline.orchestrator  # noqa: F401
    import saiq_forge.pipeline.tiering  # noqa: F401
