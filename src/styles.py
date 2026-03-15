"""
QSS Stylesheet for FreeCAD Agent UI

A modern dark theme designed for CAD workflows with:
- Professional dark color scheme optimized for long sessions
- Clear visual hierarchy with accent colors
- Smooth hover and focus transitions
- Proper spacing and readability
"""

# =============================================================================
# COLOR PALETTE
# =============================================================================
# Background colors
PRIMARY_BG = "#1e1e1e"  # Main window background
SECONDARY_BG = "#252526"  # Panel backgrounds
TERTIARY_BG = "#2d2d2d"  # Input field backgrounds
SURFACE_BG = "#333333"  # Elevated surfaces

# Text colors
PRIMARY_TEXT = "#d4d4d4"  # Main text
SECONDARY_TEXT = "#9d9d9d"  # Secondary/muted text
PLACEHOLDER_TEXT = "#6e6e6e"  # Placeholder text

# Accent colors
ACCENT_BLUE = "#0078d4"  # Primary actions (Send)
ACCENT_BLUE_HOVER = "#1a8cde"  # Primary hover
ACCENT_GREEN = "#4ec9b0"  # Success/Good actions
ACCENT_GREEN_HOVER = "#5fd9c0"  # Success hover
ACCENT_RED = "#f14c4c"  # Danger/Poor actions
ACCENT_RED_HOVER = "#ff6666"  # Danger hover
ACCENT_ORANGE = "#ce9178"  # Warning/secondary actions
ACCENT_ORANGE_HOVER = "#e0a088"  # Warning hover
ACCENT_PURPLE = "#c586c0"  # Special actions

# Border colors
BORDER_DEFAULT = "#3c3c3c"
BORDER_FOCUS = "#0078d4"
BORDER_HOVER = "#555555"

# =============================================================================
# QSS STYLESHEET
# =============================================================================

