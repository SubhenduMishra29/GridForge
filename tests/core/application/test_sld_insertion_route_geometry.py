from types import SimpleNamespace

import pytest

from core.application.errors import ValidationError
from core.application.services.sld_service import SLDService


def _old_connection():
    return SimpleNamespace(
        properties={"connection_kind": "SIMPLE_WIRE"},
        route=SimpleNamespace(points=((50.0, 0.0),)),
    )


def _nodes():
    # The SLD node centres are deliberately different from the rendered
    # terminal-anchor endpoints carried by the insertion hit snapshot.
    return (
        SimpleNamespace(x=0.0, y=0.0),
        SimpleNamespace(x=100.0, y=0.0),
    )


def _rendered_route():
    return {
        "source": (0.0, 20.0),
        "target": (100.0, 20.0),
        "points": ((50.0, 20.0),),
    }


def test_insertion_validation_uses_the_exact_rendered_route_snapshot():
    source_node, target_node = _nodes()

    position = SLDService._validate_insertion_geometry(
        connection_id="wire-1",
        old_connection=_old_connection(),
        source_node=source_node,
        target_node=target_node,
        insertion_position=(25.0, 20.0),
        segment_index=0,
        route_geometry=_rendered_route(),
    )

    assert position == (25.0, 20.0)


def test_insertion_validation_rejects_a_segment_index_from_another_route():
    source_node, target_node = _nodes()

    with pytest.raises(ValidationError):
        SLDService._validate_insertion_geometry(
            connection_id="wire-1",
            old_connection=_old_connection(),
            source_node=source_node,
            target_node=target_node,
            insertion_position=(25.0, 20.0),
            segment_index=1,
            route_geometry=_rendered_route(),
        )
