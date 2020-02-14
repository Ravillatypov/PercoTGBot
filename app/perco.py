import json
from typing import List, Dict, Union

import aiohttp

from app.settings import PERCO_LOGIN, PERCO_PASS, PERCO_URL, logger


class PercoClient:
    @staticmethod
    async def _call(uri: str, data: dict) -> Union[list, dict, str]:
        async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar(unsafe=True)) as session:
            async with session.post(f'{PERCO_URL}/login',
                                    data={'LoginForm[username]': PERCO_LOGIN,
                                          'LoginForm[password]': PERCO_PASS}
                                    ) as resp:
                logger.info(f'login status: {resp.status}')
            async with session.post(f'{PERCO_URL}{uri}', data=data) as resp:
                text = await resp.text()
                try:
                    result = json.loads(text)
                except:
                    logger.info(f'status: {resp.status}, text: {text}')
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
