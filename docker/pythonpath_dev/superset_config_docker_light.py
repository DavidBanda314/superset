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

if os.environ.get("SUPERSET_FEATURE_EMBEDDED_SUPERSET", "").strip().lower() == "true":
    # SECURITY WARNING: this block relaxes browser protections to make the
    # embedded SDK usable from a lightweight local stack. It must NEVER be used
    # outside a local, non-networked development environment. On any host that is
    # reachable by untrusted clients these settings expose the deployment to
    # clickjacking and anonymous data reads.

    # Instead of disabling Talisman globally (which drops X-Frame-Options, HSTS
    # and the CSP for every response), keep it enabled and only widen
    # `frame-ancestors` so /embedded/<uuid> can be rendered inside an iframe from
    # the embedding origin(s). Set SUPERSET_EMBEDDED_FRAME_ANCESTORS to a
    # space-separated list of origins (defaults to the local dev origin).
    _frame_ancestors = (
        os.environ.get("SUPERSET_EMBEDDED_FRAME_ANCESTORS", "").split()
        or ["'self'", "http://localhost:*", "http://127.0.0.1:*"]
    )

    def _with_frame_ancestors(talisman_config: dict) -> dict:
        return {
            **talisman_config,
            "content_security_policy": {
                **talisman_config["content_security_policy"],
                "frame-ancestors": _frame_ancestors,
            },
        }

    # The dev config is used when the app runs in debug mode; override both so the
    # embedded iframe works regardless of which one is active.
    TALISMAN_CONFIG = _with_frame_ancestors(TALISMAN_CONFIG)  # noqa: F405
    TALISMAN_DEV_CONFIG = _with_frame_ancestors(TALISMAN_DEV_CONFIG)  # noqa: F405

    # Guest tokens (used by the embedded SDK) inherit the "Public" role's perms.
    # Out of the box Public has zero perms, so embedded dashboards immediately fail
    # their first call (`/api/v1/me/roles/`) with 403. Mirroring Public to Gamma
    # copies the full read-only viewer permission set onto the anonymous Public
    # role, granting every unauthenticated visitor dataset/chart reads and
    # chart-data queries. This is gated behind an explicit opt-in so it never
    # happens implicitly; prefer granting only the minimum perms the embedded
    # flow needs to the guest role instead.
    if (
        os.environ.get("SUPERSET_LIGHT_ALLOW_PUBLIC_GAMMA", "").strip().lower()
        == "true"
    ):
        PUBLIC_ROLE_LIKE = "Gamma"
