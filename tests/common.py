from textual.pilot import Pilot


async def type_commands(commands: list[str], pilot: Pilot) -> None:
    for command in commands:
        if command not in ["up", "down", "left", "right", "enter", "tab"]:
            for char in command:
                await pilot.press(char)
        else:
            await pilot.press(command)
