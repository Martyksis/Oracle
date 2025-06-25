import discord
import random
import os
import asyncio
import datetime
import logging
import time
from discord import app_commands
from discord.ui import Button, View
from flask import Flask  # <-- Добавлено

app = Flask(__name__)  # <-- Добавлено

@app.route('/')  # <-- Добавлено
def home():      # <-- Добавлено
    return "Discord Bot is alive!"  # <-- Добавлено

def run_web():   # <-- Добавлено
    port = int(os.environ.get("PORT", 8080))  # <-- Добавлено
    app.run(host='0.0.0.0', port=port)  # <-- Добавлено

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)

# Конфигурация intents
intents = discord.Intents.default()
intents.message_content = True

bot = discord.Client(
    intents=intents, 
    status=discord.Status.online,
    activity=discord.Game("Управление графством")
)
tree = app_commands.CommandTree(bot)

# Хранение игровых сессий
active_games = {}
recent_events = {}
player_stats = {}  # Хранение статистики игроков

# Гербы графства в зависимости от уровня
COATS_OF_ARMS = {
    "poor": "🛡️",      # Бедное графство
    "normal": "🏰",     # Обычное графство
    "rich": "👑",       # Богатое графство
    "legendary": "🐉"   # Легендарное графство
}

# Все события
EVENTS = [
    # Оригинальные события
    {
        "title": "🌾 Отличный урожай!",
        "description": "Крестьяне принесли излишки урожая в ваши амбары.",
        "options": [
            {"text": "Продать излишки", "wealth": 30, "popularity": -15, "karma": -10},
            {"text": "Раздать голодающим", "wealth": -10, "popularity": 20, "karma": 15},
            {"text": "Оставить в запасе", "wealth": 10, "popularity": 0, "karma": 5}
        ]
    },
    {
        "title": "🔥 Пожар в городе!",
        "description": "Сгорели несколько жилых домов в бедном квартале.",
        "options": [
            {"text": "Выделить деньги на восстановление", "wealth": -25, "popularity": 15, "karma": 10},
            {"text": "Обложить налогом для ремонта", "wealth": 10, "popularity": -20, "karma": -15},
            {"text": "Игнорировать проблему", "wealth": 0, "popularity": -25, "karma": -20}
        ]
    },
    # Новые события
    {
        "title": "⚔️ Война с соседями",
        "description": "Соседнее графство объявило вам войну!",
        "options": [
            {"text": "Атаковать первым", "wealth": -40, "popularity": -10, "karma": -20},
            {"text": "Укрепить оборону", "wealth": -30, "popularity": 10, "karma": 5},
            {"text": "Отправить послов для переговоров", "wealth": -20, "popularity": 5, "karma": 15}
        ]
    },
    {
        "title": "🎓 Открытие университета",
        "description": "Мудрецы предлагают создать центр знаний в вашем графстве.",
        "options": [
            {"text": "Полностью профинансировать", "wealth": -50, "popularity": 10, "karma": 30},
            {"text": "Выделить часть средств", "wealth": -30, "popularity": 5, "karma": 15},
            {"text": "Отказать", "wealth": 0, "popularity": -10, "karma": -20}
        ]
    },
    {
        "title": "🌊 Загадочное существо",
        "description": "Рыбаки сообщают о странном создании в озере, пугающем жителей.",
        "options": [
            {"text": "Организовать охоту", "wealth": -20, "popularity": 15, "karma": -25},
            {"text": "Изучить существо", "wealth": -15, "popularity": 5, "karma": 10},
            {"text": "Игнорировать", "wealth": 0, "popularity": -15, "karma": -10}
        ]
    },
    {
        "title": "💍 Свадьба наследника",
        "description": "Ваш наследник решил жениться! Это отличный повод для праздника.",
        "options": [
            {"text": "Устроить королевскую свадьбу", "wealth": -60, "popularity": 40, "karma": 20},
            {"text": "Скромное семейное торжество", "wealth": -20, "popularity": 10, "karma": 10},
            {"text": "Отказаться тратиться", "wealth": 0, "popularity": -30, "karma": -25}
        ]
    }
]

