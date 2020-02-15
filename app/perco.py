import json
from typing import List, Dict, Union
from datetime import datetime, timedelta
from app.const import OPENED, CLOSED

import aiohttp

from app.settings import PERCO_LOGIN, PERCO_PASS, PERCO_URL, logger


class PercoClient:
    def __init__(self):
        self._states: Dict[int, str] = {}
        self._updated_timestamp: int = 0

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

    async def _update_states(self):
        states = await self._call('/js/deviceState.json.php', data={'request': 'getDeviceStateAll'})
        result = {}
        for item in states.get('statuses', {}).values():
            result[int(item['id'])] = OPENED if item['reader_rkd1'] == '1' else CLOSED
        self._states = result
        self._updated_timestamp = datetime.now().timestamp()

    async def get_doors_labels(self) -> Dict[int, str]:
        if datetime.now().timestamp() - self._updated_timestamp > 60:
            await self._update_states()
        return self._states
