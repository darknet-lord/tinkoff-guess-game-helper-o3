from kivy.app import App
from kivy.lang import Builder
from kivy.uix.scrollview import ScrollView

# Create both screens. Please note the root.manager.current: this is how
# you can control the ScreenManager from kv. Each screen has by default a
# property manager that gives you the instance of the ScreenManager used.
Builder.load_string(
    """
<MyView>:
    do_scroll_x: False
    do_scroll_y: True
    Label:
        size_hint_y: None
        height: self.texture_size[1]
        text_size: self.width, None
        padding: 10, 10
        text: "really some amazing text\\n" * 100


"""
)


# Declare both screens
class MyView(ScrollView):
    pass


class TestApp(App):
    def build(self):
        # Create the screen manager
        sm = MyView()
        return sm


if __name__ == "__main__":
    TestApp().run()
