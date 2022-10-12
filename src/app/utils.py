from typing import Iterable


async def aiterize(iterable: Iterable):
    for item in iterable:
        yield item
