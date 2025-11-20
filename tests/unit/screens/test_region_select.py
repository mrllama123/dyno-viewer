import pytest
from textual import work
from textual.app import App
from textual.reactive import reactive
from textual.widgets import ListView, Label

from dyno_viewer.components.screens.region_select import RegionSelect


@pytest.fixture()
def screen_app():
    class ScreensApp(App):
        BINDINGS = [
            ("r", "select_region", "Push Region Select Screen"),
        ]

        region = reactive("", recompose=True)

        def compose(self):
            yield Label(self.region or "No region selected")

        @work
        async def action_select_region(self) -> None:
            result = await self.push_screen_wait(RegionSelect())
            if result:
                self.region = result

    return ScreensApp


async def test_list_regions(iam, screen_app):
    async with screen_app().run_test() as pilot:
        await pilot.press("r")
        screen = pilot.app.screen
        assert isinstance(screen, RegionSelect)

        list_view: ListView = screen.query_one(ListView)
        regions = [item.id for item in list_view.children]
        assert regions == [
            "af-south-1",
            "ap-east-1",
            "ap-east-2",
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
            "ap-southeast-6",
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
        await pilot.press("r")
        screen = pilot.app.screen
        assert isinstance(screen, RegionSelect)

        await pilot.press("tab")

        assert screen.query_one(ListView).index == 0

        await pilot.press("down")

        assert screen.query_one(ListView).index == 1
        await pilot.press("down")

        assert screen.query_one(ListView).index == 2
        await pilot.press("enter")
        assert pilot.app.region == "ap-east-2"

        assert not screen.is_current
