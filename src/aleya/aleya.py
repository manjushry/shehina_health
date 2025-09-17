class Aleya:
    """
    Clase base genérica para gestión de contextos en frameworks de datos y grafos.
    Permite manejar múltiples configuraciones, DataFrames y objetos complejos.

    Ejemplo de uso:
    >>> alc = Aleya()
    >>> alc.set_config({'db': 'postgresql'})
    >>> alc.set_data(my_dataframe)
    >>> alc.set_context(my_context)
    """
    __version__ = "1.0.0"
    def __init__(self):
        self.config = None
        self.data = None
        self.context = None

    def set_config(self, config):
        self.config = config

    def get_config(self):
        return self.config

    def set_data(self, data):
        self.data = data

    def get_data(self):
        return self.data

    def set_context(self, context):
        self.context = context

    def get_context(self):
        return self.context
