class_registry = {}

def register(name: str):
    def deco(cls):
        class_registry[name] = cls
        return cls
    return deco
