from . import vl, vrl
from src.libdamla.supar import Version, VersionRange, resolve_conflicts
import pytest


class TestResolveConflicts:
    def test_non_matching(self):
        assert resolve_conflicts(vl, vrl) == [
            Version("0.4.0"),
            Version("0.1.3"),
            Version("1.2.3"),
        ]

    def test_none_error(self):
        with pytest.raises(ValueError):
            resolve_conflicts(vl, [VersionRange("7.8")])

    def test_matching(self):
        assert resolve_conflicts(
            vl, [VersionRange("1"), VersionRange("1.2"), VersionRange(">=1, <2")]
        ) == [Version("1.2.3")]
