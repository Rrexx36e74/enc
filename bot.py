"""
ALL-IN-ONE HARD ENCODER - Telegram Bot
Developer: REV77
Library: python-telegram-bot v20+

Install:
    pip install python-telegram-bot aiohttp aiofiles

Run:
    python bot.py
"""

import asyncio
import base64
import io
import os
import sys
import time
import urllib.parse
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# ─────────────────────────────────────────────
#  TOKEN — dibaca dari environment variable
#  Set di Railway: BOT_TOKEN = <token kamu>
# ─────────────────────────────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
if not BOT_TOKEN:
    print("ERROR: Environment variable BOT_TOKEN belum diset!")
    sys.exit(1)

# ─────────────────────────────────────────────
#  STATE KEY (disimpan per user di context.user_data)
# ─────────────────────────────────────────────
KEY_STEP        = "step"
KEY_CODE_TYPE   = "code_type"
KEY_ENC_LEVEL   = "enc_level"

STEP_IDLE       = "idle"
STEP_WAIT_CODE  = "wait_code"

# ─────────────────────────────────────────────
#  MAPPING
# ─────────────────────────────────────────────
EXTENSIONS = {
    "html":       "html",
    "javascript": "js",
    "python":     "py",
    "php":        "php",
    "css":        "css",
    "cpp":        "cpp",
    "java":       "java",
    "csharp":     "cs",
    "ruby":       "rb",
    "sql":        "sql",
}

LEVEL_LAYERS = {
    "hard":    4,
    "slow":    3,
    "extreme": 6,
}

LEVEL_LABELS = {
    "hard":    "HARD (4 Layers)",
    "slow":    "SLOW (3 Layers)",
    "extreme": "EXTREME (6 Layers)",
}

CODE_TYPE_LABELS = {
    "html":       "HTML",
    "javascript": "JavaScript",
    "python":     "Python",
    "php":        "PHP",
    "css":        "CSS",
    "cpp":        "C++",
    "java":       "Java",
    "csharp":     "C#",
    "ruby":       "Ruby",
    "sql":        "SQL",
}

# ══════════════════════════════════════════════
#  ENCRYPTION LOGIC  (identik dengan web asli)
# ══════════════════════════════════════════════

def b64_encode(s: str) -> str:
    """btoa(unescape(encodeURIComponent(s))) — safe unicode → base64"""
    return base64.b64encode(s.encode("utf-8")).decode("ascii")

def encrypt_hard(raw: str) -> str:
    """4 layers — identik encryptHard() di web"""
    # Layer 1: base64(utf-8)
    layer1 = b64_encode(raw)

    # Layer 2: chunk setiap 30 char lalu base64 lagi, gabung dengan '|'
    chunks = [
        base64.b64encode(layer1[i:i+30].encode("ascii")).decode("ascii")
        for i in range(0, len(layer1), 30)
    ]
    layer2 = "|".join(chunks)

    # Layer 3: base64 dari layer2
    layer3 = base64.b64encode(layer2.encode("ascii")).decode("ascii")

    # Layer 4: URL encode
    layer4 = urllib.parse.quote(layer3, safe="")
    return layer4


def encrypt_slow(raw: str) -> str:
    """3 layers — identik encryptSlow() di web"""
    # Layer 1
    layer1 = b64_encode(raw)
    # Layer 2
    layer2 = base64.b64encode(layer1.encode("ascii")).decode("ascii")
    # Layer 3
    layer3 = urllib.parse.quote(layer2, safe="")
    return layer3


def encrypt_extreme(raw: str) -> str:
    """6 layers — identik encryptExtreme() di web"""
    # Layer 1: base64
    layer1 = b64_encode(raw)

    # Layer 2: reverse string
    layer2 = layer1[::-1]

    # Layer 3: chunk setiap 20 char lalu base64, gabung dengan '|'
    chunks = [
        base64.b64encode(layer2[i:i+20].encode("ascii")).decode("ascii")
        for i in range(0, len(layer2), 20)
    ]
    layer3 = "|".join(chunks)

    # Layer 4: base64
    layer4 = base64.b64encode(layer3.encode("ascii")).decode("ascii")

    # Layer 5: character shifting +1
    layer5 = "".join(chr(ord(c) + 1) for c in layer4)

    # Layer 6: URI encode
    layer6 = urllib.parse.quote(layer5, safe="")
    return layer6


