---
name: ei-build-custom-synthetic-data-blocks
description: Author Edge Impulse custom synthetic data blocks (Enterprise). Use when asked to scaffold, modify, test, or push a custom synthetic data block — including parameters.json for synthetic-data blocks (secret API keys, label, sample count, upload category), the --synthetic-data-job-id argument and x-synthetic-data-job-id Ingestion API header, uploading generated images, audio, or bounding boxes to the Ingestion API, the Dockerfile, testing with docker run (the blocks runner does not support synthetic data blocks), and the edge-impulse-blocks init/push workflow.
metadata:
  version: "0.1.1"
---

Help the user author an Edge Impulse custom synthetic data block. A synthetic data block is a Docker container that Studio runs from a project's **Data acquisition → Synthetic data** tab to generate samples (images, audio, time series) with a generative model or a custom generator, and upload them to the project through the Ingestion API. Any language works. Custom synthetic data blocks are an **Enterprise-only** feature.

Before writing a block, check whether a built-in block (DALL-E image generation, FLUX Pro image generation, Whisper keyword generation, time-series data augmentation) or an official example already does the job (see *Reference repositories*). Built-in blocks that call a provider need the user's own provider API key.

## How synthetic data blocks work

A synthetic data block is a **transformation block in `standalone` mode** with `type: "synthetic-data"` in `parameters.json`. It receives no input file or directory. It generates data, then uploads each sample to the project with the project API key. There are **no required outputs**; the pattern is upload through the Ingestion API.

Studio passes `--synthetic-data-job-id <job-id>`. Send it as the `x-synthetic-data-job-id` header on every upload so Studio can show a live preview of the generated samples on the **Synthetic data** tab while the job runs.

## Required files

- `Dockerfile` — builds the container. `ENTRYPOINT` runs the script.
- `parameters.json` — block metadata (`type: "synthetic-data"`) + user-facing parameters.
- Generation script — `transform.py` in the official examples; any language that can call the Ingestion API works.
- Optional `requirements.txt` and `.dockerignore`.
- `.ei-block-config` — written by `edge-impulse-blocks init`; it binds the directory to one organization and block ID. Gitignore it in public or shared repos, commit it in a private team repo.

## Block I/O contract

### Command line arguments

Every parameter item in `parameters.json` becomes a CLI argument (`--<param> <value>`), except `secret` items (see below). Studio adds these automatically:

| Argument | When | Meaning |
| --- | --- | --- |
| `--synthetic-data-job-id <job-id>` | Always | Integer job ID. Send it as the `x-synthetic-data-job-id` header on every upload. |
| Standalone-mode transformation arguments | Always | Studio also passes the arguments that standalone transformation blocks get (see the transformation block docs). Accept them with `parse_known_args` so the block does not fail on arguments it does not use. |

Users can also append extra CLI arguments when editing the block in Studio.

How parameter types arrive:

| Type | Passed as |
| --- | --- |
| `int`, `float`, `select` | `--<param> <value>` |
| `string` | `--<param> "<value>"` |
| `boolean` | `--<param> 1` or `--<param> 0` |
| `flag` | `--<param>` when checked, nothing when unchecked |
| `bucket`, `dataset` | `--<param> "<name>"` |
| `secret` | **Environment variable** named by `param`, not an argument |

### Environment variables

Values are always strings.

| Variable | Description |
| --- | --- |
| `EI_API_ENDPOINT` | API base URL, `https://studio.edgeimpulse.com/v1`. |
| `EI_API_KEY` | Organization API key with member privileges. |
| `EI_INGESTION_HOST` | Ingestion API host, `edgeimpulse.com`. Always read it with that default. |
| `EI_ORGANIZATION_ID` | ID of the organization that owns the block. |
| `EI_PROJECT_ID` | ID of the project receiving the data. |
| `EI_PROJECT_API_KEY` | Project API key. Use it as `x-api-key` for uploads. |

Declare your own variables (provider endpoints, tokens) in `info.requiredEnvVariables`. The CLI prompts for them on `push`, and they can be edited in Studio afterwards. `secret` parameters are also delivered as environment variables.

### Mounted storage buckets

Buckets in the organization can be mounted at `/mnt/s3fs/<bucket-name>`, selected during `edge-impulse-blocks init`. The mount point can be changed by editing the block in Studio. Mount a bucket when the generator needs source assets, for example the object and background images of a composite generator.

