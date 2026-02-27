"""Tests for monitoring cron jobs."""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))


class TestCronRoutes:
    def test_cron_trigger_route_registered(self):
        from main import app
        paths = [r.path for r in app.routes]
        assert "/api/crons/{cron_type}" in paths

    def test_cron_list_route_registered(self):
        from main import app
        paths = [r.path for r in app.routes]
        assert "/api/crons" in paths

    def test_cron_types_route_registered(self):
        from main import app
        paths = [r.path for r in app.routes]
        assert "/api/crons/types" in paths


class TestCronRegistry:
    def test_all_crons_registered(self):
        from routes.crons import CRON_REGISTRY
        assert "salary_compliance" in CRON_REGISTRY
        assert "self_improvement" in CRON_REGISTRY
        assert "video_audit" in CRON_REGISTRY

    def test_cron_functions_are_callable(self):
        from routes.crons import CRON_REGISTRY
        for name, fn in CRON_REGISTRY.items():
            assert callable(fn), f"{name} is not callable"


class TestSelfImprovement:
    def test_module_imports(self):
        from crons.self_improvement import run_self_improvement
        assert callable(run_self_improvement)

    def test_salary_compliance_imports(self):
        from crons.salary_compliance import run_salary_compliance
        assert callable(run_salary_compliance)

    def test_video_audit_imports(self):
        from crons.video_audit import run_video_audit
        assert callable(run_video_audit)
