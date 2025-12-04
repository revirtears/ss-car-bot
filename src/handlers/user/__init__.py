from .user import ClientHandlers
from .search import SearchHandlers
from .editfilters import EditFiltersHandlers


user_modules = [
    ClientHandlers,
    SearchHandlers,
    EditFiltersHandlers
]


__all__ = [
    'user_modules'
]
