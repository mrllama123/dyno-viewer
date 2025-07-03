import pytest
from textual import work
from textual.app import App
from textual.reactive import reactive
from textual.widgets import ListView, Label

from dyno_viewer.components.screens.profile_select import ProfileSelectScreen


@pytest.fixture
def screen_app():
    class ScreensApp(App):
        # SCREENS = {"profile": ProfileSelectScreen}
        BINDINGS = [
            ("p", "select_profile", "Push Profile Select Screen"),
        ]

        profile = reactive("", recompose=True)

        def compose(self):
            yield Label(self.profile or "No profile selected")

        @work
        async def action_select_profile(self) -> None:
            result = await self.push_screen_wait(ProfileSelectScreen())
            if result:
                self.profile = result

    return ScreensApp


async def test_select_profiles(iam, screen_app, mocker):
    mocker.patch(
        "dyno_viewer.components.screens.profile_select.get_available_profiles",
        return_value=["default", "dev", "test"],
    )
    async with screen_app().run_test() as pilot:
        await pilot.press("p")

        await pilot.press("down")

        await pilot.press("down")

        await pilot.press("enter")

        assert pilot.app.profile == "test"