# ══════════════════════════════════════════════
#  OUTPUT TEMPLATE GENERATOR (identik web asli)
# ══════════════════════════════════════════════

def gen_js_decryption_script(enc_data: str, layers: int) -> str:
    if layers == 3:
        return (
            f'let e="{enc_data}";\n'
            'let d=decodeURIComponent(e);\n'
            'let c=atob(atob(d));\n'
            'let b=decodeURIComponent(escape(c));'
        )
    elif layers == 4:
        return (
            f'let e="{enc_data}";\n'
            'let d=decodeURIComponent(e);\n'
            'let c=atob(d);\n'
            'let b=c.split("|").map(x=>atob(x)).join("");\n'
            'let a=decodeURIComponent(escape(atob(b)));'
        )
    else:  # 6
        return (
            f'let e="{enc_data}";\n'
            'let d=decodeURIComponent(e);\n'
            "let c='';\n"
            "for(let i=0;i<d.length;i++){c+=String.fromCharCode(d.charCodeAt(i)-1);}\n"
            'let b=atob(c);\n'
            'let a=b.split("|").map(x=>atob(x)).join("");\n'
            'a=a.split("").reverse().join("");\n'
            'a=decodeURIComponent(escape(atob(a)));'
        )


def gen_python_decryption_script(enc_data: str, layers: int) -> str:
    if layers == 3:
        return (
            "import base64\nimport urllib.parse\n\n"
            f'e = "{enc_data}"\n'
            "d = urllib.parse.unquote(e)\n"
            "c = base64.b64decode(base64.b64decode(d)).decode('utf-8')\n"
            "decrypted_code = c"
        )
    elif layers == 4:
        return (
            "import base64\nimport urllib.parse\n\n"
            f'e = "{enc_data}"\n'
            "d = urllib.parse.unquote(e)\n"
            "c = base64.b64decode(d).decode('utf-8')\n"
            "b = ''.join([base64.b64decode(chunk).decode('utf-8') for chunk in c.split('|')])\n"
            "decrypted_code = base64.b64decode(b).decode('utf-8')"
        )
    else:  # 6
        return (
            "import base64\nimport urllib.parse\n\n"
            f'e = "{enc_data}"\n'
            "d = urllib.parse.unquote(e)\n"
            "c = ''.join([chr(ord(char) - 1) for char in d])\n"
            "b = base64.b64decode(c).decode('utf-8')\n"
            "a = ''.join([base64.b64decode(chunk).decode('utf-8') for chunk in b.split('|')])\n"
            "decrypted_code = base64.b64decode(a[::-1]).decode('utf-8')"
        )


def gen_php_decryption_script(enc_data: str, layers: int) -> str:
    if layers == 3:
        return (
            f'$e = "{enc_data}";\n'
            "$d = urldecode($e);\n"
            "$c = base64_decode(base64_decode($d));\n"
            "$decrypted = $c;"
        )
    elif layers == 4:
        return (
            f'$e = "{enc_data}";\n'
            "$d = urldecode($e);\n"
            "$c = base64_decode($d);\n"
            "$chunks = explode('|', $c);\n"
            "$b = '';\n"
            "foreach($chunks as $chunk) {\n"
            "    $b .= base64_decode($chunk);\n"
            "}\n"
            "$decrypted = base64_decode($b);"
        )
    else:  # 6
        return (
            f'$e = "{enc_data}";\n'
            "$d = urldecode($e);\n"
            "$c = '';\n"
            "for($i = 0; $i < strlen($d); $i++) {\n"
            "    $c .= chr(ord($d[$i]) - 1);\n"
            "}\n"
            "$b = base64_decode($c);\n"
            "$chunks = explode('|', $b);\n"
            "$a = '';\n"
            "foreach($chunks as $chunk) {\n"
            "    $a .= base64_decode($chunk);\n"
            "}\n"
            "$decrypted = base64_decode(strrev($a));"
        )


