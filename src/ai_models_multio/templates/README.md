# Grib Templates

This is a subset of grib templates sourced from `eccodes`.

Which one to use is dependent on the result of `earthkit.data.readers.grib.output.GribCoder`

If not found will fail over to `default.tmpl`

## Preperation

To prepare the original samples for use by `ai-models-multio` the following command was run on the files

`grib_set -s setLocalDefinition=1,localDefinitionNumber=1 ORIGINAL NEW`
