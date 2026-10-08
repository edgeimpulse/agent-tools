---
name: ei-build-custom-transformation-blocks
description: Author Edge Impulse custom transformation blocks (Enterprise). Use when asked to scaffold, modify, test, or push a custom transformation block — including the operating modes (file, directory, standalone), the Dockerfile, parameters.json for transform blocks (operatesOn, cliArguments, requiredEnvVariables, bucket mounts), the --in-file/--in-directory/--out-directory arguments, EI_* environment variables, ei-metadata.json for clinical datasets, and the edge-impulse-blocks init/runner/push workflow.
metadata:
  version: "0.1.0"
---

Help the user author an Edge Impulse custom transformation block. A transformation block is a Docker container that Studio runs as a **transformation job** to pre-process organization data (resample, split, merge, augment, relabel, extract metadata), to fetch external data, or to run any generic cloud job. Any language works — the contract is only the arguments, environment variables, and mounted directories the container receives. Custom transformation blocks are an **Enterprise-only** feature.

Before writing a block, check whether a pre-built transformation block (organization → **Custom blocks** → **Transformation** → *Public blocks*) or one of the examples in `edgeimpulse/transformation-blocks` already does the job. Synthetic data and AI labeling blocks are transformation blocks in `standalone` mode with their own `type` (`synthetic-data`, `ai-action`) in `parameters.json`. For those, use the `ei-build-custom-synthetic-data-blocks` and `ei-build-custom-ai-labeling-blocks` skills.

## Choose an operating mode

| Mode | Input | Runs | Shown in Studio |
| --- | --- | --- | --- |
| `file` | One file per run, via `--in-file` | Many runs, in parallel | Transformation jobs only |
| `directory` | One directory per run (a clinical data item), via `--in-directory` | Many runs, in parallel | Transformation jobs only |
| `standalone` | Nothing is passed in | One run | Transformation jobs if `showInCreateTransformationJob: true`; project data sources if `showInDataSources: true` |

Use `file` to convert or modify single files, `directory` when the output depends on several files of one data item (merging, existence checks), and `standalone` for fetching or generating data, or for jobs that call APIs. A standalone block that needs existing data must mount a storage bucket or read through the API.

## Required files

- `Dockerfile` — builds the container. `ENTRYPOINT` runs the script.
- `parameters.json` — block metadata (`type: "transform"`) + user-facing parameters.
- Transformation script — `transform.py` in the official examples; Bash, Node.js, or any other language also works.
- Optional `requirements.txt`, `.dockerignore` (exclude `data/`, `ei-block-data/`, `out/`).
- `.ei-block-config` — written by `edge-impulse-blocks init`; it binds the directory to one organization and block ID. The CLI docs recommend committing it so collaborators push to the same block; the official example repos gitignore it. Gitignore it in public or shared repos, commit it in a private team repo.

## Block I/O contract

### Command line arguments

Every parameter item in `parameters.json` becomes a CLI argument (`--<param> <value>`). Studio adds these automatically:

| Argument | When |
| --- | --- |
| `--in-file <path>` | `file` mode. The file to process. |
| `--in-directory <path>` | `directory` mode. The directory to process. |
| `--out-directory <path>` | `file` and `directory` modes. Write every output here. |
| `--hmac-key <key>` | `file` and `directory` modes. Project HMAC key, or `'0'` when none exists. |
| `--metadata <json>` | `file` and `directory` modes, when `indMetadata` is `true` and the item has metadata. Stringified JSON object. |
| `--upload-category <split\|training\|testing>` | `file`/`directory` mode, when the job imports results into a project. |
| `--upload-label <label>` | Same condition as `--upload-category`. |

Parse with `parse_known_args()` (Python) or the equivalent, so new arguments from Studio don't crash the script. Mark arguments the mode doesn't pass as `required=False`.

How parameter types arrive:

