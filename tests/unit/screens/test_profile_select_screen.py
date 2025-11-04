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


async def test_select_profile_special_characters(iam, screen_app, mocker):
    mocker.patch(
        "dyno_viewer.components.screens.profile_select.get_available_profiles",
        return_value=[
            "default",
            "dev",
            "01111111_ReadOnly",
            "01111111_Admin",
            "54321111_Dev",
        ],
    )
    async with screen_app().run_test() as pilot:
        await pilot.press("p")

        await pilot.press("down", "down")

        await pilot.press("enter")

        assert pilot.app.profile == "01111111_ReadOnly"


async def test_select_profile_escape(iam, screen_app, mocker):
    mocker.patch(
        "dyno_viewer.components.screens.profile_select.get_available_profiles",
        return_value=["default", "dev", "test"],
    )
    async with screen_app().run_test() as pilot:
        await pilot.press("p")
        assert isinstance(pilot.app.screen, ProfileSelectScreen)

        await pilot.press("escape")
        assert not isinstance(pilot.app.screen, ProfileSelectScreen)

        assert pilot.app.profile == ""


async def test_select_profile_no_profiles(screen_app, mocker):
    mocker.patch(
        "dyno_viewer.components.screens.profile_select.get_available_profiles",
        return_value=[],
    )
    async with screen_app().run_test() as pilot:
        await pilot.press("p")
        assert isinstance(pilot.app.screen, ProfileSelectScreen)
        # Check that the ListView is empty
        list_view = pilot.app.screen.query_one(ListView)
        assert len(list_view.children) == 0
