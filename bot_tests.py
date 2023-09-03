import asyncio
import discord.ext.test as dpytest

from byoctf_discord import bot


async def test_view_1():
    dpytest.configure(bot)
    await dpytest.message("!v 1")
    assert (
        dpytest.verify()
        .message()
        .contains()
        .content("challenge doesn't exist or isn't unlocked yet")
    )


async def test_view_5():
    dpytest.configure(bot)
    await dpytest.message("!v 5")
    assert dpytest.verify().message().contains().content("Title: challenge 5")


async def test_whoami():
    dpytest.configure(bot)
    await dpytest.message("!whoami")
    assert dpytest.verify().message().content("Hello World!")


asyncio.run(test_view_1())
asyncio.run(test_view_5())
asyncio.run(test_whoami())
