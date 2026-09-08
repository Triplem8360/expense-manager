from __future__ import annotations

import logging
import os
from uuid import uuid4

from locust import HttpUser, between, events, task
from locust.env import Environment
from locust.exception import StopUser

logger = logging.getLogger(__name__)

API_PREFIX = "/api/v1"
ACCESS_COOKIE_NAME = "__Host-expense_access"
DEFAULT_PASSWORD = "LoadTestPassword123"


class ExpenseApiUser(HttpUser):
    """Simulate an authenticated user reading expense data."""

    wait_time = between(0.5, 2.0)

    def on_start(self) -> None:
        self._auth_headers: dict[str, str] = {}
        self._expense_id = _configured_expense_id()
        self._email = os.getenv("LOAD_TEST_EMAIL") or (
            f"loadtest-{uuid4().hex}@example.com"
        )
        self._password = os.getenv("LOAD_TEST_PASSWORD", DEFAULT_PASSWORD)

        if not os.getenv("LOAD_TEST_EMAIL"):
            self._register_user()
        self._login()
        if self._expense_id is None:
            self._discover_expense_id()

    @task(10)
    def list_expenses(self) -> None:
        self.client.get(
            f"{API_PREFIX}/expenses",
            headers=self._auth_headers,
            name="GET /api/v1/expenses",
        )

    @task(4)
    def list_filtered_expenses(self) -> None:
        self.client.get(
            f"{API_PREFIX}/expenses",
            params={
                "limit": 10,
                "currency": "USD",
                "sort_by": "amount",
                "sort_order": "desc",
            },
            headers=self._auth_headers,
            name="GET /api/v1/expenses [filtered]",
        )

    @task(5)
    def get_expense_detail(self) -> None:
        if self._expense_id is None:
            self.client.get(
                f"{API_PREFIX}/expenses",
                headers=self._auth_headers,
                name="GET /api/v1/expenses [empty detail fallback]",
            )
            return

        self.client.get(
            f"{API_PREFIX}/expenses/{self._expense_id}",
            headers=self._auth_headers,
            name="GET /api/v1/expenses/{expense_id}",
        )

    @task(1)
    def get_service_status(self) -> None:
        self.client.get(
            f"{API_PREFIX}/localization/status",
            name="GET /api/v1/localization/status",
        )

    @task(1)
    def get_persian_welcome_message(self) -> None:
        self.client.get(
            f"{API_PREFIX}/localization/welcome",
            headers={"Accept-Language": "fa"},
            name="GET /api/v1/localization/welcome [fa]",
        )

    def _register_user(self) -> None:
        registration_failed = False
        with self.client.post(
            f"{API_PREFIX}/auth/register",
            json={"email": self._email, "password": self._password},
            name="POST /api/v1/auth/register [setup]",
            catch_response=True,
        ) as response:
            if response.status_code != 201:
                response.failure(
                    f"User setup failed with status {response.status_code}"
                )
                registration_failed = True

        if registration_failed:
            raise StopUser()

    def _login(self) -> None:
        access_token: str | None = None
        login_failed = False
        with self.client.post(
            f"{API_PREFIX}/auth/login",
            json={"email": self._email, "password": self._password},
            name="POST /api/v1/auth/login [setup]",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"Login failed with status {response.status_code}")
                login_failed = True
            else:
                access_token = response.cookies.get(ACCESS_COOKIE_NAME)
                if not access_token:
                    response.failure("Login response did not set the access cookie")
                    login_failed = True

        if login_failed or access_token is None:
            raise StopUser()

        # Secure cookies are not sent over Compose's internal HTTP connection.
        # The raw header is limited to this load-test client.
        self.client.cookies.clear()
        self._auth_headers = {
            "Cookie": f"{ACCESS_COOKIE_NAME}={access_token}",
        }

    def _discover_expense_id(self) -> None:
        response = self.client.get(
            f"{API_PREFIX}/expenses",
            params={"limit": 1},
            headers=self._auth_headers,
            name="GET /api/v1/expenses [setup]",
        )
        if response.status_code != 200:
            return

        try:
            items = response.json()["items"]
            if items:
                self._expense_id = int(items[0]["id"])
        except (KeyError, TypeError, ValueError):
            logger.warning("Could not discover an expense ID from the list response")


def _configured_expense_id() -> int | None:
    value = os.getenv("LOAD_TEST_EXPENSE_ID", "").strip()
    if not value:
        return None
    try:
        expense_id = int(value)
    except ValueError:
        logger.warning("Ignoring invalid LOAD_TEST_EXPENSE_ID=%r", value)
        return None
    return expense_id if expense_id > 0 else None


@events.quitting.add_listener
def enforce_load_test_thresholds(
    environment: Environment,
    **_: object,
) -> None:
    stats = environment.stats.total
    max_failure_ratio = float(os.getenv("LOAD_TEST_MAX_FAILURE_RATIO", "0.01"))
    max_average_ms = float(os.getenv("LOAD_TEST_MAX_AVG_RESPONSE_MS", "500"))
    max_p95_ms = float(os.getenv("LOAD_TEST_MAX_P95_RESPONSE_MS", "1000"))
    p95_response_time = stats.get_response_time_percentile(0.95) or 0

    failures: list[str] = []
    if stats.num_requests == 0:
        failures.append("no requests were executed")
    if stats.fail_ratio > max_failure_ratio:
        failures.append(
            f"failure ratio {stats.fail_ratio:.2%} exceeded {max_failure_ratio:.2%}"
        )
    if stats.avg_response_time > max_average_ms:
        failures.append(
            f"average response time {stats.avg_response_time:.0f} ms exceeded "
            f"{max_average_ms:.0f} ms"
        )
    if p95_response_time > max_p95_ms:
        failures.append(
            f"p95 response time {p95_response_time:.0f} ms exceeded {max_p95_ms:.0f} ms"
        )

    if failures:
        logger.error("Load test thresholds failed: %s", "; ".join(failures))
        environment.process_exit_code = 1
