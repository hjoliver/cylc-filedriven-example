# A file-driven workflow in Cylc.

File-driven workflow managers such as Snakemake work with task input and output
file paths rather than dependencies. Each time you run the workflow, its tasks
generate their outputs only if needed - i.e. if the outputs don't exist yet or
if the inputs are newer than existing outputs.

## A simple ML use case

A workflow to compare N models running on the same input data:
- Process raw input data to the form needed by models
- Run the N models on the processed input data
- Compare model outputs 

Add a new model and run the workflow again:
- The raw input data should not be reprocessed
- The new model should run, but not the original models
- The comparison task should run again, to include the new results

Change the raw input data and re-submit the workflow:
- All tasks should run again

## How to do it in Cylc

Cylc is dependency-driven for maximum flexibility, but we can emulate the
file-driven paradigm by adding an input/output timestamp comparison to each
task and exiting early if the outputs do not need to be regenerated.

We still have to write the dependency graph (it is not inferred from task
inputs and outputs). However, the graph is typically pretty trivial in these
kinds of workflows.

In the Cylc task definition below, the workflow configuration defines IO
locations in terms understood by the model executable (in this case,
environment variables). We pass these locations to a `skip-task` script first,
which compares input and output timesteamps and exits with success status if
the task is a no-op, or fail status if the outputs should be regenerated. 
```ini
[runtime]
   [[model]]
        script = "skip-task $MODEL_IN $MODEL_OUTPUT || run-model"
        [[[environment]]
            MODEL_IN = data.raw
            MODEL_OUT = result.nc
```

## Example workflow files

The workflow source directory contains:
- A workflow configuration (`flow.cylc`)
- Some toy executables to run in the workflow:
  - `clean` - "cleans" input data for model use
  - `model` - runs the model
  - `compare` - "compares" and reports model results
- A example implementation of `skip-task`, which takes comma-delimited lists of
  file path globs to match task inputs and outputs

## Things to note

- For convenience, the toy executables all read IO locations from the
  environment, but we can easily adapt this for any way of configuring IO
  in real executables.

- The workflow runs to completion batch-style each time (it is not a Cylc
  cycling workflow) so a new instance should installed for each new run:
```console
$ cylc install demo && cylc play demo
$ cylc tui demo
```

- To add a new model for a new run, simply add to the `m` parameter list.
  Only the new model, and the final comparison task should regenerate their
  outputs.

- The toy executables all write their output files(s) initially with a `.TMP`
  extension and sleep for a few seconds before renaming the file, so you can
  see in real time which tasks are regenerating their data during a run:
```console
$ watch -n 1 'ls -lrt <data-dir>'
```

## Model discovery

For convenience, the example just lists model names as task parameters and
assumes the parameter value is enough select the right model executable or
configuration at run time.

This can easily be extended to discover models automatically, e.g. from a list
in an external file or model configuration directory. Just write a Python
function to do the discovery, put in `<source-dir>lib/python/`, and call from
Jinja2 like this:

```ini
{% from "models" import get_models %}
{% set MODEL_CONF_DIR = "/home/oliverh/cylc-src/foo/models" %}
[task parameters]
   m = {{ ', '.join(get_models(MODEL_CONF_DIR)) }}
```
