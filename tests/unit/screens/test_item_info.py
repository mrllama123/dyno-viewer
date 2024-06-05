import pytest
from textual.app import App
from dyno_viewer.components.screens.item_info import ItemInfo
from textual.widgets import Label


@pytest.fixture
def screen_app():

    class ScreensApp(App[None]):
        BINDINGS = {
            ("i", "item_info", "open item screen"),
        }

 

        def compose(self):
            yield Label("item info main page")

        def action_item_info(self):
            self.push_screen(ItemInfo())

    return ScreensApp


async def test_empty_item_payload(screen_app):
    async with screen_app().run_test() as pilot:
        await pilot.press("i")


async def test_item_payload(screen_app):
    async with screen_app().run_test() as pilot:
        await pilot.press("i")
        pilot.app.screen.item_payload = {
            "pk": "1234567890",
            "sk": "Order1",
            "orderDate": "2023-05-17",
            "orderId": "1234567890",
            "totalAmount": 100,
        }
        await pilot.pause()
        