# Достижения
ACHIEVEMENTS = {
    "first_game": "🏁 Первые шаги",
    "wise_ruler": "🧠 Мудрый правитель",
    "people_champion": "🦸 Защитник народа",
    "wealthy_ruler": "💰 Король Мидас",
    "spiritual": "🙏 Духовный лидер",
    "legendary": "🌟 Легендарный правитель"
}

class GameSession:
    def __init__(self, user_id):
        self.wealth = 50
        self.popularity = 50
        self.karma = 50
        self.user_id = user_id
        self.last_active = asyncio.get_event_loop().time()
        self.decisions = []  # История решений
        self.title = "Барон"  # Текущий титул
        self.coat_of_arms = COATS_OF_ARMS["normal"]  # Герб графства

        # Инициализация статистики игрока
        if user_id not in player_stats:
            player_stats[user_id] = {
                "games_played": 0,
                "total_wealth": 0,
                "total_popularity": 0,
                "total_karma": 0,
                "achievements": []
            }

        # Добавляем достижение "Первые шаги"
        if "first_game" not in player_stats[user_id]["achievements"]:
            player_stats[user_id]["achievements"].append("first_game")

        if user_id not in recent_events:
            recent_events[user_id] = []

        self.current_event = self.get_random_event()

    def get_random_event(self):
        # Доступные события
        available = [e for e in EVENTS if e["title"] not in recent_events.get(self.user_id, [])]
        if not available:
            available = EVENTS
            recent_events[self.user_id] = []

        event = random.choice(available)

        # Обновляем историю
        recent_events[self.user_id].append(event["title"])
        if len(recent_events[self.user_id]) > 3:
            recent_events[self.user_id].pop(0)

        return event

    def apply_choice(self, choice):
        # Сохраняем решение
        self.decisions.append({
            "event": self.current_event["title"],
            "choice": choice["text"],
            "effects": {
                "wealth": choice["wealth"],
                "popularity": choice["popularity"],
                "karma": choice["karma"]
            }
        })

        # Обновляем значения с защитой от выхода за пределы
        self.wealth = self.clamp_value(self.wealth + choice["wealth"])
        self.popularity = self.clamp_value(self.popularity + choice["popularity"])
        self.karma = self.clamp_value(self.karma + choice["karma"])
        self.last_active = asyncio.get_event_loop().time()

        # Обновляем герб и титул
        self.update_title_and_coat()

        # Проверяем достижения
        self.check_achievements()

        return self.is_game_over()

    def clamp_value(self, value):
        """Гарантирует, что значение остаётся в диапазоне 0-100"""
        return max(0, min(100, value))

    def is_game_over(self):
        """Проверяет условия завершения игры"""
        return any((
            self.wealth <= 0, self.wealth >= 100,
            self.popularity <= 0, self.popularity >= 100,
            self.karma <= 0, self.karma >= 100
        ))

    def get_game_over_reason(self):
        """Возвращает причину завершения игры и финальное сообщение"""
        if self.wealth <= 0:
            return "💸 Банкротство!", "Ваша казна опустела! Король отстранил вас от управления графством."
        elif self.wealth >= 100:
            return "🏰 Невиданное богатство!", "Ваше состояние стало слишком велико! Вы потеряли связь с реальностью и разорились."
        elif self.popularity <= 0:
            return "🔥 Бунт!", "Народ восстал против вашего правления! Вам пришлось бежать из графства."
        elif self.popularity >= 100:
            return "👑 Народный герой!", "Ваша популярность достигла небес! Вы стали новым королём этих земель!"
        elif self.karma <= 0:
            return "⚖️ Божественная кара!", "Боги отвернулись от вас! Ваше графство постигли несчастья и разруха."
        elif self.karma >= 100:
            return "✨ Просветление!", "Ваша карма достигла совершенства! Вы оставили мирские дела ради духовного пути."
        else:
            return "🏆 Игра завершена!", "Вы достигли предела в управлении графством."

    def update_title_and_coat(self):
        """Обновляет титул и герб в зависимости от состояния"""
        avg = (self.wealth + self.popularity + self.karma) / 3

        if avg < 30:
            self.title = "Бедный Барон"
            self.coat_of_arms = COATS_OF_ARMS["poor"]
        elif avg < 50:
            self.title = "Барон"
            self.coat_of_arms = COATS_OF_ARMS["normal"]
        elif avg < 70:
            self.title = "Граф"
            self.coat_of_arms = COATS_OF_ARMS["rich"]
        else:
            self.title = "Великий Герцог"
            self.coat_of_arms = COATS_OF_ARMS["legendary"]

    def check_achievements(self):
        """Проверяет и добавляет достижения"""
        stats = player_stats[self.user_id]

        # Мудрый правитель (сбалансированное развитие)
        if 40 <= self.wealth <= 60 and 40 <= self.popularity <= 60 and 40 <= self.karma <= 60:
            if "wise_ruler" not in stats["achievements"]:
                stats["achievements"].append("wise_ruler")

        # Защитник народа (высокая популярность)
        if self.popularity >= 80:
            if "people_champion" not in stats["achievements"]:
                stats["achievements"].append("people_champion")

        # Король Мидас (высокое богатство)
        if self.wealth >= 80:
            if "wealthy_ruler" not in stats["achievements"]:
                stats["achievements"].append("wealthy_ruler")

        # Духовный лидер (высокая карма)
        if self.karma >= 80:
            if "spiritual" not in stats["achievements"]:
                stats["achievements"].append("spiritual")

        # Легендарный правитель (всё отлично)
        if self.wealth >= 70 and self.popularity >= 70 and self.karma >= 70:
            if "legendary" not in stats["achievements"]:
                stats["achievements"].append("legendary")

    def get_embed(self, choice=None):
        # Определяем цвет на основе состояния
        avg = (self.wealth + self.popularity + self.karma) / 3
        if avg > 70:
            color = discord.Color.gold()
        elif avg > 40:
            color = discord.Color.green()
        else:
            color = discord.Color.red()

        embed = discord.Embed(
            title=f"{self.coat_of_arms} Управление Графством",
            description=f"**Титул:** {self.title}",
            color=color
        )

        # Индикаторы прогресса
        embed.add_field(
            name="💰 Богатство", 
            value=self.create_progress_bar(self.wealth) + f" {self.wealth}/100", 
            inline=False
        )
        embed.add_field(
            name="👥 Популярность", 
            value=self.create_progress_bar(self.popularity) + f" {self.popularity}/100", 
            inline=False
        )
        embed.add_field(
            name="☯️ Карма", 
            value=self.create_progress_bar(self.karma) + f" {self.karma}/100", 
            inline=False
        )

        # Добавляем информацию о выборе, если он был
        if choice:
            wealth_change = f"{choice['wealth']:+}"
            popularity_change = f"{choice['popularity']:+}"
            karma_change = f"{choice['karma']:+}"

            embed.description = (
                f"**Титул:** {self.title}\n"
                f"**Вы выбрали:** {choice['text']}\n\n"
                f"```diff\n"
                f"Богатство: {wealth_change}\n"
                f"Популярность: {popularity_change}\n"
                f"Карма: {karma_change}\n"
                f"```"
            )

        return embed

    def create_progress_bar(self, value):
        """Создает визуальное представление прогресса"""
        safe_value = max(0, min(100, value))
        filled = '█' * (safe_value // 10)
        empty = '░' * (10 - (safe_value // 10))
        return f"[{filled}{empty}]"

class GameView(View):
    """Кастомное представление для игрового интерфейса"""
    def __init__(self, game):
        super().__init__(timeout=300)
        self.game = game

        # Добавляем кнопки для текущего события
        for option in game.current_event["options"]:
            self.add_item(OptionButton(option))

    async def on_timeout(self):
        # При таймауте удаляем игру
        if self.game.user_id in active_games:
            del active_games[self.game.user_id]
        if self.game.user_id in recent_events:
            del recent_events[self.game.user_id]

class OptionButton(Button):
    """Кастомная кнопка для обработки выбора в игре"""
    def __init__(self, option):
        super().__init__(label=option["text"][:80], style=discord.ButtonStyle.secondary)
        self.option = option

    async def callback(self, interaction: discord.Interaction):
        try:
            # Получаем игровую сессию из представления
            view = self.view
            if not hasattr(view, 'game') or view.game.user_id != interaction.user.id:
                await interaction.response.send_message("❌ Это не ваша игра или сессия устарела!", ephemeral=True)
                return

            game = view.game

            # Применяем выбор игрока
            game_over = game.apply_choice(self.option)

            # Получаем embed с результатами
            result_embed = game.get_embed(choice=self.option)

            # Проверяем завершение игры
            if game_over:
                # Получаем причину завершения
                title, description = game.get_game_over_reason()
                result_embed.title = f"{game.coat_of_arms} {title}"
                result_embed.description = description

                # Добавляем статистику игры
                result_embed.add_field(
                    name="📊 Итоги игры",
                    value=(
                        f"**Богатство:** {game.wealth}/100\n"
                        f"**Популярность:** {game.popularity}/100\n"
                        f"**Карма:** {game.karma}/100\n"
                        f"**Решений принято:** {len(game.decisions)}"
                    ),
                    inline=False
                )

                # Обновляем глобальную статистику игрока
                stats = player_stats[interaction.user.id]
                stats["games_played"] += 1
                stats["total_wealth"] += game.wealth
                stats["total_popularity"] += game.popularity
                stats["total_karma"] += game.karma

                # Удаляем игровую сессию
                if interaction.user.id in active_games:
                    del active_games[interaction.user.id]
                if interaction.user.id in recent_events:
                    del recent_events[interaction.user.id]

                # Отправляем финальное сообщение без кнопок
                await interaction.response.edit_message(embed=result_embed, view=None)
            else:
                # Получаем новое событие
                game.current_event = game.get_random_event()

                # Добавляем информацию о новом событии
                result_embed.add_field(
                    name=f"**{game.current_event['title']}**", 
                    value=game.current_event['description'], 
                    inline=False
                )

                # Создаем новое представление с кнопками
                new_view = GameView(game)

                # Обновляем сообщение
                await interaction.response.edit_message(embed=result_embed, view=new_view)

        except Exception as e:
            logging.error(f"Ошибка при обработке выбора: {e}", exc_info=True)
            # Удаляем сломанную сессию
            if interaction.user.id in active_games:
                del active_games[interaction.user.id]
            if interaction.user.id in recent_events:
                del recent_events[interaction.user.id]

            try:
                await interaction.response.send_message(
                    "⚠️ Критическая ошибка при обработке вашего выбора. Игра была сброшена. Используйте `/start_game` для новой игры.", 
                    ephemeral=True
                )
            except:
                await interaction.followup.send(
                    "⚠️ Критическая ошибка при обработке вашего выбора. Игра была сброшена. Используйте `/start_game` для новой игры.", 
                    ephemeral=True
                )

@tree.command(name="start_game", description="Начать игру в управление графством")
async def start_game(interaction: discord.Interaction):
    try:
        # Отложенный ответ
        await interaction.response.defer(thinking=True)

        if interaction.user.id in active_games:
            await interaction.followup.send("У вас уже есть активная игра! Завершите текущую игру сначала.", ephemeral=True)
            return

        game = GameSession(interaction.user.id)
        active_games[interaction.user.id] = game

        embed = game.get_embed()
        embed.description = (
            f"**{game.coat_of_arms} Король даровал вам графство!**\n"
            "Принимайте мудрые решения и не допустите краха.\n"
            f"**Титул:** {game.title}"
        )
        embed.add_field(
            name=f"**{game.current_event['title']}**", 
            value=game.current_event['description'], 
            inline=False
        )

        # Создаем представление с кнопками
        view = GameView(game)

        await interaction.followup.send(embed=embed, view=view)

    except Exception as e:
        logging.error(f"Ошибка при запуске игры: {e}", exc_info=True)
        await interaction.followup.send("⚠️ Критическая ошибка при запуске игры. Пожалуйста, попробуйте снова.", ephemeral=True)

@tree.command(name="stats", description="Показать вашу статистику")
async def stats(interaction: discord.Interaction):
    try:
        await interaction.response.defer()

        if interaction.user.id not in player_stats:
            await interaction.followup.send("Вы еще не играли! Начните игру с помощью `/start_game`")
            return

        stats = player_stats[interaction.user.id]
        games_played = stats["games_played"]
        avg_wealth = stats["total_wealth"] // games_played if games_played else 0
        avg_popularity = stats["total_popularity"] // games_played if games_played else 0
        avg_karma = stats["total_karma"] // games_played if games_played else 0

        # Собираем достижения
        achievements = "\n".join([ACHIEVEMENTS[a] for a in stats["achievements"]]) if stats["achievements"] else "Пока нет достижений"

        embed = discord.Embed(
            title="📊 Ваша статистика",
            color=discord.Color.blue()
        )

        embed.add_field(name="🎮 Игр сыграно", value=str(games_played), inline=True)
        embed.add_field(name="💰 Среднее богатство", value=f"{avg_wealth}/100", inline=True)
        embed.add_field(name="👥 Средняя популярность", value=f"{avg_popularity}/100", inline=True)
        embed.add_field(name="☯️ Средняя карма", value=f"{avg_karma}/100", inline=True)
        embed.add_field(name="🏆 Достижения", value=achievements, inline=False)

        await interaction.followup.send(embed=embed)

    except Exception as e:
        logging.error(f"Ошибка при показе статистики: {e}", exc_info=True)
        await interaction.followup.send("⚠️ Ошибка при получении статистики. Попробуйте позже.", ephemeral=True)

@tree.command(name="help_game", description="Помощь по игре")
async def help_game(interaction: discord.Interaction):
    embed = discord.Embed(
        title="❓ Помощь по игре 'Управление Графством'",
        description=(
            "Вы - правитель средневекового графства. Принимайте решения, которые влияют на:\n\n"
            "💰 **Богатство** - состояние вашей казны\n"
            "👥 **Популярность** - отношение народа к вам\n"
            "☯️ **Карма** - духовное благополучие ваших земель\n\n"
            "Игра продолжается до тех пор, пока один из показателей не достигнет 0 или 100.\n"
            "С каждым решением вы получаете новый титул и герб в зависимости от успехов!"
        ),
        color=discord.Color.green()
    )

    embed.add_field(
        name="🎮 Команды",
        value=(
            "`/start_game` - Начать новую игру\n"
            "`/stats` - Показать вашу статистику\n"
            "`/help_game` - Показать это сообщение"
        ),
        inline=False
    )

    embed.add_field(
        name="🏆 Достижения",
        value=(
            "Собирайте достижения за особые успехи в игре!\n"
            "Проверьте свои достижения командой `/stats`"
        ),
        inline=False
    )

    embed.set_footer(text="Удачи в управлении графством, ваша светлость!")

    await interaction.response.send_message(embed=embed)

@bot.event
async def on_ready():
    logging.info(f'Бот {bot.user.name} запущен! ID: {bot.user.id}')
    logging.info(f'Статус: {bot.status}')
    try:
        synced = await tree.sync()
        logging.info(f"Синхронизировано {len(synced)} команд")
    except Exception as e:
        logging.error(f"Ошибка синхронизации команд: {e}")

    # Запускаем фоновую задачу для поддержания активности
    bot.loop.create_task(background_activity())

# Фоновая задача для поддержания активности
async def background_activity():
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            now = datetime.datetime.now()
            logger.info(f"🔁 Активность: {now.strftime('%Y-%m-%d %H:%M:%S')}")
            await asyncio.sleep(300)  # 5 минут
        except Exception as e:
            logger.error(f"Ошибка в фоновой задаче: {e}")
            await asyncio.sleep(60)

# Фоновая очистка неактивных игр
async def clean_games():
    while True:
        await asyncio.sleep(300)  # Каждые 5 минут
        current_time = asyncio.get_event_loop().time()
        to_remove = []

        for user_id, game in list(active_games.items()):
            if current_time - game.last_active > 600:  # 10 минут без активности
                to_remove.append(user_id)

        for user_id in to_remove:
            if user_id in active_games:
                del active_games[user_id]
            if user_id in recent_events:
                del recent_events[user_id]

        if to_remove:
            logging.info(f"Удалено {len(to_remove)} неактивных игр")

# Создаем фоновые задачи
@bot.event
async def setup_hook():
    bot.loop.create_task(clean_games())
    logging.info("Фоновые задачи запущены")

# ... другой код ...

if __name__ == "__main__":
    # Запускаем веб-сервер в отдельном потоке
    import threading
    web_thread = threading.Thread(target=run_web)
    web_thread.daemon = True
    web_thread.start()

    # Запускаем Discord бота
    TOKEN = os.getenv('TOKEN')
    if TOKEN:
        try:
            bot.run(TOKEN, reconnect=True)
        except Exception as e:
            logging.critical(f"Критическая ошибка при запуске бота: {e}")
    else:
        logging.critical("Токен не найден! Проверьте переменные среды.")