## parameters.json

```json
{
  "version": 1,
  "type": "synthetic-data",
  "info": {
    "name": "My image generator",
    "description": "Generates images from a prompt and uploads them with a label.",
    "requiredEnvVariables": []
  },
  "parameters": [
    {
      "name": "Provider API key",
      "value": "",
      "type": "secret",
      "param": "PROVIDER_API_KEY",
      "help": "API key for the generation provider. Stored in Studio Secrets."
    },
    {
      "name": "Prompt",
      "value": "A photo of a factory worker wearing a hard hat",
      "type": "string",
      "param": "prompt",
      "multiline": true,
      "help": "Prompt to generate images from."
    },
    {
      "name": "Label",
      "value": "hard_hat",
      "type": "string",
      "param": "label",
      "help": "Samples are added to the project with this label."
    },
    {
      "name": "Number of images",
      "value": 3,
      "type": "int",
      "param": "images",
      "help": "Number of unique images to generate."
    },
    {
      "name": "Upload to category",
      "value": "split",
      "type": "select",
      "param": "upload-category",
      "valid": [
        { "label": "Split 80/20 between training and testing", "value": "split" },
        { "label": "Training", "value": "training" },
        { "label": "Testing", "value": "testing" }
      ],
      "help": "Data is uploaded to this category in your project."
    }
  ]
}
```

