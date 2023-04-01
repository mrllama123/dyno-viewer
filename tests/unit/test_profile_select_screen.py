from textual.app import App
from textual.screen import Screen
from textual.widgets import ListView, Label
from dyna_cli.components.screens.profile_select import ProfileSelectScreen
from textual.reactive import reactive
import pytest


@pytest.fixture
def screen_app():
    class ScreensApp(App[None]):
        SCREENS = {"profile": ProfileSelectScreen()}

        profile = reactive("")

        async def on_profile_select_screen_profile_selected(
            self, selected_profile: ProfileSelectScreen.ProfileSelected
        ) -> None:
            self.profile = selected_profile.profile

    return ScreensApp


async def test_list_profiles(iam, screen_app, mocker):
    mocker.patch(
        "dyna_cli.aws.session.get_available_profiles",
        return_value=["default", "dev", "test"],
    )
    async with screen_app().run_test() as pilot:
        await pilot.app.push_screen("profile")

        list_view = pilot.app.query_one(ListView)
        profiles = [item.id for item in list_view.children]
        assert profiles == ["default", "dev", "test"]
