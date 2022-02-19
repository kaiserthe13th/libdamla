# Supar: Sürüm Parser

import re
from typing import List, Optional

_VER_RE = r"((?P<major>\d+)(\.(?P<minor>\d+)(\.(?P<patch>\d+)(-(?P<pre>\w+))?(\+(?P<build>\w+))?)?)?)|(?P<all>\*)"
_VER_RANGE_RE = rf"\s*(?P<cmp>[<>])(?P<eq>=)?\s*(?P<ver>{_VER_RE})\s*"
_VER_RE = re.compile(_VER_RE)
_VER_RANGE_RE = re.compile(_VER_RANGE_RE)


class Version:
    """A comparable version class"""

    def __init__(self, v, loose=False) -> None:
        m = _VER_RE.fullmatch(str(v))
        if m:
            if m.group("all"):
                if not loose:
                    raise ValueError("Invalid Version: Not Loose")
                self.major = None
                self.minor = None
                self.patch = None
                self.pre = None
                self.build = None
            else:
                self.major = int(m.group("major"))
                self.minor = m.group("minor")
                if self.minor:
                    self.minor = int(self.minor)
                elif not loose:
                    raise ValueError("Invalid Version: Not Loose")
                self.patch = m.group("patch")
                if self.patch:
                    self.patch = int(self.patch)
                elif not loose:
                    raise ValueError("Invalid Version: Not Loose")
                self.pre = m.group("pre")
                self.build = m.group("build")
        else:
            raise ValueError("Invalid Version: Incorrect Format")

    def __repr__(self) -> str:
        t = f"{self.major}"
        if self.minor is not None:
            t += f".{self.minor}"
            if self.patch is not None:
                t += f".{self.patch}"
                if self.pre is not None:
                    t += f"-{self.pre}"
                if self.build is not None:
                    t += f"+{self.build}"
        return t

    def __hash__(self) -> int:
        return hash((self.major, self.minor, self.patch, self.pre, self.build))

    def __eq__(self, o) -> bool:
        if o is None:
            return True
        if self.major is not None and o.major is not None:
            t = self.major == o.major
            if self.minor is not None and o.minor is not None:
                t = t and self.minor == o.minor
                if self.patch is not None and o.patch is not None:
                    t = t and self.patch == o.patch
                    if self.pre is not None and o.pre is not None:
                        t = t and self.pre == o.pre
                    if self.build is not None and o.build is not None:
                        t = t and self.build == o.build
        return t

    def __gt__(self, o):
        if o is None:
            return True
        tle = (
            self.major > o.major
            if self.major is not None and o.major is not None
            else True
        )
        teq = (
            self.major == o.major
            if self.major is not None and o.major is not None
            else False
        )
        if teq and self.minor is not None and o.minor is not None:
            tle = self.minor > o.minor
            teq = self.minor == o.minor
            if teq and self.patch is not None and o.patch is not None:
                tle = self.patch > o.patch
                teq = self.patch == o.patch
                if teq:
                    if self.pre is not None and o.pre is not None:
                        tle = self.pre > o.pre
                    if self.build is not None and o.build is not None:
                        tle = self.build > o.build
        return tle

    def __lt__(self, o):
        if o is None:
            return True
        tle = (
            self.major < o.major
            if self.major is not None and o.major is not None
            else True
        )
        teq = (
            self.major == o.major
            if self.major is not None and o.major is not None
            else False
        )
        if teq and self.minor is not None and o.minor is not None:
            tle = self.minor < o.minor
            teq = self.minor == o.minor
            if teq and self.patch is not None and o.patch is not None:
                tle = self.patch < o.patch
                teq = self.patch == o.patch
                if teq:
                    if self.pre is not None and o.pre is not None:
                        tle = self.pre < o.pre
                    if self.build is not None and o.build is not None:
                        tle = self.build < o.build
        return tle

    def __le__(self, o):
        return self < o or self == o

    def __ge__(self, o):
        return self > o or self == o


