"""
Centralized stylesheets for the HET simulator GUI.

Light professional theme.
Design tokens kept here as a single source of truth so all panels stay consistent.
"""

# ──────────────────────────────────────────────────────────────
# Design tokens
# ──────────────────────────────────────────────────────────────

# Surfaces
COLOR_BG_APP        = "#f4f5f7"   # main window background
COLOR_BG_SURFACE    = "#ffffff"   # panels, group boxes
COLOR_BG_SIDEBAR    = "#1f2933"   # vertical navigation sidebar (dark contrast bar)
COLOR_BG_VIEWER     = "#fafbfc"   # 3D viewer frame background
COLOR_BG_SUBTLE     = "#f1f3f5"   # hover row, disabled
COLOR_BG_ELEV       = "#ffffff"   # raised surface (cards)

# Text
COLOR_TEXT_PRIMARY    = "#1f2937"
COLOR_TEXT_SECONDARY  = "#6b7280"
COLOR_TEXT_ON_DARK    = "#f9fafb"
COLOR_TEXT_MUTED      = "#9ca3af"
COLOR_TEXT_DISABLED   = "#c4cad1"

# Brand / accents
COLOR_ACCENT          = "#2563eb"  # primary blue
COLOR_ACCENT_HOVER    = "#1d4ed8"
COLOR_ACCENT_PRESSED  = "#1e40af"
COLOR_ACCENT_SOFT     = "#dbeafe"

# Semantic
COLOR_DANGER          = "#dc2626"
COLOR_SUCCESS         = "#16a34a"
COLOR_WARNING         = "#d97706"

# Borders
COLOR_BORDER          = "#e5e7eb"
COLOR_BORDER_STRONG   = "#d1d5db"
COLOR_BORDER_FOCUS    = "#93c5fd"

# Typography
FONT_FAMILY = "'Inter', 'Segoe UI', 'Helvetica Neue', Arial, sans-serif"
FONT_SIZE_CAPTION = "11px"
FONT_SIZE_BODY    = "13px"
FONT_SIZE_LABEL   = "13px"
FONT_SIZE_TITLE   = "14px"

# Radius
RADIUS_SM = "4px"
RADIUS_MD = "6px"
RADIUS_LG = "8px"


# ──────────────────────────────────────────────────────────────
# Global application stylesheet (applied on QMainWindow)
# ──────────────────────────────────────────────────────────────
def self_Style() -> str:
    return f"""
        QWidget {{
            font-family: {FONT_FAMILY};
            font-size: {FONT_SIZE_BODY};
            color: {COLOR_TEXT_PRIMARY};
        }}

        QMainWindow {{
            background-color: {COLOR_BG_APP};
        }}

        QLabel {{
            color: {COLOR_TEXT_PRIMARY};
            background: transparent;
        }}

        QGroupBox {{
            background-color: {COLOR_BG_SURFACE};
            border: 1px solid {COLOR_BORDER};
            border-radius: {RADIUS_LG};
            margin-top: 16px;
            padding: 18px 14px 14px 14px;
            font-weight: 600;
            font-size: {FONT_SIZE_TITLE};
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 14px;
            padding: 0 6px;
            color: {COLOR_TEXT_PRIMARY};
            background-color: {COLOR_BG_SURFACE};
        }}

        QLineEdit, QDoubleSpinBox, QSpinBox {{
            background-color: {COLOR_BG_SURFACE};
            color: {COLOR_TEXT_PRIMARY};
            border: 1px solid {COLOR_BORDER};
            padding: 6px 10px;
            border-radius: {RADIUS_SM};
            selection-background-color: {COLOR_ACCENT_SOFT};
            selection-color: {COLOR_TEXT_PRIMARY};
            min-height: 22px;
            font-size: {FONT_SIZE_BODY};
        }}

        QLineEdit:hover, QDoubleSpinBox:hover, QSpinBox:hover {{
            border-color: {COLOR_BORDER_STRONG};
        }}

        QLineEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus {{
            border: 1px solid {COLOR_ACCENT};
            background-color: {COLOR_BG_SURFACE};
        }}

        QLineEdit:disabled, QDoubleSpinBox:disabled, QSpinBox:disabled {{
            background-color: {COLOR_BG_SUBTLE};
            color: {COLOR_TEXT_DISABLED};
            border-color: {COLOR_BORDER};
        }}

        QDoubleSpinBox::up-button, QSpinBox::up-button,
        QDoubleSpinBox::down-button, QSpinBox::down-button {{
            background: transparent;
            border: none;
            width: 16px;
        }}
        QDoubleSpinBox::up-button:hover, QSpinBox::up-button:hover,
        QDoubleSpinBox::down-button:hover, QSpinBox::down-button:hover {{
            background-color: {COLOR_BG_SUBTLE};
        }}

        QFrame#VPartFrame {{
            background-color: {COLOR_BG_VIEWER};
            border-left: 1px solid {COLOR_BORDER};
            border-radius: 0px;
        }}

        QToolTip {{
            background-color: {COLOR_TEXT_PRIMARY};
            color: {COLOR_TEXT_ON_DARK};
            border: none;
            padding: 4px 8px;
            border-radius: {RADIUS_SM};
            font-size: {FONT_SIZE_CAPTION};
        }}

        QScrollBar:vertical {{
            background: transparent;
            width: 10px;
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background: {COLOR_BORDER_STRONG};
            border-radius: 5px;
            min-height: 20px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {COLOR_TEXT_MUTED};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}

        QProgressBar {{
            background-color: {COLOR_BG_SUBTLE};
            border: 1px solid {COLOR_BORDER};
            border-radius: {RADIUS_SM};
            text-align: center;
            color: {COLOR_TEXT_SECONDARY};
            min-height: 6px;
            max-height: 8px;
        }}
        QProgressBar::chunk {{
            background-color: {COLOR_ACCENT};
            border-radius: {RADIUS_SM};
        }}
    """


