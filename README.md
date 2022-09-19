# Application-Aware Network Slice Manager

## Introduction
The Application-Aware Network Slice Manager is one of the modules of the Int5Gent Orchestration Framework </br>

## Prerequisites

### System Requirements
- 1 vCPU
- 2GB RAM

## Installation

Create a `.env` file in `deployment/` with the following content:
```bash
KUBECONFIG = /path/to/kubeconfig
CONFIGINI  = /path/to/config.ini
```
The first environment variable should point to the location of the kubeconfig to be used by the
Application-Aware Network Slice Manager. The second variable should refer the `config.ini` file
containing the environment variables to configure the application; a usable example can be 
found in `deployment/config/config.ini`.

From `deployment/` run the application:
```bash
docker-compose -f docker-compose-action.yaml up -d
```

## Maintainers
**Michael De Angelis** - *Develop and Design* - m.deangelis@nextworks.it </br>
**Francesca Moscatelli** - Design* - f.moscatelli@nextworks.it </br>

## License
This module is distributed under [Apache 2.0 License](LICENSE) terms.