#!/bin/env python
import pytest
import asyncio
import logging
from pyqwest import Client
from pyqwest.testing import ASGITransport
from mocap_wrapper.api.v1.task_connect import (
    TaskService,
    TaskServiceASGIApplication,
    TaskServiceClient,
)
from mocap_wrapper.api.v1.task_pb2 import GetResponse, Task

HOST = "127.0.0.1"
PORT = 8000
BASE_URL = f"http://{HOST}:{PORT}"
API_URL = BASE_URL + "/v1.{Service}/"

Log = logging.getLogger(__name__)


class Tasks(TaskService):
    """await client.post(Tasks.URL + 'Get')"""

    URL: str

    def __new__(cls):
        instance = super().__new__(cls)
        cls.URL = API_URL.format(Service=cls.__base__.__name__)
        return instance

    async def Get(self, request, ctx):
        print(f"{ctx.request_headers()=}")
        # task = Task()
        response = GetResponse(tasks=[])
        # ctx.response_headers()["get-version"] = "v1"
        return response


APP = TaskServiceASGIApplication(Tasks())


@pytest.mark.asyncio
async def test_get():
    client = TaskServiceClient(Tasks.URL, http_client=Client(ASGITransport(APP)))
    response = await client.get(Task(id="1"))
    print(f"{response=}")


async def entry():
    import uvicorn

    server = uvicorn.Server(config=uvicorn.Config(APP, host=HOST, port=PORT))
    bg_task = asyncio.create_task(server.serve())
    await asyncio.sleep(1)
    await test_get()
    await bg_task


if __name__ == "__main__":
    asyncio.run(test_get())
