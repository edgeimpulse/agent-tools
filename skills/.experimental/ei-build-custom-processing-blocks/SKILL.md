---
name: ei-build-custom-processing-blocks
description: Author Edge Impulse custom processing blocks (custom DSP blocks). Use when asked to scaffold, modify, test, host, or push a custom processing block — including the HTTP server that answers GET /, GET /parameters, POST /run, and POST /batch, the generate_features function, parameters.json for dsp blocks (grouped parameters, cppType, port), graphs and feature explorer output, output_config shapes, local testing through ngrok and edge-impulse-blocks runner, and the on-device extract_<cppType>_features C++ implementation.
metadata:
  version: "0.1.0"
---

Help the user author an Edge Impulse custom processing block. A processing block (DSP block) turns a window of raw sensor data into features for the learning block. Unlike every other custom block type, it is a **long-running HTTP server**, not a run-once script: Studio sends it raw samples over HTTP and reads features, labels, and graphs back from the response. Any language works.

Hosting rules:

- **Enterprise**: `edge-impulse-blocks push` builds and hosts the block on Edge Impulse infrastructure and makes it available to every project in the organization (organization → **Custom blocks** → **DSP**).
- **Every plan**: run the server yourself, expose it on a public HTTPS URL (ngrok during development, or any server you host), and add it to an impulse by URL. This is the only option on non-Enterprise plans.

Before writing a block, check whether a built-in processing block (Raw data, Flatten, Spectral analysis, Spectrogram, MFE, MFCC, Image) with different parameters already fits. Their sources in `edgeimpulse/processing-blocks` are the best starting point for a variation.

## Required files

