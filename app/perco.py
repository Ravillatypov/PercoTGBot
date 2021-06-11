import json
from asyncio import sleep
from typing import List, Dict, Union

import aiohttp

from app.const import OPENED, CLOSED
from app.settings import logger


class PercoClient:
    def __init__(self, url: str, login: str, password: str):
        self.url = url
        self.login = login
        self.password = password
        self._cookies = aiohttp.CookieJar(unsafe=True)
        self._states: Dict[int, str] = {}
        self.last_updated = []

    async def auth(self):
        async with aiohttp.ClientSession(cookie_jar=self._cookies) as session:
            async with session.post(
                    f'{self.url}/login',
                    data={
                        'LoginForm[username]': self.login,
                        'LoginForm[password]': self.password,
                    }
            ):
                pass

    async def is_auth(self) -> bool:
        async with aiohttp.ClientSession(cookie_jar=self._cookies) as session:
            async with session.get(f'{self.url}', allow_redirects=False) as resp:
                location = resp.headers.get('Location', '')
                result = '/personal/staff' in location
        return result

    async def _call(self, uri: str, data: dict) -> Union[list, dict, str]:
        if not await self.is_auth():
            await self.auth()
        async with aiohttp.ClientSession(cookie_jar=self._cookies) as session:
            async with session.post(f'{self.url}{uri}', data=data) as resp:
                text = await resp.text()
                try:
                    result = json.loads(text)
                except Exception:
                    result = {}
        return result

    async def open_door(self, door_id: int):
        await self._change_device_state(door_id, 0)

    async def _change_device_state(self, door_id: int, state_id: int):
        await self._call(
            '/controlaccess/devicemanagement',
            {
                'command[0][type]': '0',
                'command[0][plc]': f'{door_id}',
                'command[0][number]': '1',
                'command[0][value]': f'{state_id}'
            }
        )

    async def close_door(self, door_id: int):
        await self._change_device_state(door_id, 1)

    async def get_doors(self) -> List[Dict[str, str]]:
        return await self._call(
            '/site/GetData',
            {'type': 'plc', 'listType': 'list', 'showall': 'true'}
        )

    async def _update_states(self):
        logger.info('update states started')
        states = await self._call('/js/deviceState.json.php', data={'request': 'getDeviceStateAll'})
        result = {}

        for item in states.get('status', {}).values():
            result[int(item['id'])] = CLOSED if item['reader_rkd1'] == '1' else OPENED

        self.last_updated = [k for k, v in result.items() if self._states.get(k, '') != v]
        self._states = result

    @property
    def door_states(self) -> Dict[int, str]:
        return self._states

    async def states_updater_task(self):
        logger.info('Update door states is started')
        while True:
            await self._update_states()
            await sleep(0.7)

    async def door_is_closed(self, door_id: int) -> Union[bool, None]:
        await sleep(1.6)
        state = self._states.get(door_id, '')
        if state:
            return state == CLOSED
