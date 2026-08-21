from typing import List
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from src.rag.nashta_pillars import NASHTA_PILLARS

def get_emiten_keyboard(emitens: List[str]) -> InlineKeyboardMarkup:
    """Creates a grid keyboard for selecting an emiten."""
    keyboard = []
    row = []
    for emiten in emitens:
        row.append(InlineKeyboardButton(f"🏢 {emiten}", callback_data=f"emiten:{emiten}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    return InlineKeyboardMarkup(keyboard)

def get_emiten_menu_keyboard(emiten_code: str) -> InlineKeyboardMarkup:
    """Creates menu options for selected emiten."""
    keyboard = [
        [InlineKeyboardButton("📈 Tren Masalah 5 Tahun (Executive Summary)", callback_data=f"trend:{emiten_code}")],
        [InlineKeyboardButton("📊 Analisis Lengkap 10 Pilar", callback_data=f"full:{emiten_code}:0")],
        [InlineKeyboardButton("🎯 Pilih Pilar Tertentu", callback_data=f"pillars:{emiten_code}")],
        [InlineKeyboardButton("🔄 Ganti Emiten", callback_data="change_emiten")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_trend_keyboard(emiten_code: str) -> InlineKeyboardMarkup:
    """Keyboard for 5-year trend view."""
    keyboard = [
        [
            InlineKeyboardButton("📊 Analisis 10 Pilar", callback_data=f"full:{emiten_code}:0"),
            InlineKeyboardButton("🎯 Pilih Pilar", callback_data=f"pillars:{emiten_code}")
        ],
        [
            InlineKeyboardButton("🏠 Menu Emiten", callback_data=f"menu:{emiten_code}"),
            InlineKeyboardButton("🔄 Ganti Emiten", callback_data="change_emiten")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_pillars_grid_keyboard(emiten_code: str) -> InlineKeyboardMarkup:
    """Creates a grid of all 10 Nashta pillars."""
    keyboard = []
    row = []
    for p in NASHTA_PILLARS:
        btn_text = f"{p['icon']} {p['name']}"
        row.append(InlineKeyboardButton(btn_text, callback_data=f"pillar:{emiten_code}:{p['id']}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([
        InlineKeyboardButton("📈 Tren 5 Tahun", callback_data=f"trend:{emiten_code}"),
        InlineKeyboardButton("🏠 Menu Emiten", callback_data=f"menu:{emiten_code}")
    ])
    return InlineKeyboardMarkup(keyboard)

def get_pagination_keyboard(emiten_code: str, page: int, total_pages: int = 10) -> InlineKeyboardMarkup:
    """Creates pagination buttons for multi-pillar report (1 pillar per page)."""
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("⬅️ Sebelumnya", callback_data=f"full:{emiten_code}:{page-1}"))

    nav_row.append(InlineKeyboardButton(f"📄 Pilar {page+1}/{total_pages}", callback_data="noop"))

    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("Berikutnya ➡️", callback_data=f"full:{emiten_code}:{page+1}"))

    keyboard = [nav_row]
    keyboard.append([
        InlineKeyboardButton("📈 Tren 5 Tahun", callback_data=f"trend:{emiten_code}"),
        InlineKeyboardButton("🎯 Pilih Pilar", callback_data=f"pillars:{emiten_code}")
    ])
    keyboard.append([
        InlineKeyboardButton("🏠 Menu Emiten", callback_data=f"menu:{emiten_code}")
    ])
    return InlineKeyboardMarkup(keyboard)

def get_single_pillar_keyboard(emiten_code: str) -> InlineKeyboardMarkup:
    """Keyboard for single pillar view."""
    keyboard = [
        [
            InlineKeyboardButton("🎯 Pilih Pilar Lain", callback_data=f"pillars:{emiten_code}"),
            InlineKeyboardButton("📈 Tren 5 Tahun", callback_data=f"trend:{emiten_code}")
        ],
        [
            InlineKeyboardButton("🏠 Menu Emiten", callback_data=f"menu:{emiten_code}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
