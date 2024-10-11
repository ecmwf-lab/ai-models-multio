# ai-models-multio
[![Upload Python Package](https://github.com/ecmwf-lab/ai-models-multio/actions/workflows/python-publish.yml/badge.svg)](https://github.com/ecmwf-lab/ai-models-multio/actions/workflows/python-publish.yml)

**DISCLAIMER**
This project is **BETA** and will be **Experimental** for the foreseeable future.
Interfaces and functionality are likely to change, and the project itself may be scrapped.
**DO NOT** use this software in any project/software that is operational.


## Output plugin for multio

Allows for an alternative encoding method to grib, and direct writing to FDB.

## Installation
`ai-model-multio` requires
- `multiopython` (https://github.com/ecmwf/multio-python)
- `multio` (https://github.com/ecmwf/multio)

However, `multio` does not have a build, and must be built manually.

## Usage

Once installed, three output plugins are registered with `ai-models`,
- `multio`
- `mutliofdb`
- `multiodebug`

```
ai-models MODELNAME --output multio ....
```
