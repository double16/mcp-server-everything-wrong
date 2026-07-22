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

import asyncio
import json
import os
import unittest
from unittest.mock import Mock, patch


class LambdaHandlerTest(unittest.TestCase):
    @patch("mcp_server_everything_wrong.aws_lambda.create_app")
    @patch("mcp_server_everything_wrong.aws_lambda.Mangum")
    def test_handler_delegates_event_and_context_to_asgi_adapter(
        self, mangum_class, create_app
    ):
        from mcp_server_everything_wrong.aws_lambda import lambda_handler

        event = {"requestContext": {"http": {"method": "POST"}}}
        context = object()
        app = Mock()
        adapter_call = Mock(return_value={"statusCode": 204})
        create_app.return_value = app
        mangum_class.return_value = adapter_call

        response = lambda_handler(event, context)

        self.assertEqual({"statusCode": 204}, response)
        mangum_class.assert_called_once_with(app, lifespan="on")
        adapter_call.assert_called_once_with(event, context)


class LambdaMCPRequestTest(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()
        asyncio.set_event_loop(None)

    def test_each_initialize_request_starts_a_fresh_session_manager(self):
        from mcp_server_everything_wrong.aws_lambda import lambda_handler

        event = {
            "version": "2.0",
            "routeKey": "$default",
            "rawPath": "/mcp",
            "rawQueryString": "",
            "headers": {
                "accept": "application/json, text/event-stream",
                "content-type": "application/json",
                "host": "example.lambda-url.us-east-1.on.aws",
            },
            "requestContext": {
                "http": {
                    "method": "POST",
                    "path": "/mcp",
                    "protocol": "HTTP/1.1",
                    "sourceIp": "127.0.0.1",
                },
                "requestId": "test-request",
                "timeEpoch": 0,
            },
            "body": json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-06-18",
                        "capabilities": {},
                        "clientInfo": {"name": "test-client", "version": "1.0"},
                    },
                }
            ),
            "isBase64Encoded": False,
        }

        with patch.dict(os.environ, {}, clear=True):
            responses = [lambda_handler(event, object()) for _ in range(2)]

        for response in responses:
            self.assertEqual(200, response["statusCode"])
            data_line = next(
                line for line in response["body"].splitlines() if line.startswith("data: ")
            )
            payload = json.loads(data_line.removeprefix("data: "))
            self.assertEqual("2.0", payload["jsonrpc"])
            self.assertEqual(1, payload["id"])
            self.assertIn("result", payload)


if __name__ == "__main__":
    unittest.main()
