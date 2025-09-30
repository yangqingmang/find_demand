import asyncio
import json
from pathlib import Path

from src.utils.reddit_client import RedditOAuthClient


class DummyResponse:
    def __init__(self, status: int, payload: dict):
        self.status = status
        self._payload = payload

    async def json(self, content_type=None):
        return self._payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class DummySession:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def post(self, url, data=None, headers=None, auth=None):
        self.calls.append({'url': url, 'data': data, 'headers': headers, 'auth': auth})
        response = self.responses[min(len(self.calls) - 1, len(self.responses) - 1)]
        return DummyResponse(response['status'], response['payload'])


def test_reddit_oauth_client_fetch_and_cache(tmp_path: Path):
    credentials = {
        'client_id': 'abc',
        'client_secret': 'def',
        'username': 'user',
        'password': 'pass',
        'user_agent': 'test-agent/1.0'
    }
    cache_path = tmp_path / 'token.json'
    client = RedditOAuthClient(credentials, token_cache_path=cache_path, refresh_margin=0)

    session = DummySession([
        {'status': 200, 'payload': {'access_token': 'token-1', 'expires_in': 3600}},
    ])

    async def scenario():
        token = await client.get_token(session)
        assert token == 'token-1'
        assert cache_path.exists()

        session.calls.clear()
        token_again = await client.get_token(session)
        assert token_again == 'token-1'
        assert not session.calls

        new_client = RedditOAuthClient(credentials, token_cache_path=cache_path, refresh_margin=0)
        new_session = DummySession([
            {'status': 200, 'payload': {'access_token': 'token-2', 'expires_in': 3600}}
        ])
        cached_token = await new_client.get_token(new_session)
        assert cached_token == 'token-1'
        refreshed_token = await new_client.get_token(new_session, force_refresh=True)
        assert refreshed_token == 'token-2'

    asyncio.run(scenario())


def test_reddit_oauth_client_handle_failure(tmp_path: Path):
    credentials = {
        'client_id': 'abc',
        'client_secret': 'def',
        'username': 'user',
        'password': 'pass',
        'user_agent': 'test-agent/1.0'
    }
    client = RedditOAuthClient(credentials, token_cache_path=tmp_path / 'token.json')
    session = DummySession([
        {'status': 401, 'payload': {'message': 'invalid'}}
    ])

    async def scenario():
        token = await client.get_token(session, force_refresh=True)
        assert token is None
        assert not (tmp_path / 'token.json').exists()

    asyncio.run(scenario())
