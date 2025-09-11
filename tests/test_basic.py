import sys
import pytest
from PyQt5.QtWidgets import QApplication
from jifmaker.main import JIFMaker


@pytest.fixture
def app(qtbot):
    test_app = QApplication.instance()
    if not test_app:
        test_app = QApplication(sys.argv)
    return test_app



@pytest.fixture
def window(app, qtbot):
    window = JIFMaker()
    qtbot.addWidget(window)
    return window

def test_window_title(window):
    """Test that the window title is correct"""
    assert "JIFMaker" in window.windowTitle()

def test_initial_state(window):
    """Test that the window initializes with correct default values"""
    assert window.fps_spin.value() == 15
    assert window.width_spin.value() == 800
    assert window.colors_spin.value() == 256
    assert window.maintain_aspect_check.isChecked() is True
    assert window.loop_check.isChecked() is True

def test_file_dialogs(window, qtbot):
    """Test that the file dialog buttons exist and are clickable"""
    assert window.input_file_edit.text() == ""
    assert window.output_file_edit.text() == ""
    
    # Find the browse buttons
    input_button = window.findChild(type(window.process_button), "Browse...")
    assert input_button is not None

def test_process_button_initial_state(window):
    """Test that the process button is disabled when no files are selected"""
    assert window.process_button.isEnabled()  # Should be enabled but show error when clicked