- `info` keys: `name`, `description`, `requiredEnvVariables`. There is no `operatesOn`; the block shows in the **Synthetic data** tab through the `showInSyntheticData` flag (see *Push workflow*).
- `parameters` is a flat array. Item fields: `name`, `value` (default), `type`, `param`, `help`, `valid` (for `select`; strings or `{ label, value }`), `optional`, `readonly`, `showIf` (`{ parameter, operator: "eq" | "neq", value }`, `value` as a string such as `"true"`), `multiline`, `hint`, `placeholder`.
- Types: `string`, `int`, `float`, `select`, `boolean`, `bucket`, `dataset`, `flag`, `secret`.
- Keep `param` spelling identical to what the script parses. Dashes are not converted, so `upload-category` arrives as `--upload-category` (Python's argparse exposes it as `args.upload_category`).
- `--upload-category` is **not** added by Studio for standalone blocks. Define it as a `select` parameter (as above) if the user should choose where the data goes, and validate the value in the script.
- Multiline `string` values reach the script with literal `\n` sequences. Convert them with `value.replace('\\n', '\n')`.
- Studio stores a secret the first time a user enters it. The value is no longer visible afterwards, and it is managed under organization **Secrets** (Enterprise) or **Account settings → Secrets**.
- Older example repos store `parameters.json` as a bare array with no `type` or `info`. Prefer the object format above. Also set the block type when editing the block in Studio if you inherit a bare-array file.
- Compute requests and limits and the maximum run time are not set in `parameters.json`. Set them by editing the block in Studio after the push, or with the update transformation block API.

## Dockerfile

```dockerfile
FROM python:3.10-slim
WORKDIR /app

# Add system tools you need at build time, for example: apt-get install -y ffmpeg
COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . ./

ENTRYPOINT ["python3", "-u", "transform.py"]
```

Keep `WORKDIR /app` (never `/home` or `/data`), put `ENTRYPOINT` last, and pin dependency versions. Bake static assets (backgrounds, objects) into the image or mount a bucket. Add `output/`, `.venv/`, and `load-keys.sh` to `.dockerignore`.

## Script skeleton (Python)

```python
import argparse, json, os, sys, time
import requests

for var in ("EI_PROJECT_API_KEY", "PROVIDER_API_KEY"):
    if not os.getenv(var):
        print(f"Missing {var}"); sys.exit(1)

API_KEY = os.environ["EI_PROJECT_API_KEY"]
INGESTION_HOST = os.environ.get("EI_INGESTION_HOST", "edgeimpulse.com")
INGESTION_URL = "https://ingestion." + INGESTION_HOST

parser = argparse.ArgumentParser()
parser.add_argument("--prompt", required=True)
parser.add_argument("--label", required=True)
parser.add_argument("--images", type=int, required=True)
parser.add_argument("--upload-category", default="split")
parser.add_argument("--synthetic-data-job-id", type=int, required=False)
parser.add_argument("--skip-upload", action="store_true")   # for local runs
parser.add_argument("--out-directory", default="output")
args, _unknown = parser.parse_known_args()

if args.upload_category not in ("split", "training", "testing"):
    print(f'Invalid --upload-category "{args.upload_category}"'); sys.exit(1)
os.makedirs(args.out_directory, exist_ok=True)
prompt = args.prompt.replace("\\n", "\n")
epoch = int(time.time())

def generate(prompt: str) -> bytes:
    raise NotImplementedError  # call your model here; return PNG bytes

for i in range(args.images):
    print(f"Creating image {i + 1} of {args.images}...", end="", flush=True)
    png = generate(prompt)
    path = os.path.join(args.out_directory, f"{args.label}.{epoch}.{i}.png")
    with open(path, "wb") as f:
        f.write(png)

    if not args.skip_upload:
        res = requests.post(
            f"{INGESTION_URL}/api/{args.upload_category}/files",
            headers={
                "x-api-key": API_KEY,
                "x-label": args.label,
                "x-metadata": json.dumps({"generated_by": "my-generator", "prompt": prompt}),
                # requests drops headers whose value is None
                "x-synthetic-data-job-id": str(args.synthetic_data_job_id)
                    if args.synthetic_data_job_id is not None else None,
            },
            files={"data": (os.path.basename(path), png, "image/png")},
            timeout=120,
        )
        body = res.json() if res.status_code == 200 else {}
        if res.status_code != 200 or not body.get("success") or not body["files"][0].get("success"):
            print(f"\nUpload failed ({res.status_code}): {res.text}")
            sys.exit(1)
    print(" OK", flush=True)
```

### Uploading to the Ingestion API

- Endpoint: `POST https://ingestion.<EI_INGESTION_HOST>/api/{training|testing|split}/files`. `split` sends about 80% to training and 20% to testing. The official examples build the URL from `EI_INGESTION_HOST`, and use `http://` with port `4810` only for `host.docker.internal` (Edge Impulse internal development). Don't hard-code `edgeimpulse.com`.
- Auth: `x-api-key: <EI_PROJECT_API_KEY>`. Send the file as multipart field `data` (wav, jpg, png, csv, json, cbor; see the Ingestion API docs for formats).
- Headers: `x-label` (omit it, or send `x-no-label: 1`, when labels come from bounding boxes), `x-metadata` (JSON string), `x-bounding-boxes` (JSON array), `x-disallow-duplicates`, `x-add-date-id`, and `x-synthetic-data-job-id`.
- Bounding boxes: send `x-bounding-boxes` as a JSON array of `{ "label", "x", "y", "width", "height" }` in pixels, all numbers, **one image per request**. The project's labeling method must be **Bounding boxes (object detection)** or the boxes are silently discarded.
- Check both `body["success"]` and `body["files"][i]["success"]`, because a 200 response can still hold a per-file error.
- Name files uniquely, for example `<label>.<epoch>.<index>.<ext>`, so repeated runs don't collide. Use `x-add-date-id: 1` for the server to add a unique ID.
- Tag generated samples in `x-metadata` (`generated_by`, `prompt`, model name) so users can filter synthetic data in or out when comparing experiments.

### Behavior to build in

- Support a `--skip-upload` and `--out-directory` pair for local testing; the official examples do.
- For provider calls: set timeouts, retry with backoff, and handle rate limits. Fail with a clear message and a non-zero exit code on any unrecoverable error; upload sample by sample so partial results stay in the project.
- Randomize variation (voice, speed, seed, position) per sample, so generated data isn't uniform.
- Pad or normalize output to what the project expects (for example, minimum audio length, sampling rate, image size).
- Log one flushed line per sample. Never print API keys or secrets.
- Remind users that provider calls cost money on their own account, and that they should generate a handful first.

## Local testing

The `edge-impulse-blocks runner` **does not support synthetic data blocks**. Test in this order:

1. Run the script directly with uploads off:

    ```bash
    export EI_PROJECT_API_KEY=ei_...
    export PROVIDER_API_KEY=...
    python3 -u transform.py --prompt "a hard hat" --label hard_hat --images 2 --skip-upload
    ```

2. Run it against a scratch project with the upload on, passing a fake job ID:

    ```bash
    python3 -u transform.py --prompt "a hard hat" --label hard_hat --images 2 --synthetic-data-job-id 123456789
    ```

3. Build and run the container:

    ```bash
    docker build -t custom-synthetic-data-block .
    docker run --rm -e EI_PROJECT_API_KEY='ei_...' -e PROVIDER_API_KEY='...' \
      custom-synthetic-data-block --prompt "a hard hat" --label hard_hat --images 2 --synthetic-data-job-id 123456789
    ```

4. Push, then generate a handful of samples from **Data acquisition → Synthetic data** in a test project and check the preview and the dataset before generating more.

## Push workflow (Enterprise)

```bash
edge-impulse-blocks init   # choose the organization and the transformation block type; select buckets to mount; writes .ei-block-config
edge-impulse-blocks push   # archives the directory; the image is built and hosted by Edge Impulse
edge-impulse-blocks info   # shows the name, organization, and settings
```

Authenticate non-interactively with `edge-impulse-blocks --api-key ei_...` (an organization API key). The CLI prompts for each `requiredEnvVariables` value on push. The blocks CLI docs don't list synthetic data as its own block type. After the first push, check that the block appears under organization **Custom blocks → Synthetic data**, and in the block selector on a project's **Synthetic data** tab. If it doesn't, edit the block in Studio or through the API: synthetic data blocks use the transformation block endpoints (get, add, update, delete), and the `showInSyntheticData` flag decides whether a block appears in the **Synthetic data** tab. See the `ei-api` skill.

## Documentation

- https://docs.edgeimpulse.com/studio/organizations/custom-blocks/custom-synthetic-data-blocks — custom synthetic data block interface (arguments, environment variables, job ID header, testing)
- https://docs.edgeimpulse.com/studio/projects/data-acquisition/synthetic-data — using synthetic data blocks in Studio (built-in blocks, secrets, good practice)
- https://docs.edgeimpulse.com/apis/ingestion — Ingestion API (headers, formats, bounding boxes)
- https://docs.edgeimpulse.com/tools/specifications/files/parameters-json — full parameters.json specification
- https://docs.edgeimpulse.com/studio/organizations/custom-blocks — rules common to all custom blocks
- https://docs.edgeimpulse.com/tools/clis/edge-impulse-cli/blocks — edge-impulse-blocks CLI reference

## Reference repositories

- https://github.com/edgeimpulse/example-transform-Dall-E-images — Python; DALL-E 3 image generation with upload (simplest example)
- https://github.com/edgeimpulse/example-transform-whisper-keywords — Python; keyword audio with Whisper text-to-speech, random voices and speeds, padding to a minimum length
- https://github.com/edgeimpulse/example-transform-image-composites — Python; composite object-detection images from backgrounds and objects, uploaded with `x-bounding-boxes`

The repositories are named `example-transform-<description>`, so synthetic data and transformation block examples share the name pattern. Read the repository description to tell them apart. These examples use the older bare-array `parameters.json`, so use the object format above for new blocks.

## Instructions

1. Confirm what the block should generate (images, audio, time series, bounding boxes), which model or algorithm it uses, and which credentials it needs. Confirm the user has an Enterprise organization, and whether a built-in block already fits.
2. Start from the closest example above and keep its structure. Use Python unless the user asks otherwise.
3. Write `parameters.json` with `type: "synthetic-data"`. Mirror each non-secret item as a CLI argument with the exact `param` spelling, and read secrets from the environment. Include label, count, and upload category parameters.
4. Write the script so that it accepts `--synthetic-data-job-id` and ignores unknown arguments, uploads each sample with `x-api-key`, `x-label` or `x-bounding-boxes`, `x-metadata`, and `x-synthetic-data-job-id`, and checks the upload result.
5. Handle provider calls with timeouts, retries, and clear errors. Log progress per sample. Never log secrets.
6. Test in this order: direct run with `--skip-upload`, direct run into a scratch project, `docker run`, then the **Synthetic data** tab after the push. The blocks runner cannot be used.
7. Add `.ei-block-config` (public repos), `output/`, `load-keys.sh`, `.venv/`, and `__pycache__/` to `.gitignore`, and `output/`, `.venv/`, and `load-keys.sh` to `.dockerignore`.
8. Push, then remind the user to set compute limits and maximum run time in Studio, to check the block appears in the **Synthetic data** tab, and to generate a handful of samples first.
