import sys
import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QRect, QPoint
from ui.island import DynamicIsland


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_island_properties_and_fullscreen_topmost(qapp):
    island = DynamicIsland()
    assert island.island_height == 44
    assert island.current_width == 280

    geo = island.get_target_screen_geometry()
    assert isinstance(geo, QRect)
    assert geo.width() > 0
    assert geo.height() > 0

    # Ensure target_y and hidden_y are calculated relative to screen_geo
    assert island.target_y == island.screen_geo.y() + island.target_y_offset
    assert island.hidden_y == island.screen_geo.y() + island.hidden_y_offset

    # Ensure force_on_top executes cleanly without raising any exceptions
    island.force_on_top()

    # Ensure watchdog runs safely
    island._enforce_topmost_if_visible()

    island.close()
