class StorageNotFoundError(Exception):
    def __init__(self, filename: str):
        super().__init__(f'File {filename} does not exist.')


class StorageSettedError(Exception):
    pass


class MismatchedVersionError(Exception):
    pass
