# HA Receipt Printer

Custom Home Assistant integration for a thermal receipt printer controlled by
the `api.py` FastAPI service in this repo.

## What it does

Exposes the printer as a `notify` entity you can call from automations, scripts,
the HA dashboard, or any service call:

- **Print text** — `notify.receipt_printer` with `message:` (+ optional
  `data: { fast: true }` for raw ESC/POS instead of rendered image).
- **Print an image from a URL** — `data: { image_url: "https://..." }`
  (hits `/print/url`).
- **Print a canned task** — `data: { task_type: "fortune" }`
  (hits `/print/task`, e.g. fortune / weather).

## Install

This repo is a HACS custom repository:

1. In HACS → **Custom Repositories**, add the URL of this repo and choose the
   **Integration** category.
2. Search for "Receipt Printer" in HACS and install it.
3. Restart Home Assistant (or only reload integrations once).
4. **Settings → Devices & Services → Add Integration** → "Receipt Printer".
5. Enter the host and port of the PC running `api.py`
   (e.g. `192.168.1.100` and `8000`).

## Examples

Print text from a script:

```yaml
service: notify.receipt_printer
data:
  message: "Dinner is ready"
```

Print an image:

```yaml
service: notify.receipt_printer
data:
  message: ""
  data:
    image_url: "https://7timer.info/.../weathermap.png"
```

Run a canned task:

```yaml
service: notify.receipt_printer
data:
  message: "Oslo"
  data:
    task_type: weather
```

## Mapping to api.py

| HA call                                             | api.py endpoint |
| --------------------------------------------------- | --------------- |
| `message: "x"`                                      | `/print/text`   |
| `data.image_url: "https://..."`                     | `/print/url`    |
| `message: "Oslo"`, `data.task_type: weather`        | `/print/task`   |
| `data.fast: true` (text only)                       | `/print/text?fast=true` |

> The `/print/image` (file upload) endpoint is not exposed through the notify
> service because HA really only handles images-by-URL. If you need to upload a
> local HA file, call `/print/url` with a publicly reachable URL, or extend
> this component with a custom service.

## Notes

- Uses `aiohttp` (HA's bundled async HTTP client) — never `requests`.
- Connectivity is verified during the config flow by issuing a `GET` to
  `/print/text`; a 404/405 response from FastAPI is treated as "server alive".
- Only one printer per host:port is allowed (unique id pinned to `host:port`).

## Image upload (the `/print/image` endpoint)

The notify service cannot directly push an image-file binary to the printer
(HA wraps service payloads as data, not file streams). So `/print/image` is
exposed through [two paths][image-upload]:

1. **Service: `receipt_printer.print_image`** — for automations; pass a path on
   the HA server (e.g. an image produced by `camera.snapshot` or stored under
   `/config/www`). Example:

   ```yaml
   service: receipt_printer.print_image
   data:
     file_path: /config/www/snapshot.png
   ```

2. **Custom Lovelace card:** copy
   `custom_cards/receipt-printer-card.js` to `<HA config>/www/`, then register:

   ```yaml
   lovelace:
     resources:
       - url: /local/receipt-printer-card.js
         type: module
   ```

   Add to a view:
   ```yaml
   type: custom:receipt-printer-card
   printer_url: http://192.168.1.100:8000
   ```

   The card uploads a browser-picked file directly to `/print/image`. **CORS
   must be enabled on `api.py`** — already added to the repo's `api.py` via
   `fastapi.middleware.cors.CORSMiddleware`. If you skip that change, the upload
   request from the browser will be blocked by your browser's same-origin
   policy. The `/config/www` and automations route don't need CORS — only the
   browser-side upload card does.

[image-upload]: #image-upload-the-printimage-endpoint