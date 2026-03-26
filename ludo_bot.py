import logging
import random
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# --- LOGGING ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- KONFIGURASI ---
# Token diambil dari Environment Variable (Setting di Cloud Dashboard nanti)
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    print("FATAL ERROR: BOT_TOKEN tidak ditemukan!")
    exit(1)

# Game State (Penyimpanan sementara)
games = {}

class LudoGame:
    def __init__(self, chat_id):
        self.chat_id = chat_id
        self.players = []
        self.player_names = {}
        self.turn_index = 0
        self.is_started = False
        self.positions = {}
        self.last_dice = 0

    def add_player(self, user_id, name):
        if user_id not in self.players and len(self.players) < 4:
            self.players.append(user_id)
            self.player_names[user_id] = name
            self.positions[user_id] = 0
            return True
        return False

def get_board_visual(game):
    """Visualisasi papan Ludo 4x4 mini"""
    visual = "🎲 **ARENA LUDO JAROT** 🎲\n\n"
    grid = [["⬜" for _ in range(4)] for _ in range(4)]
    emojis = ["🔴", "🔵", "🟢", "🟡"]
    
    for i, p_id in enumerate(game.players):
        pos = game.positions[p_id]
        row, col = pos // 4, pos % 4
        if row < 4: 
            grid[row][col] = emojis[i]

    for row in grid:
        visual += " ".join(row) + "\n"
    
    current_p_id = game.players[game.turn_index]
    current_p_name = game.player_names[current_p_id]
    
    visual += f"\n👉 Giliran: **{current_p_name}**"
    if game.last_dice > 0:
        visual += f"\n🎲 Dadu: **{game.last_dice}**"
    
    return visual

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in games:
        games[chat_id] = LudoGame(chat_id)
    
    keyboard = [[InlineKeyboardButton("Join Game 🎮", callback_data="join")]]
    await update.message.reply_text(
        "Woy Rot! Room Ludo dibuka. Klik tombol buat join!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    chat_id = query.message.chat_id
    game = games.get(chat_id)

    if not game: return
    await query.answer()

    if query.data == "join":
        if game.add_player(user.id, user.first_name):
            names = ", ".join(game.player_names.values())
            keyboard = [
                [InlineKeyboardButton("Join Lagi", callback_data="join")],
                [InlineKeyboardButton("GAS MAIN! 🔥", callback_data="start_game")]
            ]
            await query.edit_message_text(
                f"Player joined: {names}\nSiap mabar, Rot?",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    
    elif query.data == "start_game":
        if len(game.players) < 2:
            await query.message.reply_text("Minimal 2 orang, Rot!")
            return
        game.is_started = True
        keyboard = [[InlineKeyboardButton("🎲 KOCOK!", callback_data="roll")]]
        await query.edit_message_text(
            get_board_visual(game),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif query.data == "roll":
        if user.id != game.players[game.turn_index]: return
        
        dice = random.randint(1, 6)
        game.last_dice = dice
        game.positions[user.id] = (game.positions[user.id] + dice) % 16
        game.turn_index = (game.turn_index + 1) % len(game.players)
        
        keyboard = [[InlineKeyboardButton("🎲 KOCOK!", callback_data="roll")]]
        await query.edit_message_text(
            get_board_visual(game),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.run_polling()