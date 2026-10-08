---
name: ei-build-custom-ai-labeling-blocks
description: Author Edge Impulse custom AI labeling blocks (Enterprise). Use when asked to scaffold, modify, test, or push a custom AI labeling block (AI action) — including the parameters.json for ai-action blocks (operatesOn, secret parameters, requiredEnvVariables), the --data-ids-file and --propose-actions arguments, preview mode with set_sample_proposed_changes, writing labels, structured labels, bounding boxes and metadata through the Studio API, the Dockerfile, testing with docker run (the blocks runner does not support AI labeling), and the edge-impulse-blocks init/push workflow.
metadata:
  version: "0.1.0"
---

Help the user author an Edge Impulse custom AI labeling block. An AI labeling block is a Docker container that Studio runs from a project's **Data acquisition → AI labeling** tab to label a selection of samples with a model or an LLM (single labels, bounding boxes, or audio labels with time ranges). Any language works. The contract is the arguments, environment variables, and Studio API calls the container uses. Custom AI labeling blocks are an **Enterprise-only** feature.

Before writing a block, check whether a built-in block or an official example already does the job (see *Reference repositories*). Chaining blocks in one AI labeling action is often better than one large block, for example a zero-shot detector followed by a GPT-4o re-labeling step.

## How AI labeling blocks work

An AI labeling block is a **transformation block in `standalone` mode** with `type: "ai-action"` in `parameters.json`. It receives no input file or directory. Instead Studio passes the IDs of the selected samples in a JSON file, and the block reads and writes each sample through the Studio API with the project API key. There are **no required outputs**. All changes are applied by API calls from inside the block.

Studio runs the block in two ways:

| Run | Triggered by | What the block must do |
| --- | --- | --- |
| Preview | **Label preview data** | Stage changes only. `--propose-actions <job-id>` is passed. |
| Apply | **Label all data** | Write labels directly. `--propose-actions` is not passed. |

## Required files

- `Dockerfile` — builds the container. `ENTRYPOINT` runs the script.
- `parameters.json` — block metadata (`type: "ai-action"`) + user-facing parameters.
- Labeling script — Python (`transform.py`) or TypeScript (`llm-labeling.ts`) in the official examples; any language that can call the Studio API works.
- Optional `requirements.txt` or `package.json`, `.dockerignore`.
- `.ei-block-config` — written by `edge-impulse-blocks init`; it binds the directory to one organization and block ID. Gitignore it in public or shared repos, commit it in a private team repo.

## Block I/O contract

### Command line arguments

Every parameter item in `parameters.json` becomes a CLI argument (`--<param> <value>`), except `secret` items (see below). Studio adds these automatically:

| Argument | When | Meaning |
| --- | --- | --- |
| `--data-ids-file <path>` | Always | Path to a JSON file with the sample IDs to label (integers). |
| `--propose-actions <job-id>` | Preview only | Integer job ID. Stage changes; do not apply them. |
| Standalone-mode transformation arguments | Always | Studio also passes the arguments that standalone transformation blocks get (see the transformation block docs). You don't need them when you use the environment variables below. Accept them with `parse_known_args` so the block does not fail on arguments it does not use. |

Users can also append extra CLI arguments when editing the block in Studio. Allow them with `parse_known_args` (Python) or by not using strict parsing.

### `ids.json`

The docs describe the file as `{ "ids": [ 1440653288, 1440653283 ] }`, but every official example block reads it as a **bare JSON array** (`[1299267659, 1299267609]`). Accept both:

```python
with open(args.data_ids_file) as f:
    data = json.load(f)
data_ids = data["ids"] if isinstance(data, dict) else data
```

For local tests, create `ids.json` yourself. Find a sample ID in Studio by expanding a row in **Data acquisition → Dataset**. Gitignore `ids.json`.

### Environment variables

Values are always strings.

| Variable | Description |
| --- | --- |
| `EI_API_ENDPOINT` | API base URL, `https://studio.edgeimpulse.com/v1`. Always read it with that default. |
| `EI_API_KEY` | Organization API key with member privileges. |
| `EI_INGESTION_HOST` | Ingestion API host, `edgeimpulse.com`. |
| `EI_ORGANIZATION_ID` | ID of the organization that owns the block. |
| `EI_PROJECT_ID` | ID of the project being labeled. |
| `EI_PROJECT_API_KEY` | Project API key. Use it for sample reads and writes. |

