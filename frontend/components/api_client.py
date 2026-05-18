from __future__ import annotations

from datetime import date
from typing import Any

import requests


class APIClient:
    def __init__(self, base_url: str):
        normalized_base = base_url.rstrip("/")
        # Backends in this project expose endpoints under /api.
        # Accept both BASE_URL and BASE_URL/api to avoid config mistakes.
        self.api_base = normalized_base if normalized_base.endswith("/api") else f"{normalized_base}/api"
        self.access_token: str | None = None

    def _url(self, path: str) -> str:
        return f"{self.api_base}{path}"

    def set_token(self, token: str | None) -> None:
        self.access_token = token

    def _auth_headers(self) -> dict[str, str]:
        if not self.access_token:
            return {}
        return {"Authorization": f"Bearer {self.access_token}"}

    def signup(self, username: str, email: str, password: str, name: str) -> dict[str, Any]:
        response = requests.post(
            self._url("/signup"),
            json={
                "username": username,
                "email": email,
                "password": password,
                "name": name,
            },
            timeout=15,
        )
        response.raise_for_status()
        return response.json()

    def login(self, username: str, password: str) -> dict[str, Any]:
        response = requests.post(
            self._url("/login"),
            json={"username": username, "password": password},
            timeout=15,
        )
        response.raise_for_status()
        return response.json()

    def get_tasks(self, user_id: int, day: date) -> list[dict[str, Any]]:
        response = requests.get(
            self._url("/tasks"),
            params={"user_id": user_id, "day": day.isoformat()},
            headers=self._auth_headers(),
            timeout=15,
        )
        response.raise_for_status()
        return response.json()

    def create_task(self, user_id: int, title: str, category: str, difficulty: str, day: date) -> dict[str, Any]:
        response = requests.post(
            self._url("/tasks"),
            json={
                "user_id": user_id,
                "title": title,
                "category": category,
                "difficulty": difficulty,
                "date": day.isoformat(),
            },
            headers=self._auth_headers(),
            timeout=15,
        )
        response.raise_for_status()
        return response.json()

    def update_task_status(self, task_id: int, status: str) -> dict[str, Any]:
        response = requests.patch(
            self._url(f"/tasks/{task_id}"),
            json={"status": status},
            headers=self._auth_headers(),
            timeout=15,
        )
        response.raise_for_status()
        return response.json()

    def compute_daily_score(self, user_id: int, day: date) -> dict[str, Any]:
        response = requests.post(
            self._url("/score/daily"),
            json={"user_id": user_id, "day": day.isoformat()},
            headers=self._auth_headers(),
            timeout=15,
        )
        response.raise_for_status()
        return response.json()

    def score_history(self, user_id: int) -> list[dict[str, Any]]:
        response = requests.get(
            self._url("/score/history"),
            params={"user_id": user_id},
            headers=self._auth_headers(),
            timeout=15,
        )
        response.raise_for_status()
        return response.json()

    def weekly_summary(self) -> dict[str, Any]:
        response = requests.get(
            self._url("/score/weekly-summary"),
            headers=self._auth_headers(),
            timeout=15,
        )
        response.raise_for_status()
        return response.json()

    def smart_insights(self) -> dict[str, Any]:
        response = requests.get(
            self._url("/insights/smart"),
            headers=self._auth_headers(),
            timeout=15,
        )
        response.raise_for_status()
        return response.json()

    def get_missed_tasks(self) -> dict[str, Any]:
        response = requests.get(
            self._url("/tasks/missed"),
            headers=self._auth_headers(),
            timeout=15,
        )
        response.raise_for_status()
        return response.json()

    def get_vapid_key(self) -> dict[str, Any]:
        response = requests.get(
            self._url("/push/vapid-key"),
            timeout=15,
        )
        response.raise_for_status()
        return response.json()

    def subscribe_push(self, endpoint: str, p256dh: str, auth: str) -> dict[str, Any]:
        response = requests.post(
            self._url("/push/subscribe"),
            json={"endpoint": endpoint, "p256dh": p256dh, "auth": auth},
            headers=self._auth_headers(),
            timeout=15,
        )
        response.raise_for_status()
        return response.json()

    def unsubscribe_push(self, endpoint: str) -> dict[str, Any]:
        response = requests.delete(
            self._url("/push/unsubscribe"),
            params={"endpoint": endpoint},
            headers=self._auth_headers(),
            timeout=15,
        )
        response.raise_for_status()
        return response.json()

    def send_test_push(self, title: str, body: str, url: str = "/") -> dict[str, Any]:
        response = requests.post(
            self._url("/push/send"),
            json={"title": title, "body": body, "url": url},
            headers=self._auth_headers(),
            timeout=15,
        )
        response.raise_for_status()
        return response.json()
    
    def get_goals(self) -> list[dict[str, Any]]:
        response = requests.get(
            self._url("/goals"),
            headers=self._auth_headers(),
            timeout=15,
        )
        response.raise_for_status()
        return response.json()
    
    def create_goal(self, title: str, category: str, deadline: date, goal_type: str) -> dict[str, Any]:
        response = requests.post(
            self._url("/goals"),
            json={
                "title": title,
                "category": category,
                "deadline": deadline.isoformat(),
                "goal_type": goal_type,
            },
            headers=self._auth_headers(),
            timeout=15,
        )
        response.raise_for_status()
        return response.json()
    
    def update_goal(self, goal_id: int, **kwargs) -> dict[str, Any]:
        response = requests.patch(
            self._url(f"/goals/{goal_id}"),
            json=kwargs,
            headers=self._auth_headers(),
            timeout=15,
        )
        response.raise_for_status()
        return response.json()
    
    def delete_goal(self, goal_id: int) -> dict[str, Any]:
        response = requests.delete(
            self._url(f"/goals/{goal_id}"),
            headers=self._auth_headers(),
            timeout=15,
        )
        response.raise_for_status()
        return response.json()
    
    def get_goals_analytics(self) -> dict[str, Any]:
        response = requests.get(
            self._url("/goals/analytics"),
            headers=self._auth_headers(),
            timeout=15,
        )
        response.raise_for_status()
        return response.json()
