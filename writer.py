class SimpleWriter:
    def __init__(self, path: str) -> None:
        self.file = open(path, 'wb')

    def write(self, data: bytes) -> None:
        self.file.write(data)

    def __del__(self) -> None:
        self.file.close()
        self.file = None
