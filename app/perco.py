import json
from asyncio import sleep
from typing import List, Dict, Union

import aiohttp

from app.const import OPENED, CLOSED


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
            async with session.post(f'{self.url}/login',
                                    data={'LoginForm[username]': self.login,
                                          'LoginForm[password]': self.password}
                                    ) as resp:
                pass

    async def _call(self, uri: str, data: dict) -> Union[list, dict, str]:
        async with aiohttp.ClientSession(cookie_jar=self._cookies) as session:
            async with session.post(f'{self.url}{uri}', data=data) as resp:
                text = await resp.text()
                try:
                    result = json.loads(text)
                except:
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
        await self.auth()
        counter = 0
        while True:
            counter += 1
            if counter > 300:
                await self.auth()
                counter = 0
            await self._update_states()
            await sleep(1)
