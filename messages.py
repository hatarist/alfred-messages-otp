#!/usr/bin/env python3
import subprocess, json, re, datetime


SQL = b"""
SELECT
    name,
    created_at,
    text
FROM (
    SELECT
        message.rowid AS id,
        handle.uncanonicalized_id AS name,
        datetime(message.date/1000000000 + strftime("%s", "2001-01-01") ,"unixepoch","localtime") AS created_at,
        message.text
    FROM message
    LEFT JOIN handle ON message.handle_id = handle.rowid
    ORDER BY message.rowid DESC
    LIMIT 20
)
WHERE
    created_at > datetime("now","-8 hours","localtime")
;
"""

cmd = """sqlite3 ~/Library/Messages/chat.db -separator $'\t' -newline '\r'"""


# OTP_PATTERN = r'\b(\d{4,8})\b'
OTP_PATTERN = re.compile(
    r"""
    (?:^|\s|G-)\b
    (\d{4,8})   # OTP
    (?!  # isn't followed by:
    # ' USD' or '.12 USD'
    (?:\.\d{1,2})?\ [A-Z]{3}
    |

    # (dot and) any A-Z/0-9 character
    \.?\w
    )
    """,
    re.VERBOSE
)

OTP_PATTERN_WHITELIST = r''
OTP_PATTERN_BLACKLIST = r'(voicemail|голосов(ое|ых) сообщени[ея])'


def humanize_dt(dt):
    diff = datetime.datetime.now() - dt
    s = diff.seconds
    if diff.days > 7 or diff.days < 0:
        return dt.strftime('%Y-%M-%D')
    elif diff.days == 1:
        return '1 day ago'
    elif diff.days > 1:
        return '{} days ago'.format(diff.days)
    elif s <= 1:
        return 'just now'
    elif s < 60:
        return '{} seconds ago'.format(s)
    elif s < 120:
        return '1 minute ago'
    elif s < 3600:
        return '{} minutes ago'.format(s // 60)
    elif s < 7200:
        return '1 hour ago'
    else:
        return '{} hours ago'.format(s // 3600)


def parse_otp(text):
    if OTP_PATTERN_WHITELIST and not re.findall(OTP_PATTERN_WHITELIST, text):
        return
    
    if OTP_PATTERN_BLACKLIST and re.findall(OTP_PATTERN_BLACKLIST, text):
        return

    results = re.findall(OTP_PATTERN, text)
    if not results:
        return

    return results[0]


def get_latest_messages():
    p = subprocess.Popen([cmd], stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    data = p.communicate(input=SQL)[0].decode()
    messages = data.strip().split('\r')

    results = []

    for message in messages:
        name, dt, text = message.split('\t')
        dt = datetime.datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
        time_ago = humanize_dt(dt)

        otp = parse_otp(text)
        if otp is None:
            continue

        result = {
            # "title": text,
            # "subtitle": f"{name} @ {date}",
            "title": f"{otp} ({name} @ {time_ago})",
            "subtitle": text,
            "arg": otp,
        }
        results.append(result)

    return results


if __name__ == '__main__':
    results = get_latest_messages()
    data = json.dumps({"items": results}, ensure_ascii=False)
    print(data)
