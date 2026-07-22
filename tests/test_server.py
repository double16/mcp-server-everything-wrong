# Copyright 2025-2026 github.com/double16
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import unittest
from unittest.mock import AsyncMock, patch

from starlette.requests import Request
from starlette.responses import Response

from mcp_server_everything_wrong.server import APIKeyMiddleware, serve


class APIKeyMiddlewareTest(unittest.IsolatedAsyncioTestCase):
    async def request(self, path: str, authorization: str | None = None) -> Response:
        headers = []
        if authorization is not None:
            headers.append((b"authorization", authorization.encode()))
        request = Request(
            {
                "type": "http",
                "method": "POST",
                "path": path,
                "headers": headers,
                "scheme": "https",
                "server": ("testserver", 443),
                "client": ("127.0.0.1", 1234),
                "query_string": b"",
            }
        )
        middleware = APIKeyMiddleware(AsyncMock())
        call_next = AsyncMock(return_value=Response(status_code=204))
        return await middleware.dispatch(request, call_next)

    async def test_mcp_request_requires_configured_api_key(self):
        with patch.dict(os.environ, {"MCP_API_KEY": "secret"}):
            response = await self.request("/mcp")

        self.assertEqual(401, response.status_code)

    async def test_mcp_request_rejects_invalid_api_key(self):
        with patch.dict(os.environ, {"MCP_API_KEY": "secret"}):
            response = await self.request("/mcp", "wrong")

        self.assertEqual(401, response.status_code)

    async def test_mcp_request_accepts_raw_api_key(self):
        with patch.dict(os.environ, {"MCP_API_KEY": "secret"}):
            response = await self.request("/mcp", "secret")

        self.assertEqual(204, response.status_code)

    async def test_mcp_request_accepts_bearer_api_key(self):
        with patch.dict(os.environ, {"MCP_API_KEY": "secret"}):
            response = await self.request("/mcp", "Bearer secret")

        self.assertEqual(204, response.status_code)

    async def test_other_paths_do_not_require_api_key(self):
        with patch.dict(os.environ, {"MCP_API_KEY": "secret"}):
            response = await self.request("/health")

        self.assertEqual(204, response.status_code)

    async def test_api_key_is_optional_when_not_configured(self):
        with patch.dict(os.environ, {}, clear=True):
            response = await self.request("/mcp")

        self.assertEqual(204, response.status_code)


class StandaloneServerTest(unittest.IsolatedAsyncioTestCase):
    @patch("mcp_server_everything_wrong.server.Server")
    async def test_serve_runs_shared_asgi_application(self, server_class):
        server_class.return_value.serve = AsyncMock()

        await serve()

        config = server_class.call_args.args[0]
        self.assertEqual("0.0.0.0", config.host)
        self.assertEqual(8000, config.port)
        server_class.return_value.serve.assert_awaited_once_with()


if __name__ == "__main__":
    unittest.main()