class VersionRange:
    """A range of `Version`s, it can compress multiple versions separated by `,` \
and annotated by one of `>`, `<`, `>=`, `<=` into a min and max value or \
take a single *loose* version and turn it into a min and max value"""

    def __init__(self, ver: str) -> None:
        self.min, self.min_eq, self.max, self.max_eq = self._parse(ver)

    def _parse(self, ver: str):
        try:
            v = Version(ver, loose=True)
            min = v
            min_eq = True
            max = v
            max_eq = True
        except ValueError:
            vers = ver.split(",")
            min = []
            min_eq = []
            max = []
            max_eq = []
            for ver in vers:
                m = _VER_RANGE_RE.fullmatch(ver)
                if not m:
                    raise ValueError("Invalid Version Range: Invalid Format")
                ver = Version(m.group("ver"), loose=True)
                cmp = m.group("cmp")
                eq = m.group("eq")
                if cmp == ">":
                    if eq:
                        min_eq.append(ver)
                    else:
                        min.append(ver)
                else:
                    if eq:
                        max_eq.append(ver)
                    else:
                        max.append(ver)
            min.sort()
            min_eq.sort()
            max.sort()
            max_eq.sort()

            min = min[-1] if min else None
            min_eq = min_eq[-1] if min_eq else None
            max = max[0] if max else None
            max_eq = max_eq[0] if max_eq else None
            if min is None and min_eq is not None:
                min = min_eq
                min_eq = True
            elif min >= min_eq:
                min_eq = False
            else:
                min = min_eq
                min_eq = True

            if max is None and max_eq is not None:
                max = max_eq
                max_eq = True
            elif max <= max_eq:
                max_eq = False
            else:
                max = max_eq
                max_eq = True
        return min, min_eq, max, max_eq

    def test(self, v) -> bool:
        v = Version(v, loose=True)
        return (v >= self.min if self.min_eq else v > self.min) and (
            v <= self.max if self.max_eq else v < self.max
        )

    def __contains__(self, v):
        return self.test(v)

    def join(self, vr):
        r = VersionRange("0")
        if self.max > vr.max:
            r.max, r.max_eq = vr.max, vr.max_eq
        elif self.max == vr.max:
            r.max, r.max_eq = self.max, self.max_eq
            if not all([self.max_eq, vr.max_eq]):
                r.max_eq = False
            else:
                r.max_eq = True
        else:
            r.max, r.max_eq = self.max, self.max_eq

        if self.min < vr.min:
            r.min, r.min_eq = vr.min, vr.min_eq
        elif self.max == vr.max:
            r.min, r.min_eq = self.min, self.min_eq
            if not all([self.min_eq, vr.min_eq]):
                r.min_eq = False
            else:
                r.min_eq = True
        else:
            r.min, r.min_eq = self.min, self.min_eq
        return r

    def __repr__(self) -> str:
        return f'(>{"=" if self.min_eq else ""} {self.min}, <{"=" if self.max_eq else ""} {self.max})'

    def __str__(self) -> str:
        return f'>{"=" if self.min_eq else ""} {self.min}, <{"=" if self.max_eq else ""} {self.max}'

    def test_multiple(self, *vers) -> List[Version]:
        return [*filter(self.test, vers)]


def filter_matches(ver: List[Version], vrs: VersionRange) -> List[Version]:
    return [*filter(lambda v: v in vrs, ver)]


def max_match(ver: List[Version], vr: VersionRange) -> Optional[Version]:
    try:
        return max(filter_matches(ver, vr))
    except ValueError:
        return None


def resolve_conflicts(vers: List[Version], vrs: List[VersionRange]) -> List[Version]:
    narrow = [*vers]
    wide = []
    for i in vrs:
        f = filter_matches(narrow, i)
        if f:
            narrow = f
        else:
            g = filter_matches(vers, i)
            if not g:
                raise ValueError("No Version Fits in the Version Range")
            wide.append(i)
    if wide:
        return resolve_conflicts([*filter(lambda x: x not in narrow, vers)], wide) + [
            max(narrow)
        ]
    else:
        return [max(narrow)]
