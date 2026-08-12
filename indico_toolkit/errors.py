class ToolkitError(Exception):
    pass


class ToolkitInputError(ToolkitError):
    def __init__(self, msg: str):
        super().__init__(msg)


class ToolkitInstantiationError(ToolkitError):
    def __init__(self, msg: str):
        super().__init__(msg)
