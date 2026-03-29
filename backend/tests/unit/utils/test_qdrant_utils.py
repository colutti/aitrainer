from types import SimpleNamespace
from unittest.mock import Mock

from src.utils.qdrant_utils import point_to_dict, scroll_all_user_points


def test_point_to_dict_falls_back_to_point_id_and_data_payload():
    point = SimpleNamespace(
        id="abc123",
        payload={"data": "remember this", "translations": {"pt-BR": "lembre disto"}, "user_id": "u-1"},
    )
    assert point_to_dict(point) == {
        "id": "abc123",
        "memory": "remember this",
        "translations": {"pt-BR": "lembre disto"},
        "user_id": "u-1",
        "created_at": None,
        "updated_at": None,
    }


def test_scroll_all_user_points_keeps_scrolling_until_offset_is_none():
    client = Mock()
    client.scroll.side_effect = [
        ([SimpleNamespace(id="1", payload={})], "next"),
        ([SimpleNamespace(id="2", payload={})], None),
    ]

    result = scroll_all_user_points(client, "memories", Mock())

    assert [point.id for point in result] == ["1", "2"]
    assert client.scroll.call_count == 2
