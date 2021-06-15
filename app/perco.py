import json
from asyncio import sleep
from dataclasses import dataclass
from datetime import datetime, timedelta
from itertools import groupby
from random import randrange
from typing import List, Dict, Union

import aiohttp

from app.const import OPENED, CLOSED
from app.models import Door
from app.settings import logger


@dataclass
class EventSystem:
    plc_name: str
    time_label: str
    identifier: str
    time_shift: timedelta
    id: int

    @property
    def dt(self) -> datetime:
        return datetime.strptime(self.time_label, '%Y-%m-%d %H:%M:%S') - self.time_shift


class PercoClient:

    def __init__(self, url: str, login: str, password: str, timezone_shift_minutes: int = 180):
        self.url = url
        self.login = login
        self.password = password
        self._cookies = aiohttp.CookieJar(unsafe=True)
        self._states: Dict[int, str] = {}
        self.last_updated = []
        self.timezone_shift = timedelta(minutes=timezone_shift_minutes)
        self._last_event_id: int = 0

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

    async def _call(self, uri: str, data: dict, only_json: bool = True, headers=None) -> Union[list, dict, str]:
        if not await self.is_auth():
            await self.auth()

        async with aiohttp.ClientSession(cookie_jar=self._cookies, headers=headers) as session:
            async with session.post(f'{self.url}{uri}', data=data) as resp:
                text = await resp.text()
                try:
                    result = json.loads(text)
                except Exception:
                    result = {} if only_json else text

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
        logger.info('Update door states is started')
        while True:
            await self._update_states()
            await sleep(0.7)

    async def door_is_closed(self, door_id: int) -> Union[bool, None]:
        await sleep(1.6)
        state = self._states.get(door_id, '')
        if state:
            return state == CLOSED

    async def get_events(self, minutes_ago: int = 10) -> List[EventSystem]:
        now = datetime.utcnow() + self.timezone_shift
        dates = now - timedelta(minutes=minutes_ago), now
        dates = '#'.join([i.strftime('%Y-%m-%d %H:%M:%S') for i in dates])

        data = {
            'clientId': randrange(1, 1_000_000),
            'date': dates,
            '_search': 'true',
            'nd': int(now.timestamp() * 1000),
            'rows': 200,
            'page': 1,
            'sidx': '',
            'sord': 'asc',
            'autorefresh': 'false',
            'search_string': '',
            'column_list': '{}',
            'filters': '{"groupOp":"AND","rules":[{"field":"category","op":"eq","data":"События контроллеров системы '
                       'безопасности"},{"field":"subcategory","op":"eq","data":"13.2 События связанные с доступом по '
                       'коду идентификатора (категория 1)"}]}'
        }

        res = await self._call(
            '/administration/eventssystem', data, headers={'X-Requested-With': 'XMLHttpRequest'}
        )

        rows = res.get('rows', [])
        cells = [i['cell'] for i in rows if i.get('cell')]
        return [
            EventSystem(
                c['plc_name'], c['time_label'], c['identifier'], self.timezone_shift, int(c['id'])
            ) for c in cells
        ]

    async def check_events(self):
        logger.info('check events is started')
        await sleep(30)

        while True:
            events = await self.get_events(1)
            await sleep(3)
            actual_events = [e for e in events if e.id > self._last_event_id]

            if len(actual_events) < 3:
                continue

            for _, events in groupby(actual_events, key=lambda e: e.identifier + e.plc_name):
                events = list(events)
                max_dt = max([e.dt for e in events])
                min_dt = min([e.dt for e in events])

                if len(events) > 2 and max_dt - min_dt < timedelta(seconds=30):
                    self._last_event_id = max([e.id for e in events])
                    await self.invert_door_state(events[0].plc_name)

            await sleep(12)

    async def invert_door_state(self, name: str):
        door = await Door.filter(name=name).first()

        if not door:
            logger.warning(f'Door by name not found', name=name)
            return

        await self._update_states()

        state = self.door_states.get(door.id, '')

        if state == OPENED:
            await self.close_door(door.id)

        elif state == CLOSED:
            await self.open_door(door.id)