def generate_output(code_type: str, enc_data: str, layers: int) -> str:
    """Identik generateOutputTemplate() di web asli"""
    if code_type == "html":
        js_script = gen_js_decryption_script(enc_data, layers)
        return (
            '<!DOCTYPE html>\n<html>\n<head>\n<meta charset="UTF-8">\n'
            '<title>Protected Content</title>\n</head>\n<body>\n<script>\n'
            f'{js_script}\n'
            'document.write(a);\n'
            '</script>\n</body>\n</html>'
        )
    elif code_type == "javascript":
        js_script = gen_js_decryption_script(enc_data, layers)
        return (
            "// Encrypted JavaScript Code\n"
            f"{js_script}\n"
            "// Execute decrypted code\n"
            "eval(a);"
        )
    elif code_type == "python":
        py_script = gen_python_decryption_script(enc_data, layers)
        return (
            "# Encrypted Python Code\n"
            f"{py_script}\n\n"
            "# Execute decrypted code\n"
            "exec(decrypted_code)"
        )
    elif code_type == "php":
        php_script = gen_php_decryption_script(enc_data, layers)
        return (
            "<?php\n// Encrypted PHP Code\n"
            f"{php_script}\n\n"
            "// Execute decrypted code\n"
            "eval($decrypted);\n?>"
        )
    else:
        # CSS, C++, Java, C#, Ruby, SQL — pakai JS wrapper generic
        js_script = gen_js_decryption_script(enc_data, layers)
        return (
            f"// Encrypted {code_type.upper()} Code\n"
            f"{js_script}\n"
            "// Execute decrypted code\n"
            "eval(a);"
        )


def run_encryption(raw: str, enc_level: str) -> str:
    """Jalankan encryption sesuai level yang dipilih"""
    if enc_level == "hard":
        return encrypt_hard(raw)
    elif enc_level == "slow":
        return encrypt_slow(raw)
    elif enc_level == "extreme":
        return encrypt_extreme(raw)
    return encrypt_hard(raw)


# ══════════════════════════════════════════════
#  KEYBOARD BUILDERS
# ══════════════════════════════════════════════

def keyboard_code_type() -> InlineKeyboardMarkup:
    types = list(CODE_TYPE_LABELS.items())
    rows = []
    for i in range(0, len(types), 2):
        row = []
        for key, label in types[i:i+2]:
            row.append(InlineKeyboardButton(label, callback_data=f"ct_{key}"))
        rows.append(row)
    return InlineKeyboardMarkup(rows)


def keyboard_enc_level() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton("🔒 HARD (4 Layers)",    callback_data="el_hard")],
        [InlineKeyboardButton("🐢 SLOW (3 Layers)",    callback_data="el_slow")],
        [InlineKeyboardButton("💀 EXTREME (6 Layers)", callback_data="el_extreme")],
    ]
    return InlineKeyboardMarkup(rows)


def keyboard_cancel() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("❌ Cancel / Reset", callback_data="cancel")
    ]])


# ══════════════════════════════════════════════
#  HANDLERS
# ══════════════════════════════════════════════

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    ctx.user_data[KEY_STEP] = STEP_IDLE

    await update.message.reply_text(
        "🔐 *ALL-IN-ONE HARD ENCODER*\n"
        "_Developer by REV77 — Very Hard Encryption_\n\n"
        "Pilih *CODE TYPE* terlebih dahulu:",
        parse_mode="Markdown",
        reply_markup=keyboard_code_type(),
    )


async def cb_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # ── Cancel / Reset ──────────────────────────────────────────
    if data == "cancel":
        ctx.user_data.clear()
        ctx.user_data[KEY_STEP] = STEP_IDLE
        await query.edit_message_text(
            "❌ Dibatalkan. Ketik /start untuk memulai lagi.",
        )
        return

    # ── Pilih CODE TYPE ─────────────────────────────────────────
    if data.startswith("ct_"):
        code_type = data[3:]
        ctx.user_data[KEY_CODE_TYPE] = code_type
        label = CODE_TYPE_LABELS.get(code_type, code_type.upper())

        await query.edit_message_text(
            f"✅ Code Type: *{label}*\n\n"
            "Pilih *ENCRYPTION LEVEL*:",
            parse_mode="Markdown",
            reply_markup=keyboard_enc_level(),
        )
        return

    # ── Pilih ENCRYPTION LEVEL ──────────────────────────────────
    if data.startswith("el_"):
        enc_level = data[3:]
        ctx.user_data[KEY_ENC_LEVEL] = enc_level
        ctx.user_data[KEY_STEP] = STEP_WAIT_CODE

        code_type = ctx.user_data.get(KEY_CODE_TYPE, "?")
        ct_label   = CODE_TYPE_LABELS.get(code_type, code_type.upper())
        el_label   = LEVEL_LABELS.get(enc_level, enc_level.upper())
        layers     = LEVEL_LAYERS[enc_level]

        await query.edit_message_text(
            f"✅ Code Type: *{ct_label}*\n"
            f"✅ Level: *{el_label}* ({layers} layers)\n\n"
            "Sekarang kirimkan kode yang ingin dienkripsi:\n"
            "• Ketik/paste langsung sebagai *teks*\n"
            "• Atau kirim sebagai *file*",
            parse_mode="Markdown",
            reply_markup=keyboard_cancel(),
        )
        return


