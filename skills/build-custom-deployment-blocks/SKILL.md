---
name: build-custom-deployment-blocks
description: Author Edge Impulse custom deployment blocks (Enterprise). Use when asked to scaffold, modify, test, or push a custom deployment block — including Dockerfile, parameters.json schema, the build script that reads deployment-metadata.json and produces deploy.zip, and the edge-impulse-blocks CLI workflow.
metadata:
  version: "1.0.0"
---

Help the user author an Edge Impulse custom deployment block. A deployment block is a Docker container that Studio runs to turn a trained impulse into a downloadable artifact (firmware, library, container image, etc.). Custom deployment blocks are an **Enterprise-only** feature.

## Required files

A deployment block directory contains:

- `Dockerfile` — builds the container Studio runs.
- `parameters.json` — block metadata + user-facing parameter definitions.
- Build script — `build.py` (Python) or `build.js` (Node.js). Entry point of the container.
- Optional `package.json` (Node.js) or `requirements.txt` (Python) for dependencies.
- Optional `app/` directory for static template files copied into the build.

## Block I/O contract

Studio runs the container with `--metadata <path>` pointing at `deployment-metadata.json`. The build script must:

1. Parse `--metadata` and load the JSON.
2. Read input from `metadata.folders.input`. The input directory contains:

       deployment-metadata.json
       edge-impulse-sdk/
       model-parameters/
       tflite-model/
       trained.h5.zip
       trained.savedmodel.zip
       trained.tflite

3. Write a single `deploy.zip` into `metadata.folders.output`.

Never hard-code paths — always read them from the metadata file. Input and output dirs are on network storage; copy what you need into a local `/tmp/build` directory before doing heavy work.

## parameters.json schema

```json
{
  "version": 1,
  "type": "deploy",
  "info": {
    "name": "My deploy block",
    "description": "Build a standalone Linux application",
    "category": "firmware",
    "mountLearnBlock": false,
    "supportsEonCompiler": true,
    "showOptimizations": true,
    "cliArguments": "",
    "privileged": false
  },
  "parameters": [
    {
      "name": "Build Option",
      "value": "option-a",
      "type": "select",
      "param": "build-option-1",
      "help": "Choose compilation target",
      "valid": ["option-a", "option-b", "option-c"]
    },
    {
      "name": "Advanced Setting",
      "value": "default",
      "type": "select",
      "param": "advanced-option",
      "valid": ["default", "custom"],
      "showIf": {
        "parameter": "build-option-1",
        "operator": "eq",
        "value": "option-a"
      }
    }
  ]
}
```

`info` flags:

- `mountLearnBlock` — mount the project's training data at `/data` in the container.
- `privileged` — give the container internet access and inject the project API key.
- `showOptimizations` — show the int8/float32 optimization picker in the UI.
- `supportsEonCompiler` — show the EON Compiler toggle in the UI.
- `cliArguments` — extra args appended to the container entrypoint.
- `category` — UI grouping (e.g. `firmware`, `library`).

Each entry in `parameters[]` becomes a UI control. The chosen value is passed to the build script as `--<param>`. Use `showIf` to display a parameter only when another parameter has a given value.

## Dockerfile skeleton (Python)

```dockerfile
FROM ubuntu:20.04
ARG DEBIAN_FRONTEND=noninteractive
WORKDIR /ei

RUN apt update && apt install -y build-essential python3 python3-pip wget

# COPY any app/ template files first
COPY app ./app

# COPY the build script and any deps
COPY *.py ./
# COPY requirements.txt ./ && pip3 install -r requirements.txt

ENTRYPOINT [ "python3", "-u", "build.py" ]
```

## Dockerfile skeleton (Node.js)

```dockerfile
FROM node:18
WORKDIR /ei

COPY app ./app
COPY package*.json ./
RUN npm ci --omit=dev
COPY *.js ./

ENTRYPOINT [ "node", "build.js" ]
```

## Build script skeleton (Python)

