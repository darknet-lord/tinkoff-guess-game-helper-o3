import re
from enum import Enum
from dataclasses import dataclass

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.checkbox import CheckBox
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
from tinkoff_guess_game_helper_py import guess


WORDS_COUNT = 5
LETTERS_COUNT = 5


class CachedWordLetterColor(Enum):
    GREY = "g"
    WHITE = "w"
    YELLOW = "y"

    @classmethod
    def string_to_color(cls, value):
        return getattr(cls, value.upper())


@dataclass
class CachedWordLetter:
    letter: str
    color: CachedWordLetterColor


class WordsCache:
    words = dict.fromkeys(range(7))

    def add(self, pos: int, word: dict):
        self.words[pos] = word

    @property
    def available_slots(self):
        count = len(self.words)
        for key, value in self.words.items():
            if value is None:
                return key, count
        return count, count

    @property
    def is_empty(self):
        return not any(self.words.values())

    def make_arguments(self):
        color_prefixes = {
            CachedWordLetterColor.GREY.value: "^",
            CachedWordLetterColor.WHITE.value: "?",
            CachedWordLetterColor.YELLOW.value: "=",
        }
        words = filter(lambda w: w is not None, self.words.values())
        for word in words:
            yield "".join(
                color_prefixes[cached_letter.color.value] + cached_letter.letter
                for cached_letter in word.values()
            )


words_cache = WordsCache()


class Color(Enum):
    GREY = (0.5, 0.5, 0.5, 1)
    WHITE = (1, 1, 1, 1)
    YELLOW = (1, 0.9, 0, 1)

    @classmethod
    def string_to_color(cls, colorname):
        return {
            CachedWordLetterColor.GREY.value: cls.GREY,
            CachedWordLetterColor.WHITE.value: cls.WHITE,
            CachedWordLetterColor.YELLOW.value: cls.YELLOW,
        }[colorname[0]]


class Letter(TextInput):
    _max_length = 1
    _ptrn = re.compile(r"^[а-я]*$")

    def __init__(self, letter=None, color=Color.GREY, **kwargs):
        super().__init__(**kwargs)
        self.letter = letter
        self.color = color

    def is_valid(self, text):
        if len(self.text) >= self._max_length:
            return False
        return bool(re.match(self._ptrn, text))

    def insert_text(self, substring, from_undo=False):
        text = substring.lower()
        if self.is_valid(text):
            self.letter = text

            if word := words_cache.words[self.current_word_id()]:
                if letter := word.get(self.current_letter_id()):
                    letter.letter = text
                else:
                    word[self.current_letter_id()] = CachedWordLetter(letter=text, color=CachedWordLetterColor.GREY)
            else:
                words_cache.words[self.current_word_id()] = {
                    self.current_letter_id(): CachedWordLetter(letter=text, color=CachedWordLetterColor.GREY)
                }
            return super().insert_text(text, from_undo=from_undo)

    def current_word_id(self):
        return next(
            int(id_[1])
            for id_, val in self.parent.parent.parent.parent.ids.items()
            if val == self.parent.parent
        )

    def current_letter_id(self):
        return next(
            int(id_[1])
            for id_, val in self.parent.parent.ids.items()
            if val == self.parent
        )


class ColorButton(ToggleButton):
    def change_color(self, color_name):
        color = Color.string_to_color(color_name).value
        current_word_id = self.current_word_id()
        current_letter_id = self.current_letter_id()

        if (w := words_cache.words[current_word_id]) and (letter := w[current_letter_id]):
            letter.color = CachedWordLetterColor.string_to_color(color_name)
            self.parent.parent.ids["letter"].background_color = color

    def current_word_id(self):
        return next(
            int(id_[1])
            for id_, val in self.parent.parent.parent.parent.parent.ids.items()
            if val == self.parent.parent.parent
        )

    def current_letter_id(self):
        return next(
            int(id_[1])
            for id_, val in self.parent.parent.parent.ids.items()
            if val == self.parent.parent
        )


class MainWindow(Screen):
    def on_pre_enter(self, *args):
        words = ((key, val) for key, val in words_cache.words.items() if val)
        for widx, cached_word in words:
            word_elem = self.ids[f"w{widx}"]
            for lidx, cached_letter in cached_word.items():
                letter_elem = word_elem.ids[f"l{lidx}"].children[1]
                letter_elem.text = cached_letter.letter
                # Change text input background color.
                letter_elem.background_color = Color.string_to_color(
                    cached_letter.color.value
                ).value
                # Grey buttons to pressed state.
                word_elem.ids[f"l{lidx}"].children[0].children[2].state = "down"


class ResultWindow(Screen):

    def on_pre_enter(self, *args):
        words = guess(list(words_cache.make_arguments()))

        box = self.ids["suggested_words"]
        box.clear_widgets()

        for word in words[:10]:
            row = BoxLayout(orientation="horizontal", height=100)
            row.add_widget(Label(text=word))
            box.add_widget(row)


class TinkoffGuessGameHelperApp(App):

    @staticmethod
    def _populate(main_window):
        initial_words = guess([])
        for word_idx, word in enumerate(initial_words):
            wi = f"w{word_idx}"
            words_cache.words[word_idx] = {}
            for letter_idx, letter in enumerate(word):
                main_window.ids[wi].ids[f"l{letter_idx}"].ids['letter'].text = letter
                words_cache.words[word_idx][letter_idx] = CachedWordLetter(
                    letter=letter, color=CachedWordLetterColor.GREY)

    def build(self):
        screen_manager = ScreenManager()
        main_window = MainWindow(name="MainWindow")
        self._populate(main_window)
        screen_manager.add_widget(main_window)
        screen_manager.add_widget(ResultWindow(name="ResultWindow"))
        return screen_manager
