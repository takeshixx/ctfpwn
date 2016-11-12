import sys


__all__ = []


class LazyImporter:
    def __init__(self, m):
        self.__attribs = {}
        self.__wrapped_module = m

    def add(self, submodule, name):
        self.__attribs[name] = submodule
        getattr(self, '__all__').append(name)

    def __getattr__(self, name):
        try:
            return getattr(self.__wrapped_module, name)
        except AttributeError:
            pass

        try:
            module = self.__attribs[name]
        except KeyError:
            raise AttributeError(name)

        import importlib
        module = importlib.import_module(module, __name__)
        attrib = getattr(module, name)
        setattr(self, name, attrib)
        return attrib


wrapper = sys.modules[__name__] = LazyImporter(sys.modules[__name__])
wrapper.add('.api', 'run_api')
wrapper.add('.exploitservice', 'run_exploitservice')
wrapper.add('.flagservice', 'run_flagservice')
wrapper.add('.targets', 'run_targetservice')
del wrapper  # remove wrapper reference
del LazyImporter