async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if ctx.user_data.get(KEY_STEP) != STEP_WAIT_CODE:
        await update.message.reply_text(
            "Ketik /start untuk memulai enkripsi.",
        )
        return

    raw = update.message.text.strip()
    if not raw:
        await update.message.reply_text("⚠️ Kode tidak boleh kosong!")
        return

    await process_and_send(update, ctx, raw)


async def handle_file(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if ctx.user_data.get(KEY_STEP) != STEP_WAIT_CODE:
        await update.message.reply_text(
            "Ketik /start untuk memulai enkripsi.",
        )
        return

    doc = update.message.document
    if not doc:
        await update.message.reply_text("⚠️ File tidak ditemukan.")
        return

    # Download file
    wait_msg = await update.message.reply_text("⏳ Mengunduh file...")
    file_obj = await doc.get_file()
    buf = await file_obj.download_as_bytearray()

    try:
        raw = buf.decode("utf-8")
    except UnicodeDecodeError:
        await wait_msg.delete()
        await update.message.reply_text(
            "⚠️ File harus berupa teks (UTF-8). Binary file tidak didukung."
        )
        return

    await wait_msg.delete()
    await process_and_send(update, ctx, raw)


async def process_and_send(
    update: Update, ctx: ContextTypes.DEFAULT_TYPE, raw: str
):
    code_type  = ctx.user_data.get(KEY_CODE_TYPE, "html")
    enc_level  = ctx.user_data.get(KEY_ENC_LEVEL, "hard")
    layers     = LEVEL_LAYERS[enc_level]
    ext        = EXTENSIONS.get(code_type, "txt")
    ct_label   = CODE_TYPE_LABELS.get(code_type, code_type.upper())
    el_label   = LEVEL_LABELS.get(enc_level, enc_level.upper())

    processing_msg = await update.message.reply_text("⚙️ Memproses enkripsi...")

    try:
        t_start = time.perf_counter()

        # Jalankan encryption
        enc_data = run_encryption(raw, enc_level)

        # Generate output dengan wrapper template
        result = generate_output(code_type, enc_data, layers)

        t_end = time.perf_counter()
        duration_ms = round((t_end - t_start) * 1000, 2)

        input_len  = len(raw)
        output_len = len(result)

    except Exception as e:
        await processing_msg.delete()
        await update.message.reply_text(f"❌ Encryption gagal: {e}")
        return

    await processing_msg.delete()

    # Kirim file hasil
    filename = f"encrypted.{ext}"
    file_buf = io.BytesIO(result.encode("utf-8"))
    file_buf.name = filename

    await update.message.reply_document(
        document=file_buf,
        filename=filename,
        caption=(
            f"✅ *Enkripsi Berhasil!*\n\n"
            f"📄 Code Type   : `{ct_label}`\n"
            f"🔐 Level       : `{el_label}`\n"
            f"🔢 Layers      : `{layers}`\n\n"
            f"📊 *Statistik:*\n"
            f"• Input length  : `{input_len:,}` chars\n"
            f"• Output length : `{output_len:,}` chars\n"
            f"• Waktu proses  : `{duration_ms} ms`\n\n"
            f"_File: `{filename}`_"
        ),
        parse_mode="Markdown",
    )

    # Reset state, tawarkan encrypt lagi
    ctx.user_data.clear()
    ctx.user_data[KEY_STEP] = STEP_IDLE

    await update.message.reply_text(
        "🔄 Mau enkripsi lagi? Ketik /start",
    )


# ══════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CallbackQueryHandler(cb_handler))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("🤖 Bot berjalan...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
