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
#
# Configuration for docker-compose-light.yml - disables Redis and uses minimal services

# Import all settings from the main config first
import os

from flask_caching.backends.filesystemcache import FileSystemCache

from superset_config import *  # noqa: F403

# Override caching to use simple in-memory cache instead of Redis
RESULTS_BACKEND = FileSystemCache("/app/superset_home/sqllab")

CACHE_CONFIG = {
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": 300,
    "CACHE_KEY_PREFIX": "superset_light_",
}
DATA_CACHE_CONFIG = CACHE_CONFIG
THUMBNAIL_CACHE_CONFIG = CACHE_CONFIG


# Disable Celery entirely for lightweight mode
CELERY_CONFIG = None  # type: ignore[assignment,misc]

# Honor SUPERSET_FEATURE_<NAME> env vars on top of any flags inherited from
# superset_config. Lets local dev/e2e enable features (e.g. EMBEDDED_SUPERSET)
# without editing shipped config files. Only the literal string "true"
# (case-insensitive) is treated as enabled — "1"/"yes"/"on" are not, matching
# the strict-string convention used elsewhere in Superset's env parsing.
FEATURE_FLAGS = {
    **FEATURE_FLAGS,  # noqa: F405
    **{
        name[len("SUPERSET_FEATURE_") :]: value.strip().lower() == "true"
        for name, value in os.environ.items()
        if name.startswith("SUPERSET_FEATURE_")
    },
}


def _env_true(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() == "true"


# WARNING: The settings below make the embedded SDK usable from a lightweight
# local stack by dropping browser protections and granting the anonymous
# "Public" role broad read access. They MUST NEVER be enabled on any host that
# is reachable by untrusted clients:
#   * TALISMAN_ENABLED = False removes X-Frame-Options, HSTS and the CSP from
#     *every* response (not just /embedded/<uuid>), exposing the whole stack to
#     clickjacking.
#   * PUBLIC_ROLE_LIKE = "Gamma" copies the full Gamma permission set onto the
#     anonymous Public role, letting every unauthenticated visitor read
#     datasets/charts and issue chart-data queries.
# Because this file is a copy-paste template for embedding, these are gated
# behind an explicit opt-in so they never take effect implicitly. Enable them
# only in a local, non-networked development environment, and prefer granting
# the guest role the minimum perms the embedded flow needs over widening Public.
if _env_true("SUPERSET_FEATURE_EMBEDDED_SUPERSET") and _env_true(
    "SUPERSET_LIGHT_INSECURE_EMBEDDED"
):
    TALISMAN_ENABLED = False
    PUBLIC_ROLE_LIKE = "Gamma"
