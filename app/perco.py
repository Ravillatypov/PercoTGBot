from typing import List, Dict

import aiohttp

from app.settings import PERCO_LOGIN, PERCO_PASS, PERCO_URL, logger


class PercoClient:
    def __init__(self):
        self.jar = aiohttp.CookieJar(unsafe=True)
        self.client_id = None
        self.session = aiohttp.ClientSession(cookie_jar=self.jar)

    async def login(self):
        async with self.session as sess:
            resp = await sess.post(f'{PERCO_URL}/login', data={
                'LoginForm[username]': PERCO_LOGIN,
                'LoginForm[password]': PERCO_PASS
            })
            logger.info(f'login status: {resp.status}')

    async def open_door(self, door_id: int):
        await self._change_device_state(door_id, 0)

    async def _change_device_state(self, door_id: int, state_id: int):
        async with self.session as sess:
            resp = await sess.post(f'{PERCO_URL}/controlaccess/devicemanagement', data={
                'command[0][type]': '0',
                'command[0][plc]': f'{door_id}',
                'command[0][number]': '1',
                'command[0][value]': f'{state_id}'
            })
            logger.info(f'status: {resp.status}')

    async def close_door(self, door_id: int):
        await self._change_device_state(door_id, 1)

    async def get_doors(self) -> List[Dict[str, str]]:
        async with self.session as sess:
            resp = await sess.post(
                f'{PERCO_URL}/site/GetData',
                data={'type': 'plc', 'listType': 'list', 'showall': 'true'}
            )
            logger.info(f'login status: {resp.status}')
            return await resp.json()
