<h1 align="center">
    Dataspace Portal Backend
</h1>

<p align="center">
    <a href="/../../commits/" title="Last Commit"><img src="https://img.shields.io/github/last-commit/decentralised-dataexchange/data-space-backend?style=flat"></a>
    <a href="/../../issues" title="Open Issues"><img src="https://img.shields.io/github/issues/decentralised-dataexchange/data-space-backend?style=flat"></a>
</p>

<p align="center">
  <a href="#about">About</a> •
  <a href="#licensing">Licensing</a>
</p>

## About

This repository hosts the source code for Dataspace Portal Backend

## Installation

Requirements:
- python 3.8.1.2

## Steps to run
### **Pre-requisite:**   

1. Docker is installed in the local system
2. [Setup up SSH in github](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)

### **Steps:**

1. Clone this repo

```sh
$ git clone https://github.com/decentralised-dataexchange/data-space-backend
```


2. Change the current direcotry to *dataspace-backend*

```bash
cd data-space-backend
```

3. To get an overview of different commands available in the current project run

```bash
make
```

The following commands are currently supported

```bash
------------------------------------------------------------------------
Dataspace Backend
------------------------------------------------------------------------
bootstrap                      Boostraps development environment
build                          Builds the docker image
build/docker/deployable        Builds deployable docker image for preview, staging and production
deploy/production              Deploy to K8s cluster (e.g. make deploy/{preview,staging,production})
deploy/staging                 Deploy to K8s cluster (e.g. make deploy/{preview,staging,staging})
docs/bundle                    Bundle OpenAPI documentation
docs/run                       Run OpenAPI documentation
publish                        Publish latest production Docker image to docker hub
run                            Run backend locally for development purposes
setup                          Sets up development environment
```

4. Build the project

```bash
make build
```

5. Finally to run the server (http://localhost:8000) locally,

```bash
make run
```

Django admin dashboard is accessible at http://localhost:8000/admin/ endpoint. Super user credentials are as given below:

```
email: admin@example.com
password: admin
```

## Contributing

Feel free to improve the plugin and send us a pull request. If you find any problems, please create an issue in this repo.

## Licensing
Copyright (c) 2023-25 LCubed AB (iGrant.io), Sweden

Licensed under the Apache 2.0 License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the LICENSE for the specific language governing permissions and limitations under the License.