# ──────────────────────────────────────────────────────────────
# Buttons
# ──────────────────────────────────────────────────────────────
def button_parameters_style() -> str:
    """Primary action button (e.g. Update, Run, Apply)."""
    return f"""
        QPushButton {{
            background-color: {COLOR_ACCENT};
            color: #ffffff;
            font-weight: 600;
            font-size: {FONT_SIZE_BODY};
            padding: 7px 14px;
            border-radius: {RADIUS_SM};
            border: 1px solid {COLOR_ACCENT};
            min-height: 18px;
        }}
        QPushButton:hover {{
            background-color: {COLOR_ACCENT_HOVER};
            border-color: {COLOR_ACCENT_HOVER};
        }}
        QPushButton:pressed {{
            background-color: {COLOR_ACCENT_PRESSED};
            border-color: {COLOR_ACCENT_PRESSED};
        }}
        QPushButton:disabled {{
            background-color: {COLOR_BG_SUBTLE};
            color: {COLOR_TEXT_DISABLED};
            border: 1px solid {COLOR_BORDER};
        }}
    """


def button_secondary_style() -> str:
    """Secondary / neutral action."""
    return f"""
        QPushButton {{
            background-color: {COLOR_BG_SURFACE};
            color: {COLOR_TEXT_PRIMARY};
            font-weight: 500;
            font-size: {FONT_SIZE_BODY};
            padding: 7px 14px;
            border-radius: {RADIUS_SM};
            border: 1px solid {COLOR_BORDER_STRONG};
        }}
        QPushButton:hover {{
            background-color: {COLOR_BG_SUBTLE};
            border-color: {COLOR_TEXT_MUTED};
        }}
        QPushButton:pressed {{
            background-color: {COLOR_BORDER};
        }}
        QPushButton:disabled {{
            background-color: {COLOR_BG_SUBTLE};
            color: {COLOR_TEXT_DISABLED};
        }}
    """


def button_activate_style() -> str:
    """Vertical sidebar tab — active (selected) state."""
    return f"""
        QPushButton {{
            background-color: {COLOR_ACCENT};
            color: #ffffff;
            font-size: {FONT_SIZE_CAPTION};
            font-weight: 600;
            border: none;
            border-radius: {RADIUS_MD};
            padding: 10px 6px;
            text-align: center;
        }}
        QPushButton:hover {{
            background-color: {COLOR_ACCENT_HOVER};
        }}
    """