- `Dockerfile` — builds the server image. Uses `EXPOSE <port>` and `ENTRYPOINT` to start the server.
- `parameters.json` — block metadata (`type: "dsp"`) and **grouped** parameters.
- The HTTP server (the Python example's `dsp-server.py` is generic and normally left unchanged).
- The feature function (`dsp.py` with `generate_features(...)` in the Python example).
- `requirements-blocks.txt` (Python example), and optionally `.dockerignore`.
- `.ei-block-config` — written by `edge-impulse-blocks init`; it binds the directory to one organization and block ID. Gitignore it in public or shared repos; commit it in a private team repo so collaborators push to the same block.

## HTTP contract

| Method | Path | Returns |
| --- | --- | --- |
| GET | `/` | Plain text describing the block (for example `Edge Impulse DSP block: <title> by <author>`). |
| GET | `/parameters` | The `parameters.json` contents as JSON (set `version: 1`). |
| POST | `/run` | Features (and graphs, when requested) for **one** sample. Used by the parameters page preview. |
| POST | `/batch` | Features for **many** samples. Used by **Generate features**, training, and testing. |

Request headers: `x-ei-project-id` on run and batch, `x-ei-sample-id` on run, `x-ei-sample-ids` on batch.

`POST /run` body:

```typescript
{
  features: number[];            // flattened raw window: interleaved axes, row-major
  axes: string[];                // e.g. ['accX', 'accY', 'accZ']
  sampling_freq: number;
  draw_graphs: boolean;          // only build graphs when true
  project_id: number;
  implementation_version: number;
  params: { [k: string]: string | number | boolean | number[] | string[] | null };
  calculate_performance: boolean;
  named_axes: { [k: string]: string | false } | false | undefined;
}
```

`POST /batch` body is the same, except `features` is `number[][]` (one array per sample), there is no `draw_graphs`, `project_id`, or `calculate_performance`, and a `state: string` field carries state between samples for blocks that set `usesState`.

Parameter names arrive with **dashes replaced by underscores**: a `param` of `scale-axes` arrives as `params.scale_axes`. The Python example splats `params` straight into `generate_features(**args)`, so each parameter must be a keyword argument with the underscore name, or the call fails.

Response for `/run`:

```typescript
{
  success: true,
  features: number[],
  graphs: DSPRunGraph[],          // [] when draw_graphs is false
  labels?: string[],              // one name per feature, shown in the feature explorer
  fft_used?: number[],            // FFT lengths used; lets MCUs drop unused FFT tables
  output_config: OutputConfig,
  state_string?: string,
}
```

Response for `/batch`: `{ success: true, features: number[][], labels, output_config, state }`.

`output_config` tells Studio how to reshape the flat features for the learning block:

- `{ type: 'flat', shape: { width: N } }` — one feature vector (dense networks, anomaly, classical ML).
- `{ type: 'spectrogram', shape: { width, height } }` — 2-D time-frequency output (1-D/2-D convolutions).
- `{ type: 'image', shape: { width, height, channels, frames? } }` — image output for vision models.

**Errors:** respond with **HTTP 200** and `{ "success": false, "error": "<message>" }`. Studio shows the message to the user. Don't use 4xx/5xx for processing failures.

### Input layout

- **Time series:** `features` is the window flattened as `[s0_ax0, s0_ax1, ..., s1_ax0, ...]`. Reshape with `raw_data.reshape(-1, len(axes))` and slice per axis.
- **Images:** `raw_data[0]` is the width and `raw_data[1]` the height; each following value is one pixel packed as `0xRRGGBB`. Unpack it the way the built-in Image block does (`raw_data[2:].astype(np.uint32).view(np.uint8)` gives B, G, R, pad bytes per pixel), and scale to 0..1.

## parameters.json

```json
{
  "version": 1,
  "type": "dsp",
  "info": {
    "title": "RMS and peak features",
    "author": "Your Name",
    "description": "Per-axis RMS, peak-to-peak, and zero-crossing rate.",
    "name": "RMS features",
    "cppType": "rms_features",
    "preferConvolution": false,
    "visualization": "dimensionalityReduction",
    "experimental": false,
    "latestImplementationVersion": 1,
    "port": 4446
  },
  "parameters": [
    {
      "group": "Scaling",
      "items": [
        {
          "name": "Scale axes",
          "value": 1,
          "type": "float",
          "help": "Multiplies axes by this number",
          "param": "scale-axes"
        }
      ]
    }
  ]
}
```

Rules:

- `parameters` is an **array of groups** (`{ group, items: [...] }`), unlike every other block type, where it's a flat array of items. Each `group` renders as a header in Studio.
- `cppType` names the on-device function: `extract_<cppType>_features`. Use snake_case with no spaces, and keep it unique within the impulse.
- `port` must match the server's listen port and the Dockerfile's `EXPOSE`. When pushing, the CLI asks for the port if `port` is missing, defaulting to the `EXPOSE` value.
- `visualization: "dimensionalityReduction"` runs UMAP for the feature explorer. Set it when the output is high-dimensional (spectrograms, images, long vectors). Leave it out for a handful of named features so the explorer can plot them directly against each other.
- `latestImplementationVersion` is passed to the block as `implementation_version`. To change behavior without breaking existing impulses, raise it, branch on `implementation_version` in code, and gate new parameters with `showForImplementationVersion`.
- Other `info` keys: `axes` (named input axes, `{ name, description, optional? }`), `usesState` (keep and send back `state` between batch calls), `preferConvolution`/`convolutionColumns`/`convolutionKernelSize` (hints for the default neural network), `hasFeatureImportance`, `hasAutoTune`, `supportedTargets`, `dontAllowDataNormalization`.
- Parameter item types available to processing blocks: `int`, `float`, `string`, `select`, `boolean`, `flag`. `bucket`, `dataset`, and `secret` are not. Processing-block-only item fields: `showForImplementationVersion` and `createMacro` (emits `#define EI_DSP_PARAMS_<CPPTYPE>_<PARAM> <value>` in the exported library).

## Feature function skeleton (Python)

The generic `dsp-server.py` from `example-custom-processing-block-python` calls `generate_features` with `implementation_version`, `draw_graphs`, `raw_data` (a NumPy array), `axes`, `sampling_freq`, and every parameter (underscored). For `/batch` it calls it once per sample, with `draw_graphs=False`, and also passes `state` when the function signature has a `state` argument.

```python
import numpy as np

def generate_features(implementation_version, draw_graphs, raw_data, axes, sampling_freq, scale_axes):
    raw_data = raw_data.reshape(-1, len(axes)) * scale_axes

    features, labels = [], []
    for ax_ix, ax in enumerate(axes):
        x = raw_data[:, ax_ix]
        rms = float(np.sqrt(np.mean(x ** 2)))
        p2p = float(np.max(x) - np.min(x))
        zcr = float(np.mean(np.abs(np.diff(np.sign(x - np.mean(x)))) > 0))
        features += [rms, p2p, zcr]
        labels += [f'{ax} RMS', f'{ax} Peak-to-peak', f'{ax} ZCR']

    graphs = []
    if draw_graphs:
        graphs.append({
            'name': 'RMS per axis',
            'X': {'RMS': features[0::3]},
            'y': list(range(len(axes))),
            'suggestedYMin': 0,
            'suggestedYMax': len(axes),
            'type': 'linear',
        })

    return {
        'features': features,
        'graphs': graphs,
        'labels': labels,
        'fft_used': [],
        'output_config': {'type': 'flat', 'shape': {'width': len(features)}},
    }
```

Return plain Python floats or lists. The example server converts a top-level NumPy `features` array, but not NumPy scalars nested inside lists or graphs, which break `json.dumps`.

### Graphs

Only build graphs when `draw_graphs` is true. They are shown on the block's parameters page for the selected sample.

- `type: 'linear'` or `'logarithmic'` — `X` is `{ seriesName: number[] }` and `y` is the shared axis. In the official tutorial, `X` holds the values and `y` the time steps, and `suggestedYMin`/`suggestedYMax` actually bound the **value** axis. Copy that pattern rather than reasoning from the names.
- `type: 'image'` — `image` is a base64 string with `imageMimeType` (`image/png` or `image/svg+xml`). Use this for spectrograms and processed images. Render with Matplotlib or PIL into a `BytesIO`.
- Optional: `axisLabels: { X, y }`, `lineWidth`, `smoothing`, `highlights`.

## Dockerfile

```dockerfile
FROM python:3.10-slim
WORKDIR /app

COPY requirements-blocks.txt ./
RUN pip3 install --no-cache-dir -r requirements-blocks.txt

COPY . ./

EXPOSE 4446
ENTRYPOINT ["python3", "-u", "dsp-server.py"]
```

Rules:

- Never set `WORKDIR` to `/home` or `/data`. Edge Impulse mounts over both. Use `/app`.
- Start the server with `ENTRYPOINT`, not `RUN` or `CMD`. Use `python3 -u` so logs aren't buffered.
- Listen on `0.0.0.0` (not `localhost`), on the `EXPOSE`d port. The example server reads optional `HOST` and `PORT` environment variables.
- Hosted processing blocks have **no network access** at runtime. Install every dependency and bake in every asset at build time.
- The server must handle concurrent requests (the example uses `ThreadingMixIn`). Batch calls during feature generation can be large.

## Local testing

1. Run the server without Docker for the fastest loop:

    ```bash
    pip3 install -r requirements-blocks.txt
    python3 dsp-server.py
    curl http://localhost:4446/            # block info
    curl http://localhost:4446/parameters  # parameters.json
    ```

2. Exercise `/run` with a synthetic window before connecting Studio:

    ```bash
    curl -s -X POST http://localhost:4446/run -H 'Content-Type: application/json' -d '{
      "features": [1,2,3,4,5,6,7,8,9], "axes": ["accX","accY","accZ"], "sampling_freq": 100,
      "draw_graphs": true, "implementation_version": 1, "params": {"scale_axes": 1}
    }'
    ```

3. Run it in Docker the way Edge Impulse will: `docker build -t my-dsp-block . && docker run -p 4446:4446 -it --rm my-dsp-block`.
4. Expose it to Studio, using one of these:
    - `edge-impulse-blocks runner` — builds the image, runs it with the `EXPOSE` port published (or `--port` from the init config), starts ngrok, and prints the public URL. Requires Docker and `ngrok` on `PATH`.
    - Manually: `ngrok http 4446`, then copy the `https://` forwarding URL.
5. In the project: **Create impulse** → **Add a processing block** → **Add custom block** (bottom left of the modal) → paste the URL. The block then behaves like a built-in block: tune parameters, **Generate features**, and train.

Studio calls the URL every time features are generated, so the tunnel and server must stay up while training. Free ngrok URLs change on every restart, so re-add the block when the URL changes.

## Push workflow (Enterprise)

```bash
edge-impulse-blocks init   # pick the organization, choose "DSP block", name it; writes .ei-block-config
edge-impulse-blocks push   # uploads the directory; the image is built and hosted by Edge Impulse
```

`push` asks which port the server listens on if `parameters.json` has no `port`. Afterwards, the block appears in the processing block list of every project in the organization. Compute requests and limits are set by editing the block in Studio (organization → **Custom blocks** → **DSP** → **Edit DSP block**), not in `parameters.json`. If a hosted block becomes unreachable, use **Retry connection** (or the retry connection API) before re-pushing. Use `--clean` with any blocks command to reset the stored CLI configuration.

## Running on device

Edge Impulse **does not generate on-device code** for custom processing blocks. After exporting a C++ library (Deployment → C++ library), `model-parameters/model_variables.h` contains a forward declaration:

```cpp
int extract_<cppType>_features(signal_t *signal, matrix_t *output_matrix, void *config_ptr, const float frequency);
```

Implement it in the application (for example `main.cpp`) so that it produces the same features, in the same order, as the Python block:

- Read input with `signal->get_data(offset, length, out_ptr)`. The window is interleaved by axis, exactly like `features` in `/run`.
- Cast `config_ptr` to the generated config struct (see `model_variables.h`) to read the block's parameter values.
- Write `output_matrix->rows * output_matrix->cols` floats into `output_matrix->buffer`, and return `EIDSP_OK` (0) on success.
- Use the built-in implementations in `inferencing-sdk-cpp/dsp` (and `edge-impulse-sdk/dsp/` in the export) as patterns, and the SDK's `numpy` helpers for FFTs and statistics.

Verify parity before trusting device results: run a test sample's raw features through both the Python block and the C++ function, and compare them value by value.

## Documentation

- https://docs.edgeimpulse.com/studio/organizations/custom-blocks/custom-processing-blocks — custom processing block interface (requests, responses, graphs, testing, on device)
- https://docs.edgeimpulse.com/tutorials/topics/feature-extraction/build-custom-processing-blocks — step-by-step tutorial (parameters, smoothing, graphs, images, C++)
- https://docs.edgeimpulse.com/studio/organizations/custom-blocks — rules common to all custom blocks (Dockerfile, no runtime network, editing after push)
- https://docs.edgeimpulse.com/tools/specifications/files/parameters-json — full parameters.json specification, including parameter groups and showForImplementationVersion
- https://docs.edgeimpulse.com/tools/clis/edge-impulse-cli/blocks — edge-impulse-blocks CLI reference (init, runner, push)

## Reference repositories

- https://github.com/edgeimpulse/example-custom-processing-block-python — canonical Python block; copy its generic `dsp-server.py` and edit only `dsp.py` and `parameters.json`
- https://github.com/edgeimpulse/example-custom-processing-block-cpp — features written in C++ and exposed to the Python server with pybind11; use when the same code should run in Studio and on device
- https://github.com/edgeimpulse/processing-blocks — sources of the built-in blocks (Flatten, Spectral analysis, Spectrogram, MFE, MFCC, Image); consult for graphs, image input unpacking, and `output_config` examples
- https://github.com/edgeimpulse/inferencing-sdk-cpp — C++ SDK; its `dsp/` directory shows on-device implementations to model `extract_<cppType>_features` on

## Instructions

1. Confirm the sensor type, axes, window length, sampling rate, and the features the user wants. Ask whether they're on Enterprise (hosted block) or will self-host (ngrok or their own server).
2. Start from `example-custom-processing-block-python`: keep `dsp-server.py`, and write `generate_features` in `dsp.py`. Pick another language only when the user asks for one, and then implement all four endpoints and the error convention.
3. Mirror every `parameters.json` item as a `generate_features` keyword argument, with dashes converted to underscores. Group items under `group` headers. Choose a unique snake_case `cppType`.
4. Return `features`, `labels` (for named features), `graphs` (only when `draw_graphs`), `fft_used`, and an `output_config` whose shape matches the feature count exactly.
5. Keep `port`, the server's listen port, and `EXPOSE` the same value. Install every dependency at build time.
6. Test with `curl` against `/`, `/parameters`, and `/run` before connecting Studio, then use `edge-impulse-blocks runner` (or Docker plus `ngrok http <port>`) and add the URL in **Create impulse**.
7. Add `.ei-block-config` to `.gitignore` when the repo is public or shared, plus `__pycache__/` and any local test data.
8. After the block works in Studio, remind the user that deployment needs a hand-written `extract_<cppType>_features` C++ function, and offer to write it along with a parity check.
