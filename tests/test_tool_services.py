import importlib.util
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient


SERVICES = Path(__file__).resolve().parents[1] / "services"
TEST_KEY = "test-only-not-a-deployment-secret-0001"


class ToolServiceTests(unittest.TestCase):
    def load_service(self, service, key=TEST_KEY):
        environment = patch.dict(os.environ, {"API_KEY": key, "REQUIRE_API_KEY": "true"})
        environment.start()
        self.addCleanup(environment.stop)
        name = f"test_{service.replace('-', '_')}"
        spec = importlib.util.spec_from_file_location(name, SERVICES / service / "server.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        self.addCleanup(sys.modules.pop, name, None)
        spec.loader.exec_module(module)
        return module

    def test_inventory_health_and_authentication(self):
        service = self.load_service("inventory-mcp")
        with TestClient(service.app) as client:
            self.assertEqual(client.get("/health").status_code, 200)
            for headers in ({}, {"x-api-key": "wrong"}):
                self.assertEqual(client.post("/mcp", headers=headers, json={}).status_code, 401)
            response = client.post(
                "/mcp",
                headers={"x-api-key": TEST_KEY, "Accept": "application/json, text/event-stream"},
                json={
                    "jsonrpc": "2.0", "id": 1, "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-03-26", "capabilities": {},
                        "clientInfo": {"name": "test", "version": "1"},
                    },
                },
            )
            self.assertEqual(response.status_code, 200, response.text)

    def test_inventory_requires_key_when_protected(self):
        service = self.load_service("inventory-mcp", key="")
        with self.assertRaisesRegex(RuntimeError, "at least 32"):
            with TestClient(service.app):
                pass

    def test_work_orders_require_key_when_protected(self):
        service = self.load_service("work-orders-api", key="")
        with self.assertRaisesRegex(RuntimeError, "at least 32"):
            with TestClient(service.app):
                pass

    def test_work_orders_protect_every_operation(self):
        service = self.load_service("work-orders-api")
        with TestClient(service.app) as client:
            self.assertEqual(client.get("/health").status_code, 200)
            for method, path in [
                ("get", "/work-orders"),
                ("get", "/work-orders/WO-001"),
                ("post", "/work-orders"),
                ("patch", "/work-orders/WO-001"),
            ]:
                for headers in ({}, {"x-api-key": "wrong"}):
                    response = client.request(method, path, headers=headers, json={})
                    self.assertEqual(response.status_code, 401, f"{method} {path}")
            response = client.get("/work-orders", headers={"x-api-key": TEST_KEY})
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json())

    def test_work_order_spec_declares_header_security(self):
        service = self.load_service("work-orders-api")
        spec = service.app.openapi()
        self.assertEqual(
            spec["components"]["securitySchemes"]["APIKeyHeader"],
            {"type": "apiKey", "in": "header", "name": "x-api-key"},
        )
        for path, methods in spec["paths"].items():
            if path.startswith("/work-orders"):
                for operation in methods.values():
                    self.assertEqual(operation["security"], [{"APIKeyHeader": []}])

    def test_dashboard_parser_excludes_script_and_style(self):
        service = self.load_service("inventory-mcp")
        parser = service.DashboardText()
        parser.feed("<h1>Status</h1><style>.hidden{}</style><script>ignore()</script><p>Online</p>")
        self.assertEqual(parser.parts, ["Status", "Online"])


if __name__ == "__main__":
    unittest.main()
