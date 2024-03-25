<h1 align="center">
    Bolagsverket (Proof of Business) - MyCompany Wallet Portal Backend
</h1>

<p align="center">
    <a href="/../../commits/" title="Last Commit"><img src="https://img.shields.io/github/last-commit/L3-iGrant/pob-backend?style=flat"></a>
    <a href="/../../issues" title="Open Issues"><img src="https://img.shields.io/github/issues/L3-iGrant/pob-backend?style=flat"></a>
</p>

<p align="center">
  <a href="#about">About</a> •
  <a href="#release-status">Release Status</a> •
  <a href="#licensing">Licensing</a>
</p>

## About

This repository hosts the source code for Bolagsverket Proof-Of-Business project  (Portal backend)
## Release Status

Release 1.0 - The release is in alpha demo stage. 
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
$ git clone https://github.com/L3-iGrant/pob-backend
```


2. Change the current direcotry to *pob-backend*

```bash
cd pob-backend
```

3. To get an overview of different commands available in the current project run

```bash
make
```

The following commands are currently supported

```bash
------------------------------------------------------------------------
Bolagsverket (Proof Of Business) - Backend
------------------------------------------------------------------------
bootstrap                      Boostraps development environment
build/docker/deployable        Builds deployable docker image for preview, staging and production
build/docker/deployable_x86    Builds deployable docker image explicitly for x86 architecture
build                          Builds the docker image
deploy/production              Deploy to K8s cluster (e.g. make deploy/{preview,staging,production})
deploy/staging                 Deploy to K8s cluster (e.g. make deploy/{preview,staging,staging})
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


## Licensing
Copyright (c) 2022-25 Bolagsverket, Sweden

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the LICENSE for the specific language governing permissions and limitations under the License.
