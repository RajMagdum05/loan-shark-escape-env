import pytest
import sys

class FailureOnlyPlugin:
    def pytest_runtest_logreport(self, report):
        if report.failed:
            with open("error_reason.txt", "a") as f:
                f.write(f"FAILED: {report.nodeid}\n")
                f.write(str(report.longrepr))
                f.write("\n" + "="*20 + "\n")

if __name__ == "__main__":
    pytest.main(["grader.py"], plugins=[FailureOnlyPlugin()])
