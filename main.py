
import asyncio
import inspect
import json
import random
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import flet as ft

from core.engine import GameEngine
from core.events import GameEvent, GameEventType
from core.models import RoundConfig, RoundState, WordReviewStatus
from core.session import GameSession
from data.word_provider import (
    USER_WORDS_SUBJECT,
    StaticWordProvider,
    UserWordProvider,
    WordProvider,
    parse_user_words,
)
from datawords import DATA, DIFFICULTIES
from ui.swipe_handlers import SwipeHandlersMixin
from ui.viewmodel import GameViewModel
from usecases.next_word import NextWordUseCase
from usecases.start_round import StartRoundUseCase
from usecases.submit_answer import SubmitAnswerUseCase
from usecases.tick_round import TickRoundUseCase

try:
    import winsound

    HAS_WINSOUND = True
except Exception:
    HAS_WINSOUND = False


LEADERBOARD_FILE = Path(__file__).resolve().with_name("leaderboard.json")

THEME_PRESETS = {
    "Ocean Neon": {
        "bg": ["#070E1A", "#0F1A2D", "#172740"],
        "card": ["#1E3557", "#15243C", "#0F192A"],
        "accent": ft.Colors.CYAN_300,
        "accent_soft": ft.Colors.BLUE_200,
        "ok": ft.Colors.GREEN_300,
        "bad": ft.Colors.RED_300,
        "warm": ft.Colors.AMBER_300,
    },
    "Sunset Pulse": {
        "bg": ["#1A0D12", "#341622", "#5A2238"],
        "card": ["#692945", "#4A2036", "#311527"],
        "accent": ft.Colors.PINK_300,
        "accent_soft": ft.Colors.ORANGE_300,
        "ok": ft.Colors.LIGHT_GREEN_300,
        "bad": ft.Colors.RED_300,
        "warm": ft.Colors.AMBER_300,
    },
    "Mint Grid": {
        "bg": ["#071510", "#10261E", "#1A3B2F"],
        "card": ["#1E4C3D", "#173A2F", "#122D25"],
        "accent": ft.Colors.TEAL_300,
        "accent_soft": ft.Colors.LIGHT_BLUE_200,
        "ok": ft.Colors.GREEN_300,
        "bad": ft.Colors.RED_300,
        "warm": ft.Colors.AMBER_300,
    },
    "Chalk Slate": {
        "bg": ["#07100D", "#10201A", "#182D24"],
        "card": ["#203A31", "#172A24", "#101E1A"],
        "accent": ft.Colors.LIME_200,
        "accent_soft": ft.Colors.TEAL_100,
        "ok": ft.Colors.GREEN_300,
        "bad": ft.Colors.DEEP_ORANGE_200,
        "warm": ft.Colors.AMBER_200,
    },
    "Notebook Pop": {
        "bg": ["#090B16", "#171B2E", "#232A47"],
        "card": ["#26345A", "#1D2744", "#141B30"],
        "accent": ft.Colors.INDIGO_100,
        "accent_soft": ft.Colors.CYAN_200,
        "ok": ft.Colors.LIGHT_GREEN_300,
        "bad": ft.Colors.PINK_200,
        "warm": ft.Colors.YELLOW_200,
    },
}

PERFORMANCE_PROFILES = {
    "Performance": {
        "orb_blur": 6,
        "orb_interval": 8.0,
        "orb_shadow": 6,
        "card_shadow": 8,
        "drag_fps": 24,
        "effects": False,
    },
    "Ultra": {
        "orb_blur": 24,
        "orb_interval": 2.9,
        "orb_shadow": 22,
        "card_shadow": 22,
        "drag_fps": 36,
        "effects": True,
    },
}

LANGUAGE_LABELS = {
    "ru": "Русский",
    "en": "English",
    "de": "Deutsch",
    "zh": "中文",
    "es": "Español",
}

LANGUAGE_WORDS = {
    "en": {
        "Литература": {
            "easy": ["Shakespeare", "Novel", "Poet", "Chapter", "Hero", "Library"],
            "medium": ["Metaphor", "Dialogue", "Narrator", "Plot", "Genre", "Sonnet"],
            "hard": ["Intertext", "Allusion", "Deconstruction", "Postmodernism", "Polysemy", "Versification"],
        },
        "Наука": {
            "easy": ["Atom", "Cell", "DNA", "Formula", "Gravity", "Experiment"],
            "medium": ["Isotope", "Catalyst", "Inertia", "Hypothesis", "Vacuum", "Orbit"],
            "hard": ["Entropy", "Singularity", "Stochastic", "Turbulence", "Epistemology", "Quantization"],
        },
        "Кино и музыка": {
            "easy": ["Scene", "Actor", "Song", "Rhythm", "Guitar", "Album"],
            "medium": ["Soundtrack", "Director", "Trailer", "Casting", "Refrain", "Solo"],
            "hard": ["Orchestration", "Counterpoint", "Diegetics", "Mise en scene", "Postproduction", "Improvisation"],
        },
        "Путешествия": {
            "easy": ["Flight", "Passport", "Hotel", "Beach", "Map", "Luggage"],
            "medium": ["Transit", "Route", "Archipelago", "Excursion", "Airport", "Transfer"],
            "hard": ["Acclimatization", "Urbanism", "Ecotourism", "Geopolitics", "Insolation", "Landscape"],
        },
        "Технологии": {
            "easy": ["Smartphone", "Screen", "File", "Folder", "Keyboard", "Website"],
            "medium": ["Startup", "Server", "Interface", "Backup", "Browser", "Encryption"],
            "hard": ["Asynchrony", "Compilation", "Containerization", "Cryptography", "Orchestration", "Inference"],
        },
    },
    "de": {
        "Литература": {
            "easy": ["Goethe", "Roman", "Dichter", "Kapitel", "Held", "Bibliothek"],
            "medium": ["Metapher", "Dialog", "Erzaehler", "Handlung", "Genre", "Sonett"],
            "hard": ["Intertext", "Allusion", "Dekonstruktion", "Postmoderne", "Polysemie", "Versifikation"],
        },
        "Наука": {
            "easy": ["Atom", "Zelle", "DNA", "Formel", "Gravitation", "Experiment"],
            "medium": ["Isotop", "Katalysator", "Traegheit", "Hypothese", "Vakuum", "Orbit"],
            "hard": ["Entropie", "Singularitaet", "Stochastik", "Turbulenz", "Epistemologie", "Quantisierung"],
        },
        "Кино и музыка": {
            "easy": ["Szene", "Schauspieler", "Lied", "Rhythmus", "Gitarre", "Album"],
            "medium": ["Soundtrack", "Regisseur", "Trailer", "Casting", "Refrain", "Solo"],
            "hard": ["Orchestrierung", "Kontrapunkt", "Diegese", "Mise en scene", "Postproduktion", "Improvisation"],
        },
        "Путешествия": {
            "easy": ["Flug", "Pass", "Hotel", "Strand", "Karte", "Gepaeck"],
            "medium": ["Transit", "Route", "Archipel", "Ausflug", "Flughafen", "Umstieg"],
            "hard": ["Akklimatisation", "Urbanistik", "Oekotourismus", "Geopolitik", "Insolation", "Landschaft"],
        },
        "Технологии": {
            "easy": ["Smartphone", "Bildschirm", "Datei", "Ordner", "Tastatur", "Webseite"],
            "medium": ["Startup", "Server", "Schnittstelle", "Backup", "Browser", "Verschluesselung"],
            "hard": ["Asynchronitaet", "Kompilierung", "Containerisierung", "Kryptographie", "Orchestrierung", "Inferenz"],
        },
    },
    "zh": {
        "Литература": {
            "easy": ["作家", "小说", "诗人", "章节", "主角", "图书馆"],
            "medium": ["隐喻", "对话", "叙述者", "情节", "体裁", "十四行诗"],
            "hard": ["互文", "典故", "解构", "后现代", "多义", "诗律"],
        },
        "Наука": {
            "easy": ["原子", "细胞", "DNA", "公式", "重力", "实验"],
            "medium": ["同位素", "催化剂", "惯性", "假说", "真空", "轨道"],
            "hard": ["熵", "奇点", "随机性", "湍流", "认识论", "量化"],
        },
        "Кино и музыка": {
            "easy": ["场景", "演员", "歌曲", "节奏", "吉他", "专辑"],
            "medium": ["原声带", "导演", "预告片", "选角", "副歌", "独奏"],
            "hard": ["配器", "对位法", "叙内声", "场面调度", "后期制作", "即兴"],
        },
        "Путешествия": {
            "easy": ["航班", "护照", "酒店", "海滩", "地图", "行李"],
            "medium": ["中转", "路线", "群岛", "游览", "机场", "换乘"],
            "hard": ["适应环境", "城市学", "生态旅游", "地缘政治", "日照", "地貌"],
        },
        "Технологии": {
            "easy": ["智能手机", "屏幕", "文件", "文件夹", "键盘", "网站"],
            "medium": ["初创公司", "服务器", "界面", "备份", "浏览器", "加密"],
            "hard": ["异步", "编译", "容器化", "密码学", "编排", "推理"],
        },
    },
    "es": {
        "Литература": {
            "easy": ["Escritor", "Novela", "Poeta", "Capitulo", "Heroe", "Biblioteca"],
            "medium": ["Metafora", "Dialogo", "Narrador", "Trama", "Genero", "Soneto"],
            "hard": ["Intertexto", "Alusion", "Deconstruccion", "Posmodernismo", "Polisemia", "Versificacion"],
        },
        "Наука": {
            "easy": ["Atomo", "Celula", "ADN", "Formula", "Gravedad", "Experimento"],
            "medium": ["Isotopo", "Catalizador", "Inercia", "Hipotesis", "Vacio", "Orbita"],
            "hard": ["Entropia", "Singularidad", "Estocastica", "Turbulencia", "Epistemologia", "Cuantizacion"],
        },
        "Кино и музыка": {
            "easy": ["Escena", "Actor", "Cancion", "Ritmo", "Guitarra", "Album"],
            "medium": ["Banda sonora", "Director", "Trailer", "Casting", "Estribillo", "Solo"],
            "hard": ["Orquestacion", "Contrapunto", "Diegesis", "Mise en scene", "Postproduccion", "Improvisacion"],
        },
        "Путешествия": {
            "easy": ["Vuelo", "Pasaporte", "Hotel", "Playa", "Mapa", "Equipaje"],
            "medium": ["Transito", "Ruta", "Archipielago", "Excursion", "Aeropuerto", "Conexion"],
            "hard": ["Aclimatacion", "Urbanismo", "Ecoturismo", "Geopolitica", "Insolacion", "Paisaje"],
        },
        "Технологии": {
            "easy": ["Smartphone", "Pantalla", "Archivo", "Carpeta", "Teclado", "Sitio web"],
            "medium": ["Startup", "Servidor", "Interfaz", "Respaldo", "Navegador", "Cifrado"],
            "hard": ["Asincronia", "Compilacion", "Contenerizacion", "Criptografia", "Orquestacion", "Inferencia"],
        },
    },
}

