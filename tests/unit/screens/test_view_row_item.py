import pytest
from textual.app import App
from textual.widgets import Label

from dyno_viewer.components.screens.view_row_item import ViewRowItem


@pytest.fixture
def screen_app():

    class ScreensApp(App[None]):
        BINDINGS = {
            ("i", "item_info", "open item screen"),
        }

        item_payload = {}

        def compose(self):
            yield Label("item info main page")

        def action_item_info(self):
            self.push_screen(ViewRowItem(item=self.item_payload))

    return ScreensApp


@pytest.mark.skip(
    reason="textual snapshot tool needs to allow passing in app class, Keep for manual debugging"
)
async def test_empty_item_payload(screen_app):
    async with screen_app().run_test() as pilot:
        await pilot.press("i")


@pytest.mark.skip(
    reason="textual snapshot tool needs to allow passing in app class, Keep for manual debugging"
)
async def test_item_payload(screen_app):
    async with screen_app().run_test() as pilot:
        pilot.app.item_payload = {
            "pk": "1234567890",
            "sk": "Order1",
            "orderDate": "2023-05-17",
            "orderId": "1234567890",
            "totalAmount": 100,
        }
        await pilot.press("i")
        await pilot.pause()
