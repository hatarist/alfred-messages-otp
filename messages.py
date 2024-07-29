#!/usr/bin/env python3
import codecs, datetime, json, re, subprocess


"""
Make sure to grant Alfred access: System Preferences - Privacy & Security - Full Disk Access.
If trying to debug, grant Full Disk Access to iTerm (or whatever), as well.
"""


SQL = """
SELECT
    name,
    created_at,
    text,
    body
FROM (
    SELECT
        message.rowid AS id,
        handle.uncanonicalized_id AS name,
        datetime(message.date/1000000000 + strftime('%s', '2001-01-01') ,'unixepoch','localtime') AS created_at,
        hex(message.text) AS text,
        hex(message.attributedBody) AS body
    FROM message
    LEFT JOIN handle ON message.handle_id = handle.rowid
    ORDER BY message.rowid DESC
    LIMIT {0}
)
WHERE
    1
    --AND created_at > datetime('now','-8 hours','localtime')
    AND name != '' AND (text != '' OR body != '')
;
"""

cmd = """sqlite3 ~/Library/Messages/chat.db -separator $'\t' -newline '\n'"""


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

    |

    # (comma and) any A-Z/0-9 character
    ,?\w
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


def get_messages(limit=20):
    p = subprocess.Popen([cmd], stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    sql = SQL.format(limit).encode()
    data = p.communicate(input=sql)[0].decode()

    messages = data.rstrip('\r\n').split('\n')

    results = []

    for message in messages:
        # print(message)
        parts = message.split('\t')

        if len(parts) == 3:
            name, dt, text = parts

            text = codecs.decode(text, 'hex').decode('utf-8')

        elif len(parts) == 4:
            name, dt, text, body = parts

            if not text:
                # deciphering serialized craziness
                payload = codecs.decode(body, 'hex')

                try:
                    text = payload.split(b"NSString")[1]
                    text = text[5:]
                    # shamelessly stolen from https://github.com/niftycode/imessage_reader/blob/c46379f6af0349ec9605fbb8d5e0c89db3913f12/imessage_reader/fetch_data.py#L74
                    if text[0] == 129:
                        length = int.from_bytes(text[1:3], "little")
                        text = text[3: length + 3]
                    else:
                        length = text[0]
                        text = text[1: length + 1]
                    text = text.decode()

                except Exception as e:
                    print("exception while trying to read attributedBody:", e)
                    continue
            else:
                text = codecs.decode(text, 'hex').decode('utf-8')
        
        else:
            # print('wtf? parts:', parts)
            continue

        dt = datetime.datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
        
        result = (name, dt, text)
        results.append(result)

    return results


def get_latest_messages():
    messages = get_messages()
    results = []
    for name, dt, text in messages:
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