```python
import argparse, json, os, shutil

parser = argparse.ArgumentParser()
parser.add_argument('--metadata', type=str, required=True)
# Add one parser.add_argument per entry in parameters.json, e.g.:
# parser.add_argument('--build-option-1', type=str)
args = parser.parse_args()

with open(args.metadata) as f:
    metadata = json.load(f)

input_dir = metadata['folders']['input']
output_dir = metadata['folders']['output']
app_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'app')

build_dir = '/tmp/build'
if os.path.exists(build_dir):
    shutil.rmtree(build_dir)
os.makedirs(build_dir)

os.system(f'cp -r {input_dir}/* {build_dir}')
os.system(f'cp -r {app_dir}/* {build_dir}')

# --- Build step goes here. Examples: invoke make, compile a binary,
#     run a code generator, package files. ---
os.chdir(build_dir)
os.system('make -j8')

os.makedirs(output_dir, exist_ok=True)
shutil.make_archive(os.path.join(output_dir, 'deploy'), 'zip', os.path.join(build_dir, 'build'))
```

## Build script skeleton (Node.js)

```javascript
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const { program } = require('commander');

program.requiredOption('--metadata <file>');
// .option('--build-option-1 <value>')
program.parse(process.argv);
const opts = program.opts();

const metadata = JSON.parse(fs.readFileSync(opts.metadata, 'utf8'));
const inputDir = metadata.folders.input;
const outputDir = metadata.folders.output;
const appDir = path.join(__dirname, 'app');

const buildDir = '/tmp/build';
fs.rmSync(buildDir, { recursive: true, force: true });
fs.mkdirSync(buildDir, { recursive: true });

execSync(`cp -r ${inputDir}/* ${buildDir}`);
if (fs.existsSync(appDir)) execSync(`cp -r ${appDir}/* ${buildDir}`);

// --- Build step goes here ---
execSync('make -j8', { cwd: buildDir });

fs.mkdirSync(outputDir, { recursive: true });
execSync(`cd ${path.join(buildDir, 'build')} && zip -r ${path.join(outputDir, 'deploy.zip')} .`);
```

## Local testing

Use the Edge Impulse block runner to download real project data and execute the block locally:

```bash
edge-impulse-blocks runner --extra-args "--build-option-1 option-a"
```

This creates `ei-block-data/` with `downloads/`, `input/`, and `output/` subdirectories.

To test the raw Docker image:

```bash
edge-impulse-blocks runner --download-data input/
docker build -t my-deploy-block .
docker run --rm -v $PWD:/home my-deploy-block --metadata /home/input/deployment-metadata.json
```

## Push workflow

```bash
edge-impulse-blocks init   # one-time: links this directory to an org block
edge-impulse-blocks push   # upload + build
```

After push, the block appears under the organization's **Custom blocks** and is selectable as a deployment target in any project.

## Reference

- Docs: https://docs.edgeimpulse.com/studio/organizations/custom-blocks/custom-deployment-blocks
- Example: https://github.com/edgeimpulse/example-custom-deployment-block
- Multi-impulse example: https://github.com/edgeimpulse/multi-impulse-deployment-block

## Instructions

1. Ask the user whether the build script should be **Python** or **Node.js** if not specified. Use the matching Dockerfile and build script skeleton.
2. Ask what the block actually does (compile firmware, package model files, generate language bindings, build a container image, etc.) so the build step in the script is meaningful — do not leave a placeholder `make` call without confirming it fits.
3. Only add entries to `parameters[]` if the user described user-facing options. Otherwise leave `parameters` empty or omitted.
4. For every parameter in `parameters.json`, add a matching `parser.add_argument` (Python) or `.option` (Node.js) in the build script.
5. Always read `metadata.folders.input` and `metadata.folders.output` from the metadata file. Never hard-code paths.
6. Always write the final artifact as `deploy.zip` into `folders.output`.
7. Set `privileged: true` only if the build genuinely needs internet access or the project API key — it is off by default.
8. Set `mountLearnBlock: true` only if the build needs the raw training data at `/data`.
9. Recommend the user test locally with `edge-impulse-blocks runner` before pushing.
10. After scaffolding, tell the user to run `edge-impulse-blocks init` (once) then `edge-impulse-blocks push` to upload. Remind them that custom deployment blocks require an **Enterprise** plan.
