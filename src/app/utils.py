# Copyright (c) 2025 AccelByte Inc. All Rights Reserved.
# This is licensed software from AccelByte Inc, for limitations
# and restrictions contact your company contract manager.

from typing import Iterable

from environs import Env

from accelbyte_grpc_plugin.utils import create_env as _create_env


async def aiterize(iterable: Iterable):
    for item in iterable:
        yield item


def create_env(**kwargs) -> Env:
    env = _create_env(**kwargs)

    env("AB_BASE_URL")
    env("AB_CLIENT_ID")
    env("AB_CLIENT_SECRET")
    env("AB_NAMESPACE")

    return env
