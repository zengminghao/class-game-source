"""
pretty_date adapted from
https://stackoverflow.com/questions/1551382/user-friendly-time-format-in-python
"""

import time


def pretty_date(now):
    diff = int(time.time()) - now
    second_diff = diff % 86400
    day_diff = diff // 86400

    if diff < 0:
        return "future"
    if day_diff == 0:
        if second_diff < 10:
            return "just now"
        if second_diff < 60:
            return str(second_diff) + " seconds ago"
        if second_diff < 120:
            return "a minute ago"
        if second_diff < 3600:
            return str(second_diff // 60) + " minutes ago"
        if second_diff < 7200:
            return "an hour ago"
        if second_diff < 86400:
            return str(second_diff // 3600) + " hours ago"
    if day_diff == 1:
        return "yesterday"
    if day_diff < 7:
        return str(day_diff) + " days ago"
    if day_diff < 14:
        return "a week ago"
    if day_diff < 31:
        return str(day_diff // 7) + " weeks ago"
    if day_diff < 60:
        return "a month ago"
    if day_diff < 365:
        return str(day_diff // 30) + " months ago"
    if day_diff < 730:
        return "a year ago"
    return str(day_diff // 365) + " years ago"


"""
next_7am: written by myself
"""


def next_7am():
    now = int(time.time())
    nxt = (now // 86400 - 1) * 86400 + 23 * 3600
    while nxt < now:
        nxt += 86400
    dlt = nxt - now
    if dlt < 120 or dlt > 86400 - 120:
        return ""
    hours = dlt // 3600
    minutes = (dlt - hours * 3600) // 60

    hm, mm, duration, message = "", "", "", ""
    if hours >= 1:
        hm = "{} {}".format(hours, "hours" if hours > 1 else "hour")
    if minutes >= 1:
        mm = "{} {}".format(minutes, "minutes" if minutes > 1 else "minute")
    if len(hm) != 0 and len(mm) != 0:
        duration = hm + " and " + mm
    else:
        duration = hm + mm
    if len(duration) != 0:
        message = "The next action point update is in {}.".format(duration)
    return message


"""
html_escape adapted from
https://stackoverflow.com/questions/33490888/flask-html-escape-decorator
"""

html_escape_table = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;",
    ">": "&gt;",
    "<": "&lt;",
    '/': '&#x2F;',
    '`': '&#x60;'
}


def html_escape(text):
    return "".join(html_escape_table.get(c, c) for c in text)

