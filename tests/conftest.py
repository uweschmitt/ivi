import pytest

@pytest.fixture(scope="module")
def here():
    import os.path
    return os.path.dirname(os.path.abspath(__file__))

@pytest.fixture(scope="module")
def data_path():
    import os.path
    def inner(path, _here=here()):
        return os.path.join(_here, "data", path)
    return inner
