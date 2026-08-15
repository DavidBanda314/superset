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

from uuid import uuid4

import pytest
from marshmallow import Schema

from superset.themes.schemas import (
    ImportV1ThemeSchema,
    ThemePostSchema,
    ThemePutSchema,
)
from superset.utils import json

MALICIOUS_THEME = {
    "token": {
        "brandSpinnerSvg": '<svg onload="alert(1)"><script>alert(2)</script></svg>'
    }
}


@pytest.mark.parametrize("schema", [ThemePostSchema(), ThemePutSchema()])
def test_load_returns_sanitized_json_data(schema: Schema) -> None:
    loaded = schema.load(
        {"theme_name": "malicious", "json_data": json.dumps(MALICIOUS_THEME)}
    )

    svg = json.loads(loaded["json_data"])["token"]["brandSpinnerSvg"]
    assert "onload" not in svg
    assert "<script>" not in svg


def test_import_load_returns_sanitized_json_data() -> None:
    loaded = ImportV1ThemeSchema().load(
        {
            "theme_name": "malicious",
            "json_data": json.dumps(MALICIOUS_THEME),
            "uuid": str(uuid4()),
            "version": "1.0.0",
        }
    )

    svg = json.loads(loaded["json_data"])["token"]["brandSpinnerSvg"]
    assert "onload" not in svg
    assert "<script>" not in svg
