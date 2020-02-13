import re


def get_phone(text: str) -> str:
    text = text.replace(' ', '').replace('-', '')
    g = re.search(r'\d{10}', text)
    if g is None:
        return ''
    return '7' + g.group()

