# Testing textual notes 

As there is no documentation for unit testing a textual app. I thought i would write up some notes on how to do unit testing for my benefit (as i will probably forget this :slightly_smiling_face:) and others

## how does it work ?

The way it works is that the `App` class has a special method called `run_test()` which runs the app in a headless mode and returns a context that has methods to simulate
pressing keys, hovering mouse etc. While this isn't documented there are some really good [examples](https://github.com/Textualize/textual/tree/main/tests) in the textual repo test folder. 
See this [discussion](https://github.com/Textualize/textual/discussions/2506#discussioncomment-5827644) for more info

## how to test 

to test textual apps. You need to run them as async functions so for that you need have pytest plugin: pytest-aiohttp installed as a dev dependency. Also as async tests are slower using concurrency for the tests is a good idea i used the pytest-xdist pytest plugin for that

in terms of the test structure, I have broken it down into testing the individual widgets/screens using [sort key filter](../tests/unit/query/test_sort_key_query.py) test as an example:

- create a class that inherits the `App`  class just like you normally do for creating textual apps. That adds the SortKeyFilter widget and any setup that needs to be done before testing:

```python
@pytest.fixture()
def app() -> App:
    class SortKeyFilterApp(App):
        def compose(self):
            yield SortKeyFilter()

    return SortKeyFilterApp
```

- in a test instantiate the class and call `run_test()` and from there you can simulate key presses, mouse and get app info e.g for `test_sort_key_value` test:

```python
async def test_sort_key_value(app):
    async with app().run_test() as pilot:
        await type_commands(["tab", "tab", "tab", "raven"], pilot)
        input_value = pilot.app.query_one("#attrValue")
        assert input_value.value == "raven"
```
this instantiates the app in a context then it simulate key presses, Which calls a [helper function](../tests/common.py) that wraps around the `pilot.press(char)`, Which i wrote to make the test
code less boilerplate as `pilot.press(char)` will only accept one key so when you are typing text into a Input widget like in this test it becomes a pain.Then lastly the pilot context object also has a reference to the app
object. So i use that to query for the Input value and assert if the typed out text is in the Input widget 