| Type | Passed as |
| --- | --- |
| `int`, `float`, `select` | `--<param> <value>` |
| `string` | `--<param> "<value>"` |
| `boolean` | `--<param> 1` or `--<param> 0` |
| `flag` | `--<param>` when checked, nothing when unchecked |
| `bucket`, `dataset` | `--<param> "<name>"` (transformation, synthetic data, and AI labeling blocks only) |
| `secret` | **Environment variable** named by `param`, not an argument |

Extra arguments: set `cliArguments` in `info` for fixed arguments, and `allowExtraCliArguments: true` to let users type more when they configure a job.

### Environment variables

Always passed: `EI_API_ENDPOINT` (`https://studio.edgeimpulse.com/v1`), `EI_API_KEY` (organization API key with member privileges), `EI_INGESTION_HOST`, `EI_ORGANIZATION_ID`, `EI_LAST_SUCCESSFUL_RUN` (set when the block runs in a data pipeline). Passed only when the block is a project data source: `EI_PROJECT_ID`, `EI_PROJECT_API_KEY`. All values are strings.

Declare your own in `info.requiredEnvVariables`; the CLI prompts for their values on `push`, and they can be changed later by editing the block in Studio. Never hard-code credentials, and never print `EI_API_KEY` or secrets to the job log.

### Mounted storage buckets

Organization storage buckets mount at `/mnt/s3fs/<bucket-name>` by default. The CLI offers the buckets during `init` (select each with the space bar — forgetting this is the usual reason a bucket is missing). The mount is stored in `info.transformMountpoints` as `{ bucketId, mountPoint }` and can be edited in Studio after the push.

### Outputs

Nothing is required. In `file` and `directory` mode, write results into `--out-directory`; Studio uploads them to the output location configured on the job (no subfolders, one subfolder per input item, or the full input path). In `file` mode with a subfolder option, the folder is named after the input file without its extension. In `standalone` mode, act through the API or a mounted bucket.

**Exit with code `0` on success and non-zero on failure.** A script that never exits, or that swallows errors, leaves the job running indefinitely.

### Updating data item metadata

In `directory` mode on a clinical dataset, write `ei-metadata.json` into `--out-directory` to change the item's metadata. The official examples also write it from `file` mode blocks.

```json
{ "version": 1, "action": "add", "metadata": { "ei_check_files_present": "1" } }
```

`action` is `add` (merge new keys into existing metadata), `replace` (delete all existing metadata, then add), or `replace-checks` (delete existing keys that begin with `ei_check`, then add). The documented type is `{ [k: string]: string }`, so write values as strings to be safe. Keys that begin with `ei_check` are the convention for data quality checks, which filters such as `metadata->ei_check = 1` then use. When you rewrite metadata, start from the `--metadata` value so you don't lose existing keys.

## parameters.json

```json
{
  "version": 1,
  "type": "transform",
  "info": {
    "name": "Resample CSV",
    "description": "Upsample or downsample CSV files to a constant sampling rate.",
    "operatesOn": "file",
    "indMetadata": true,
    "allowExtraCliArguments": false,
    "requiredEnvVariables": []
  },
  "parameters": [
    {
      "name": "Sampling interval (ms)",
      "value": 10,
      "type": "int",
      "param": "sampling-interval",
      "help": "Output sampling interval in milliseconds."
    },
    {
      "name": "Resampling mode",
      "value": "mean",
      "type": "select",
      "valid": ["mean", "median"],
      "param": "resampling-mode",
      "help": "How to combine samples inside each interval."
    }
  ]
}
```

Rules:

