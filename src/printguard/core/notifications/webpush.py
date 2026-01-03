import asyncio
from dataclasses import dataclass
from typing import Optional

from pywebpush import WebPushException, webpush


@dataclass(frozen=True)
class WebPushSendResult:
    sent: int
    failed: int
    deleted: int


@dataclass(frozen=True)
class WebPushAttempt:
    ok: bool
    status_code: Optional[int] = None

    @property
    def should_delete(self) -> bool:
        # 410 Gone: subscription is no longer valid (permissions reset)
        # 404 Not Found: some push services return this for expired subscriptions
        return self.status_code in {404, 410}


class WebPushClient:
    def __init__(self, *, vapid_private_key: str, vapid_subject: str):
        self._vapid_private_key = vapid_private_key
        self._vapid_claims = {"sub": vapid_subject}

    async def send(
        self,
        *,
        endpoint: str,
        p256dh: str,
        auth: str,
        payload_json: str,
        ttl: int = 60,
    ) -> WebPushAttempt:
        subscription_info = {
            "endpoint": endpoint,
            "keys": {"p256dh": p256dh, "auth": auth},
        }

        def _send_sync() -> WebPushAttempt:
            try:
                webpush(
                    subscription_info,
                    data=payload_json,
                    vapid_private_key=self._vapid_private_key,
                    vapid_claims=self._vapid_claims,
                    ttl=ttl,
                )
                return WebPushAttempt(ok=True)
            except WebPushException as e:
                status_code = None
                if getattr(e, "response", None) is not None:
                    status_code = getattr(e.response, "status_code", None)
                return WebPushAttempt(ok=False, status_code=status_code)

        return await asyncio.to_thread(_send_sync)