UI_TEXT = {
    "ru": {
        "app_name": "SCool Alias",
        "splash_tagline": "Школьный Alias со свайпами, командами и быстрыми раундами",
        "skip_splash": "Пропустить",
        "settings": "Настройки",
        "current_turn": "Сейчас ход: {team}",
        "words_language": "Язык слов: {lang}",
        "ui_language": "Язык интерфейса: {lang}",
        "team_a": "Team A",
        "team_b": "Team B",
        "subject": "Тема",
        "difficulty": "Сложность",
        "target_match": "Цель матча: {target} очков",
        "round_time": "Время раунда: {seconds} с",
        "choose_topic_diff": "Выбери тему/сложность и запускай раунд",
        "start_game": "Начать игру",
        "setup_title": "Подготовка раунда",
        "setup_subtitle": "Собери параметры и запусти игру",
        "back": "Назад",
        "exit_app": "Выход",
        "start_round": "Старт раунда",
        "to_win": "До победы: {target}",
        "records_title": "Локальные рекорды",
        "records_empty": "Пока нет результатов. Сыграй первый раунд!",
        "performance_mode": "Режим производительности",
        "interface_theme": "Тема интерфейса",
        "custom_words": "Свои слова",
        "custom_words_hint": "Вставь слова через запятую или каждое с новой строки",
        "settings_title": "Настройки",
        "settings_subtitle": "Performance / Ultra",
        "anim_speed": "Скорость анимаций: x{value}",
        "card_size": "Размер карточки: x{value}",
        "sound_swipe": "Звук при свайпе",
        "vibration": "Вибро-отклик (визуальный на desktop)",
        "cancel": "Отмена",
        "save": "Сохранить",
        "round_title": "Раунд",
        "turn": "Ход: {team}",
        "swipe_hint": "Свайп вправо = Верно, влево = Пропуск",
        "skip_upper": "ПРОПУСК",
        "correct_upper": "ВЕРНО",
        "skip_btn": "Пропуск",
        "correct_btn": "Верно",
        "score_short": "Очки",
        "combo_short": "Комбо",
        "correct_short": "Верно",
        "skip_short": "Пропуск",
        "penalty_skip": "Штраф за пропуск: -{penalty}",
        "end_round": "Завершить раунд",
        "to_lobby": "В лобби",
        "round_finished": "Раунд завершен: {team}",
        "time_up": "Время вышло",
        "round_stopped": "Раунд остановлен",
        "match_winner": "Матч завершен. Победитель: {winner}",
        "points": "Очки",
        "best_streak": "Лучший стрик",
        "topic_difficulty": "Тема: {subject} · Сложность: {difficulty}",
        "team_total": "Сумма команды '{team}' в матче: {total}",
        "new_match": "Новый матч",
        "next_round": "Следующий раунд ({team})",
        "review_title": "Слова раунда",
        "review_hint": "Исправь спорные слова перед следующим раундом",
    },
    "en": {
        "app_name": "SCool Alias",
        "splash_tagline": "School Alias with swipes, teams, and fast rounds",
        "skip_splash": "Skip",
        "settings": "Settings",
        "current_turn": "Current turn: {team}",
        "words_language": "Words language: {lang}",
        "ui_language": "UI language: {lang}",
        "team_a": "Team A",
        "team_b": "Team B",
        "subject": "Topic",
        "difficulty": "Difficulty",
        "target_match": "Match target: {target} pts",
        "round_time": "Round time: {seconds}s",
        "choose_topic_diff": "Pick topic/difficulty and start the round",
        "start_game": "Start game",
        "setup_title": "Round setup",
        "setup_subtitle": "Configure options and start",
        "back": "Back",
        "exit_app": "Exit",
        "start_round": "Start round",
        "to_win": "To win: {target}",
        "records_title": "Local records",
        "records_empty": "No results yet. Play your first round!",
        "performance_mode": "Performance mode",
        "interface_theme": "Interface theme",
        "custom_words": "Custom words",
        "custom_words_hint": "Paste words separated by commas or one per line",
        "settings_title": "Settings",
        "settings_subtitle": "Performance / Ultra",
        "anim_speed": "Animation speed: x{value}",
        "card_size": "Card size: x{value}",
        "sound_swipe": "Swipe sound",
        "vibration": "Vibration feedback (desktop visual)",
        "cancel": "Cancel",
        "save": "Save",
        "round_title": "Round",
        "turn": "Turn: {team}",
        "swipe_hint": "Swipe right = Correct, left = Skip",
        "skip_upper": "SKIP",
        "correct_upper": "CORRECT",
        "skip_btn": "Skip",
        "correct_btn": "Correct",
        "score_short": "Score",
        "combo_short": "Combo",
        "correct_short": "Correct",
        "skip_short": "Skipped",
        "penalty_skip": "Skip penalty: -{penalty}",
        "end_round": "End round",
        "to_lobby": "Lobby",
        "round_finished": "Round finished: {team}",
        "time_up": "Time is up",
        "round_stopped": "Round stopped",
        "match_winner": "Match finished. Winner: {winner}",
        "points": "Points",
        "best_streak": "Best streak",
        "topic_difficulty": "Topic: {subject} · Difficulty: {difficulty}",
        "team_total": "Team '{team}' total: {total}",
        "new_match": "New match",
        "next_round": "Next round ({team})",
        "review_title": "Round words",
        "review_hint": "Adjust doubtful words before the next round",
    },
    "de": {
        "settings": "Einstellungen",
        "current_turn": "Aktiver Zug: {team}",
        "words_language": "Wortsprache: {lang}",
        "ui_language": "Sprache der UI: {lang}",
        "subject": "Thema",
        "difficulty": "Schwierigkeit",
        "target_match": "Ziel im Match: {target} Punkte",
        "choose_topic_diff": "Thema/Schwierigkeit waehlen und starten",
        "start_game": "Spiel starten",
        "setup_title": "Runden-Setup",
        "setup_subtitle": "Optionen setzen und starten",
        "back": "Zurueck",
        "exit_app": "Beenden",
        "start_round": "Runde starten",
        "to_win": "Bis zum Sieg: {target}",
        "records_title": "Lokale Rekorde",
        "records_empty": "Noch keine Ergebnisse. Spiele die erste Runde!",
        "settings_title": "Einstellungen",
        "anim_speed": "Animationsgeschwindigkeit: x{value}",
        "card_size": "Kartengroesse: x{value}",
        "cancel": "Abbrechen",
        "save": "Speichern",
        "round_title": "Runde",
        "turn": "Zug: {team}",
        "swipe_hint": "Rechts = Richtig, links = Ueberspringen",
        "skip_btn": "Ueberspringen",
        "correct_btn": "Richtig",
        "score_short": "Punkte",
        "combo_short": "Combo",
        "correct_short": "Richtig",
        "skip_short": "Skip",
        "penalty_skip": "Strafe fuer Skip: -{penalty}",
        "end_round": "Runde beenden",
        "to_lobby": "Lobby",
        "round_finished": "Runde beendet: {team}",
        "time_up": "Zeit ist um",
        "round_stopped": "Runde gestoppt",
        "match_winner": "Match beendet. Sieger: {winner}",
        "points": "Punkte",
        "best_streak": "Beste Serie",
        "topic_difficulty": "Thema: {subject} · Schwierigkeit: {difficulty}",
        "team_total": "Team '{team}' gesamt: {total}",
        "new_match": "Neues Match",
        "next_round": "Naechste Runde ({team})",
    },
    "zh": {
        "settings": "设置",
        "current_turn": "当前回合: {team}",
        "words_language": "词语语言: {lang}",
        "ui_language": "界面语言: {lang}",
        "subject": "主题",
        "difficulty": "难度",
        "target_match": "比赛目标: {target} 分",
        "choose_topic_diff": "选择主题/难度并开始回合",
        "start_game": "开始游戏",
        "setup_title": "回合设置",
        "setup_subtitle": "设置参数并开始",
        "back": "返回",
        "exit_app": "退出",
        "start_round": "开始回合",
        "to_win": "获胜目标: {target}",
        "records_title": "本地记录",
        "records_empty": "还没有记录，先开始第一局！",
        "settings_title": "设置",
        "anim_speed": "动画速度: x{value}",
        "card_size": "卡片大小: x{value}",
        "cancel": "取消",
        "save": "保存",
        "round_title": "回合",
        "turn": "轮到: {team}",
        "swipe_hint": "右滑=正确，左滑=跳过",
        "skip_btn": "跳过",
        "correct_btn": "正确",
        "score_short": "得分",
        "combo_short": "连击",
        "correct_short": "正确",
        "skip_short": "跳过",
        "penalty_skip": "跳过扣分: -{penalty}",
        "end_round": "结束回合",
        "to_lobby": "大厅",
        "round_finished": "回合结束: {team}",
        "time_up": "时间到",
        "round_stopped": "回合已停止",
        "match_winner": "比赛结束，赢家: {winner}",
        "points": "分数",
        "best_streak": "最佳连击",
        "topic_difficulty": "主题: {subject} · 难度: {difficulty}",
        "team_total": "队伍 '{team}' 总分: {total}",
        "new_match": "新比赛",
        "next_round": "下一回合 ({team})",
    },
    "es": {
        "settings": "Configuracion",
        "current_turn": "Turno actual: {team}",
        "words_language": "Idioma de palabras: {lang}",
        "ui_language": "Idioma de interfaz: {lang}",
        "subject": "Tema",
        "difficulty": "Dificultad",
        "target_match": "Objetivo del partido: {target} pts",
        "choose_topic_diff": "Elige tema/dificultad y empieza la ronda",
        "start_game": "Iniciar juego",
        "setup_title": "Configuracion de ronda",
        "setup_subtitle": "Ajusta opciones y comienza",
        "back": "Atras",
        "exit_app": "Salir",
        "start_round": "Iniciar ronda",
        "to_win": "Para ganar: {target}",
        "records_title": "Records locales",
        "records_empty": "Aun no hay resultados. Juega la primera ronda!",
        "settings_title": "Configuracion",
        "anim_speed": "Velocidad de animacion: x{value}",
        "card_size": "Tamano de tarjeta: x{value}",
        "cancel": "Cancelar",
        "save": "Guardar",
        "round_title": "Ronda",
        "turn": "Turno: {team}",
        "swipe_hint": "Derecha = Correcto, izquierda = Pasar",
        "skip_btn": "Pasar",
        "correct_btn": "Correcto",
        "score_short": "Puntos",
        "combo_short": "Combo",
        "correct_short": "Correcto",
        "skip_short": "Pasar",
        "penalty_skip": "Penalizacion por pasar: -{penalty}",
        "end_round": "Terminar ronda",
        "to_lobby": "Lobby",
        "round_finished": "Ronda terminada: {team}",
        "time_up": "Tiempo agotado",
        "round_stopped": "Ronda detenida",
        "match_winner": "Partido terminado. Ganador: {winner}",
        "points": "Puntos",
        "best_streak": "Mejor racha",
        "topic_difficulty": "Tema: {subject} · Dificultad: {difficulty}",
        "team_total": "Total del equipo '{team}': {total}",
        "new_match": "Nuevo partido",
        "next_round": "Siguiente ronda ({team})",
    },
}


@dataclass
class UISettings:
    quality: str = "Performance"
    animation_speed: float = 1.0
    card_scale: float = 1.0
    theme_name: str = "Ocean Neon"
    sounds: bool = True
    vibration: bool = True
    round_time_seconds: int = 60


