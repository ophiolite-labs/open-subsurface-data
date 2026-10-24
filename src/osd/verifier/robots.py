"""robots.txt as RFC 9309 reads it (H3): the groups and rules of one file, matched against a URL.

Groups (section 2.2.1): a group is one or more `user-agent` lines followed by rules; it ends at the
next `user-agent` line after a rule, never at a blank line or a comment. Other records (`sitemap`,
`crawl-delay`) neither end a group nor count as rules. Rules before the first `user-agent` line
belong to no group and are ignored. Every group naming the product token (case-insensitive) is
combined into one; if none does, every `*` group is; if neither exists, no rules apply.

Rules (sections 2.2.2, 2.2.3): `allow` and `disallow` patterns match from the first octet of the
path (with its query); `*` is any run of characters, a trailing `$` ends the pattern. The match with
the most octets in its pattern wins and `allow` wins a tie; no match allows. An empty pattern is no
rule (an empty `disallow` allows). `/robots.txt` is always allowed.

Percent-encoding (section 2.2.2): both sides are compared as ASCII. Non-ASCII octets are encoded,
escapes are written in upper case, and an escaped unreserved character (`A-Z a-z 0-9 - . _ ~`) is
decoded; a literal `*` or `$` in the URL is encoded so that only a pattern's `%2A`/`%24` matches it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import cache
from urllib.parse import urlsplit

UNRESERVED = frozenset(b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~")
ESCAPE = re.compile(rb"%([0-9A-Fa-f]{2})")


def normalise(text: str, url: bool = False) -> str:
    """`text` as the ASCII octets RFC 9309 compares; `url` encodes a literal `*` and `$` too."""
    def unescape(m: re.Match) -> bytes:
        o = int(m.group(1), 16)
        return bytes([o]) if o in UNRESERVED else b"%" + m.group(1).upper()

    raw = ESCAPE.sub(unescape, text.encode("utf-8"))
    special = b"*$" if url else b""
    return "".join(f"%{o:02X}" if o > 0x7E or o <= 0x20 or o in special else chr(o) for o in raw)


@cache
def _pattern(path: str) -> re.Pattern:
    end = path.endswith("$")
    body = ".*".join(re.escape(part) for part in (path[:-1] if end else path).split("*"))
    return re.compile(body + (r"\Z" if end else ""), re.DOTALL)


@dataclass(frozen=True)
class Rules:
    """The rules that apply to one product token: (allow, normalised pattern) pairs."""
    rules: tuple[tuple[bool, str], ...] = ()

    @classmethod
    def disallow_all(cls) -> Rules:
        return cls(((False, "/"),))

    def allowed(self, url: str) -> bool:
        u = urlsplit(url)
        if u.path == "/robots.txt":
            return True
        target = normalise((u.path or "/") + (f"?{u.query}" if u.query else ""), url=True)
        best = None  # (octets, allow): the longest match, allow above disallow at equal length
        for allow, path in self.rules:
            if _pattern(path).match(target) and (best is None or (len(path), allow) > best):
                best = (len(path), allow)
        return best is None or best[1]


def parse(text: str, token: str) -> Rules:
    """The rules of `text` for the product `token` (letters, `_` and `-`)."""
    groups: list[tuple[set[str], list[tuple[bool, str]]]] = []
    open_ = False  # the last group still takes user-agent lines (no rule seen since)
    for line in text.removeprefix("\ufeff").splitlines():  # a byte order mark is not part of the first key
        key, sep, value = line.split("#", 1)[0].partition(":")
        key, value = key.strip().lower(), value.strip()
        if not sep:
            continue
        if key == "user-agent":
            agent = "*" if value.startswith("*") else re.match(r"[A-Za-z_-]*", value).group().lower()
            if not open_:
                groups.append((set(), []))
                open_ = True
            groups[-1][0].add(agent)
        elif key in ("allow", "disallow") and groups:
            open_ = False
            if value:
                groups[-1][1].append((key == "allow", normalise(value if value[0] in "/*" else "/" + value)))
    for name in (token.lower(), "*"):
        if matched := [rules for agents, rules in groups if name in agents]:
            return Rules(tuple(r for rules in matched for r in rules))
    return Rules()
