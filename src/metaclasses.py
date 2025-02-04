import weakref


class TransientSingleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        # Check if an instance already exists
        if cls in cls._instances:
            raise Exception(
                f"There was an attempt to create more than one simultaneous instance of {cls.__name__}."
            )

        # Create and register a new instance
        instance = super().__call__(*args, **kwargs)
        cls._instances[cls] = weakref.ref(
            instance, lambda ref: cls._instances.pop(cls, None)
        )

        # Dynamically inject the `deregister` method into the instance
        def deregister_as_singleton():
            type(instance).deregister()

        instance.deregister_as_singleton = deregister_as_singleton

        return instance

    def deregister(cls):
        """Manually deregister the instance."""
        if cls in cls._instances:
            cls._instances.pop(cls, None)