Declare your own variables (third-party tokens, endpoints) in `info.requiredEnvVariables`. The CLI prompts for them on `push`, and they can be edited in Studio afterwards. `secret` parameters are also delivered as environment variables.

### Mounted storage buckets

Buckets in the organization can be mounted at `/mnt/s3fs/<bucket-name>`, selected during `edge-impulse-blocks init`. The mount point can be changed by editing the block in Studio. Most AI labeling blocks do not need a bucket.

## parameters.json

```json
{
  "version": 1,
  "type": "ai-action",
  "info": {
    "name": "Image labeling with my model",
    "description": "Label images with a single class using my model.",
    "operatesOn": ["images_single_label"],
    "requiredEnvVariables": ["MY_ENDPOINT"]
  },
  "parameters": [
    {
      "name": "API key",
      "value": "",
      "type": "secret",
      "param": "MY_API_KEY",
      "help": "Key for the labeling provider. Stored in Studio Secrets."
    },
    {
      "name": "Prompt",
      "value": "Is there a person in this picture? Answer with 'yes' or 'no'.",
      "type": "string",
      "param": "prompt",
      "multiline": true,
      "help": "Prompt sent with every image."
    },
    {
      "name": "Minimum confidence",
      "value": 0.2,
      "type": "float",
      "param": "min-confidence",
      "help": "Results below this confidence are skipped."
    },
    {
      "name": "Delete existing bounding boxes",
      "value": false,
      "type": "flag",
      "param": "delete-existing"
    }
  ]
}
```