class AliasNeonApp(SwipeHandlersMixin):
    APP_NAME = "SCool Alias"

    def __init__(
        self,
        page: ft.Page,
        word_provider: Optional[WordProvider] = None,
        rng: Optional[random.Random] = None,
    ):
        self.page = page
        self.page.title = self.APP_NAME
        self.page.padding = 0
        self.page.bgcolor = "#060A13"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.on_keyboard_event = self._on_keyboard_event

        self.settings = UISettings()

        self.selected_words_language = "ru"
        self.selected_ui_language = "ru"
        base_word_provider = word_provider or StaticWordProvider(
            base_catalog=DATA,
            localized_catalogs=LANGUAGE_WORDS,
        )
        self.word_provider = UserWordProvider(base_word_provider)
        self.custom_words_text = ""
        self.rng = rng or random.Random()

        self.subject_labels = self.word_provider.get_subjects(self.selected_words_language)
        if not self.subject_labels:
            self.subject_labels = list(DATA.keys())
        self.difficulty_labels = list(DIFFICULTIES.keys())
        self.language_codes = list(LANGUAGE_LABELS.keys())

        self.selected_subject = self.subject_labels[0]
        self.selected_difficulty = self.difficulty_labels[0]

        self.team_names = [self._t("team_a"), self._t("team_b")]
        self.active_team_idx = 0
        self.match_target = 30
        self.match_scores = {self.team_names[0]: 0, self.team_names[1]: 0}

        self.start_round_use_case = StartRoundUseCase()
        self.next_word_use_case = NextWordUseCase()
        self.submit_answer_use_case = SubmitAnswerUseCase()
        self.tick_round_use_case = TickRoundUseCase()

        self.game_session: Optional[GameSession] = None
        self.game_vm = GameViewModel()
        self.last_game_event: Optional[GameEvent] = None
        self.round_state: Optional[RoundState] = None
        self.review_round_state: Optional[RoundState] = None
        self.last_round_result = None
        self.pending_team_idx = 1

        self.current_view = "lobby"
        self.return_view_from_settings = "lobby"

        self.timer_token = 0
        self.flash_token = 0

        self.drag_dx = 0.0
        self.drag_target_dx = 0.0
        self.drag_raw_dx = 0.0
        self.drag_pointer_x = None
        self.drag_start_x = None
        self.drag_last_render_dx = 0.0
        self.drag_render_token = 0
        self.card_drag_animation = None
        self.in_transition = False
        self.is_dragging = False
        self.drag_velocity_x = 0.0
        self.last_pan_event = 0.0
        self.last_pan_frame = 0.0
        self.last_drag_fx_frame = 0.0
        self.last_drag_direction = 0
        self.card_base_left = 0.0
        self.card_base_top = 0.0
        self.swipe_max_dx = 260.0
        self.swipe_commit_threshold = 92.0

        self.orb_a = None
        self.orb_b = None
        self.orb_c = None
        self.state_tint = None
        self._state_tint_cache = ("", -1.0)
        self.combo_burst = None
        self.combo_burst_text = None
        self.combo_burst_token = 0
        self.event_fx_token = 0

        self.leaderboard = self._load_leaderboard()
        self._update_game_vm()

        self.root = ft.Container(expand=True)
        self.page.add(self.root)

        self.show_splash()
        self.page.run_task(self._splash_to_lobby_loop)
        self.page.run_task(self._ambient_loop)

    # -------- Utility --------

    def _theme(self):
        return THEME_PRESETS.get(self.settings.theme_name, THEME_PRESETS["Ocean Neon"])

    def _profile(self):
        return PERFORMANCE_PROFILES.get(
            self.settings.quality, PERFORMANCE_PROFILES["Ultra"]
        )

    def _anim_ms(self, base_ms: int) -> int:
        speed = max(0.5, min(2.0, self.settings.animation_speed))
        return max(60, int(base_ms / speed))

    def _clamp(self, value: float, min_value: float, max_value: float) -> float:
        return max(min_value, min(max_value, value))

    def _safe_int(self, value, default: int = 0) -> int:
        try:
            return int(float(value))
        except Exception:
            return default

    def _page_is_active(self) -> bool:
        try:
            session = self.page.session
        except Exception:
            return False

        if session is None:
            return False

        try:
            connection = session.connection
        except Exception:
            return False

        return connection is not None

    def _safe_update(self, *controls) -> bool:
        if not self._page_is_active():
            return False
        try:
            if controls:
                self.page.update(*controls)
            else:
                self.page.update()
            return True
        except Exception:
            return False

    def _on_keyboard_event(self, e):
        key = (getattr(e, "key", "") or "").lower()
        if key in {"escape", "esc"}:
            self._schedule_close_app()

    def _exit_app_click(self, _):
        self._schedule_close_app()

    def _schedule_close_app(self):
        try:
            self.page.run_task(self._close_app_async)
        except Exception:
            pass

    async def _close_app_async(self):
        self.timer_token += 1
        self.drag_render_token += 1
        self.in_transition = False
        self.is_dragging = False
        self.game_session = None
        self.round_state = None
        self._update_game_vm()

        window = getattr(self.page, "window", None)
        if window is not None:
            close_fn = getattr(window, "close", None)
            if callable(close_fn):
                try:
                    close_result = close_fn()
                    if inspect.isawaitable(close_result):
                        await close_result
                    return
                except Exception:
                    pass

            destroy_fn = getattr(window, "destroy", None)
            if callable(destroy_fn):
                try:
                    destroy_result = destroy_fn()
                    if inspect.isawaitable(destroy_result):
                        await destroy_result
                    return
                except Exception:
                    pass

    def _format_time(self, seconds: float) -> str:
        seconds = max(0, int(seconds + 0.999))
        m, s = divmod(seconds, 60)
        return f"{m:02d}:{s:02d}"

    def _normalize_slider_value(
        self, value: float, min_value: float, max_value: float, digits: int = 2
    ) -> float:
        try:
            normalized = round(float(value), digits)
        except Exception:
            normalized = min_value
        return self._clamp(normalized, min_value, max_value)

    def _layout_width(self, desired: int = 760, min_width: int = 360, margin: int = 32) -> int:
        try:
            page_width = float(self.page.width or 0)
        except Exception:
            page_width = 0
        if page_width <= 0:
            return desired
        return int(self._clamp(page_width - margin, min_width, desired))

    def _layout_height(self, desired: int = 880, min_height: int = 520, margin: int = 24) -> int:
        try:
            page_height = float(self.page.height or 0)
        except Exception:
            page_height = 0
        if page_height <= 0:
            return desired
        return int(self._clamp(page_height - margin, min_height, desired))

    def _is_compact(self) -> bool:
        try:
            width = float(self.page.width or 0)
            height = float(self.page.height or 0)
        except Exception:
            return False
        return (0 < width <= 560) or (0 < height <= 760)

    def _safe_team_names(self, left: str, right: str):
        a = (left or "").strip() or self._t("team_a")
        b = (right or "").strip() or self._t("team_b")
        if a == b:
            b = f"{b} 2"
        return [a, b]

    def _words_language_caption(self) -> str:
        return LANGUAGE_LABELS.get(self.selected_words_language, "Русский")

    def _ui_language_caption(self) -> str:
        return LANGUAGE_LABELS.get(self.selected_ui_language, "Русский")

    def _t(self, key: str, **kwargs) -> str:
        lang_table = UI_TEXT.get(self.selected_ui_language, UI_TEXT["ru"])
        text = lang_table.get(key, UI_TEXT["ru"].get(key, key))
        try:
            return text.format(**kwargs)
        except Exception:
            return text

    def _update_game_vm(self):
        self.game_vm = GameViewModel.from_round_state(
            self.round_state, language_caption=self._words_language_caption()
        )

    def _emit_game_event(self, event_type: GameEventType, **payload):
        self.last_game_event = GameEvent(event_type=event_type, payload=payload)

    def _badge(self, text: str, *, accent: bool = False):
        theme = self._theme()
        base_color = theme["accent"] if accent else ft.Colors.WHITE
        border_color = theme["accent_soft"] if accent else ft.Colors.WHITE
        return ft.Container(
            padding=ft.Padding.symmetric(horizontal=12, vertical=6),
            border_radius=999,
            bgcolor=ft.Colors.with_opacity(0.16 if accent else 0.1, base_color),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.24, border_color)),
            content=ft.Text(
                text,
                size=11,
                weight="bold",
                color=ft.Colors.with_opacity(0.96, ft.Colors.WHITE),
            ),
        )

    def _surface_panel(
        self,
        content,
        *,
        width: Optional[int] = None,
        padding=None,
        radius: int = 20,
        tone: str = "normal",
        ink: bool = False,
        on_click=None,
    ):
        theme = self._theme()
        padding_value = padding if padding is not None else ft.Padding.all(16)
        if isinstance(padding_value, (int, float)):
            padding_value = ft.Padding.all(int(padding_value))

        tone_map = {
            "soft": (0.09, 0.18, ft.Colors.WHITE, ft.Colors.WHITE, 0.0),
            "normal": (0.13, 0.22, ft.Colors.WHITE, ft.Colors.WHITE, 0.0),
            "strong": (0.2, 0.28, ft.Colors.WHITE, ft.Colors.WHITE, 0.1),
            "accent": (0.18, 0.34, theme["accent"], theme["accent_soft"], 0.16),
        }
        bg_opacity, border_opacity, bg_base, border_base, glow_opacity = tone_map.get(
            tone, tone_map["normal"]
        )
        shadow = (
            [
                ft.BoxShadow(
                    blur_radius=18,
                    color=ft.Colors.with_opacity(glow_opacity, theme["accent"]),
                    offset=ft.Offset(0, 8),
                )
            ]
            if glow_opacity > 0
            else []
        )

        return ft.Container(
            width=width,
            padding=padding_value,
            border_radius=radius,
            bgcolor=ft.Colors.with_opacity(bg_opacity, bg_base),
            border=ft.Border.all(1, ft.Colors.with_opacity(border_opacity, border_base)),
            shadow=shadow,
            ink=ink,
            on_click=on_click,
            content=content,
        )

    def _section_panel(
        self,
        title: str,
        content,
        *,
        subtitle: Optional[str] = None,
        width: Optional[int] = None,
        compact: bool = False,
        tone: str = "normal",
    ):
        header_controls = [
            ft.Text(title, size=15 if compact else 16, weight="bold"),
        ]
        if subtitle:
            header_controls.append(
                ft.Text(
                    subtitle,
                    size=11,
                    color=ft.Colors.with_opacity(0.74, ft.Colors.WHITE),
                )
            )

        return self._surface_panel(
            width=width,
            padding=ft.Padding.all(14 if compact else 16),
            radius=18,
            tone=tone,
            content=ft.Column(
                spacing=10,
                controls=[
                    ft.Column(spacing=2, controls=header_controls),
                    content,
                ],
            ),
        )

    def _set_words_language(self, code: str):
        if code not in LANGUAGE_LABELS:
            return
        self.selected_words_language = code
        subjects = self.word_provider.get_subjects(code)
        if subjects:
            self.subject_labels = subjects
            if self.selected_subject not in self.subject_labels:
                self.selected_subject = self.subject_labels[0]
        if self.current_view == "setup":
            self.show_setup()
        elif self.current_view == "lobby":
            self.show_lobby()
        elif self.current_view == "settings":
            self.show_settings()
        elif self.current_view == "round":
            self.show_round()

    def _set_ui_language(self, code: str):
        if code not in LANGUAGE_LABELS:
            return
        self.selected_ui_language = code
        if self.current_view == "splash":
            self.show_splash()
        elif self.current_view == "setup":
            self.show_setup()
        elif self.current_view == "settings":
            self.show_settings()
        elif self.current_view == "round":
            self.show_round()
        elif self.current_view == "final":
            self.show_final()
        else:
            self.show_lobby()

    def _language_selector(self, selected_code: str, on_select):
        buttons = []
        for code, title in LANGUAGE_LABELS.items():
            active = code == selected_code
            buttons.append(
                ft.Button(
                    title,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=(
                            ft.Colors.with_opacity(0.36, self._theme()["accent"])
                            if active
                            else ft.Colors.with_opacity(0.18, ft.Colors.WHITE)
                        ),
                        shape=ft.RoundedRectangleBorder(radius=10),
                        side=ft.BorderSide(
                            1,
                            ft.Colors.with_opacity(
                                0.46 if active else 0.22,
                                self._theme()["accent"] if active else ft.Colors.WHITE,
                            ),
                        ),
                        padding=ft.Padding.symmetric(horizontal=10, vertical=8),
                    ),
                    on_click=lambda _, c=code: on_select(c),
                )
            )
        return ft.ResponsiveRow(
            columns=12,
            run_spacing=6,
            controls=[
                ft.Container(col={"xs": 6, "sm": 4, "md": 3}, content=buttons[0]),
                ft.Container(col={"xs": 6, "sm": 4, "md": 3}, content=buttons[1]),
                ft.Container(col={"xs": 6, "sm": 4, "md": 3}, content=buttons[2]),
                ft.Container(col={"xs": 6, "sm": 4, "md": 3}, content=buttons[3]),
                ft.Container(col={"xs": 6, "sm": 4, "md": 3}, content=buttons[4]),
            ],
        )

    # -------- Splash --------

    def show_splash(self):
        self.current_view = "splash"
        theme = self._theme()
        compact = self._is_compact()
        stage_width = self._layout_width(desired=620, min_width=300, margin=20)

        self.splash_glow = ft.Container(
            width=230 if compact else 280,
            height=230 if compact else 280,
            border_radius=110,
            scale=0.82,
            animate_scale=ft.Animation(1300, "easeOutBack"),
            gradient=ft.RadialGradient(
                colors=[
                    ft.Colors.with_opacity(0.46, theme["accent"]),
                    ft.Colors.with_opacity(0.0, theme["accent"]),
                ]
            ),
            blur=18,
        )
        accent_ring = ft.Container(
            width=170 if compact else 206,
            height=170 if compact else 206,
            border_radius=999,
            border=ft.Border.all(2, ft.Colors.with_opacity(0.42, theme["accent_soft"])),
            opacity=0.86,
            rotate=0.08,
            animate_rotation=ft.Animation(1500, "easeInOut"),
        )
        self.splash_logo = ft.Container(
            width=134 if compact else 164,
            height=134 if compact else 164,
            border_radius=34,
            scale=0.76,
            animate_scale=ft.Animation(1100, "easeOutBack"),
            bgcolor=ft.Colors.with_opacity(0.9, theme["accent"]),
            shadow=[
                ft.BoxShadow(
                    blur_radius=28,
                    color=ft.Colors.with_opacity(0.28, theme["accent"]),
                    offset=ft.Offset(0, 12),
                )
            ],
            alignment=ft.Alignment(0, 0),
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
                controls=[
                    ft.Text("A", size=60 if compact else 74, weight="bold", color=ft.Colors.WHITE),
                    ft.Container(
                        width=38 if compact else 48,
                        height=5,
                        border_radius=8,
                        bgcolor=ft.Colors.with_opacity(0.78, ft.Colors.WHITE),
                    ),
                ],
            ),
        )

        panel = self._surface_panel(
            width=stage_width,
            radius=28,
            tone="strong",
            padding=ft.Padding.symmetric(horizontal=22 if compact else 34, vertical=30 if compact else 42),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=18,
                controls=[
                    self._badge("SCool Alias", accent=True),
                    ft.Stack(
                        width=240 if compact else 290,
                        height=220 if compact else 270,
                        controls=[
                            ft.Container(alignment=ft.Alignment(0, 0), content=self.splash_glow),
                            ft.Container(alignment=ft.Alignment(0, 0), content=accent_ring),
                            ft.Container(alignment=ft.Alignment(0, 0), content=self.splash_logo),
                        ],
                    ),
                    ft.Text(self._t("app_name"), size=36 if compact else 48, weight="bold"),
                    ft.Text(
                        self._t("splash_tagline"),
                        size=15 if compact else 17,
                        color=ft.Colors.with_opacity(0.8, ft.Colors.WHITE),
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Button(
                        self._t("skip_splash"),
                        style=self._button_style("ghost"),
                        on_click=self._skip_splash,
                    ),
                ],
            ),
        )

        content = ft.SafeArea(
            content=ft.Container(
                expand=True,
                alignment=ft.Alignment(0, 0),
                padding=ft.Padding.all(14),
                content=panel,
            )
        )

        self.root.content = self._build_shell(content, scene_mode="light")
        self._safe_update()
        self.splash_logo.scale = 1.0
        self.splash_glow.scale = 1.0
        accent_ring.rotate = -0.08
        self._safe_update(self.splash_logo, self.splash_glow, accent_ring)

    async def _splash_to_lobby_loop(self):
        await asyncio.sleep(2.1)
        if self.current_view != "splash":
            return
        if not self._page_is_active():
            return
        self.show_lobby()

    def _skip_splash(self, _):
        self.show_lobby()

    def _build_shell(self, content, scene_mode: str = "none"):
        theme = self._theme()
        profile = self._profile()
        use_orbs = scene_mode in ("full", "light") and bool(profile.get("effects", True))
        light_scene = scene_mode == "light"

        background = ft.Container(
            expand=True,
            gradient=ft.LinearGradient(
                colors=theme["bg"],
                begin=ft.Alignment(-1, -1),
                end=ft.Alignment(1, 1),
            ),
        )

        controls = [background]

        if use_orbs:
            self.state_tint = ft.Container(
                expand=True,
                bgcolor=ft.Colors.with_opacity(0.0, theme["accent"]),
                opacity=1,
                ignore_interactions=True,
                animate=ft.Animation(self._anim_ms(220), "easeOut"),
            )
            controls.append(self.state_tint)
            self._state_tint_cache = ("", -1.0)
        else:
            self.state_tint = None
            self._state_tint_cache = ("", -1.0)

        if use_orbs:
            blur_value = profile["orb_blur"] if not light_scene else max(8, profile["orb_blur"] - 10)
            glow = profile["orb_shadow"] if not light_scene else max(0, profile["orb_shadow"] - 12)
            accent = theme["accent"]
            warm = theme["warm"]
            orb_a_shadow = (
                [
                    ft.BoxShadow(
                        blur_radius=glow,
                        color=ft.Colors.with_opacity(0.2 if not light_scene else 0.12, accent),
                        offset=ft.Offset(0, 6),
                    )
                ]
                if glow > 0
                else []
            )
            orb_b_shadow = (
                [
                    ft.BoxShadow(
                        blur_radius=glow,
                        color=ft.Colors.with_opacity(0.2 if not light_scene else 0.12, warm),
                        offset=ft.Offset(0, 6),
                    )
                ]
                if glow > 0
                else []
            )

            self.orb_a = ft.Container(
                width=260,
                height=260,
                border_radius=260,
                gradient=ft.RadialGradient(
                    colors=[
                        ft.Colors.with_opacity(0.45 if not light_scene else 0.28, accent),
                        ft.Colors.with_opacity(0.0, accent),
                    ]
                ),
                blur=blur_value,
                left=-110,
                top=-90,
                scale=1,
                animate_position=ft.Animation(self._anim_ms(2600), "easeInOut"),
                animate_scale=ft.Animation(self._anim_ms(2600), "easeInOut"),
                shadow=orb_a_shadow,
            )

            self.orb_b = ft.Container(
                width=220,
                height=220,
                border_radius=220,
                gradient=ft.RadialGradient(
                    colors=[
                        ft.Colors.with_opacity(0.4 if not light_scene else 0.24, warm),
                        ft.Colors.with_opacity(0.0, warm),
                    ]
                ),
                blur=max(8, blur_value - 4),
                right=-90,
                top=120,
                scale=1,
                animate_position=ft.Animation(self._anim_ms(3200), "easeInOut"),
                animate_scale=ft.Animation(self._anim_ms(3200), "easeInOut"),
                shadow=orb_b_shadow,
            )

            self.orb_c = ft.Container(
                width=210,
                height=210,
                border_radius=210,
                gradient=ft.RadialGradient(
                    colors=[
                        ft.Colors.with_opacity(
                            0.34 if not light_scene else 0.2, theme["accent_soft"]
                        ),
                        ft.Colors.with_opacity(0.0, theme["accent_soft"]),
                    ]
                ),
                blur=max(8, blur_value - 6),
                right=25,
                bottom=-90,
                scale=1,
                animate_position=ft.Animation(self._anim_ms(3600), "easeInOut"),
                animate_scale=ft.Animation(self._anim_ms(3600), "easeInOut"),
            )

            controls.extend([self.orb_a, self.orb_b, self.orb_c])
        else:
            self.orb_a = None
            self.orb_b = None
            self.orb_c = None

        controls.append(content)
        controls.append(
            ft.Container(
                top=10,
                right=10,
                content=ft.Button(
                    self._t("exit_app"),
                    icon=ft.Icons.CLOSE_ROUNDED,
                    style=self._button_style("quiet"),
                    on_click=self._exit_app_click,
                ),
            )
        )
        return ft.Stack(expand=True, controls=controls)

    def _set_state_tint(self, color, opacity: float, update_now: bool = True):
        if self.state_tint is None:
            return

        normalized_opacity = self._clamp(opacity, 0.0, 0.38)
        cache_key = (str(color), round(normalized_opacity, 3))
        if cache_key == self._state_tint_cache:
            return

        self.state_tint.bgcolor = ft.Colors.with_opacity(normalized_opacity, color)
        self._state_tint_cache = cache_key
        if update_now:
            self._safe_update(self.state_tint)

    def _build_scoreboard_row(self):
        left = self.team_names[0]
        right = self.team_names[1]
        return self._surface_panel(
            padding=ft.Padding.symmetric(horizontal=14, vertical=10),
            radius=16,
            tone="soft",
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text(f"{left}: {self.match_scores.get(left, 0)}", size=14, weight="bold"),
                    ft.Text(
                        self._t("to_win", target=self.match_target),
                        size=12,
                        color=ft.Colors.with_opacity(0.74, ft.Colors.WHITE),
                    ),
                    ft.Text(f"{right}: {self.match_scores.get(right, 0)}", size=14, weight="bold"),
                ],
            ),
        )

    def _build_leaderboard_panel(self, limit: int = 8):
        items = self.leaderboard[:limit]
        rows = []
        if not items:
            rows.append(
                ft.Text(
                    self._t("records_empty"),
                    size=12,
                    color=ft.Colors.with_opacity(0.7, ft.Colors.WHITE),
                )
            )
        else:
            for idx, entry in enumerate(items, start=1):
                timestamp = entry.get("timestamp", "")
                try:
                    dt = datetime.fromisoformat(timestamp)
                    ts = dt.strftime("%d.%m %H:%M")
                except Exception:
                    ts = timestamp or "-"
                rows.append(
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(
                                f"#{idx} {entry.get('team', '-')}",
                                size=12,
                                weight="bold" if idx <= 3 else "normal",
                            ),
                            ft.Text(
                                f"{entry.get('score', 0)} очк.",
                                size=12,
                                color=ft.Colors.with_opacity(0.9, ft.Colors.WHITE),
                            ),
                            ft.Text(
                                ts,
                                size=11,
                                color=ft.Colors.with_opacity(0.6, ft.Colors.WHITE),
                            ),
                        ],
                    )
                )

        return self._surface_panel(
            padding=ft.Padding.all(14),
            radius=18,
            tone="soft",
            content=ft.Column(
                spacing=7,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(self._t("records_title"), size=16, weight="bold"),
                            ft.Text(
                                str(len(items)),
                                size=11,
                                color=ft.Colors.with_opacity(0.72, ft.Colors.WHITE),
                            ),
                        ],
                    ),
                    ft.Divider(height=8, color=ft.Colors.with_opacity(0.2, ft.Colors.WHITE)),
                    *rows,
                ],
            ),
        )
    # -------- Lobby --------

    def _build_lobby_start_cta(self, compact: bool):
        theme = self._theme()
        return self._surface_panel(
            width=360 if compact else 500,
            padding=ft.Padding.symmetric(horizontal=22 if compact else 28, vertical=22 if compact else 28),
            radius=24,
            tone="accent",
            ink=True,
            on_click=self.start_round_from_lobby,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Row(
                        spacing=14,
                        controls=[
                            ft.Container(
                                width=58 if compact else 68,
                                height=58 if compact else 68,
                                border_radius=18,
                                bgcolor=ft.Colors.with_opacity(0.14, ft.Colors.WHITE),
                                alignment=ft.Alignment(0, 0),
                                content=ft.Icon(
                                    ft.Icons.PLAY_ARROW_ROUNDED,
                                    size=30 if compact else 36,
                                    color=ft.Colors.WHITE,
                                ),
                            ),
                            ft.Column(
                                spacing=4,
                                controls=[
                                    ft.Text(
                                        self._t("start_round"),
                                        size=24 if compact else 30,
                                        weight="bold",
                                        color=ft.Colors.WHITE,
                                    ),
                                    ft.Text(
                                        self._t("topic_difficulty", subject=self.selected_subject, difficulty=self.selected_difficulty),
                                        size=11 if compact else 13,
                                        color=ft.Colors.with_opacity(0.9, ft.Colors.WHITE),
                                    ),
                                ],
                            ),
                        ],
                    ),
                    ft.Icon(
                        ft.Icons.ARROW_FORWARD_ROUNDED,
                        size=26,
                        color=ft.Colors.WHITE,
                    ),
                ],
            ),
        )

    def show_lobby(self):
        self.current_view = "lobby"
        compact = self._is_compact()
        stage_width = self._layout_width(desired=680, min_width=300, margin=22)

        self.team_a_input = ft.TextField(
            label=self._t("team_a"),
            value=self.team_names[0],
            border_radius=12,
        )
        self.team_b_input = ft.TextField(
            label=self._t("team_b"),
            value=self.team_names[1],
            border_radius=12,
        )

        teams_panel = self._section_panel(
            f"{self._t('team_a')} / {self._t('team_b')}",
            ft.ResponsiveRow(
                controls=[
                    ft.Container(col={"xs": 12, "md": 6}, content=self.team_a_input),
                    ft.Container(col={"xs": 12, "md": 6}, content=self.team_b_input),
                ]
            ),
            compact=compact,
            tone="soft",
        )

        hero = self._surface_panel(
            width=stage_width,
            radius=28,
            tone="strong",
            padding=ft.Padding.all(22 if compact else 28),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=16,
                controls=[
                    self._badge("SCool Alias", accent=True),
                    ft.Text(self._t("app_name"), size=32 if compact else 42, weight="bold"),
                    ft.Text(
                        self._t("current_turn", team=self.team_names[self.active_team_idx]),
                        size=14,
                        color=ft.Colors.with_opacity(0.75, ft.Colors.WHITE),
                        text_align=ft.TextAlign.CENTER,
                    ),
                    self._build_scoreboard_row(),
                    teams_panel,
                    self._build_lobby_start_cta(compact),
                    ft.Button(
                        self._t("settings"),
                        icon=ft.Icons.TUNE,
                        style=self._button_style("secondary"),
                        on_click=self.open_settings,
                    ),
                    ft.Text(
                        self._t("splash_tagline"),
                        size=12,
                        color=ft.Colors.with_opacity(0.62, ft.Colors.WHITE),
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
            ),
        )

        content = ft.SafeArea(
            content=ft.Container(
                expand=True,
                alignment=ft.Alignment(0, 0),
                padding=ft.Padding.all(12),
                content=hero,
            )
        )

        self.root.content = self._build_shell(content, scene_mode="light")
        self._safe_update()

    def show_setup(self):
        self.show_lobby()

    def _on_target_slider(self, e):
        slider_min = float(e.control.min if e.control.min is not None else 10)
        slider_max = float(e.control.max if e.control.max is not None else 100)
        value = self._normalize_slider_value(e.control.value, slider_min, slider_max, digits=0)
        e.control.value = value
        self.match_target = int(value)
        self.target_label.value = self._t("target_match", target=self.match_target)
        self.page.update(self.target_label)

    def _on_round_time_slider(self, e):
        slider_min = float(e.control.min if e.control.min is not None else 30)
        slider_max = float(e.control.max if e.control.max is not None else 180)
        value = self._normalize_slider_value(e.control.value, slider_min, slider_max, digits=0)
        e.control.value = value
        self.settings.round_time_seconds = int(value)
        self.round_time_label.value = self._t("round_time", seconds=self.settings.round_time_seconds)
        self.page.update(self.round_time_label)

    def start_round_from_lobby(self, _):
        team_a_value = getattr(getattr(self, "team_a_input", None), "value", self.team_names[0])
        team_b_value = getattr(getattr(self, "team_b_input", None), "value", self.team_names[1])
        new_names = self._safe_team_names(team_a_value, team_b_value)
        current_scores = [
            self.match_scores.get(self.team_names[0], 0),
            self.match_scores.get(self.team_names[1], 0),
        ]
        self.team_names = new_names
        self.match_scores = {
            self.team_names[0]: current_scores[0],
            self.team_names[1]: current_scores[1],
        }

        self._start_round(self.selected_subject, self.selected_difficulty)

    # -------- Settings --------

    def open_settings(self, _):
        self.return_view_from_settings = self.current_view
        self.show_settings()

    def show_settings(self):
        self.current_view = "settings"
        compact = self._is_compact()
        stage_width = self._layout_width(desired=660, min_width=320, margin=22)

        self.settings_quality_dd = ft.Dropdown(
            label=self._t("performance_mode"),
            value=self.settings.quality,
            options=[ft.dropdown.Option(x) for x in PERFORMANCE_PROFILES.keys()],
            border_radius=12,
        )
        self.settings_theme_dd = ft.Dropdown(
            label=self._t("interface_theme"),
            value=self.settings.theme_name,
            options=[ft.dropdown.Option(x) for x in THEME_PRESETS.keys()],
            border_radius=12,
        )
        self.subject_dd = ft.Dropdown(
            label=self._t("subject"),
            value=self.selected_subject,
            options=[ft.dropdown.Option(label) for label in self.subject_labels],
            border_radius=12,
        )
        self.difficulty_dd = ft.Dropdown(
            label=self._t("difficulty"),
            value=self.selected_difficulty,
            options=[ft.dropdown.Option(label) for label in self.difficulty_labels],
            border_radius=12,
        )
        self.target_label = ft.Text(self._t("target_match", target=self.match_target), size=12)
        self.target_slider = ft.Slider(
            min=10,
            max=100,
            divisions=18,
            value=self.match_target,
            on_change=self._on_target_slider,
        )
        self.round_time_label = ft.Text(
            self._t("round_time", seconds=self.settings.round_time_seconds), size=12
        )
        self.round_time_slider = ft.Slider(
            min=30,
            max=180,
            divisions=15,
            value=self.settings.round_time_seconds,
            on_change=self._on_round_time_slider,
        )
        self.anim_speed_label = ft.Text(
            self._t("anim_speed", value=f"{self.settings.animation_speed:.2f}"), size=12
        )
        self.anim_speed_slider = ft.Slider(
            min=0.6,
            max=1.8,
            value=self._normalize_slider_value(self.settings.animation_speed, 0.6, 1.8),
            divisions=12,
            on_change=self._on_anim_speed_change,
        )
        self.card_size_label = ft.Text(
            self._t("card_size", value=f"{self.settings.card_scale:.2f}"), size=12
        )
        self.card_size_slider = ft.Slider(
            min=0.85,
            max=1.25,
            value=self._normalize_slider_value(self.settings.card_scale, 0.85, 1.25),
            divisions=8,
            on_change=self._on_card_size_change,
        )
        self.sound_switch = ft.Switch(label=self._t("sound_swipe"), value=self.settings.sounds)
        self.vibration_switch = ft.Switch(
            label=self._t("vibration"), value=self.settings.vibration
        )

        round_panel = self._section_panel(
            self._t("setup_title"),
            ft.Column(
                spacing=8,
                controls=[
                    ft.ResponsiveRow(
                        controls=[
                            ft.Container(col={"xs": 12, "md": 7}, content=self.subject_dd),
                            ft.Container(col={"xs": 12, "md": 5}, content=self.difficulty_dd),
                        ]
                    ),
                    self.target_label,
                    self.target_slider,
                    self.round_time_label,
                    self.round_time_slider,
                    ft.Text(
                        self._t("words_language", lang=self._words_language_caption()),
                        size=12,
                        color=ft.Colors.with_opacity(0.78, ft.Colors.WHITE),
                    ),
                    self._language_selector(
                        selected_code=self.selected_words_language,
                        on_select=self._set_words_language,
                    ),
                    ft.TextField(
                        label=self._t("custom_words"),
                        hint_text=self._t("custom_words_hint"),
                        value=self.custom_words_text,
                        multiline=True,
                        min_lines=3,
                        max_lines=6,
                        border_radius=12,
                        on_change=self._on_custom_words_change,
                    ),
                ],
            ),
            compact=compact,
            tone="soft",
        )

        interface_panel = self._section_panel(
            self._t("settings_title"),
            ft.Column(
                spacing=8,
                controls=[
                    self.settings_quality_dd,
                    self.settings_theme_dd,
                    ft.Text(
                        self._t("ui_language", lang=self._ui_language_caption()),
                        size=12,
                        color=ft.Colors.with_opacity(0.78, ft.Colors.WHITE),
                    ),
                    self._language_selector(
                        selected_code=self.selected_ui_language,
                        on_select=self._set_ui_language,
                    ),
                    self.anim_speed_label,
                    self.anim_speed_slider,
                    self.card_size_label,
                    self.card_size_slider,
                    self.sound_switch,
                    self.vibration_switch,
                ],
            ),
            compact=compact,
            tone="soft",
        )

        card = self._surface_panel(
            width=stage_width,
            padding=ft.Padding.all(18),
            radius=22,
            tone="strong",
            content=ft.Column(
                spacing=12,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(self._t("settings_title"), size=21 if compact else 24, weight="bold"),
                            ft.Text(
                                self._t("settings_subtitle"),
                                size=12,
                                color=ft.Colors.with_opacity(0.7, ft.Colors.WHITE),
                            ),
                        ],
                    ),
                    round_panel,
                    interface_panel,
                    ft.ResponsiveRow(
                        columns=12,
                        run_spacing=8,
                        controls=[
                            ft.Container(
                                col={"xs": 12, "sm": 6},
                                content=ft.TextButton(self._t("cancel"), on_click=self._cancel_settings),
                            ),
                            ft.Container(
                                col={"xs": 12, "sm": 6},
                                alignment=ft.Alignment(1, 0),
                                content=ft.Button(
                                    self._t("save"),
                                    style=self._button_style("secondary"),
                                    on_click=self._save_settings,
                                ),
                            ),
                        ],
                    ),
                ],
            ),
        )

        content = ft.SafeArea(
            content=ft.Container(
                expand=True,
                alignment=ft.Alignment(0, 0),
                padding=ft.Padding.all(12),
                content=ft.Column(
                    scroll=ft.ScrollMode.AUTO,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[card],
                ),
            )
        )

        self.root.content = self._build_shell(content, scene_mode="none")
        self.page.update()

    def _on_anim_speed_change(self, e):
        slider_min = float(e.control.min if e.control.min is not None else 0.6)
        slider_max = float(e.control.max if e.control.max is not None else 1.8)
        value = self._normalize_slider_value(e.control.value, slider_min, slider_max)
        e.control.value = value
        self.anim_speed_label.value = self._t("anim_speed", value=f"{value:.2f}")
        self.page.update(self.anim_speed_label)

    def _on_card_size_change(self, e):
        slider_min = float(e.control.min if e.control.min is not None else 0.85)
        slider_max = float(e.control.max if e.control.max is not None else 1.25)
        value = self._normalize_slider_value(e.control.value, slider_min, slider_max)
        e.control.value = value
        self.card_size_label.value = self._t("card_size", value=f"{value:.2f}")
        self.page.update(self.card_size_label)

    def _cancel_settings(self, _):
        if self.return_view_from_settings == "round" and self.round_state:
            self.show_round()
        elif self.return_view_from_settings == "final" and self.last_round_result:
            self.show_final()
        elif self.return_view_from_settings == "setup":
            self.show_lobby()
        else:
            self.show_lobby()

    def _save_settings(self, _):
        self.settings.quality = self.settings_quality_dd.value or "Ultra"
        self.settings.theme_name = self.settings_theme_dd.value or "Ocean Neon"
        subject_value = self.subject_dd.value or self.subject_labels[0]
        difficulty_value = self.difficulty_dd.value or self.difficulty_labels[0]
        if subject_value not in self.subject_labels:
            subject_value = self.subject_labels[0]
        if difficulty_value not in self.difficulty_labels:
            difficulty_value = self.difficulty_labels[0]
        self.selected_subject = subject_value
        self.selected_difficulty = difficulty_value
        self.match_target = max(10, self._safe_int(self.target_slider.value, self.match_target))
        self.settings.round_time_seconds = int(
            self._normalize_slider_value(self.round_time_slider.value, 30, 180, digits=0)
        )
        self.settings.animation_speed = self._normalize_slider_value(
            self.anim_speed_slider.value, 0.6, 1.8
        )
        self.settings.card_scale = self._normalize_slider_value(
            self.card_size_slider.value, 0.85, 1.25
        )
        self.anim_speed_slider.value = self.settings.animation_speed
        self.card_size_slider.value = self.settings.card_scale
        self.settings.sounds = bool(self.sound_switch.value)
        self.settings.vibration = bool(self.vibration_switch.value)
        self._apply_custom_words()

        if self.return_view_from_settings == "round" and self.round_state:
            self.show_round()
        elif self.return_view_from_settings == "final" and self.last_round_result:
            self.show_final()
        elif self.return_view_from_settings == "setup":
            self.show_lobby()
        else:
            self.show_lobby()
    # -------- Round --------

    def _start_round(self, subject: str, difficulty_label: str):
        diff = DIFFICULTIES[difficulty_label]
        config = RoundConfig(
            subject=subject,
            difficulty_label=difficulty_label,
            difficulty_id=diff["id"],
            time_total=self.settings.round_time_seconds,
            penalty=diff["penalty"],
            team=self.team_names[self.active_team_idx],
            language_code=self.selected_words_language,
        )
        self.game_session = self.start_round_use_case.execute(
            config=config,
            word_provider=self.word_provider,
            rng=self.rng,
        )
        self.round_state = self.game_session.state
        self._update_game_vm()
        self._emit_game_event(
            GameEventType.ROUND_STARTED,
            subject=subject,
            difficulty=difficulty_label,
            team=self.round_state.team,
            language=self._words_language_caption(),
        )

        self.timer_token += 1
        self.flash_token = 0
        self.drag_dx = 0
        self.in_transition = False
        self.is_dragging = False

        self.show_round()
        self._next_word()
        self._update_round_hud()
        self._update_timer_hud()
        self.page.update()

        self.page.run_task(self._run_timer_loop, self.timer_token)
        self._play_sound("start")

    def show_round(self):
        self.current_view = "round"
        rs = self.round_state
        if rs is None:
            self.show_lobby()
            return

        theme = self._theme()
        profile = self._profile()

        compact = self._is_compact()
        page_height = self._layout_height(desired=880, min_height=540, margin=26)
        stage_width = self._layout_width(desired=760, min_width=320, margin=22)
        base_card_w = int(self._clamp(stage_width - (118 if compact else 130), 210, 340))
        card_w = int(self._clamp(base_card_w * self.settings.card_scale, 195, stage_width - 86))
        card_h = int(card_w * 1.28)
        max_card_h = int(self._clamp(page_height - (450 if compact else 490), 220, 430))
        if card_h > max_card_h:
            card_h = max_card_h
            card_w = int(self._clamp(card_h / 1.28, 190, stage_width - 86))
        deck_w = card_w + 90
        deck_h = card_h + 60
        card_left = (deck_w - card_w) / 2
        chip_width = None if compact else max(96, int((stage_width - 56) / 3))

        self.timer_ring = ft.ProgressRing(
            value=1.0,
            width=72,
            height=72,
            stroke_width=8,
            color=theme["accent"],
            bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
        )
        self.timer_text = ft.Text(
            self._format_time(rs.time_left),
            size=12,
            weight="bold",
            text_align=ft.TextAlign.CENTER,
        )

        timer_widget = ft.Stack(
            width=76,
            height=76,
            controls=[
                self.timer_ring,
                ft.Container(expand=True, alignment=ft.Alignment(0, 0), content=self.timer_text),
            ],
        )

        self.round_score_text = ft.Text("0", size=28, weight="bold")
        self.combo_text = ft.Text("x1", size=20, weight="bold", color=theme["warm"])
        self.correct_text = ft.Text("0", size=17, weight="bold")
        self.skipped_text = ft.Text("0", size=17, weight="bold")
        self.penalty_text = ft.Text(f"-{rs.penalty}", size=17, weight="bold", color=theme["bad"])
        self.team_turn_text = ft.Text(self._t("turn", team=rs.team), size=13)

        self.word_text = ft.Text(
            rs.current_word or "Готов?",
            size=29 if compact else 35,
            weight="bold",
            text_align=ft.TextAlign.CENTER,
        )
        self.card_status_text = ft.Text(
            self._t("swipe_hint"),
            size=13,
            color=ft.Colors.with_opacity(0.8, ft.Colors.WHITE),
            text_align=ft.TextAlign.CENTER,
        )

        self.left_hint = ft.Container(
            left=10,
            top=16,
            bgcolor=ft.Colors.with_opacity(0.18, theme["bad"]),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.44, theme["bad"])),
            border_radius=12,
            padding=ft.Padding.symmetric(horizontal=10, vertical=6),
            ignore_interactions=True,
            opacity=0,
            animate_opacity=ft.Animation(self._anim_ms(120), "easeOut"),
            content=ft.Text(self._t("skip_upper"), size=12, weight="bold", color=theme["bad"]),
        )
        self.right_hint = ft.Container(
            right=10,
            top=16,
            bgcolor=ft.Colors.with_opacity(0.18, theme["ok"]),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.44, theme["ok"])),
            border_radius=12,
            padding=ft.Padding.symmetric(horizontal=10, vertical=6),
            ignore_interactions=True,
            opacity=0,
            animate_opacity=ft.Animation(self._anim_ms(120), "easeOut"),
            content=ft.Text(self._t("correct_upper"), size=12, weight="bold", color=theme["ok"]),
        )

        self.event_fx_text = ft.Text("", size=20, weight="bold")
        self.event_fx = ft.Container(
            opacity=0,
            alignment=ft.Alignment(0, 0),
            animate_opacity=ft.Animation(self._anim_ms(150), "easeOut"),
            bgcolor=ft.Colors.with_opacity(0.0, ft.Colors.WHITE),
            border_radius=18,
            padding=ft.Padding.symmetric(horizontal=12, vertical=8),
            content=self.event_fx_text,
        )
        self.combo_burst_text = ft.Text("", size=26, weight="bold", color=theme["warm"])
        self.combo_burst = ft.Container(
            opacity=0,
            alignment=ft.Alignment(0, -0.1),
            animate_opacity=ft.Animation(self._anim_ms(170), "easeOut"),
            content=self.combo_burst_text,
        )

        back_1 = ft.Container(
            width=card_w,
            height=card_h,
            left=card_left,
            top=25,
            ignore_interactions=True,
            border_radius=24,
            bgcolor=ft.Colors.with_opacity(0.16, ft.Colors.WHITE),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.12, ft.Colors.WHITE)),
        )
        back_2 = ft.Container(
            width=card_w,
            height=card_h,
            left=card_left,
            top=16,
            ignore_interactions=True,
            border_radius=24,
            bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.18, ft.Colors.WHITE)),
        )

        self.card_drag_animation = ft.Animation(self._anim_ms(180), "easeOut")
        self.drag_live_animation = ft.Animation(40, "linear")
        card_shadow = [
            ft.BoxShadow(
                blur_radius=profile["card_shadow"],
                color=ft.Colors.with_opacity(0.28, theme["accent"]),
                offset=ft.Offset(0, 8),
            )
        ]
        self.card_idle_shadow = card_shadow
        self.card_base_left = float(card_left)
        self.card_base_top = 8.0
        self.card = ft.Container(
            width=card_w,
            height=card_h,
            left=self.card_base_left,
            top=self.card_base_top,
            ignore_interactions=True,
            opacity=1.0,
            rotate=0.0,
            animate_position=self.card_drag_animation,
            animate_rotation=self.card_drag_animation,
            animate_opacity=self.card_drag_animation,
            border_radius=24,
            padding=ft.Padding.all(20),
            gradient=ft.LinearGradient(
                colors=theme["card"],
                begin=ft.Alignment(-1, -1),
                end=ft.Alignment(1, 1),
            ),
            border=ft.Border.all(1.6, ft.Colors.with_opacity(0.52, theme["accent"])),
            shadow=card_shadow,
            content=ft.Column(
                expand=True,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text(
                        f"{rs.subject} · {rs.difficulty_label} · {self._words_language_caption()}",
                        size=12,
                        color=ft.Colors.with_opacity(0.78, ft.Colors.WHITE),
                    ),
                    ft.Container(
                        expand=True,
                        alignment=ft.Alignment(0, 0),
                        content=self.word_text,
                    ),
                    self.card_status_text,
                ],
            ),
        )

        self.deck = ft.Stack(
            width=deck_w,
            height=deck_h,
            controls=[back_1, back_2, self.card, self.left_hint, self.right_hint],
        )
        deck_gesture = ft.GestureDetector(
            content=self.deck,
            on_horizontal_drag_start=self.on_pan_start,
            on_horizontal_drag_update=self.on_pan_update,
            on_horizontal_drag_end=self.on_pan_end,
        )
        if hasattr(deck_gesture, "drag_interval"):
            deck_gesture.drag_interval = 5
        if hasattr(deck_gesture, "mouse_cursor"):
            deck_gesture.mouse_cursor = ft.MouseCursor.MOVE

        swipe_actions = ft.ResponsiveRow(
            columns=12,
            run_spacing=8,
            controls=[
                ft.Container(
                    col={"xs": 12, "sm": 6},
                    content=ft.Button(
                        self._t("skip_btn"),
                        icon=ft.Icons.CLOSE,
                        style=self._button_style("warn"),
                        on_click=lambda _: self._manual_swipe(False),
                    ),
                ),
                ft.Container(
                    col={"xs": 12, "sm": 6},
                    content=ft.Button(
                        self._t("correct_btn"),
                        icon=ft.Icons.CHECK,
                        style=self._button_style("cta"),
                        on_click=lambda _: self._manual_swipe(True),
                    ),
                ),
            ],
        )

        hud = ft.ResponsiveRow(
            columns=12,
            run_spacing=8,
            controls=[
                ft.Container(
                    col={"xs": 6, "sm": 3},
                    content=self._stat_chip(self._t("score_short"), self.round_score_text, theme["accent"], chip_width),
                ),
                ft.Container(
                    col={"xs": 6, "sm": 3},
                    content=self._stat_chip(self._t("combo_short"), self.combo_text, theme["warm"], chip_width),
                ),
                ft.Container(
                    col={"xs": 6, "sm": 3},
                    content=self._stat_chip(self._t("correct_short"), self.correct_text, theme["ok"], chip_width),
                ),
                ft.Container(
                    col={"xs": 6, "sm": 3},
                    content=self._stat_chip(self._t("skip_short"), self.skipped_text, theme["bad"], chip_width),
                ),
            ],
        )

        actions = ft.ResponsiveRow(
            columns=12,
            run_spacing=8,
            controls=[
                ft.Container(
                    col={"xs": 12, "sm": 4},
                    content=ft.Button(
                        self._t("settings"),
                        icon=ft.Icons.TUNE,
                        style=self._button_style("secondary"),
                        on_click=self.open_settings,
                    ),
                ),
                ft.Container(
                    col={"xs": 12, "sm": 4},
                    content=ft.Button(
                        self._t("end_round"),
                        icon=ft.Icons.TIMER_OFF,
                        style=self._button_style("warn"),
                        on_click=self._end_round_click,
                    ),
                ),
                ft.Container(
                    col={"xs": 12, "sm": 4},
                    content=ft.Button(
                        self._t("to_lobby"),
                        icon=ft.Icons.HOME,
                        style=self._button_style("ghost"),
                        on_click=self._go_lobby_click,
                    ),
                ),
            ],
        )

        top_line = ft.ResponsiveRow(
            columns=12,
            run_spacing=8,
            controls=[
                ft.Container(
                    col={"xs": 8, "sm": 9},
                    content=ft.Column(
                        spacing=2,
                        controls=[
                            ft.Text(self._t("round_title"), size=20 if compact else 22, weight="bold"),
                            self.team_turn_text,
                        ],
                    ),
                ),
                ft.Container(
                    col={"xs": 4, "sm": 3},
                    alignment=ft.Alignment(1, 0),
                    content=timer_widget,
                ),
            ],
        )

        stage = self._surface_panel(
            width=stage_width,
            padding=ft.Padding.symmetric(horizontal=12 if compact else 16, vertical=12 if compact else 14),
            radius=24,
            tone="strong",
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=14,
                controls=[
                    top_line,
                    self._build_scoreboard_row(),
                    hud,
                    self.event_fx,
                    self.combo_burst,
                    deck_gesture,
                    swipe_actions,
                    ft.Text(
                        self._t("penalty_skip", penalty=rs.penalty),
                        size=12,
                        color=ft.Colors.with_opacity(0.72, ft.Colors.WHITE),
                    ),
                    actions,
                ],
            ),
        )

        content = ft.SafeArea(
            content=ft.Container(
                expand=True,
                alignment=ft.Alignment(0, 0),
                padding=ft.Padding.symmetric(horizontal=10 if compact else 14, vertical=10),
                content=ft.Column(
                    scroll=ft.ScrollMode.AUTO,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[stage, ft.Container(height=6)],
                ),
            )
        )

        self.root.content = self._build_shell(content, scene_mode="light")
        self._update_round_hud()
        self._update_timer_hud()
        self._safe_update()

    def _stat_chip(self, title: str, value_control, color, width: Optional[int] = None):
        return self._surface_panel(
            width=width if width and width > 0 else None,
            padding=ft.Padding.symmetric(horizontal=10, vertical=8),
            radius=14,
            tone="soft",
            content=ft.Column(
                spacing=2,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text(
                        title,
                        size=11,
                        color=ft.Colors.with_opacity(0.68, color),
                    ),
                    value_control,
                ],
            ),
        )

    def _button_style(self, kind: str = "primary"):
        theme = self._theme()
        common_shape = ft.RoundedRectangleBorder(radius=14)
        if kind == "secondary":
            return ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.with_opacity(0.18, theme["accent"]),
                padding=ft.Padding.symmetric(horizontal=14, vertical=13),
                shape=common_shape,
                side=ft.BorderSide(1, ft.Colors.with_opacity(0.34, theme["accent_soft"])),
            )
        if kind == "warn":
            return ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.with_opacity(0.18, theme["bad"]),
                padding=ft.Padding.symmetric(horizontal=14, vertical=13),
                shape=common_shape,
                side=ft.BorderSide(1, ft.Colors.with_opacity(0.42, theme["bad"])),
            )
        if kind == "ghost":
            return ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.WHITE),
                padding=ft.Padding.symmetric(horizontal=14, vertical=13),
                shape=common_shape,
                side=ft.BorderSide(1, ft.Colors.with_opacity(0.22, ft.Colors.WHITE)),
            )
        if kind == "quiet":
            return ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                padding=ft.Padding.symmetric(horizontal=12, vertical=10),
                shape=ft.RoundedRectangleBorder(radius=999),
                side=ft.BorderSide(1, ft.Colors.with_opacity(0.2, ft.Colors.WHITE)),
            )
        if kind == "cta":
            return ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.with_opacity(0.9, self._theme()["ok"]),
                padding=ft.Padding.symmetric(horizontal=18, vertical=16),
                shape=ft.RoundedRectangleBorder(radius=16),
                side=ft.BorderSide(1, ft.Colors.with_opacity(0.32, ft.Colors.WHITE)),
            )
        return ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.with_opacity(0.78, theme["accent"]),
            padding=ft.Padding.symmetric(horizontal=16, vertical=14),
            shape=common_shape,
            side=ft.BorderSide(1, ft.Colors.with_opacity(0.34, theme["accent_soft"])),
        )

    def _register_answer(self, is_correct: bool):
        session = self.game_session
        if session is None:
            return
        rs = session.state

        theme = self._theme()
        result = self.submit_answer_use_case.execute(session=session, is_correct=is_correct)
        if result.is_correct:
            self._play_sound("ok")
            self._flash_event_fx(f"+{max(0, result.score_delta)}", theme["ok"])
            if result.combo_triggered and rs.multiplier >= 2:
                self._trigger_combo_burst(rs.multiplier)
        else:
            self._play_sound("skip")
            self._flash_event_fx(f"-{rs.penalty}", theme["bad"])

        self.round_state = session.state
        self._update_game_vm()
        self._emit_game_event(
            GameEventType.ANSWER_SUBMITTED,
            is_correct=is_correct,
            score=rs.score,
            correct=rs.correct,
            skipped=rs.skipped,
            multiplier=rs.multiplier,
        )

    def _trigger_combo_burst(self, multiplier: int):
        profile = self._profile()
        if not profile["effects"]:
            return
        if self.combo_burst is None or self.combo_burst_text is None:
            return
        self.combo_burst_token += 1
        token = self.combo_burst_token
        self.page.run_task(self._combo_burst_loop, token, multiplier)

    async def _combo_burst_loop(self, token: int, multiplier: int):
        if token != self.combo_burst_token or self.combo_burst is None:
            return
        theme = self._theme()
        self.combo_burst_text.value = f"COMBO x{multiplier}"
        self.combo_burst_text.color = theme["warm"]
        self.combo_burst.opacity = 1.0
        if not self._safe_update(self.combo_burst):
            return
        await asyncio.sleep(self._anim_ms(320) / 1000)
        if token != self.combo_burst_token or self.combo_burst is None:
            return
        self.combo_burst.opacity = 0.0
        self._safe_update(self.combo_burst)

    def _flash_event_fx(self, text: str, color):
        if self.event_fx is None or self.event_fx_text is None:
            return
        self.event_fx_token += 1
        token = self.event_fx_token
        self.event_fx_text.value = text
        self.event_fx_text.color = color
        self.event_fx.bgcolor = ft.Colors.with_opacity(0.2, color)
        self.event_fx.opacity = 1.0
        if not self._safe_update(self.event_fx, self.event_fx_text):
            return
        self.page.run_task(self._fade_event_fx, token)

    async def _fade_event_fx(self, token: int):
        await asyncio.sleep(self._anim_ms(290) / 1000)
        if token != self.event_fx_token or self.event_fx is None:
            return
        self.event_fx.opacity = 0.0
        self._safe_update(self.event_fx)

    def _next_word(self):
        session = self.game_session
        if session is None:
            return
        self.round_state = session.state
        word = self.next_word_use_case.execute(session=session, empty_word="Нет слов")
        self._update_game_vm()
        self._emit_game_event(
            GameEventType.WORD_CHANGED,
            word=word,
            words_left=len(session.state.words_pool),
        )

        if hasattr(self, "word_text") and self.word_text is not None:
            self.word_text.value = word

    def _update_round_hud(self):
        rs = self.round_state
        if rs is None:
            return

        self.round_score_text.value = str(max(0, rs.score))
        self.combo_text.value = f"x{rs.multiplier}"
        self.correct_text.value = str(rs.correct)
        self.skipped_text.value = str(rs.skipped)
        self.penalty_text.value = f"-{rs.penalty}"
        self.team_turn_text.value = self._t("turn", team=rs.team)
        self.combo_text.color = self._theme()["warm"] if rs.multiplier > 1 else ft.Colors.WHITE

    def _update_timer_hud(self):
        rs = self.round_state
        if rs is None:
            return
        total = max(1, rs.time_total)
        ratio = self._clamp(rs.time_left / total, 0.0, 1.0)
        self.timer_ring.value = ratio
        self.timer_text.value = self._format_time(rs.time_left)
        theme = self._theme()
        if rs.time_left <= 10:
            self.timer_ring.color = theme["warm"]
        elif rs.time_left <= 20:
            self.timer_ring.color = theme["accent_soft"]
        else:
            self.timer_ring.color = theme["accent"]

    async def _run_timer_loop(self, token: int):
        session = self.game_session
        if session is None:
            return
        rs = session.state

        last = time.perf_counter()
        while True:
            if token != self.timer_token:
                return
            if self.current_view != "round":
                return
            if self.game_session is not session:
                return
            if session.is_finished():
                break
            if not self._page_is_active():
                return

            await asyncio.sleep(0.1)
            now = time.perf_counter()
            delta = max(0.0, now - last)
            last = now

            self.tick_round_use_case.execute(session=session, delta_seconds=delta)
            self.round_state = session.state
            self._update_game_vm()
            self._emit_game_event(
                GameEventType.TIME_UPDATED,
                time_left=round(session.state.time_left, 2),
                time_total=session.state.time_total,
            )
            self._update_timer_hud()
            if not self._safe_update(self.timer_ring, self.timer_text):
                return

        if token == self.timer_token and self.game_session is session and session.is_finished():
            self.finish_round("time")

    def _end_round_click(self, _):
        self.finish_round("manual")

    def _go_lobby_click(self, _):
        self.timer_token += 1
        self.drag_render_token += 1
        self.is_dragging = False
        self.game_session = None
        self.round_state = None
        self._update_game_vm()
        self.show_lobby()

    def finish_round(self, reason: str = "manual"):
        rs = self.round_state
        if rs is None:
            return

        for item in rs.reviewed_words or []:
            if item.status == WordReviewStatus.PENDING:
                item.status = WordReviewStatus.IGNORED

        self.timer_token += 1
        self.in_transition = False
        self.is_dragging = False

        score = max(0, self._safe_int(rs.score, 0))
        team = rs.team
        self.match_scores[team] = self.match_scores.get(team, 0) + score

        match_winner = None
        if self.match_scores.get(team, 0) >= self.match_target:
            match_winner = team

        timestamp = datetime.now().isoformat(timespec="seconds")
        entry = {
            "team": team,
            "score": score,
            "subject": rs.subject,
            "difficulty": rs.difficulty_label,
            "language": self._words_language_caption(),
            "correct": rs.correct,
            "skipped": rs.skipped,
            "best_streak": rs.best_streak,
            "timestamp": timestamp,
        }
        self._push_leaderboard_entry(entry)

        self.pending_team_idx = self.active_team_idx if match_winner else 1 - self.active_team_idx

        self.last_round_result = {
            "team": team,
            "score": score,
            "applied_score": score,
            "correct": rs.correct,
            "skipped": rs.skipped,
            "best_streak": rs.best_streak,
            "subject": rs.subject,
            "difficulty_label": rs.difficulty_label,
            "language": self._words_language_caption(),
            "reason": reason,
            "timestamp": timestamp,
            "match_winner": match_winner,
            "next_team": self.team_names[self.pending_team_idx],
            "team_total": self.match_scores.get(team, 0),
            "reviewed_words": self._serialize_reviewed_words(rs),
        }
        self._emit_game_event(
            GameEventType.ROUND_FINISHED,
            reason=reason,
            team=team,
            score=score,
            match_winner=match_winner,
        )
        self.game_session = None
        self.review_round_state = rs
        self.round_state = None
        self._update_game_vm()
        self._play_sound("end")
        self.show_final()

    # -------- Final --------

    def show_final(self):
        self.current_view = "final"
        result = self.last_round_result
        if not result:
            self.show_lobby()
            return

        compact = self._is_compact()
        stage_width = self._layout_width(desired=700, min_width=320, margin=22)
        team = result["team"]
        winner = result.get("match_winner")
        title = self._t("round_finished", team=team)
        subtitle = self._t("time_up") if result.get("reason") == "time" else self._t("round_stopped")
        if winner:
            subtitle = self._t("match_winner", winner=winner)

        summary_card = self._surface_panel(
            width=stage_width,
            padding=ft.Padding.all(18),
            radius=22,
            tone="strong",
            content=ft.Column(
                spacing=10,
                controls=[
                    ft.Text(title, size=22 if compact else 26, weight="bold"),
                    ft.Text(subtitle, size=13, color=ft.Colors.with_opacity(0.78, ft.Colors.WHITE)),
                    self._build_scoreboard_row(),
                    ft.ResponsiveRow(
                        columns=12,
                        run_spacing=8,
                        controls=[
                            ft.Container(
                                col={"xs": 6, "sm": 3},
                                content=self._result_tile(self._t("points"), str(result["score"])),
                            ),
                            ft.Container(
                                col={"xs": 6, "sm": 3},
                                content=self._result_tile(self._t("correct_short"), str(result["correct"])),
                            ),
                            ft.Container(
                                col={"xs": 6, "sm": 3},
                                content=self._result_tile(self._t("skip_short"), str(result["skipped"])),
                            ),
                            ft.Container(
                                col={"xs": 6, "sm": 3},
                                content=self._result_tile(self._t("best_streak"), str(result["best_streak"])),
                            ),
                        ],
                    ),
                    ft.Text(
                        self._t(
                            "topic_difficulty",
                            subject=result["subject"],
                            difficulty=result["difficulty_label"],
                        ),
                        size=12,
                        color=ft.Colors.with_opacity(0.74, ft.Colors.WHITE),
                    ),
                    ft.Text(
                        self._t("words_language", lang=result.get("language", self._words_language_caption())),
                        size=12,
                        color=ft.Colors.with_opacity(0.74, ft.Colors.WHITE),
                    ),
                    ft.Text(
                        self._t("team_total", team=team, total=result["team_total"]),
                        size=12,
                        color=ft.Colors.with_opacity(0.74, ft.Colors.WHITE),
                    ),
                    self._build_reviewed_words_panel(result.get("reviewed_words", [])),
                ],
            ),
        )

        next_button_label = self._t("new_match") if winner else self._t("next_round", team=result["next_team"])
        next_button_handler = self._start_new_match if winner else self._start_next_round

        buttons = ft.ResponsiveRow(
            columns=12,
            run_spacing=8,
            controls=[
                ft.Container(
                    col={"xs": 12, "sm": 4},
                    content=ft.Button(
                        next_button_label,
                        icon=ft.Icons.SKIP_NEXT if not winner else ft.Icons.RESTART_ALT,
                        style=self._button_style("secondary"),
                        on_click=next_button_handler,
                    ),
                ),
                ft.Container(
                    col={"xs": 12, "sm": 4},
                    content=ft.Button(
                        self._t("settings"),
                        icon=ft.Icons.TUNE,
                        style=self._button_style("ghost"),
                        on_click=self.open_settings,
                    ),
                ),
                ft.Container(
                    col={"xs": 12, "sm": 4},
                    content=ft.Button(
                        self._t("to_lobby"),
                        icon=ft.Icons.HOME,
                        style=self._button_style("ghost"),
                        on_click=lambda _: self.show_lobby(),
                    ),
                ),
            ],
        )

        content = ft.SafeArea(
            content=ft.Container(
                expand=True,
                alignment=ft.Alignment(0, 0),
                padding=ft.Padding.symmetric(horizontal=10 if compact else 14, vertical=10),
                content=ft.Column(
                    scroll=ft.ScrollMode.AUTO,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                    controls=[
                        summary_card,
                        ft.Container(width=stage_width, content=buttons),
                        ft.Container(width=stage_width, content=self._build_leaderboard_panel(limit=10)),
                        ft.Container(height=6),
                    ],
                ),
            )
        )

        self.root.content = self._build_shell(content, scene_mode="none")
        self._safe_update()

    def _result_tile(self, title: str, value: str):
        return self._surface_panel(
            padding=ft.Padding.symmetric(horizontal=10, vertical=9),
            radius=14,
            tone="soft",
            content=ft.Column(
                spacing=2,
                controls=[
                    ft.Text(title, size=11, color=ft.Colors.with_opacity(0.78, ft.Colors.WHITE)),
                    ft.Text(value, size=20, weight="bold"),
                ],
            ),
        )

    def _serialize_reviewed_words(self, rs: RoundState):
        return [
            {"word": item.word, "status": item.status}
            for item in (rs.reviewed_words or [])
        ]

    def _review_reaction(self, index: int, status: str, selected_status: str, icon: str, color):
        selected = status == selected_status
        return ft.Container(
            width=36,
            height=36,
            border_radius=18,
            alignment=ft.Alignment(0, 0),
            bgcolor=ft.Colors.with_opacity(0.9 if selected else 0.0, color),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.55 if selected else 0.22, color)),
            on_click=lambda _, idx=index, value=status: self._set_review_status(idx, value),
            content=ft.Text(
                icon,
                size=18,
                color=ft.Colors.BLACK if selected else ft.Colors.with_opacity(0.74, ft.Colors.WHITE),
                text_align=ft.TextAlign.CENTER,
            ),
        )

    def _build_reviewed_words_panel(self, reviewed_words):
        theme = self._theme()
        if not reviewed_words:
            return ft.Container()

        rows = [
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text(
                        item.get("word", ""),
                        size=14,
                        weight="bold",
                        expand=True,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    ft.Row(
                        spacing=6,
                        controls=[
                            self._review_reaction(i, WordReviewStatus.CORRECT, item.get("status"), "👍", theme["ok"]),
                            self._review_reaction(i, WordReviewStatus.IGNORED, item.get("status"), "–", theme["warm"]),
                            self._review_reaction(i, WordReviewStatus.SKIPPED, item.get("status"), "👎", theme["bad"]),
                        ],
                    ),
                ],
            )
            for i, item in enumerate(reviewed_words)
        ]

        return self._surface_panel(
            padding=ft.Padding.symmetric(horizontal=12, vertical=10),
            radius=16,
            tone="soft",
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Text(self._t("review_title"), size=15, weight="bold"),
                    ft.Text(
                        self._t("review_hint"),
                        size=11,
                        color=ft.Colors.with_opacity(0.7, ft.Colors.WHITE),
                    ),
                    *rows,
                ],
            ),
        )

    def _set_review_status(self, index: int, status: str):
        if not self.last_round_result or self.review_round_state is None:
            return
        if not (0 <= index < len(self.review_round_state.reviewed_words)):
            return

        self.review_round_state.reviewed_words[index].status = status
        recalculated = GameEngine().recalculate_from_reviews(self.review_round_state)
        result = self.last_round_result
        team = result["team"]
        previous_applied = self._safe_int(result.get("applied_score", result.get("score", 0)), 0)
        delta = recalculated.score - previous_applied
        self.match_scores[team] = max(0, self.match_scores.get(team, 0) + delta)

        winner = team if self.match_scores.get(team, 0) >= self.match_target else None
        self.pending_team_idx = self.active_team_idx if winner else 1 - self.active_team_idx
        result.update(
            {
                "score": recalculated.score,
                "applied_score": recalculated.score,
                "correct": recalculated.correct,
                "skipped": recalculated.skipped,
                "best_streak": recalculated.best_streak,
                "match_winner": winner,
                "next_team": self.team_names[self.pending_team_idx],
                "team_total": self.match_scores.get(team, 0),
                "reviewed_words": self._serialize_reviewed_words(self.review_round_state),
            }
        )
        self._refresh_leaderboard_entry(result)
        self.show_final()

    def _start_next_round(self, _):
        if not self.last_round_result:
            self.show_lobby()
            return
        self.active_team_idx = self.pending_team_idx
        self._start_round(self.selected_subject, self.selected_difficulty)

    def _on_custom_words_change(self, e):
        self.custom_words_text = e.control.value or ""

    def _apply_custom_words(self):
        custom_words = parse_user_words(self.custom_words_text)
        if hasattr(self.word_provider, "set_user_words"):
            self.word_provider.set_user_words(custom_words)

        self.subject_labels = self.word_provider.get_subjects(self.selected_words_language)
        if not self.subject_labels:
            self.subject_labels = list(DATA.keys())
        if custom_words:
            self.selected_subject = USER_WORDS_SUBJECT
        elif self.selected_subject not in self.subject_labels:
            self.selected_subject = self.subject_labels[0]

    def _start_new_match(self, _):
        self.match_scores = {self.team_names[0]: 0, self.team_names[1]: 0}
        self.active_team_idx = 0
        self.pending_team_idx = 1
        self.last_round_result = None
        self.game_session = None
        self.round_state = None
        self._update_game_vm()
        self.timer_token += 1
        self.show_lobby()

    # -------- Leaderboard --------

    def _load_leaderboard(self):
        if not LEADERBOARD_FILE.exists():
            return []
        try:
            data = json.loads(LEADERBOARD_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []

        if not isinstance(data, list):
            return []

        cleaned = []
        for row in data:
            if not isinstance(row, dict):
                continue
            cleaned.append(
                {
                    "team": str(row.get("team", "-"))[:40] or "-",
                    "score": self._safe_int(row.get("score", 0), 0),
                    "subject": str(row.get("subject", "")),
                    "difficulty": str(row.get("difficulty", "")),
                    "language": str(row.get("language", "Русский")),
                    "correct": self._safe_int(row.get("correct", 0), 0),
                    "skipped": self._safe_int(row.get("skipped", 0), 0),
                    "best_streak": self._safe_int(row.get("best_streak", 0), 0),
                    "timestamp": str(row.get("timestamp", "")),
                }
            )

        cleaned.sort(key=lambda x: (x["score"], x.get("timestamp", "")), reverse=True)
        return cleaned[:120]

    def _push_leaderboard_entry(self, entry):
        self.leaderboard.append(
            {
                "team": str(entry.get("team", "-")),
                "score": self._safe_int(entry.get("score", 0), 0),
                "subject": str(entry.get("subject", "")),
                "difficulty": str(entry.get("difficulty", "")),
                "language": str(entry.get("language", "Русский")),
                "correct": self._safe_int(entry.get("correct", 0), 0),
                "skipped": self._safe_int(entry.get("skipped", 0), 0),
                "best_streak": self._safe_int(entry.get("best_streak", 0), 0),
                "timestamp": str(entry.get("timestamp", "")),
            }
        )
        self.leaderboard.sort(key=lambda x: (x["score"], x.get("timestamp", "")), reverse=True)
        self.leaderboard = self.leaderboard[:120]
        self._save_leaderboard()

    def _refresh_leaderboard_entry(self, result):
        timestamp = str(result.get("timestamp", ""))
        team = str(result.get("team", ""))
        for row in self.leaderboard:
            if row.get("timestamp") == timestamp and row.get("team") == team:
                row["score"] = self._safe_int(result.get("score", 0), 0)
                row["correct"] = self._safe_int(result.get("correct", 0), 0)
                row["skipped"] = self._safe_int(result.get("skipped", 0), 0)
                row["best_streak"] = self._safe_int(result.get("best_streak", 0), 0)
                break
        self.leaderboard.sort(key=lambda x: (x["score"], x.get("timestamp", "")), reverse=True)
        self.leaderboard = self.leaderboard[:120]
        self._save_leaderboard()

    def _save_leaderboard(self):
        try:
            LEADERBOARD_FILE.write_text(
                json.dumps(self.leaderboard, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass

    # -------- Effects --------

    def _play_sound(self, kind: str):
        if not self.settings.sounds or not HAS_WINSOUND:
            return
        tones = {
            "start": (880, 70),
            "ok": (1080, 85),
            "skip": (380, 95),
            "end": (640, 160),
        }
        freq, duration = tones.get(kind, (620, 70))
        try:
            winsound.Beep(freq, duration)
        except Exception:
            pass

    async def _ambient_loop(self):
        while True:
            if not self._page_is_active():
                return

            wait_for = max(1.2, float(self._profile()["orb_interval"]))
            await asyncio.sleep(wait_for)

            if not self._page_is_active():
                return
            if self.orb_a is None or self.orb_b is None or self.orb_c is None:
                continue

            self.orb_a.left = self.rng.randint(-130, 40)
            self.orb_a.top = self.rng.randint(-100, 70)
            self.orb_a.scale = round(self.rng.uniform(0.92, 1.12), 2)

            self.orb_b.right = self.rng.randint(-95, 40)
            self.orb_b.top = self.rng.randint(40, 190)
            self.orb_b.scale = round(self.rng.uniform(0.9, 1.15), 2)

            self.orb_c.right = self.rng.randint(-40, 80)
            self.orb_c.bottom = self.rng.randint(-120, 20)
            self.orb_c.scale = round(self.rng.uniform(0.88, 1.12), 2)

            if not self._safe_update(self.orb_a, self.orb_b, self.orb_c):
                return


def main(page: ft.Page):
    AliasNeonApp(page)


if __name__ == "__main__":
    ft.run(main)