def button_options_style() -> str:
    """Vertical sidebar tab — idle state."""
    return f"""
        QPushButton {{
            background-color: transparent;
            color: {COLOR_TEXT_ON_DARK};
            font-size: {FONT_SIZE_CAPTION};
            font-weight: 500;
            border: none;
            border-radius: {RADIUS_MD};
            padding: 10px 6px;
            text-align: center;
        }}
        QPushButton:hover {{
            background-color: rgba(255, 255, 255, 0.08);
            color: #ffffff;
        }}
        QPushButton:pressed {{
            background-color: rgba(255, 255, 255, 0.04);
        }}
        QPushButton:disabled {{
            color: {COLOR_TEXT_MUTED};
        }}
    """


# ──────────────────────────────────────────────────────────────
# Form controls
# ──────────────────────────────────────────────────────────────
def box_render_style() -> str:
    """QComboBox styling (also re-used on some QGroupBox — harmless)."""
    return f"""
        QComboBox {{
            background-color: {COLOR_BG_SURFACE};
            color: {COLOR_TEXT_PRIMARY};
            border: 1px solid {COLOR_BORDER};
            border-radius: {RADIUS_SM};
            padding: 5px 8px;
            min-height: 18px;
        }}
        QComboBox:hover {{
            border-color: {COLOR_TEXT_MUTED};
        }}
        QComboBox:focus {{
            border-color: {COLOR_ACCENT};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {COLOR_BG_SURFACE};
            color: {COLOR_TEXT_PRIMARY};
            selection-background-color: {COLOR_ACCENT_SOFT};
            selection-color: {COLOR_TEXT_PRIMARY};
            border: 1px solid {COLOR_BORDER};
            outline: 0;
        }}

        QGroupBox {{
            background-color: {COLOR_BG_SURFACE};
            border: 1px solid {COLOR_BORDER};
            border-radius: {RADIUS_MD};
            margin-top: 14px;
            padding: 12px 10px 10px 10px;
            font-weight: 600;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 10px;
            padding: 0 6px;
            color: {COLOR_TEXT_PRIMARY};
            background-color: {COLOR_BG_SURFACE};
        }}
    """


def checkbox_style() -> str:
    return f"""
        QCheckBox {{
            spacing: 8px;
            color: {COLOR_TEXT_PRIMARY};
            font-weight: 500;
            background: transparent;
        }}
        QCheckBox::indicator {{
            width: 16px;
            height: 16px;
            border: 1px solid {COLOR_BORDER_STRONG};
            border-radius: {RADIUS_SM};
            background: {COLOR_BG_SURFACE};
        }}
        QCheckBox::indicator:checked {{
            background-color: {COLOR_ACCENT};
            border: 1px solid {COLOR_ACCENT};
            image: url(:/qt-project.org/styles/commonstyle/images/checkbox_checked.png);
        }}
        QCheckBox::indicator:hover {{
            border: 1px solid {COLOR_ACCENT};
        }}
        QCheckBox::indicator:disabled {{
            background-color: {COLOR_BG_SUBTLE};
            border: 1px solid {COLOR_BORDER};
        }}
    """


def checkbox_parameters_style() -> str:
    return checkbox_style()


# ──────────────────────────────────────────────────────────────
# Collapsible "Advanced options" panel
# ──────────────────────────────────────────────────────────────
def advanced_toggle_style() -> str:
    return f"""
        QPushButton {{
            background-color: {COLOR_BG_SUBTLE};
            color: {COLOR_TEXT_PRIMARY};
            border: 1px solid {COLOR_BORDER};
            font-weight: 600;
            text-align: left;
            padding: 8px 12px;
            border-radius: {RADIUS_SM};
        }}
        QPushButton:hover {{
            background-color: {COLOR_BG_SURFACE};
            border-color: {COLOR_BORDER_STRONG};
        }}
        QPushButton:checked {{
            background-color: {COLOR_ACCENT_SOFT};
            border-color: {COLOR_ACCENT};
            color: {COLOR_ACCENT_HOVER};
        }}
    """