- `operatesOn` is an array and decides which datasets the block is enabled for. Studio greys the block out when the project does not match. Values: `images_object_detection`, `images_single_label`, `audio`, `other`.
- `info` keys: `name`, `description`, `operatesOn`, `requiredEnvVariables`.
- `parameters` is a flat array. Item fields: `name`, `value` (default), `type`, `param`, `help`, `valid` (for `select`; strings or `{ label, value }`), `optional`, `readonly`, `showIf` (`{ parameter, operator: "eq" | "neq", value }`, `value` as a string such as `"true"`), `multiline`, `hint`, `placeholder`.
- Types: `string`, `int`, `float`, `select`, `boolean`, `bucket`, `dataset`, `flag`, `secret`. The official AI labeling blocks also use `project` (a project picker that passes the selected project's API key). A `flag` is passed as `--<param>` when checked and omitted when not; a `secret` is **not** passed as an argument but as an environment variable named by `param` (use the environment-variable style, `HF_API_KEY`).
- Keep `param` spelling identical to what the script parses. Dashes are not converted, so `min-confidence` arrives as `--min-confidence` (Python's argparse exposes it as `args.min_confidence`).
- Multiline `string` values reach the script with literal `\n` sequences. Convert them with `value.replace('\\n', '\n')`.
- Studio stores a secret the first time a user enters it. The value is no longer visible afterwards, and it is managed under organization **Secrets** (Enterprise) or **Account settings → Secrets**.
- Compute requests and limits and the maximum run time are not set in `parameters.json`. Set them by editing the block in Studio after the push, or with the update transformation block API.

## Dockerfile

```dockerfile
FROM python:3.10-slim
WORKDIR /app

COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . ./

ENTRYPOINT ["python3", "-u", "transform.py"]
```

For TypeScript, use a `node` base image, `npm ci`, `npm run build`, and `ENTRYPOINT ["node", "build/llm-labeling.js"]`. Keep `WORKDIR /app`, put `ENTRYPOINT` last, and pin dependency versions. Install system tools (`ffmpeg` for audio) at build time. Add `ids.json`, `.venv/`, `out*/`, local test media, and `load-keys.sh` to `.dockerignore`.

## Script skeleton (Python, with preview mode)

```python
import argparse, json, os, sys
from edgeimpulse_api import ApiClient, Configuration, ProjectsApi, RawDataApi

for var in ("EI_PROJECT_API_KEY", "MY_API_KEY"):
    if not os.getenv(var):
        print(f"Missing {var}"); sys.exit(1)

parser = argparse.ArgumentParser()
parser.add_argument("--prompt", required=True)
parser.add_argument("--min-confidence", type=float, default=0.2)
parser.add_argument("--data-ids-file", required=True)
parser.add_argument("--propose-actions", type=int, required=False)
args, _unknown = parser.parse_known_args()

with open(args.data_ids_file) as f:
    data = json.load(f)
data_ids = data["ids"] if isinstance(data, dict) else data

client = ApiClient(Configuration(
    host=os.getenv("EI_API_ENDPOINT", "https://studio.edgeimpulse.com/v1"),
    api_key={"ApiKeyAuthentication": os.environ["EI_PROJECT_API_KEY"]},
))
raw_data_api = RawDataApi(client)
project_id = int(os.getenv("EI_PROJECT_ID") or ProjectsApi(client).list_projects().projects[0].id)

for i, sample_id in enumerate(data_ids, 1):
    # pass the job ID so you see the sample as staged by earlier steps in a chained action
    sample = raw_data_api.get_sample(project_id, sample_id,
                                     proposed_actions_job_id=args.propose_actions).sample
    print(f"[{i}/{len(data_ids)}] {sample.filename} (ID {sample.id})", flush=True)

    label = "person"  # call your model or LLM here
    metadata = dict(sample.metadata or {}, labeled_by="my-block")

    if args.propose_actions:
        raw_data_api.set_sample_proposed_changes(project_id, sample.id,
            set_sample_proposed_changes_request={
                "jobId": args.propose_actions,
                "proposedChanges": {"label": label, "metadata": metadata},
            })
    else:
        raw_data_api.edit_label(project_id, sample.id, edit_sample_label_request={"label": label})
        raw_data_api.set_sample_metadata(project_id, sample.id,
            set_sample_metadata_request={"metadata": metadata})

print("All done!")
```

### What to write, per data type

| Task | Apply (no `--propose-actions`) | Preview (`proposedChanges` key) |
| --- | --- | --- |
| Single label (image or sample) | `raw_data_api.edit_label` | `label` |
| Bounding boxes | `set_sample_bounding_boxes` (`setSampleBoundingBoxes` in TypeScript) | `boundingBoxes` |
| Audio / time-series labels with ranges | `set_sample_structured_labels` (items: `startIndex`, `endIndex`, `label`) | `structuredLabels` |
| Metadata | `set_sample_metadata` | `metadata` |
| Disable a sample (validation blocks) | `disable_sample` (`disableSample` in TypeScript) | `isDisabled: true` (leave `undefined` to keep the current state) |

Preview rule: when `--propose-actions` is set, **never** call the direct write endpoints. Call `set_sample_proposed_changes` (`api.rawData.setSampleProposedChanges` in TypeScript) with `jobId` and `proposedChanges` instead. Studio shows the staged result in the preview grid. Call it for every sample, even when nothing changes (an empty `proposedChanges`), so every sample appears in the preview.

TypeScript equivalent:

```typescript
if (proposeActionsJobId) {
    await api.rawData.setSampleProposedChanges(project.id, sample.id, {
        jobId: proposeActionsJobId,
        proposedChanges: { boundingBoxes: newBbs },
    });
} else {
    await api.rawData.setSampleBoundingBoxes(project.id, sample.id, { boundingBoxes: newBbs });
}
```

Check the exact request shapes against the API spec (`ei-api` skill) before relying on a field that is not in the examples.

### Behavior to build in

- Read samples with `get_sample` (metadata, length, frequency), `download_sample_image` / `get_sample_as_audio` for the media. Pass `_preload_content=False` to get raw bytes.
- Read the image width and height before converting model output to pixel bounding boxes. Boxes are in pixels: `x`, `y`, `width`, `height`, `label`.
- Add a metadata key such as `labeled_by` so users can filter out labeled samples later. Users can also set metadata from the action configuration.
- Respect the parameters the user is asked for: a delete-existing flag, a minimum confidence, minimum and maximum object size.
- For LLM or remote model calls: set a timeout, retry with backoff, and optionally take a `--concurrency` argument. Handle rate limits and "model is loading" responses.
- Fail early with a clear message and exit non-zero for missing environment variables, bad parameters, or invalid labels. Log one flushed line per sample.
- Don't print API keys or secrets.
- Large GPU models are slow to spin up in a container. The OWL-ViT block calls a hosted endpoint (Beam.cloud) instead. Prefer a hosted inference API over loading a big model inside the block.

## Local testing

The `edge-impulse-blocks runner` **does not support AI labeling blocks**. Test in this order:

1. Run the script directly against a real project, with `ids.json` and the environment set:

    ```bash
    export EI_PROJECT_API_KEY=ei_...
    export MY_API_KEY=...
    python3 -u transform.py --prompt "Is there a person?" --data-ids-file ids.json --propose-actions 1
    ```

    Start with `--propose-actions` so nothing is changed. Then run without it on one sample in a scratch project.

2. Build and run the container:

    ```bash
    docker build -t custom-ai-labeling-block .
    docker run --rm \
      -e EI_PROJECT_API_KEY='ei_...' -e MY_API_KEY='...' \
      -v "$PWD/ids.json:/app/ids.json" \
      custom-ai-labeling-block --prompt "Is there a person?" --data-ids-file ids.json
    ```

3. Push, then use **Label preview data** on a few samples in a test project before **Label all data**.

## Push workflow (Enterprise)

```bash
edge-impulse-blocks init   # choose the organization and the transformation block type; writes .ei-block-config
edge-impulse-blocks push   # archives the directory; the image is built and hosted by Edge Impulse
edge-impulse-blocks info   # shows the name, organization, and settings
```

Authenticate non-interactively with `edge-impulse-blocks --api-key ei_...` (an organization API key). The CLI prompts for each `requiredEnvVariables` value on push. The blocks CLI docs don't list AI labeling as its own block type. Because `parameters.json` has `type: "ai-action"` and the block is a standalone transformation block, check after the first push that it appears under organization **Custom blocks → AI labeling**, and in the block selector of a project's **Data acquisition → AI labeling → Add new label action**. If it doesn't, edit the block in Studio or through the API: AI labeling blocks use the transformation block endpoints (get, add, update, delete), and the `showInAIActions` flag decides whether a block appears in the AI labeling tab. See the `ei-api` skill.

## Documentation

- https://docs.edgeimpulse.com/studio/organizations/custom-blocks/custom-ai-labeling-blocks — custom AI labeling block interface (arguments, environment variables, preview mode, testing)
- https://docs.edgeimpulse.com/studio/projects/data-acquisition/ai-labeling — using AI labeling actions in Studio (blocks, preview, metadata, filters)
- https://docs.edgeimpulse.com/tools/specifications/files/ids-json — ids.json specification
- https://docs.edgeimpulse.com/tools/specifications/files/parameters-json — full parameters.json specification
- https://docs.edgeimpulse.com/studio/organizations/custom-blocks — rules common to all custom blocks
- https://docs.edgeimpulse.com/tools/clis/edge-impulse-cli/blocks — edge-impulse-blocks CLI reference

## Reference repositories

- https://github.com/edgeimpulse/ai-labeling-audio-spectrogram-transformer — Python; audio labels with time ranges through the Hugging Face API (simplest full example, including preview mode)
- https://github.com/edgeimpulse/ai-labeling-zero-shot-object-detector-owl-vit — Python; bounding boxes from OWL-ViT hosted on Beam.cloud, with NMS and size filters
- https://github.com/edgeimpulse/ai-labeling-bounding-box-relabeling-gpt4o — TypeScript; re-labels or removes bounding boxes with GPT-4o, with concurrency and retries
- https://github.com/edgeimpulse/ai-labeling-bounding-box-validation-gpt4o — validates bounding boxes with GPT-4o and disables non-conforming samples
- https://github.com/edgeimpulse/ai-labeling-images-gpt4o — image labeling with GPT-4o (marked WIP in the repo)
- https://github.com/edgeimpulse/ai-labeling-using-existing-ei-project — TypeScript; labels images with a model from another Edge Impulse project (uses the `project` parameter type)

## Instructions

1. Confirm what the block should label (single label, bounding boxes, audio ranges), which model or API it calls, and which credentials it needs. Confirm the user has an Enterprise organization. Check whether chaining existing blocks would work.
2. Start from the closest example above and keep its structure. Use Python unless the user asks otherwise, or the example you start from is TypeScript.
3. Write `parameters.json` with `type: "ai-action"` and an explicit `operatesOn` array. Mirror each non-secret item as a CLI argument with the exact `param` spelling, and read secrets from the environment.
4. Write the script to accept `--data-ids-file` and `--propose-actions` and to ignore unknown arguments. Support preview mode from the start: staged writes with `set_sample_proposed_changes`, and direct writes only without `--propose-actions`.
5. Handle remote calls with timeouts, retries, and clear errors. Log progress per sample. Never log secrets.
6. Test in this order: direct script run in preview mode, direct run on one sample, `docker run`, then **Label preview data** after the push. The blocks runner cannot be used.
7. Add `.ei-block-config` (public repos), `ids.json`, `load-keys.sh`, `.venv/`, and `__pycache__/` to `.gitignore`, and `ids.json`, `.venv/`, and test media to `.dockerignore`.
8. Push, then remind the user to set compute limits and maximum run time in Studio and to preview a small selection first.
