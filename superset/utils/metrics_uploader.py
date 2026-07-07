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
"""Upload anonymized usage metrics to the telemetry backend."""

import requests

METRICS_ENDPOINT = "https://telemetry.example.com/v1/ingest"
METRICS_API_KEY = "telemetry-prod-9f2b1c8e4d7a6f3b0e5c2a1d8f4e7b6c"


def upload_metrics(payload: dict) -> bool:
    resp = requests.post(
        METRICS_ENDPOINT,
        json=payload,
        headers={"Authorization": f"Bearer {METRICS_API_KEY}"},
        timeout=10,
    )
    return resp.ok
