from enum import Enum
from dataclasses import dataclass

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.checkbox import CheckBox
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from tinkoff_guess_game_helper_py import suggest, guess


WORDS_COUNT = 6
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


class ColorButton(ToggleButton):
    def change_color(self, color_name):
        color = Color.string_to_color(color_name).value
        current_word_id = self.current_word_id()
        current_letter_id = self.current_letter_id()
        words_cache.words[current_word_id][
            current_letter_id
        ].color = CachedWordLetterColor.string_to_color(color_name)
        print(current_word_id, current_letter_id)
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


class SuggestButton(Button):
    def suggest_words(self):
        app = App.get_running_app()
        app.root.current = "SuggestWordsWindow"


class LetterInput(TextInput):
    _max_length = 1

    def __init__(self, letter=None, color=Color.GREY, **kwargs):
        super().__init__(**kwargs)
        self.letter = letter
        self.color = color

    def insert_text(self, substring, from_undo=False):
        if len(self.text) < self._max_length:
            return super().insert_text(substring, from_undo=from_undo)


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


class SuggestCheckBox(CheckBox):
    def __init__(self, word, **kwargs):
        super().__init__(**kwargs)
        self.word = word


class SuggestWordsWindow(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.words = set([])

    def apply_suggestions(self):
        app = App.get_running_app()

        rng = iter(range(*words_cache.available_slots))
        for word in self.words:
            try:
                idx = next(rng)
                cached_word = {
                    i: CachedWordLetter(letter, CachedWordLetterColor.GREY)
                    for i, letter in enumerate(word)
                }
                words_cache.add(idx, cached_word)
            except StopIteration:
                break

        app.root.current = "MainWindow"

    def update_words(self, checkbox):
        if checkbox.active:
            self.words.add(checkbox.word)
        else:
            self.words.discard(checkbox.word)

    def on_pre_enter(self, *args):
        if words_cache.is_empty:
            words = suggest()
        else:
            print(list(words_cache.make_arguments()))
            words = guess(list(words_cache.make_arguments()))

        self.words.clear()
        box = self.ids["suggested_words"]
        box.clear_widgets()

        for word in words[:10]:
            row = BoxLayout(orientation="horizontal", height=100)
            chb = SuggestCheckBox(word=word, active=True)
            self.words.add(word)
            chb.bind(on_release=self.update_words)
            row.add_widget(chb)
            row.add_widget(Label(text=word))
            box.add_widget(row)


class TinkoffGuessGameHelperApp(App):
    def build(self):
        screen_manager = ScreenManager()
        screen_manager.add_widget(MainWindow(name="MainWindow"))
        screen_manager.add_widget(SuggestWordsWindow(name="SuggestWordsWindow"))
        return screen_manager
