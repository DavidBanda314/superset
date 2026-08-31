<!--
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied.  See the License for the
specific language governing permissions and limitations
under the License.
-->

# Hive test cluster

Throwaway Hadoop/Hive cluster used by the Presto/Hive integration test job.

## Usage

The metastore credentials have no committed defaults and must be supplied in the
environment, together with the CSV upload folder bind-mounted into the containers:

```bash
export UPLOAD_FOLDER=/tmp/.superset/uploads/
export HIVE_METASTORE_USER=...
export HIVE_METASTORE_PASSWORD=...
docker compose -f docker-compose.yml up -d
```

`docker compose` fails fast if either variable is unset. The values must match the
credentials of the metastore database in use; the `bde2020/hive-metastore-postgresql`
image shipped in this fixture is a disposable container whose built-in account is
`hive`/`hive`. Point `HIVE_SITE_CONF_javax_jdo_option_ConnectionURL` at your own
metastore database and use its credentials for anything that is not throwaway.
