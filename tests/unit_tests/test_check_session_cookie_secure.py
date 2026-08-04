# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
"""Tests for SupersetAppInitializer.check_session_cookie_secure."""

from unittest.mock import MagicMock, patch

from superset.initialization import SupersetAppInitializer


def _make_initializer(
    session_cookie_secure: bool,
    *,
    debug: bool = False,
    testing: bool = False,
) -> SupersetAppInitializer:
    """Build a bare initializer with the attributes the check needs."""
    init = object.__new__(SupersetAppInitializer)
    init.config = {"SESSION_COOKIE_SECURE": session_cookie_secure}
    app = MagicMock()
    app.debug = debug
    app.config = {"TESTING": testing}
    init.superset_app = app
    return init


def test_warns_when_insecure_outside_development() -> None:
    initializer = _make_initializer(False)
    with (
        patch("superset.initialization.is_test", return_value=False),
        patch.dict("os.environ", {"SUPERSET_ENV": "production"}, clear=False),
        patch.object(initializer, "_log_config_warning") as log_warning,
    ):
        initializer.check_session_cookie_secure()
    log_warning.assert_called_once()


def test_no_warning_when_secure() -> None:
    initializer = _make_initializer(True)
    with (
        patch("superset.initialization.is_test", return_value=False),
        patch.object(initializer, "_log_config_warning") as log_warning,
    ):
        initializer.check_session_cookie_secure()
    log_warning.assert_not_called()


def test_no_warning_in_development_env() -> None:
    initializer = _make_initializer(False)
    with (
        patch("superset.initialization.is_test", return_value=False),
        patch.dict("os.environ", {"SUPERSET_ENV": "development"}, clear=False),
        patch.object(initializer, "_log_config_warning") as log_warning,
    ):
        initializer.check_session_cookie_secure()
    log_warning.assert_not_called()


def test_no_warning_in_debug_mode() -> None:
    initializer = _make_initializer(False, debug=True)
    with (
        patch("superset.initialization.is_test", return_value=False),
        patch.dict("os.environ", {"SUPERSET_ENV": "production"}, clear=False),
        patch.object(initializer, "_log_config_warning") as log_warning,
    ):
        initializer.check_session_cookie_secure()
    log_warning.assert_not_called()
