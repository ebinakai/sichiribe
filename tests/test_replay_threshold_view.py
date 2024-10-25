import pytest
from unittest.mock import MagicMock, patch
from gui.views.replay_threshold_view import ReplayThresholdWindow
import numpy as np


@pytest.fixture(autouse=True)
def prevent_window_show():
    with patch('PySide6.QtWidgets.QWidget.show'):
        yield


@pytest.fixture
def window(qtbot):
    screen_manager = MagicMock()
    screen_manager.save_screen_size.return_value = (800, 600)
    window = ReplayThresholdWindow(screen_manager)
    qtbot.addWidget(window)
    window.show()
    window.startup({
        'first_frame': np.zeros((100, 100, 3), dtype=np.uint8),
        'click_points': [[10, 10], [90, 90], [10, 90], [90, 10]]
    })
    return window


def test_initial_ui_state(window):
    assert window.binarize_th.value() == 0
    assert window.binarize_th_label.text() == '自動設定'
    assert window.extracted_label.pixmap() is not None


def test_threshold_update(window):
    window.binarize_th.setValue(128)
    assert window.binarize_th_label.text() == '128'
    assert window.extracted_label.pixmap().isNull() == False


def test_next_button_action(window):
    window.binarize_th.setValue(150)
    window.next_button.click()

    window.screen_manager.get_screen.assert_called_with('replay_exe')
    args, kwargs = window.screen_manager.get_screen().frame_devide_process.call_args
    assert 'threshold' in args[0], 'Not found binarize_th in args'
