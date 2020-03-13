import yaml
import json
import asyncio
import traceback
from aiohttp import request

dynamic_keys_from_type = {
    1: ['item', 'content'],
    2: ['item', 'description'],
    4: ['item', 'content'],
    8: ['dynamic']
}


def get_value(obj: dict, keys: list):
    for key in keys:
        obj = obj[key]
    return obj


def get_dynamic(card: dict):
    item = {}
    try:
        desc = card['desc']
        user_name = desc['user_profile']['info']['uname']
        item['user_name'] = user_name
        item['timestamp'] = desc['timestamp']
        item['dynamic_id'] = desc['dynamic_id_str']

        _card = json.loads(card['card'])

        _type = desc['type']
        dynamic_keys = dynamic_keys_from_type[_type]
        item['dynamic'] = get_value(_card, dynamic_keys)
    except Exception:
        traceback.print_exc()
    return item


async def user_dynamic(user_id: str) -> dict:
    api_url = 'https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/space_history'
    async with request("GET", api_url, params={'host_uid': user_id, 'visitor_id': "0", 'offset_dynamic_id': "0"}) as response:
        cards = (await response.json())['data']['cards']

        return [get_dynamic(card) for card in cards]


def filter_dynamic(items: list, timestamp: int):
    return [item for item in items if item['timestamp'] > timestamp]


async def user_new_dynamic(user_ids, timestamp: int):
    new_dynamics = []
    for user_id in user_ids:
        dynamics = await user_dynamic(user_id)

        _new_dynamics = filter_dynamic(dynamics, timestamp)
        print(len(_new_dynamics) != 0)
        if _new_dynamics != []:
            new_dynamics.append(_new_dynamics)

    return new_dynamics


async def room_statu(room_id: str):
    room_info_url = 'https://api.live.bilibili.com/room/v1/Room/get_info'
    async with request('GET', room_info_url, params={'room_id': room_id}) as resp:
        response = (await resp.json())

        if response['msg'] == 'ok':
            return response['data']['live_status'] == 1
        else:
            raise ValueError(str(response))


async def monitor(timestamp: int):
    config = yaml.safe_load(open('./bilibili.yaml', 'rb'))
    user_ids = config['user_ids']
    room_ids = config['room_ids']

    if type(user_ids) != list:
        user_ids = [user_ids]

    if type(room_ids) != list:
        room_ids = [room_ids]

    print(user_ids)
    print(room_ids)

    new_dynamics = await user_new_dynamic(user_ids, timestamp)

    live_rooms = ['https://live.bilibili.com/' + str(room_id)
                  for room_id in room_ids if await room_statu(room_id)]

    return {'dynamic': new_dynamics, 'live': live_rooms}


if __name__ == "__main__":
    asyncio.run(monitor(1583232556))