- `info` keys for transform blocks: `name`, `description`, `operatesOn` (`file` | `directory` | `standalone`), `transformMountpoints`, `indMetadata`, `cliArguments`, `allowExtraCliArguments`, `showInDataSources`, `showInCreateTransformationJob`, `requiredEnvVariables`.
- `parameters` is a flat array of items (no groups; groups are for processing blocks only). Each `param` has no spaces, and the script must accept it as `--<param>` with the **same spelling**. Dashes are not converted, so `sampling-interval` arrives as `--sampling-interval` (Python's argparse exposes it as `args.sampling_interval`). The official examples mix `snake_case` and `kebab-case`; pick one style and stay consistent.
- Item fields: `name`, `value` (default), `type`, `param`, `help`, `valid` (for `select`; strings or `{ label, value }`), `optional`, `readonly`, `showIf` (`{ parameter, operator: "eq" | "neq", value }`, with `value` as a string such as `"true"`), `multiline`, `hint`, `placeholder`.
- Older example repos store `parameters.json` as a bare array of items with no `info`. The CLI-generated format is the object above; prefer it, and set `operatesOn` explicitly. If you inherit a bare-array file, the operating mode can also be set when editing the block in Studio.
- Compute requests and limits (CPUs, memory) and maximum run time are **not** set in `parameters.json`. Set them by editing the block in Studio after the push, or through the update transformation block API.

## Dockerfile

```dockerfile
FROM python:3.10-slim
WORKDIR /app

COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . ./

ENTRYPOINT ["python3", "-u", "transform.py"]
```

Rules:

- Never set `WORKDIR` to `/home` or `/data`. Edge Impulse mounts over both. Use `/app`.
- Set `ENTRYPOINT`, not `RUN` or `CMD`, and use `python3 -u` (or `flush=True` on prints) so logs reach the job log live.
- Pin dependency versions in `requirements.txt`.
- Bake in large static assets at build time (noise recordings, models); the official noise-mixing example does this.

## Script skeleton (Python, file mode)

```python
import argparse
import json
import os
import sys

parser = argparse.ArgumentParser(description='Resample CSV transformation block')
parser.add_argument('--in-file', type=str, required=True)
parser.add_argument('--out-directory', type=str, required=True)
parser.add_argument('--metadata', type=json.loads, required=False)
parser.add_argument('--sampling-interval', type=int, required=True)
parser.add_argument('--resampling-mode', type=str, default='mean')
args, _ = parser.parse_known_args()

if not os.path.exists(args.in_file):
    print('Input file does not exist:', args.in_file, flush=True)
    sys.exit(1)

os.makedirs(args.out_directory, exist_ok=True)

# ... read args.in_file, transform, write into args.out_directory ...
out_path = os.path.join(args.out_directory, os.path.basename(args.in_file))
print('Wrote', out_path, flush=True)

sys.exit(0)
```

For `directory` mode, swap `--in-file` for `--in-directory` and iterate over its contents. For `standalone` mode, drop both input arguments and read `EI_*` environment variables instead.

## Local testing

1. Run the script directly with test arguments and any required environment variables.
2. Build the image and run it the way Edge Impulse does. Put test data in a local `data/` directory.

    ```bash
    docker build -t custom-transformation-block .

    # file mode
    docker run --rm -v $PWD/data:/data -e CUSTOM_ENV_VAR='<value>' custom-transformation-block \
      --in-file /data/<file> --out-directory /data/out --sampling-interval 10

    # directory mode
    docker run --rm -v $PWD/data:/data custom-transformation-block \
      --in-directory /data --out-directory /data/out

    # standalone mode
    docker run --rm -e EI_API_KEY='<org-key>' -e EI_ORGANIZATION_ID='<id>' custom-transformation-block --name test
    ```

3. Use `edge-impulse-blocks runner` for a full test against real organization data. In `file` and `directory` mode it asks for a dataset and a data item or file (or take them from flags), downloads it into `ei-block-data/`, then builds and runs the container.

    | Flag | Meaning |
    | --- | --- |
    | `--dataset <name>` | Dataset to look files and directories up in. |
    | `--data-item <name>` | Clinical data only, `directory` mode. |
    | `--file <name>` | Clinical data only, `file` mode. Use with `--data-item`. |
    | `--skip-download` | Reuse data already downloaded. |
    | `--extra-args "<args>"` | Extra arguments passed to your script, as one string. |

    Add `ei-block-data/` to `.gitignore` and `.dockerignore`. Pass `--clean` to any blocks command to reset the stored configuration, for example to run against a different dataset.

## Push workflow (Enterprise)

```bash
edge-impulse-blocks init   # choose the organization and "Transformation block"; select buckets to mount; writes .ei-block-config
edge-impulse-blocks push   # archives the directory; the image is built and hosted by Edge Impulse
edge-impulse-blocks info   # shows the name, organization, operating mode, and bucket mounts
```

Authenticate non-interactively with `edge-impulse-blocks --api-key ei_...` (an organization API key). The block then appears under organization → **Custom blocks** → **Transformation**, and in the block dropdown of **Data transformation** → *Create job*, according to its mode. To use an image already hosted on Docker Hub, use **+ Add new transformation block** in Studio and enter `username/image:tag`. The same lifecycle (list, add, update, delete) is available through the organization API; see the `ei-api` skill.

## Documentation

- https://docs.edgeimpulse.com/studio/organizations/custom-blocks/custom-transformation-blocks — custom transformation block interface (arguments, environment variables, modes, testing)
- https://docs.edgeimpulse.com/studio/organizations/transformation-blocks — operating modes and pre-built blocks
- https://docs.edgeimpulse.com/studio/organizations/data-transformation — creating and running transformation jobs (input filters, output rules, parallel jobs)
- https://docs.edgeimpulse.com/studio/organizations/custom-blocks — rules common to all custom blocks (Dockerfile, editing after push, compute limits)
- https://docs.edgeimpulse.com/tools/specifications/files/parameters-json — full parameters.json specification
- https://docs.edgeimpulse.com/tools/specifications/files/ei-metadata-json — ei-metadata.json specification
- https://docs.edgeimpulse.com/tools/clis/edge-impulse-cli/blocks — edge-impulse-blocks CLI reference (init, runner, push)

## Reference repositories

- https://github.com/edgeimpulse/transformation-blocks — examples for each mode (resample, split, and merge CSV; metadata checks; graphs; Kaggle fetch; data access helpers); start here
- https://github.com/edgeimpulse/template-transformation-block-python — minimal Python file-mode template that `edge-impulse-blocks init` can download
- https://github.com/edgeimpulse/example-transform-block-mix-noise — Bash block that mixes background noise into audio, with assets baked into the image
- https://github.com/edgeimpulse/image-resize-transformation-block — block that reads a project through `EI_PROJECT_API_KEY` and the API

## Instructions

1. Confirm what the block should do, what data it reads, and where results go. Choose the operating mode (`file`, `directory`, or `standalone`) and, for `standalone`, whether it appears in transformation jobs, data sources, or both. Confirm the user has an Enterprise organization.
2. Start from `edge-impulse-blocks init` (Python template) or the closest example in `transformation-blocks`. Use another language only when the user asks.
3. Write `parameters.json` with `type: "transform"`, set `operatesOn`, and mirror each item as a CLI argument with the exact `param` spelling. Use `secret` items or `requiredEnvVariables` for credentials.
4. Write the script so that it parses with `parse_known_args`, validates inputs, writes only into `--out-directory`, logs with flushed prints, and exits `0` or non-zero explicitly.
5. Keep dependencies pinned and installed at build time, `WORKDIR /app`, and `ENTRYPOINT` as the last instruction.
6. Test in this order: direct script run, `docker run` with a small local dataset, then `edge-impulse-blocks runner` against real data.
7. Add `.ei-block-config` (public repos), `ei-block-data/`, `data/`, and `__pycache__/` to `.gitignore`, and `ei-block-data/` and `data/` to `.dockerignore`.
8. Push, then remind the user to set compute requests, limits, and maximum run time in Studio, and to try the block on a small selection before running it over a whole dataset.
