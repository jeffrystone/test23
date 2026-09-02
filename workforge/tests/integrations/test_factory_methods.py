from src import container as ct
from src.common.services.filter_service import FilterService


def test_getting_filter_service():
    filter_service = ct.get_filter_service()
    assert isinstance(filter_service, FilterService)
