import json


class Dynamic():

    @staticmethod
    def get_value(obj: dict, keys: list):
        for key in keys:
            obj = obj[key]
        return obj

    dynamic_keys_from_type = {
        1: ['item', 'content'],
        2: ['item', 'description'],
        4: ['item', 'content'],
        8: ['dynamic']
    }

    def __init__(self, card):

        desc = card['desc']
        user_name = desc['user_profile']['info']['uname']
        self.user_name = user_name
        self.timestamp = desc['timestamp']
        self.dynamic_id = desc['dynamic_id_str']
        self.user_id = desc['uid']

        _card = json.loads(card['card'])

        _type = desc['type']
        dynamic_keys = self.dynamic_keys_from_type[_type]

        self.content = self.get_value(_card, dynamic_keys)
        self.url = 'https://t.bilibili.com/{dynamic_id}'.format(dynamic_id=self.dynamic_id)
        self.raw = card