QSS = f"""
/* ==========================================================================
   BASE WIDGET STYLES
   ========================================================================== */

QWidget {{
    background-color: {PRIMARY_BG};
    color: {PRIMARY_TEXT};
    font-family: "Segoe UI", "Ubuntu", "Sans Serif";
    font-size: 10pt;
    selection-background-color: {ACCENT_BLUE};
    selection-color: #ffffff;
}}

/* ==========================================================================
   LABELS
   ========================================================================== */

QLabel {{
    background-color: transparent;
    color: {SECONDARY_TEXT};
    padding: 4px 0px;
    font-weight: 500;
}}

QLabel[heading="true"] {{
    color: {PRIMARY_TEXT};
    font-size: 11pt;
    font-weight: 600;
    padding: 8px 0px 4px 0px;
}}

/* ==========================================================================
   TEXT EDIT (Input/Output Areas)
   ========================================================================== */

QTextEdit, QPlainTextEdit {{
    background-color: {TERTIARY_BG};
    color: {PRIMARY_TEXT};
    border: 1px solid {BORDER_DEFAULT};
    border-radius: 6px;
    padding: 10px;
    selection-background-color: {ACCENT_BLUE};
    selection-color: #ffffff;
}}

QTextEdit:focus, QPlainTextEdit:focus {{
    border: 1px solid {BORDER_FOCUS};
}}

QTextEdit:disabled, QPlainTextEdit:disabled {{
    background-color: {SECONDARY_BG};
    color: {PLACEHOLDER_TEXT};
}}

QTextEdit[readOnly="true"] {{
    background-color: {SECONDARY_BG};
}}

/* Placeholder text */
QTextEdit::placeholder, QPlainTextEdit::placeholder {{
    color: {PLACEHOLDER_TEXT};
}}

/* Scrollbar for text areas */
QTextEdit QScrollBar:vertical, QPlainTextEdit QScrollBar:vertical {{
    background: {TERTIARY_BG};
    width: 12px;
    border-radius: 6px;
}}

QTextEdit QScrollBar::handle:vertical, QPlainTextEdit QScrollBar::handle:vertical {{
    background: {BORDER_HOVER};
    border-radius: 5px;
    min-height: 30px;
    margin: 2px;
}}

QTextEdit QScrollBar::handle:vertical:hover, QPlainTextEdit QScrollBar::handle:vertical:hover {{
    background: {ACCENT_BLUE};
}}

QTextEdit QScrollBar::add-line:vertical, QPlainTextEdit QScrollBar::add-line:vertical {{
    height: 0px;
}}

QTextEdit QScrollBar::sub-line:vertical, QPlainTextEdit QScrollBar::sub-line:vertical {{
    height: 0px;
}}

/* ==========================================================================
   PUSH BUTTONS
   ========================================================================== */

QPushButton {{
    background-color: {SURFACE_BG};
    color: {PRIMARY_TEXT};
    border: 1px solid {BORDER_DEFAULT};
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 500;
    min-height: 24px;
}}

QPushButton:hover {{
    background-color: {BORDER_HOVER};
    border-color: {BORDER_HOVER};
}}

QPushButton:pressed {{
    background-color: {TERTIARY_BG};
    border-color: {BORDER_DEFAULT};
}}

QPushButton:disabled {{
    background-color: {SECONDARY_BG};
    color: {PLACEHOLDER_TEXT};
    border-color: {BORDER_DEFAULT};
}}

QPushButton:focus {{
    border: 1px solid {ACCENT_BLUE};
    outline: none;
}}

/* Primary Action Button (Send) */
QPushButton#submit_button,
QPushButton[primary="true"] {{
    background-color: {ACCENT_BLUE};
    color: #ffffff;
    border: 1px solid {ACCENT_BLUE};
    font-weight: 600;
}}

QPushButton#submit_button:hover,
QPushButton[primary="true"]:hover {{
    background-color: {ACCENT_BLUE_HOVER};
    border-color: {ACCENT_BLUE_HOVER};
}}

QPushButton#submit_button:pressed,
QPushButton[primary="true"]:pressed {{
    background-color: #005a9e;
    border-color: #005a9e;
}}

/* Success Button (Good) */
QPushButton#confirm_button,
QPushButton[success="true"] {{
    background-color: {ACCENT_GREEN};
    color: #1e1e1e;
    border: 1px solid {ACCENT_GREEN};
    font-weight: 600;
}}

QPushButton#confirm_button:hover,
QPushButton[success="true"]:hover {{
    background-color: {ACCENT_GREEN_HOVER};
    border-color: {ACCENT_GREEN_HOVER};
}}

/* Danger Button (Poor) */
QPushButton#reject_button,
QPushButton[danger="true"] {{
    background-color: {ACCENT_RED};
    color: #ffffff;
    border: 1px solid {ACCENT_RED};
    font-weight: 600;
}}

QPushButton#reject_button:hover,
QPushButton[danger="true"]:hover {{
    background-color: {ACCENT_RED_HOVER};
    border-color: {ACCENT_RED_HOVER};
}}

/* Secondary Action Buttons */
QPushButton#reset_model_button,
QPushButton#run_manual_button {{
    background-color: {ACCENT_ORANGE};
    color: #1e1e1e;
    border: 1px solid {ACCENT_ORANGE};
    font-weight: 500;
}}

QPushButton#reset_model_button:hover,
QPushButton#run_manual_button:hover {{
    background-color: {ACCENT_ORANGE_HOVER};
    border-color: {ACCENT_ORANGE_HOVER};
}}

/* Icon Buttons (smaller, more compact) */
QPushButton#record_button,
QPushButton#load_prompt_button,
QPushButton#image_button,
QPushButton#clean_manual_button,
QPushButton#save_macro_button {{
    padding: 6px 12px;
    min-width: 70px;
}}

/* ==========================================================================
   COMBOBOX (Dropdowns)
   ========================================================================== */

QComboBox {{
    background-color: {TERTIARY_BG};
    color: {PRIMARY_TEXT};
    border: 1px solid {BORDER_DEFAULT};
    border-radius: 6px;
    padding: 8px 12px;
    min-height: 20px;
}}

QComboBox:hover {{
    border-color: {BORDER_HOVER};
}}

QComboBox:focus {{
    border: 1px solid {ACCENT_BLUE};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {SECONDARY_TEXT};
    margin-right: 8px;
}}

QComboBox QAbstractItemView {{
    background-color: {SECONDARY_BG};
    color: {PRIMARY_TEXT};
    border: 1px solid {BORDER_DEFAULT};
    border-radius: 6px;
    selection-background-color: {ACCENT_BLUE};
    selection-color: #ffffff;
    padding: 4px;
}}

QComboBox QAbstractItemView::item {{
    padding: 8px 12px;
    border-radius: 4px;
}}

QComboBox QAbstractItemView::item:hover {{
    background-color: {SURFACE_BG};
}}

/* ==========================================================================
   DOCK WIDGET (Panel Container)
   ========================================================================== */

QDockWidget {{
    background-color: {PRIMARY_BG};
    titlebar-normal-icon: url(none);
    titlebar-close-icon: url(none);
}}

QDockWidget::title {{
    background-color: {SECONDARY_BG};
    color: {PRIMARY_TEXT};
    padding: 8px;
    border-bottom: 1px solid {BORDER_DEFAULT};
}}

QDockWidget QWidget {{
    background-color: {PRIMARY_BG};
}}

/* ==========================================================================
   LAYOUT SPACING
   ========================================================================== */

QVBoxLayout, QHBoxLayout {{
    spacing: 8px;
    margin: 8px;
}}

/* ==========================================================================
   SCROLLBAR (Global)
   ========================================================================== */

QScrollBar:vertical {{
    background: {SECONDARY_BG};
    width: 12px;
    border-radius: 6px;
}}

QScrollBar::handle:vertical {{
    background: {BORDER_HOVER};
    border-radius: 5px;
    min-height: 30px;
    margin: 2px;
}}

QScrollBar::handle:vertical:hover {{
    background: {ACCENT_BLUE};
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background: {SECONDARY_BG};
    height: 12px;
    border-radius: 6px;
}}

QScrollBar::handle:horizontal {{
    background: {BORDER_HOVER};
    border-radius: 5px;
    min-width: 30px;
    margin: 2px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {ACCENT_BLUE};
}}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* ==========================================================================
   FILE DIALOG
   ========================================================================== */

QFileDialog {{
    background-color: {PRIMARY_BG};
}}

QFileDialog QLabel {{
    color: {PRIMARY_TEXT};
}}

QFileDialog QPushButton {{
    background-color: {SURFACE_BG};
    border: 1px solid {BORDER_DEFAULT};
    border-radius: 6px;
    padding: 8px 16px;
}}

QFileDialog QPushButton[primary="true"] {{
    background-color: {ACCENT_BLUE};
    color: #ffffff;
    border-color: {ACCENT_BLUE};
}}

/* ==========================================================================
   MESSAGE BOX
   ========================================================================== */

QMessageBox {{
    background-color: {PRIMARY_BG};
}}

QMessageBox QLabel {{
    color: {PRIMARY_TEXT};
    font-size: 10pt;
}}

QMessageBox QPushButton {{
    background-color: {SURFACE_BG};
    border: 1px solid {BORDER_DEFAULT};
    border-radius: 6px;
    padding: 8px 20px;
    min-width: 80px;
}}

QMessageBox QPushButton[default="true"] {{
    background-color: {ACCENT_BLUE};
    color: #ffffff;
    border-color: {ACCENT_BLUE};
}}

/* ==========================================================================
   TOOLTIP
   ========================================================================== */

QToolTip {{
    background-color: {SECONDARY_BG};
    color: {PRIMARY_TEXT};
    border: 1px solid {BORDER_DEFAULT};
    border-radius: 4px;
    padding: 6px 10px;
}}

"""


