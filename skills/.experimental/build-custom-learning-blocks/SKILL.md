---
name: build-custom-learning-blocks
description: Author Edge Impulse custom learning blocks (custom ML blocks). Use when asked to scaffold, modify, test, or push a custom learning block — including the training container Dockerfile, parameters.json for machine-learning blocks, train scripts that read X/Y npy splits and write model artifacts (saved_model.zip, model.onnx, TFLite, model.pkl), and the edge-impulse-blocks CLI init/runner/push workflow.
metadata:
  version: "0.1.0"
---

Help the user author an Edge Impulse custom learning block. A learning block is a Docker container that Studio runs to train a model on the features produced by the input and processing (DSP) blocks. Any framework and language work — the contract is only the CLI arguments in, and model files written to the output directory.

Unlike other custom block types, custom learning blocks are available on **all plans**: Enterprise users push blocks into their organization; everyone else pushes into their developer profile (profile photo → **Custom ML blocks**).

Before building a full custom block, check whether a lighter path fits: small architecture or loss tweaks can be done in **expert mode** (learning block settings → three dots → *Switch to Keras (expert) mode*), and most built-in blocks (classifier, regression, FOMO) can be downloaded as a starting point (learning block settings → three dots → *Edit block locally*).

## Required files

- `Dockerfile` — builds the training container. `ENTRYPOINT` runs the train script.
- `parameters.json` — block metadata (`type: "machine-learning"`) + user-facing parameters.
- Train script(s) — any language (the official examples use Python and Bash).
- Optional `requirements.txt`, `.dockerignore` (exclude `data/`, `out/`).
- `.ei-block-config` — created by `edge-impulse-blocks init`; it binds the directory to one account/organization and block ID. The CLI docs recommend committing it so collaborators push to the same block; the official public example repos gitignore it instead so each user initializes their own. Gitignore it in public or shared repos, commit it in a private team repo.

## CLI contract

Studio invokes the container's ENTRYPOINT with:

| Argument | When |
| --- | --- |
| `--data-directory <dir>` | Always. Processed training/validation data. |
| `--out-directory <dir>` | Always. Where model artifacts must be written. |
| `--info-file <file>` | Always. Path to `train_input.json` (one docs page calls the flag `--input-file`; accept both if you use it). |
| `--epochs <int>`, `--learning-rate <float>` | Only if the block defines **no** custom parameters. |
| `--<param> <value>` | One per entry in `parameters.json` (see mapping below). |

Parameter-type → argument mapping: `int`/`float`/`select` → `--<param> <value>`; `string` → `--<param> "<value>"`; `boolean` → `--<param> 1` or `--<param> 0`; `flag` → `--<param>` present or omitted. The `bucket`, `dataset`, and `secret` types are only available to AI labeling, synthetic data, and transformation blocks — not machine-learning blocks.

Rules from the official examples:

- Parse with `parse_known_args()` (Python) or ignore unknown flags (shell) — Studio may pass arguments the script does not declare.
- Create the out directory if missing; its existence is not guaranteed.
- Once the block declares any custom parameter, Studio stops auto-passing `--epochs`/`--learning-rate` — declare `epochs` yourself (param name `epochs`; every official example does), plus `learning-rate` when the trainer exposes it (the Keras and PyTorch examples do; the YOLOv5 block passes `model-size` and `batch-size` instead).
- `train_input.json` (class names, mode, input shape, int8 conversion flags, training time limits) is **not available when running locally** with the blocks runner — treat it as optional or the block can only run in Studio.

## Data directory contents

    X_split_train.npy   X_split_test.npy
    Y_split_train.npy   Y_split_test.npy
    sample_id_details.json

