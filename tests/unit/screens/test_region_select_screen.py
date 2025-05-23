import pytest
from textual.app import App
from textual.reactive import reactive
from textual.widgets import ListView

from dyno_viewer.components.screens.region_select import RegionSelectScreen


@pytest.fixture()
def screen_app():
    class ScreensApp(App[None]):
        SCREENS = {"regionSelect": RegionSelectScreen}

        region = reactive("")

        async def on_region_select_screen_region_selected(
            self, selected_region: RegionSelectScreen.RegionSelected
        ) -> None:
            self.region = selected_region.region

    return ScreensApp


async def test_list_regions(iam, screen_app):
    async with screen_app().run_test() as pilot:
        await pilot.app.push_screen("regionSelect")
        screen = pilot.app.get_screen("regionSelect")

        list_view: ListView = screen.query_one(ListView)
        regions = [item.id for item in list_view.children]
        assert regions == [
            "af-south-1",
            "ap-east-1",
            "ap-northeast-1",
            "ap-northeast-2",
            "ap-northeast-3",
            "ap-south-1",
            "ap-south-2",
            "ap-southeast-1",
            "ap-southeast-2",
            "ap-southeast-3",
            "ap-southeast-4",
            "ap-southeast-5",
            "ap-southeast-7",
            "ca-central-1",
            "ca-west-1",
            "eu-central-1",
            "eu-central-2",
            "eu-north-1",
            "eu-south-1",
            "eu-south-2",
            "eu-west-1",
            "eu-west-2",
            "eu-west-3",
            "il-central-1",
            "me-central-1",
            "me-south-1",
            "mx-central-1",
            "sa-east-1",
            "us-east-1",
            "us-east-2",
            "us-west-1",
            "us-west-2",
        ]


# @pytest.mark.asyncio
async def test_select_region(iam, screen_app):
    async with screen_app().run_test() as pilot:
        await pilot.app.push_screen("regionSelect")

        screen = pilot.app.get_screen("regionSelect")
        assert screen.is_current

        await pilot.press("tab")

        assert screen.query_one(ListView).index == 0

        await pilot.press("down")

        assert screen.query_one(ListView).index == 1
        await pilot.press("down")

        assert screen.query_one(ListView).index == 2
        await pilot.press("enter")
        assert pilot.app.region == "ap-northeast-1"

        assert not screen.is_current
