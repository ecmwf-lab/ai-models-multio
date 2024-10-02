# ai-models-multio

Output plugin for multio

Allows for an alternative encoding method to grib, and direct writing to FDB.

## Installation
`ai-model-multio` requires
- `multiopython` (https://github.com/ecmwf/multio-python)
- `multio` (https://github.com/ecmwf/multio)

However, `multio` does not have a build, and must be built manually.

## Usage

Once installed, three output plugins are registered with `ai-models`,
- `multio`
- `mutliofdb`
- `multiodebug`

```
ai-models MODELNAME --output multio ....
```
