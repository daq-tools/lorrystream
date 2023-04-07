# Copyright (c) 2013-2023, The Kotori developers and contributors.
# Distributed under the terms of the GPLv3 license, see LICENSE.

import asyncio
import functools


def make_sync(func):
    """
    Click entrypoint decorator for wrapping asynchronous functions.

    https://github.com/pallets/click/issues/2033
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))

    return wrapper


def tornado_asyncio_run_forever():
    from tornado.platform.asyncio import AsyncIOMainLoop

    AsyncIOMainLoop().install()

    def run_asyncio_loop():
        loop = asyncio.get_event_loop()
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            loop.close()

    run_asyncio_loop()