def advanced_content_style() -> str:
    return f"""
        QFrame {{
            background-color: {COLOR_BG_SURFACE};
            color: {COLOR_TEXT_PRIMARY};
            border: 1px solid {COLOR_BORDER};
            border-radius: {RADIUS_SM};
            padding: 10px;
        }}
    """


# ──────────────────────────────────────────────────────────────
# Reusable shared QMessageBox style
# ──────────────────────────────────────────────────────────────
def messagebox_style() -> str:
    return f"""
        QMessageBox {{
            background-color: {COLOR_BG_SURFACE};
            color: {COLOR_TEXT_PRIMARY};
            font-family: {FONT_FAMILY};
        }}
        QMessageBox QLabel {{
            color: {COLOR_TEXT_PRIMARY};
            font-size: {FONT_SIZE_BODY};
            min-width: 380px;
            padding: 6px 8px;
            line-height: 150%;
        }}
        QMessageBox QPushButton {{
            background-color: {COLOR_ACCENT};
            color: #ffffff;
            border: 1px solid {COLOR_ACCENT};
            border-radius: {RADIUS_MD};
            padding: 8px 22px;
            min-width: 88px;
            font-weight: 600;
            font-size: {FONT_SIZE_BODY};
        }}
        QMessageBox QPushButton:hover {{
            background-color: {COLOR_ACCENT_HOVER};
            border-color: {COLOR_ACCENT_HOVER};
        }}
        QMessageBox QPushButton:pressed {{
            background-color: {COLOR_ACCENT_PRESSED};
        }}
        QMessageBox QPushButton:default {{
            background-color: {COLOR_ACCENT};
        }}
    """


def alert_banner_style(level: str = "warning") -> str:
    """Inline banner card (non-modal alert) — used at the top of panels."""
    palettes = {
        "warning": {"bg": "#fff7ed", "border": "#f59e0b", "title": "#7c2d12", "body": "#92400e"},
        "info":    {"bg": "#eff6ff", "border": "#2563eb", "title": "#1e3a8a", "body": "#1d4ed8"},
        "success": {"bg": "#ecfdf5", "border": "#16a34a", "title": "#14532d", "body": "#166534"},
        "danger":  {"bg": "#fef2f2", "border": "#dc2626", "title": "#7f1d1d", "body": "#b91c1c"},
    }
    p = palettes.get(level, palettes["warning"])
    return f"""
        QFrame#AlertBanner {{
            background-color: {p["bg"]};
            border: 1px solid {p["border"]};
            border-left: 4px solid {p["border"]};
            border-radius: {RADIUS_MD};
        }}
        QLabel#AlertTitle {{
            color: {p["title"]};
            font-weight: 700;
            font-size: 13px;
            background: transparent;
            border: none;
        }}
        QLabel#AlertBody {{
            color: {p["body"]};
            font-size: 12px;
            background: transparent;
            border: none;
        }}
        QLabel#AlertIcon {{
            background: transparent;
            border: none;
        }}
    """


def input_unit_chip_style() -> str:
    return f"""
        QLabel#UnitChip {{
            background-color: {COLOR_BG_SUBTLE};
            color: {COLOR_TEXT_SECONDARY};
            border: 1px solid {COLOR_BORDER};
            border-radius: {RADIUS_SM};
            padding: 3px 8px;
            font-size: 11px;
            font-weight: 600;
            margin-left: 6px;
        }}
    """


# ──────────────────────────────────────────────────────────────
# Panel / surface helpers
# ──────────────────────────────────────────────────────────────
def parameters_panel_style() -> str:
    return f"""
        QFrame {{
            background-color: {COLOR_BG_APP};
            border-right: 1px solid {COLOR_BORDER};
        }}
        QStackedWidget#Parameters_Views {{
            background-color: {COLOR_BG_APP};
            border: none;
        }}
    """


def options_panel_style() -> str:
    return f"""
        QFrame {{
            background-color: {COLOR_BG_SIDEBAR};
            border-right: 1px solid {COLOR_BORDER};
        }}
    """


def viewer_frame_style() -> str:
    return f"""
        background-color: {COLOR_BG_VIEWER};
        border: 1px solid {COLOR_BORDER};
        border-radius: {RADIUS_MD};
    """
