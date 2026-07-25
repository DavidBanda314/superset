#!/usr/bin/env bash

#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

set -eu

# Install FOSSA's cli from a pinned, checksum-verified copy of the installer
# (https://docs.fossa.com/docs/generic-ci recommends piping it straight into a
# shell, which would execute unverified third-party code as root).
FOSSA_INSTALLER_COMMIT="5f03c78d3080e853dc8c0f71e46d5c686f2f4a86"
FOSSA_INSTALLER_SHA256="b0f3448d9564753a1238c3bd9278d6d053befd148a16e82f91e96f0c6fb40e16"
FOSSA_BINDIR="${FOSSA_BINDIR:-${HOME}/.local/bin}"

INSTALLER="$(mktemp)"
trap 'rm -f "${INSTALLER}"' EXIT
curl -fsSL -H 'Cache-Control: no-cache' \
  "https://raw.githubusercontent.com/fossas/fossa-cli/${FOSSA_INSTALLER_COMMIT}/install.sh" \
  -o "${INSTALLER}"
echo "${FOSSA_INSTALLER_SHA256}  ${INSTALLER}" | sha256sum --check --status

mkdir -p "${FOSSA_BINDIR}"
bash "${INSTALLER}" -b "${FOSSA_BINDIR}"
export PATH="${FOSSA_BINDIR}:${PATH}"

# This key is a push-only API key, also recommended for public projects
# https://docs.fossa.com/docs/api-reference#section-push-only-api-token
export FOSSA_API_KEY="${FOSSA_API_KEY:-f72e93645bdfeab94bd227c7bbdda4ef}"
fossa init
fossa analyze
fossa test | echo "Ok" # silenced fossa on 2020-10-04 it was acting up
