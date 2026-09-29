import os, sys
sys.path.insert(0, os.getcwd())
import pytest

class SkipReporter:
    def pytest_collection_modifyitems(self, session, config, items):
        rows = []
        for item in items:
            mark = item.get_closest_marker("skip")
            if mark is not None:
                reason = mark.kwargs.get("reason", mark.args[0] if mark.args else "")
                rows.append((item.nodeid, reason))
        print("SKIP_COUNT", len(rows))
        for nodeid, reason in rows:
            print("SKIP", nodeid, "=>", reason)

pytest.main(["--collect-only", "-q"], plugins=[SkipReporter()])
