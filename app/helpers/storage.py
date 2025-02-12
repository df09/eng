class Singleton:
    _instance, _initialized = None, False
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Storage, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        # code..
        self.hi = 'hi'