# =============================================================================
# HELPER FUNCTION TO APPLY STYLESHEET
# =============================================================================


def get_stylesheet():
    """
    Returns the complete QSS stylesheet string.

    Usage:
        from src.styles import get_stylesheet
        app.setStyleSheet(get_stylesheet())

        # Or for a specific widget:
        widget.setStyleSheet(get_stylesheet())
    """
    return QSS


def apply_stylesheet(widget):
    """
    Applies the stylesheet to a Qt widget.

    Args:
        widget: A QWidget or QApplication instance

    Returns:
        bool: True if stylesheet was applied successfully
    """
    if widget is None:
        return False

    try:
        widget.setStyleSheet(QSS)
        return True
    except Exception as e:
        print(f"Failed to apply stylesheet: {e}")
        return False


def apply_to_app(app):
    """
    Applies the stylesheet to a QApplication instance.

    Args:
        app: QApplication instance

    Returns:
        bool: True if stylesheet was applied successfully
    """
    if app is None:
        return False

    try:
        app.setStyleSheet(QSS)
        return True
    except Exception as e:
        print(f"Failed to apply stylesheet to app: {e}")
        return False


# =============================================================================
# COLOR UTILITIES (Optional - for programmatic access)
# =============================================================================


class Colors:
    """Color constants for programmatic access if needed."""

    PRIMARY_BG = PRIMARY_BG
    SECONDARY_BG = SECONDARY_BG
    TERTIARY_BG = TERTIARY_BG
    SURFACE_BG = SURFACE_BG

    PRIMARY_TEXT = PRIMARY_TEXT
    SECONDARY_TEXT = SECONDARY_TEXT
    PLACEHOLDER_TEXT = PLACEHOLDER_TEXT

    ACCENT_BLUE = ACCENT_BLUE
    ACCENT_GREEN = ACCENT_GREEN
    ACCENT_RED = ACCENT_RED
    ACCENT_ORANGE = ACCENT_ORANGE
    ACCENT_PURPLE = ACCENT_PURPLE

    BORDER_DEFAULT = BORDER_DEFAULT
    BORDER_FOCUS = BORDER_FOCUS
    BORDER_HOVER = BORDER_HOVER


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    # Example: How to use in your FreeCAD plugin
    """
    # In your FreeCADAgent.py:
    
    from src.styles import apply_stylesheet
    from PySide2 import QtWidgets
    
    # After creating your QApplication or widget:
    class CADAssistantPanel(QtWidgets.QWidget):
        def __init__(self):
            super().__init__()
            # ... your existing setup code ...
            
            # Apply the dark theme
            apply_stylesheet(self)
    
    # Or apply to the entire application:
    # from src.styles import apply_to_app
    # apply_to_app(QtWidgets.QApplication.instance())
    """
    print("QSS Stylesheet loaded successfully!")
    print("Use get_stylesheet() to get the stylesheet string.")
    print("Use apply_stylesheet(widget) to apply to a widget.")
