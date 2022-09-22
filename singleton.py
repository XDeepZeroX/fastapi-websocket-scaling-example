class MetaSingleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        _args = '_'.join(map(str, args))
        _kwargs = ','.join(map(lambda item: f'{item[0]}={item[1]}', sorted(kwargs.items())))
        key = f'{cls.__module__}.{cls.__name__}___{_args}___{_kwargs}'.strip('_ ')

        if key not in cls._instances:
            cls._instances[key] = super(MetaSingleton, cls).__call__(*args, **kwargs)
        return cls._instances[key]