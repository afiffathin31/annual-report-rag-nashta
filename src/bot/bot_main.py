import html
import asyncio
import logging
from typing import Dict
from telegram import Update, constants
from telegram.request import HTTPXRequest
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)
import config
from src.rag.engine import RAGEngine
from src.rag.trend_engine import TemporalTrendEngine, render_trend_html, render_trend_html_parts
from src.rag.nashta_pillars import NASHTA_PILLARS, PILLAR_DICT
from src.bot.keyboards import (
    get_emiten_keyboard,
    get_emiten_menu_keyboard,
    get_pillars_grid_keyboard,
    get_pagination_keyboard,
    get_single_pillar_keyboard,
    get_trend_keyboard
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("NashtaBot")

engine = RAGEngine()
trend_engine = TemporalTrendEngine()

def render_pillar_html(emiten_code: str, res: Dict, pillar_index: int = None, total_pillars: int = 10) -> str:
    """Format single pillar result with structured citation and solution points."""
    solutions_text = []
    sols = res.get("solutions", [])
    num_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
    for idx, s in enumerate(sols):
        emoji = num_emojis[idx] if idx < len(num_emojis) else f"{idx+1}."
        title = html.escape(s.get("title", f"Solusi {idx+1}"))
        desc = html.escape(s.get("description", ""))
        solutions_text.append(f"  {emoji} <b>{title}</b>\n     ↳ {desc}")

    sol_str = "\n\n".join(solutions_text) if solutions_text else "  • Konsultasi solusi Nashta."

    header_title = f"<b>{res['icon']} {html.escape(res['pillar_name'])}</b>"
    if pillar_index is not None:
        header_title = f"<b>{res['icon']} Pilar {pillar_index}/{total_pillars}: {html.escape(res['pillar_name'])}</b>"

    msg = (
        f"{header_title}\n"
        f"🏢 <b>Emiten:</b> <code>{emiten_code}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"⚠️ <b>KESIMPULAN MASALAH:</b>\n"
        f"{html.escape(res['problem_summary'])}\n\n"
        f"📖 <b>SUMBER / CITATION:</b>\n"
        f"📄 <b>Dokumen:</b> {html.escape(res.get('citation_doc', '-'))}\n"
        f"📑 <b>Lokasi:</b> {html.escape(res.get('citation_location', '-'))}\n"
        f"💬 <b>Kutipan Dokumen:</b>\n"
        f"<i>\"{html.escape(res.get('citation_quote', '-'))}\"</i>\n\n"
        f"💡 <b>REKOMENDASI SOLUSI NASHTA:</b>\n"
        f"{sol_str}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━"
    )

    if len(msg) > 3900:
        msg = msg[:3850] + "...\n\n<i>[Teks dipersingkat untuk batas pesan]</i>"

    return msg

async def safe_edit_or_reply(query, text: str, reply_markup=None):
    """Safely edit message text or fallback to sending a new message with length check."""
    if len(text) > 3950:
        text = text[:3900] + "...\n\n<i>[Teks terpotong karena batas tampilan]</i>"

    try:
        await query.edit_message_text(
            text=text,
            parse_mode=constants.ParseMode.HTML,
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.warning(f"edit_message_text warning ({e}), falling back to new reply message.")
        try:
            if query.message:
                await query.message.reply_text(
                    text=text,
                    parse_mode=constants.ParseMode.HTML,
                    reply_markup=reply_markup
                )
        except Exception as e2:
            logger.error(f"Fallback reply also failed: {e2}")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    emitens = await asyncio.to_thread(engine.vector_store.get_available_emitens)
    if not emitens:
        emitens = ["SIDO", "BANK", "KLBF", "HEAL", "CARE", "PDSB"]

    user_name = update.effective_user.first_name if update.effective_user else "User"

    msg = (
        f"👋 <b>Halo {html.escape(user_name)}!</b>\n\n"
        f"Selamat datang di <b>Nashta AI Advisory Assistant</b>.\n"
        f"Sistem ini menganalisis dokumen Laporan Tahunan resmi emiten (5 Tahun Terakhir) dan menyajikan diagnosis berbasis <b>10 Pilar Layanan Nashta</b>:\n"
        f"<i>1. Managed Service | 2. Hybrid Infra | 3. Business App | 4. Cyber Security | 5. Data & AI\n"
        f"6. Digital Platform | 7. IoT & Edge | 8. Consulting | 9. Cloud | 10. Bootcamp</i>\n\n"
        f"👉 <b>Silakan pilih Emiten yang ingin Anda analisis:</b>"
    )
    reply_markup = get_emiten_keyboard(emitens)

    if update.message:
        await update.message.reply_text(msg, parse_mode=constants.ParseMode.HTML, reply_markup=reply_markup)
    elif update.callback_query:
        await safe_edit_or_reply(update.callback_query, msg, reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_text = (
        "💡 <b>Panduan Penggunaan Bot Nashta:</b>\n\n"
        "1. <b>/start</b> - Memulai bot dan menampilkan pilihan emiten.\n"
        "2. <b>/emiten</b> - Mengganti emiten yang sedang aktif.\n"
        "3. <b>📈 Tren Masalah 5 Tahun</b> - Analisis ringkas evolusi masalah 5 tahun & Strategic Roadmap Nashta.\n"
        "4. <b>📊 Analisis Lengkap 10 Pilar</b> - Menghasilkan laporan lengkap untuk 10 pilar Nashta secara berurutan.\n"
        "5. <b>🎯 Pilih Pilar Tertentu</b> - Fokus diagnosis pada 1 pilar (misal: Cyber Security, Data & AI, dll).\n"
        "6. <b>💬 Tanya Jawab Bebas (Q&A)</b> - Anda dapat langsung mengetikkan pertanyaan bebas tentang emiten aktif di chat ini!\n\n"
        "<i>Setiap analisis menyertakan: Ringkasan Masalah, Citation Terstruktur (Dokumen, Halaman, Kutipan Asli), dan Solusi Nashta.</i>"
    )
    if update.message:
        await update.message.reply_text(help_text, parse_mode=constants.ParseMode.HTML)

async def emiten_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /emiten command."""
    await start_command(update, context)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all button callback queries."""
    query = update.callback_query
    if not query:
        return

    try:
        await query.answer()
    except Exception as e:
        logger.warning(f"query.answer() ignored: {e}")

    data = query.data
    user_id = query.from_user.id

    if data == "noop":
        return

    if data == "change_emiten":
        emitens = await asyncio.to_thread(engine.vector_store.get_available_emitens)
        if not emitens:
            emitens = ["SIDO", "BANK", "KLBF", "HEAL", "CARE", "PDSB"]
        msg = "🏢 <b>Silakan pilih Emiten yang ingin Anda analisis:</b>"
        await safe_edit_or_reply(query, msg, reply_markup=get_emiten_keyboard(emitens))
        return

    if data.startswith("emiten:"):
        emiten_code = data.split(":")[1].upper()
        await asyncio.to_thread(engine.set_user_emiten, user_id, emiten_code)

        msg = (
            f"🏢 <b>Emiten Terpilih: {emiten_code}</b>\n"
            f"📄 <i>Basis Data: Laporan Tahunan Resmi 5 Tahun Terakhir</i>\n\n"
            f"Silakan pilih menu analisis di bawah, atau langsung <b>ketikkan pertanyaan Anda</b> di chat untuk berdiskusi dengan AI:"
        )
        await safe_edit_or_reply(query, msg, reply_markup=get_emiten_menu_keyboard(emiten_code))
        return

    if data.startswith("menu:"):
        emiten_code = data.split(":")[1].upper()
        msg = (
            f"🏢 <b>Menu Emiten: {emiten_code}</b>\n\n"
            f"Silakan pilih mode analisis atau ajukan pertanyaan bebas di chat:"
        )
        await safe_edit_or_reply(query, msg, reply_markup=get_emiten_menu_keyboard(emiten_code))
        return

    if data.startswith("trend:"):
        emiten_code = data.split(":")[1].upper()
        await safe_edit_or_reply(
            query,
            f"⏳ <i>Sedang menyusun <b>Executive Brief & Roadmap 5 Tahun ({emiten_code})</b>...</i>"
        )

        trend_result = await asyncio.to_thread(trend_engine.analyze_5_year_trend, emiten_code)
        parts = render_trend_html_parts(emiten_code, trend_result)

        if len(parts) == 1:
            await safe_edit_or_reply(query, parts[0], reply_markup=get_trend_keyboard(emiten_code))
        else:
            # Edit current message with Part 1 (Evolusi Tren & Root Cause Issues)
            await safe_edit_or_reply(query, parts[0])
            # Send Part 2 (Strategic Roadmap Solusi Nashta 3-Fase) with the navigation keyboard
            if query.message:
                await query.message.reply_text(
                    parts[1],
                    parse_mode=constants.ParseMode.HTML,
                    reply_markup=get_trend_keyboard(emiten_code)
                )
        return

    if data.startswith("pillars:"):
        emiten_code = data.split(":")[1].upper()
        msg = (
            f"🎯 <b>Pilih Pilar Layanan Nashta untuk {emiten_code}:</b>\n\n"
            f"Klik salah satu dari 10 pilar di bawah untuk melihat diagnosis spesifik:"
        )
        await safe_edit_or_reply(query, msg, reply_markup=get_pillars_grid_keyboard(emiten_code))
        return

    if data.startswith("pillar:"):
        _, emiten_code, pillar_id = data.split(":")
        emiten_code = emiten_code.upper()
        pillar_meta = PILLAR_DICT.get(pillar_id, {"name": pillar_id, "icon": "📌"})

        await safe_edit_or_reply(
            query,
            f"⏳ <i>Sedang menganalisis pilar <b>{pillar_meta.get('name', pillar_id)}</b> untuk <b>{emiten_code}</b>...</i>"
        )

        result = await asyncio.to_thread(engine.analyze_single_pillar, emiten_code, pillar_id)
        msg = render_pillar_html(emiten_code, result)
        await safe_edit_or_reply(query, msg, reply_markup=get_single_pillar_keyboard(emiten_code))
        return

    if data.startswith("full:"):
        parts = data.split(":")
        emiten_code = parts[1].upper()
        page = int(parts[2]) if len(parts) > 2 else 0

        total_pillars = len(NASHTA_PILLARS)
        if page < 0 or page >= total_pillars:
            page = 0

        target_pillar = NASHTA_PILLARS[page]

        await safe_edit_or_reply(
            query,
            f"⏳ <i>Sedang menyusun diagnosis <b>Pilar {page+1}/{total_pillars} ({target_pillar['name']})</b> untuk <b>{emiten_code}</b>...</i>"
        )

        res = await asyncio.to_thread(engine.analyze_single_pillar, emiten_code, target_pillar["id"])
        full_text = render_pillar_html(emiten_code, res, pillar_index=page+1, total_pillars=total_pillars)

        reply_markup = get_pagination_keyboard(emiten_code, page, total_pages=total_pillars)
        await safe_edit_or_reply(query, full_text, reply_markup=reply_markup)
        return

def markdown_to_telegram_html(text: str) -> str:
    """Converts LLM Markdown into valid, beautiful Telegram HTML without raw symbols."""
    if not text:
        return ""

    lines = text.split("\n")
    processed_lines = []

    for line in lines:
        stripped = line.strip()

        # Skip table divider |---|---|
        if re.match(r"^\|?(\s*:?-+:?\s*\|)+\s*$", stripped):
            continue

        # Convert horizontal rules --- or ***
        if stripped in ["---", "***", "___"]:
            processed_lines.append("━━━━━━━━━━━━━━━━━━━━━━")
            continue

        # Convert headers ### Header -> 📌 <b>Header</b>
        header_match = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if header_match:
            header_text = header_match.group(2)
            safe_hdr = html.escape(header_text)
            safe_hdr = re.sub(r"\*\*(.*?)\*\*", r"\1", safe_hdr)
            processed_lines.append(f"\n📌 <b>{safe_hdr}</b>")
            continue

        # Convert table row | Col1 | Col2 | Col3 | to bullet points
        if stripped.startswith("|") and stripped.endswith("|") and stripped.count("|") >= 3:
            cols = [c.strip() for c in stripped.split("|")[1:-1]]
            if any(cols):
                col_str = "  ↳  ".join(c for c in cols if c)
                escaped_col = html.escape(col_str)
                escaped_col = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", escaped_col)
                processed_lines.append(f"  • {escaped_col}")
                continue

        # Escape HTML entities first
        escaped_line = html.escape(line)

        # Convert `code`
        escaped_line = re.sub(r"`(.*?)`", r"<code>\1</code>", escaped_line)

        # Convert **bold** -> <b>bold</b>
        escaped_line = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", escaped_line)

        # Convert *italic* or _italic_
        escaped_line = re.sub(r"(?<!\w)\*(.*?)\*(?!\w)", r"<i>\1</i>", escaped_line)
        escaped_line = re.sub(r"(?<!\w)_(.*?)_(?!\w)", r"<i>\1</i>", escaped_line)

        processed_lines.append(escaped_line)

    res = "\n".join(processed_lines)
    return re.sub(r"\n{3,}", "\n\n", res).strip()

async def send_long_chat_message(update: Update, raw_text: str, emiten_code: str):
    """Sends converted HTML response in logical untruncated chunks without raw symbols."""
    # Convert Markdown to Telegram HTML
    text = markdown_to_telegram_html(raw_text)

    footer = (
        f"\n\n━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏢 <i>Emiten: {emiten_code} | /emiten (ganti) | /reset (hapus riwayat chat)</i>"
    )

    # Check if single message is within safe length (<3800 chars)
    if len(text) + len(footer) < 3800:
        full_msg = f"🤖 <b>Analisis Advisory untuk {emiten_code}:</b>\n\n{text}{footer}"
        try:
            await update.message.reply_text(full_msg, parse_mode=constants.ParseMode.HTML)
        except Exception:
            clean_plain = re.sub(r"<[^>]+>", "", full_msg)
            await update.message.reply_text(clean_plain)
        return

    # If message is long, split by double newlines into chunks (<3400 chars each)
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = []
    current_len = 0

    for p in paragraphs:
        if current_len + len(p) + 2 > 3400 and current_chunk:
            chunks.append("\n\n".join(current_chunk))
            current_chunk = [p]
            current_len = len(p)
        else:
            current_chunk.append(p)
            current_len += len(p) + 2

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    total_chunks = len(chunks)
    for idx, chunk in enumerate(chunks, 1):
        header = f"🤖 <b>Analisis Advisory untuk {emiten_code} (Bagian {idx}/{total_chunks}):</b>\n\n"
        msg_to_send = f"{header}{chunk}"
        if idx == total_chunks:
            msg_to_send += footer

        try:
            await update.message.reply_text(msg_to_send, parse_mode=constants.ParseMode.HTML)
        except Exception:
            clean_plain = re.sub(r"<[^>]+>", "", msg_to_send)
            await update.message.reply_text(clean_plain)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle free-form user text messages / Q&A."""
    if not update.message or not update.message.text:
        return

    user_id = update.effective_user.id
    user_query = update.message.text.strip()

    emiten_code = await asyncio.to_thread(engine.get_user_emiten, user_id)
    if not emiten_code:
        emitens = await asyncio.to_thread(engine.vector_store.get_available_emitens)
        if not emitens:
            emitens = ["SIDO", "BANK", "KLBF", "HEAL", "CARE", "PDSB"]
        msg = (
            "⚠️ <b>Anda belum memilih emiten.</b>\n\n"
            "Silakan pilih emiten terlebih dahulu agar kami dapat menjawab berdasarkan dokumen resmi perusahaan:"
        )
        await update.message.reply_text(msg, parse_mode=constants.ParseMode.HTML, reply_markup=get_emiten_keyboard(emitens))
        return

    # Send Typing Action
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=constants.ChatAction.TYPING)

    # Process Query in background worker thread with persistent multi-turn chat memory
    response_text = await asyncio.to_thread(engine.answer_free_query, emiten_code, user_query, user_id)

    # Send untruncated message
    await send_long_chat_message(update, response_text, emiten_code)

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /reset command to clear conversational memory."""
    user_id = update.effective_user.id
    emiten_code = await asyncio.to_thread(engine.get_user_emiten, user_id)
    if emiten_code:
        await asyncio.to_thread(engine.db_manager.clear_chat_history, user_id, emiten_code)
        msg = f"🧹 <b>Riwayat percakapan untuk emiten {emiten_code} telah direset.</b>\nAnda dapat memulai diskusi baru!"
    else:
        msg = "ℹ️ Tidak ada emiten aktif. Silakan pilih emiten dengan /emiten."

    if update.message:
        await update.message.reply_text(msg, parse_mode=constants.ParseMode.HTML)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Log errors caused by updates."""
    logger.error(msg="Exception while handling update:", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ <i>Maaf, terjadi kendala teknis sementara. Silakan coba kembali atau ketik /start.</i>",
                parse_mode=constants.ParseMode.HTML
            )
        except Exception:
            pass

def run_bot():
    """Start the Telegram bot with resilient timeout settings and auto-reconnect."""
    token = config.TELEGRAM_BOT_TOKEN
    print(f"Starting Telegram Bot with token prefix: {token[:10]}...")

    while True:
        try:
            request_client = HTTPXRequest(
                connection_pool_size=16,
                read_timeout=60.0,
                write_timeout=60.0,
                connect_timeout=60.0,
                pool_timeout=60.0,
            )

            app = (
                ApplicationBuilder()
                .token(token)
                .request(request_client)
                .concurrent_updates(True)
                .build()
            )

            app.add_handler(CommandHandler("start", start_command))
            app.add_handler(CommandHandler("help", help_command))
            app.add_handler(CommandHandler("emiten", emiten_command))
            app.add_handler(CommandHandler("reset", reset_command))
            app.add_handler(CallbackQueryHandler(handle_callback))
            app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
            app.add_error_handler(error_handler)

            print("Bot is polling for updates with concurrent execution. Press Ctrl+C to stop.")
            app.run_polling(drop_pending_updates=True, close_loop=False)
        except (KeyboardInterrupt, SystemExit):
            print("Bot stopped by user.")
            break
        except Exception as e:
            logger.error(f"Bot polling exception ({e}), restarting polling in 3 seconds...")
            import time
            time.sleep(3)

if __name__ == "__main__":
    run_bot()
