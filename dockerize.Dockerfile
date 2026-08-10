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

FROM alpine:3.22@sha256:14358309a308569c32bdc37e2e0e9694be33a9d99e68afb0f5ff33cc1f695dce

ARG DOCKERIZE_VERSION=v0.7.0
ARG DOCKERIZE_SHA256_AMD64=bb9b55630aa63da22bafb2132f06fe00f298ef16272a99134e69495c37b33ce9
ARG DOCKERIZE_SHA256_ARM64=c73c547159bcc12467f5163f86f49d493237cf007f8b7507783f51f35ed9bea1

RUN set -eux; \
    apk update --no-cache; \
    apk add --no-cache wget openssl; \
    case "$(apk --print-arch)" in \
        x86_64) ARCH=amd64; EXPECTED_SHA="${DOCKERIZE_SHA256_AMD64}" ;; \
        aarch64) ARCH=arm64; EXPECTED_SHA="${DOCKERIZE_SHA256_ARM64}" ;; \
        *) echo "unsupported architecture: $(apk --print-arch)" >&2; exit 1 ;; \
    esac; \
    wget -O /tmp/dockerize.tar.gz "https://github.com/jwilder/dockerize/releases/download/${DOCKERIZE_VERSION}/dockerize-linux-${ARCH}-${DOCKERIZE_VERSION}.tar.gz"; \
    echo "${EXPECTED_SHA}  /tmp/dockerize.tar.gz" | sha256sum -c -; \
    tar -xzf /tmp/dockerize.tar.gz --no-same-owner -C /usr/local/bin dockerize; \
    rm /tmp/dockerize.tar.gz; \
    apk del wget

USER 10001
