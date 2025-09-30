"""Reddit OAuth helper used to fetch and cache access tokens."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import aiohttp


@dataclass
class RedditCredentials:
    client_id: str
    client_secret: str
    username: str
    password: str
    user_agent: str


class RedditOAuthClient:
    """Manage Reddit OAuth access tokens using username/password grant."""

    TOKEN_ENDPOINT = "https://www.reddit.com/api/v1/access_token"

    def __init__(
        self,
        credentials: Dict[str, Any],
        *,
        token_cache_path: Path,
        refresh_margin: int = 300,
        verbose: bool = False,
    ) -> None:
        self.verbose = verbose
        self.refresh_margin = max(int(refresh_margin), 0)
        self.cache_path = Path(token_cache_path)

        try:
            self.credentials = RedditCredentials(
                client_id=str(credentials['client_id']).strip(),
                client_secret=str(credentials['client_secret']).strip(),
                username=str(credentials['username']).strip(),
                password=str(credentials['password']).strip(),
                user_agent=str(credentials.get('user_agent', 'find-demand/1.0')).strip() or 'find-demand/1.0',
            )
        except KeyError as exc:
            missing = exc.args[0]
            raise ValueError(f"缺少 Reddit OAuth 凭证字段: {missing}")

        self._token: Optional[str] = None
        self._token_expires_at: float = 0.0

    # ------------------------------------------------------------------
    async def get_token(self, session: aiohttp.ClientSession, *, force_refresh: bool = False) -> Optional[str]:
        now = time.time()

        if not force_refresh and self._token and now < self._token_expires_at - self.refresh_margin:
            return self._token

        if not force_refresh and self._load_cached_token():
            if self._token and now < self._token_expires_at - self.refresh_margin:
                return self._token

        await self._request_new_token(session)
        return self._token

    async def invalidate_token(self) -> None:
        self._token = None
        self._token_expires_at = 0.0
        try:
            if self.cache_path.exists():
                self.cache_path.unlink()
        except OSError:
            pass

    # ------------------------------------------------------------------
    def _load_cached_token(self) -> bool:
        try:
            if not self.cache_path.exists():
                return False
            with self.cache_path.open('r', encoding='utf-8') as fh:
                payload = json.load(fh)
            token = payload.get('access_token')
            expires_at = float(payload.get('expires_at', 0))
            if not token or time.time() >= expires_at - self.refresh_margin:
                return False
            self._token = token
            self._token_expires_at = expires_at
            return True
        except Exception:
            return False

    def _save_cached_token(self) -> None:
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            with self.cache_path.open('w', encoding='utf-8') as fh:
                json.dump(
                    {
                        'access_token': self._token,
                        'expires_at': self._token_expires_at,
                        'cached_at': time.time(),
                    },
                    fh,
                    ensure_ascii=False,
                    indent=2,
                )
        except Exception:
            pass

    async def _request_new_token(self, session: aiohttp.ClientSession) -> None:
        auth = aiohttp.BasicAuth(self.credentials.client_id, self.credentials.client_secret)
        data = {
            'grant_type': 'password',
            'username': self.credentials.username,
            'password': self.credentials.password,
            'scope': 'read',
        }
        headers = {'User-Agent': self.credentials.user_agent}

        try:
            async with session.post(self.TOKEN_ENDPOINT, data=data, headers=headers, auth=auth) as response:
                payload = await response.json(content_type=None)
                if response.status != 200:
                    message = payload.get('message') if isinstance(payload, dict) else payload
                    self._log(f"获取 Reddit token 失败: status={response.status}, message={message}")
                    self._token = None
                    self._token_expires_at = 0.0
                    return

                token = payload.get('access_token')
                expires_in = int(payload.get('expires_in', 3600))
                if not token:
                    self._log(f"返回数据缺少 access_token: {payload}")
                    self._token = None
                    self._token_expires_at = 0.0
                    return

                self._token = token
                self._token_expires_at = time.time() + max(expires_in, 60)
                self._save_cached_token()
        except Exception as exc:
            self._log(f"请求 Reddit token 出错: {exc}")
            self._token = None
            self._token_expires_at = 0.0

    # ------------------------------------------------------------------
    def _log(self, message: str) -> None:
        if self.verbose:
            print(f"[RedditOAuth] {message}")

