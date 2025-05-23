import pytest
from textual.app import App
from textual.reactive import reactive
from textual.widgets import ListView

from dyno_viewer.components.screens.profile_select import ProfileSelectScreen


@pytest.fixture
def screen_app():
    class ScreensApp(App[None]):
        SCREENS = {"profile": ProfileSelectScreen}

        profile = reactive("")

        async def on_profile_select_screen_profile_selected(
            self, selected_profile: ProfileSelectScreen.ProfileSelected
        ) -> None:
            self.profile = selected_profile.profile

    return ScreensApp


async def test_list_profiles(iam, screen_app, mocker):
    mocker.patch(
        "dyno_viewer.components.screens.profile_select.get_available_profiles",
        return_value=["default", "dev", "test"],
    )
    async with screen_app().run_test() as pilot:
        await pilot.app.push_screen("profile")

        screen = pilot.app.get_screen("profile")
        assert screen.is_current

        list_view = screen.query_one(ListView)
        profiles = [item.id for item in list_view.children]
        assert profiles == ["default", "dev", "test"]


async def test_select_profiles(iam, screen_app, mocker):
    mocker.patch(
        "dyno_viewer.components.screens.profile_select.get_available_profiles",
        return_value=["default", "dev", "test"],
    )
    async with screen_app().run_test() as pilot:
        await pilot.app.push_screen("profile")

        screen = pilot.app.get_screen("profile")
        assert screen.is_current

        list_view = screen.query_one(ListView)


        await pilot.press("tab")

        assert list_view.index == 0

        await pilot.press("down")

        assert list_view.index == 1
        await pilot.press("down")

        assert list_view.index == 2

        await pilot.press("enter")

        assert pilot.app.profile == "test"

        assert not screen.is_current