The `_test` files are the validation split (default 80/20, adjustable in Studio's Advanced training settings). Data has already passed through the DSP block — these are features, not raw samples.

- `X_*.npy` — float32 arrays; official examples load with `np.load(..., mmap_mode='r')`. Derive the input shape from `X_train.shape[1:]`.
- `Y_*.npy` (classification) — in all official example repos, a one-hot 2-D array; derive the class count from `Y_train.shape[1]`. The docs instead describe an int32 array with four columns (`label_index`, `sample_id`, `sample_slice_start_ms`, `sample_slice_end_ms`); `train_input.json` carries a `yType` field (`npy` | `structured`) — inspect the array shape rather than assuming either layout.
- **Object detection** — `Y_*.npy` files are JSON text despite the extension (`json.loads`, not `np.load`): a list of `{"sampleId": ..., "boundingBoxes": [{"label", "x", "y", "w", "h"}]}` with pixel coordinates and **1-based** label indices. X is `(N, height, width, channels)`.
- **Anomaly detection** — `*_test.npy` files are empty; all nominal training data is in `*_train.npy`.
- Images arrive RGB, NHWC, with pixels already scaled per the block's `imageInputScaling` — do not rescale. For PyTorch/NCHW models, transpose yourself; if you output ONNX, the NCHW→NHWC conversion on device is handled automatically.
- Real class-name strings are not in the data directory; they are only in `train_input.json` (`classes`).

## Output contract

Write at least one of these exact filenames to `--out-directory`:

| File | Notes |
| --- | --- |
| `saved_model.zip` | Zipped TensorFlow SavedModel; the Keras example zips a top-level `saved_model/` directory (`make_archive` with `base_dir='saved_model'`). Studio converts to float32 + int8 TFLite. |
| `model.onnx` | ONNX with int8, float16, or float32 I/O. Studio converts to both TFLite variants. |
| `model.tflite` | TFLite with float32 I/O, if converting yourself. |
| `model_quantized_int8_io.tflite` | int8 TFLite with int8 (not uint8) inputs/outputs. |
| `model.pkl` | Pickled scikit-learn model. Pin `scikit-learn==1.3.2` (what Edge Impulse converts with); LightGBM 3.3.5 and XGBoost 1.7.6 also supported; arbitrary pipelines are not convertible. |

Emitting only `saved_model.zip` (Keras example) or only `model.onnx` (PyTorch example) is sufficient. Object detection models must end in a last layer Studio supports (including FOMO, MobileNet SSD, YOLOv2 for BrainChip Akida, YOLOv5/v7/v11/X/Pro, and NVIDIA TAO variants — the API's `ObjectDetectionLastLayer` enum is the current list). Anomaly blocks must output a single score (1-D) or a score grid (2-D, visual anomaly).

## parameters.json

```json
{
  "version": 1,
  "type": "machine-learning",
  "info": {
    "name": "My learning block",
    "description": "What the block trains",
    "operatesOn": "other",
    "indRequiresGpu": false,
    "repositoryUrl": "https://github.com/org/repo"
  },
  "parameters": [
    {
      "name": "Number of training cycles",
      "value": 30,
      "type": "int",
      "help": "Number of epochs to train the neural network on.",
      "param": "epochs"
    },
    {
      "name": "Learning rate",
      "value": 0.001,
      "type": "float",
      "help": "How fast the neural network learns.",
      "param": "learning-rate"
    }
  ]
}
```

`info` keys:

- `operatesOn` — `object_detection` | `audio` | `image` | `regression` | `other`.
- `objectDetectionLastLayer` — required for object detection (e.g. `fomo`, `yolov5`, `mobilenet-ssd`), so Studio can decode the output tensors.
- `imageInputScaling` — `0..1` | `-1..1` | `-128..127` | `0..255` | `torch` | `bgr-subtract-imagenet-mean`. Chosen when initializing the block, changeable in Studio; must match what the training code assumes.
- `indRequiresGpu` — set `true` only if training cannot run on CPU.
- `customModelVariants`, `displayCategory` (`classical` | `tao`) — advanced Studio grouping/variants.

Parameter entries: `param` becomes the CLI flag (kebab-case, no leading dashes); `name` is the form label, `help` the tooltip, `value` the default (string, number, or boolean — the docs example uses bare numbers, the committed example repos quote them as strings; both work). `select` adds `valid` (strings or `{label, value}` pairs); `optional: true` renders as "click to set"; `showIf` shows a parameter conditionally; `section: "advanced"` moves it under Advanced settings.

## Dockerfile

```dockerfile
FROM ubuntu:22.04
ARG DEBIAN_FRONTEND=noninteractive
WORKDIR /app

RUN apt update && apt install -y python3 python3-pip

COPY requirements.txt ./
RUN pip3 install -r requirements.txt

COPY . ./

ENTRYPOINT ["python3", "-u", "train.py"]
```

Rules:

- Never set `WORKDIR` to `/home` or `/data` — both are reserved by Edge Impulse and your files would be overwritten. Any other path works (the Python examples use `/app`; the YOLOv5 block keeps its scripts in `/scripts` with the vendored trainer in `/app`).
- Set the executable with `ENTRYPOINT` (not `RUN` or `CMD`); use `python3 -u` so logs stream unbuffered into Studio.
- Containers have **no network access at runtime** in Studio — install every dependency and download pretrained weights at build time.
- Copy and install `requirements.txt` before `COPY . ./` for layer caching.
- GPU training: start from an `nvidia/cuda` base image and install CUDA/cuDNN userland packages (see the Keras example's `dependencies/install_cuda.sh`, which skips CUDA on aarch64 so the image still builds on Apple Silicon); set `indRequiresGpu` accordingly.

## Train script skeleton (Keras)

Pin TensorFlow to a Keras 2 release in `requirements.txt` (the official example uses `tensorflow==2.11.0`; anything below 2.16 works) — under Keras 3 `model.save()` rejects `save_format='tf'` and SavedModel directories; there use `model.export(saved_model_path)` instead.

```python
import argparse, os, shutil
import numpy as np
import tensorflow as tf

parser = argparse.ArgumentParser()
parser.add_argument('--data-directory', type=str, required=True)
parser.add_argument('--epochs', type=int, required=True)
parser.add_argument('--learning-rate', type=float, required=True)
parser.add_argument('--out-directory', type=str, required=True)
args, unknown = parser.parse_known_args()

os.makedirs(args.out_directory, exist_ok=True)

X_train = np.load(os.path.join(args.data_directory, 'X_split_train.npy'), mmap_mode='r')
Y_train = np.load(os.path.join(args.data_directory, 'Y_split_train.npy'))
X_test = np.load(os.path.join(args.data_directory, 'X_split_test.npy'), mmap_mode='r')
Y_test = np.load(os.path.join(args.data_directory, 'Y_split_test.npy'))

classes = Y_train.shape[1]
train_ds = tf.data.Dataset.from_tensor_slices((X_train, Y_train)).batch(32)
val_ds = tf.data.Dataset.from_tensor_slices((X_test, Y_test)).batch(32)

model = tf.keras.Sequential([
    tf.keras.layers.Dense(20, activation='relu'),
    tf.keras.layers.Dense(10, activation='relu'),
    tf.keras.layers.Dense(classes, activation='softmax', name='y_pred'),
])
model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=args.learning_rate),
              loss='categorical_crossentropy', metrics=['accuracy'])
model.fit(train_ds, validation_data=val_ds, epochs=args.epochs, verbose=2)

saved_model_path = os.path.join(args.out_directory, 'saved_model')
model.save(saved_model_path, save_format='tf')
shutil.make_archive(saved_model_path, 'zip',
                    root_dir=os.path.dirname(saved_model_path),
                    base_dir='saved_model')
```

For PyTorch, train as usual, then export ONNX instead — this single call is the official example's entire conversion step:

```python
torch.onnx.export(model.cpu(),
                  torch.randn(tuple([1] + list(X_train.shape[1:]))),
                  os.path.join(args.out_directory, 'model.onnx'),
                  export_params=True, opset_version=10, do_constant_folding=True,
                  input_names=['input'], output_names=['output'])
```

For third-party training pipelines (the YOLOv5 block), the entrypoint can be a shell script that converts the Edge Impulse data layout into the pipeline's native format in `/tmp`, invokes the vendored trainer (pinned to an exact commit, weights baked into the image), and copies/renames the resulting artifacts to the exact output filenames above.

## Local testing

Requires Docker plus the Edge Impulse CLI (the example READMEs require v1.16.0 or higher for `--download-data`), and an Edge Impulse project whose impulse matches the block (`edge-impulse-blocks runner` pulls that project's processed features).

Fastest loop — download real data once, then run the container directly:

```bash
edge-impulse-blocks runner --download-data data/
docker build -t my-learning-block .
docker run --rm -v $PWD:/app my-learning-block --data-directory /app/data --epochs 30 --learning-rate 0.01 --out-directory out/
```

Because the repo is bind-mounted over `/app`, script edits need no rebuild; only `requirements.txt` changes do. Add `--gpus all` for NVIDIA GPUs, `--shm-size=1024m` for PyTorch dataloaders. Re-run `--download-data` when project data changes; add `--clean` to any blocks command to switch projects.

Alternatively run everything through the runner: `edge-impulse-blocks runner --extra-args "--data-directory /home --out-directory /home/out"` (also accepts `--epochs`, `--learning-rate`, `--validation-set-size`, `--input-shape`). It creates `ei-block-data/<projectId>/`, mounted into the container as `/home`.

After local training, profile on-device latency/RAM/ROM with the Studio profiling API or Python SDK.

## Push workflow

```bash
edge-impulse-blocks init   # one-time: pick account/org, block type, name; writes .ei-block-config
edge-impulse-blocks push   # upload; container is built on Edge Impulse infrastructure
```

The block then appears under **Create impulse > Add learning block** in any project, like a built-in block. Compute requests/limits and maximum training time are configured by editing the block in Studio after push — not in `parameters.json`. If parameter changes don't show up after a push, update the CLI (`npm update -g edge-impulse-cli`). Any blocks command accepts `--clean` to reset stored CLI configuration; to change a block's type, the example READMEs' procedure is to delete both `parameters.json` and `.ei-block-config` and re-run `init`.

## Documentation

- https://docs.edgeimpulse.com/studio/organizations/custom-blocks/custom-learning-blocks — custom learning blocks guide (arguments, data, outputs, testing)
- https://docs.edgeimpulse.com/studio/organizations/custom-blocks — rules common to all custom blocks (Dockerfile, no runtime network)
- https://docs.edgeimpulse.com/tools/specifications/files/parameters-json — full parameters.json specification
- https://docs.edgeimpulse.com/tools/specifications/files/train-input-json — train_input.json fields
- https://docs.edgeimpulse.com/tools/specifications/files/sample-id-details-json — sample_id_details.json format
- https://docs.edgeimpulse.com/tools/clis/edge-impulse-cli/blocks — edge-impulse-blocks CLI reference

## Reference repositories

- https://github.com/edgeimpulse/example-custom-ml-block-keras — canonical Keras block (SavedModel output, CUDA-capable Dockerfile)
- https://github.com/edgeimpulse/example-custom-ml-block-pytorch — canonical PyTorch block (ONNX output)
- https://github.com/edgeimpulse/ml-block-yolov5 — production object-detection block wrapping a third-party trainer (JSON labels, bash entrypoint, multi-format output)
- https://github.com/edgeimpulse/example-custom-ml-block-scikit — scikit-learn block (model.pkl output)

## Instructions

1. Ask which framework (Keras/TensorFlow, PyTorch, scikit-learn, or a third-party pipeline) and which task (classification, regression, object detection, anomaly detection) if not stated — they determine the skeleton, `operatesOn`, and output format.
2. Prefer the simplest output the framework supports: `saved_model.zip` for TensorFlow/Keras, `model.onnx` for PyTorch, `model.pkl` for scikit-learn. Only hand-convert to TFLite when the user needs control over quantization.
3. Mirror every `parameters.json` entry with a matching argument in the train script. Always include an `epochs` parameter, and `learning-rate` when the trainer exposes it. Use `parse_known_args()` and create the out directory.
4. For object detection: load `Y_*.npy` as JSON, convert 1-based labels to the trainer's base, set `operatesOn: "object_detection"` and a supported `objectDetectionLastLayer`, and keep `imageInputScaling` consistent with the training code.
5. Never add runtime downloads to the Dockerfile; bake pretrained weights and dependencies into the image. Pin third-party trainer repos to exact commits.
6. Recommend testing locally with `edge-impulse-blocks runner --download-data data/` + `docker run` before pushing, and warn that `train_input.json` is unavailable locally.
7. Add `data/`, `out/`, and `ei-block-data/` to `.gitignore` — plus `.ei-block-config` when the repo is public or shared (commit it in a private team repo). Keep `data/` and `out/` in `.dockerignore`.
8. After scaffolding, tell the user to run `edge-impulse-blocks init` then `edge-impulse-blocks push`, and where the block lands (organization on Enterprise, otherwise their developer profile's Custom ML blocks).
