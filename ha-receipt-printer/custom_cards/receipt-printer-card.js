/**
 * Receipt Printer Card
 * A single-file custom Lovelace card providing a UI for every endpoint exposed
 * by api.py: /print/text, /print/url, /print/image.
 *
 * Install:
 *   1. Copy this file to <HA config>/www/receipt-printer-card.js
 *   2. Add a Lovelace resource (UI: Edit Dashboard -> ⋮ -> Manage Resources):
 *        URL: /local/receipt-printer-card.js
 *        Resource type: JavaScript
 *   3. Add to a view (YAML):
 *        type: custom:receipt-printer-card
 *        printer_url: http://192.168.1.100:8000
 *   4. Developer Tools -> YAML -> Reload All YAML, then hard-refresh the browser.
 *
 * Requires CORS to be enabled on api.py (already added via CORSMiddleware).
 */
(function () {
  "use strict";

  function el(tag, attrs, kids) {
    var e = document.createElement(tag);
    if (attrs) {
      Object.keys(attrs).forEach(function (k) {
        if (k === "style") {
          Object.assign(e.style, attrs[k]);
        } else if (k === "class") {
          e.className = attrs[k];
        } else if (k === "onclick") {
          e.addEventListener("click", attrs[k]);
        } else if (k === "oninput") {
          e.addEventListener("input", attrs[k]);
        } else if (k === "onchange") {
          e.addEventListener("change", attrs[k]);
        } else {
          e.setAttribute(k, attrs[k]);
        }
      });
    }
    if (kids) {
      (Array.isArray(kids) ? kids : [kids]).forEach(function (k) {
        if (k == null) return;
        e.appendChild(typeof k === "string" ? document.createTextNode(k) : k);
      });
    }
    return e;
  }

  function styledBtn(label) {
    var b = el(
      "button",
      {
        type: "button",
        style: {
          padding: "8px 16px",
          background: "var(--primary-color)",
          color: "var(--text-primary-color, #fff)",
          border: "none",
          borderRadius: "4px",
          cursor: "pointer",
          fontSize: "14px",
          fontWeight: "500",
        },
      },
      label
    );
    b.addEventListener("mouseenter", function () {
      b.style.opacity = "0.85";
    });
    b.addEventListener("mouseleave", function () {
      b.style.opacity = "1";
    });
    return b;
  }

  function labeledInput(labelText, inputEl) {
    return el(
      "label",
      {
        style: {
          display: "flex",
          flexDirection: "column",
          gap: "4px",
          fontSize: "0.85em",
          color: "var(--secondary-text-color)",
        },
      },
      [el("span", null, labelText), inputEl]
    );
  }

  function field() {
    return el("input", {
      type: "text",
      style: {
        padding: "6px 8px",
        background: "var(--card-background-color)",
        color: "var(--primary-text-color)",
        border: "1px solid var(--divider-color)",
        borderRadius: "4px",
        fontSize: "14px",
      },
    });
  }

  function area() {
    var a = el("textarea", {
      rows: "3",
      style: {
        padding: "6px 8px",
        background: "var(--card-background-color)",
        color: "var(--primary-text-color)",
        border: "1px solid var(--divider-color)",
        borderRadius: "4px",
        fontSize: "14px",
        fontFamily: "inherit",
        resize: "vertical",
      },
    });
    return a;
  }

  function checkbox() {
    var c = el("input", { type: "checkbox" });
    c.style.width = "16px";
    c.style.height = "16px";
    return c;
  }

  function select(options) {
    var s = el("select", {
      style: {
        padding: "6px 8px",
        background: "var(--card-background-color)",
        color: "var(--primary-text-color)",
        border: "1px solid var(--divider-color)",
        borderRadius: "4px",
        fontSize: "14px",
      },
    });
    options.forEach(function (o) {
      s.appendChild(el("option", { value: o }, o));
    });
    return s;
  }

  function setStatus(node, msg, kind) {
    node.textContent = msg;
    node.style.color =
      kind === "error"
        ? "var(--error-color)"
        : kind === "success"
        ? "var(--success-color)"
        : "var(--secondary-text-color)";
  }

  async function postForm(baseUrl, path, fields) {
    var fd = new FormData();
    Object.keys(fields).forEach(function (k) {
      fd.append(k, fields[k]);
    });
    var res = await fetch(baseUrl + path, { method: "POST", body: fd });
    var ctype = res.headers.get("content-type") || "";
    if (ctype.indexOf("application/json") >= 0) {
      return await res.json();
    }
    return { status: res.ok ? "success" : "error", message: "HTTP " + res.status };
  }

  async function postFile(baseUrl, path, file) {
    var fd = new FormData();
    fd.append("file", file, file.name);
    var res = await fetch(baseUrl + path, { method: "POST", body: fd });
    var ctype = res.headers.get("content-type") || "";
    if (ctype.indexOf("application/json") >= 0) {
      return await res.json();
    }
    return { status: res.ok ? "success" : "error", message: "HTTP " + res.status };
  }

  class ReceiptPrinterCard extends HTMLElement {
    setConfig(config) {
      if (!config || !config.printer_url) {
        throw new Error("printer_url is required");
      }
      this._config = config;
      this._render();
    }

    set hass(h) {
      this._hass = h;
    }

    getCardSize() {
      return 6;
    }

    _render() {
      var self = this;
      var cfg = this._config;
      var baseUrl = cfg.printer_url.replace(/\/$/, "");

      // --- shared status line per section ---
      var statusText = el("div", {
        style: { fontSize: "0.85em", marginTop: "4px", minHeight: "1em" },
      });
      var statusUrl = el("div", {
        style: { fontSize: "0.85em", marginTop: "4px", minHeight: "1em" },
      });
      var statusImg = el("div", {
        style: { fontSize: "0.85em", marginTop: "4px", minHeight: "1em" },
      });

      // --- 1. Print text ---
      var textArea = area();
      var fastBox = checkbox();
      var btnText = styledBtn("Print text");
      btnText.addEventListener("click", async function () {
        var v = textArea.value.trim();
        if (!v) {
          setStatus(statusText, "Type something first.", "error");
          return;
        }
        btnText.disabled = true;
        setStatus(statusText, "Printing…");
        try {
          var r = await postForm(baseUrl, "/print/text", {
            text: v,
            fast: fastBox.checked ? "true" : "false",
          });
          setStatus(
            statusText,
            r.status === "success" ? "Printed." : "Error: " + (r.message || "?"),
            r.status === "success" ? "success" : "error"
          );
        } catch (e) {
          setStatus(statusText, "Request failed: " + e.message, "error");
        } finally {
          btnText.disabled = false;
        }
      });

      // --- 2. Print image from URL ---
      var urlInput = field();
      urlInput.setAttribute("placeholder", "https://example.com/image.png");
      var btnUrl = styledBtn("Print URL");
      btnUrl.addEventListener("click", async function () {
        var v = urlInput.value.trim();
        if (!v) {
          setStatus(statusUrl, "Paste an image URL first.", "error");
          return;
        }
        btnUrl.disabled = true;
        setStatus(statusUrl, "Printing…");
        try {
          var r = await postForm(baseUrl, "/print/url", { url: v });
          setStatus(
            statusUrl,
            r.status === "success" ? "Printed." : "Error: " + (r.message || "?"),
            r.status === "success" ? "success" : "error"
          );
        } catch (e) {
          setStatus(statusUrl, "Request failed: " + e.message, "error");
        } finally {
          btnUrl.disabled = false;
        }
      });

      // --- 3. Print image (file upload) ---
      var fileInput = el("input", { type: "file", accept: "image/png,image/jpeg,image/gif" });
      fileInput.style.fontSize = "13px";
      var btnImg = styledBtn("Print uploaded image");
      btnImg.addEventListener("click", async function () {
        var file = fileInput.files[0];
        if (!file) {
          setStatus(statusImg, "Pick an image file first.", "error");
          return;
        }
        btnImg.disabled = true;
        setStatus(statusImg, "Uploading…");
        try {
          var r = await postFile(baseUrl, "/print/image", file);
          setStatus(
            statusImg,
            r.status === "success" ? "Printed: " + file.name : "Error: " + (r.message || "?"),
            r.status === "success" ? "success" : "error"
          );
        } catch (e) {
          setStatus(statusImg, "Request failed: " + e.message + " (check CORS on api.py)", "error");
        } finally {
          btnImg.disabled = false;
        }
      });

      // --- layout ---
      var section = function (title, kids) {
        return el(
          "div",
          {
            style: {
              borderTop: "1px solid var(--divider-color)",
              paddingTop: "12px",
              marginTop: "12px",
            },
          },
          [
            el(
              "div",
              {
                style: {
                  fontWeight: "600",
                  marginBottom: "8px",
                  color: "var(--primary-text-color)",
                },
              },
              title
            ),
          ].concat(kids)
        );
      };

      var row = function (kids) {
        return el(
          "div",
          { style: { display: "flex", gap: "8px", alignItems: "flex-end", flexWrap: "wrap" } },
          kids
        );
      };

      var grid2 = function (a, b) {
        return el(
          "div",
          { style: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" } },
          [a, b]
        );
      };

      var card = el("ha-card", { header: "Receipt Printer" }, [
        el(
          "div",
          { style: { padding: "16px" } },
          [
            section("Print text", [
              labeledInput("Text", textArea),
              row([
                el(
                  "label",
                  { style: { display: "flex", gap: "6px", alignItems: "center", fontSize: "13px" } },
                  [fastBox, el("span", null, "Fast (raw ESC/POS)")]
                ),
                btnText,
              ]),
              statusText,
            ]),
            section("Print image from URL", [
              labeledInput("Image URL", urlInput),
              row([btnUrl]),
              statusUrl,
            ]),
            section("Upload image", [
              fileInput,
              row([btnImg]),
              statusImg,
            ]),
          ]
        ),
      ]);

      this.innerHTML = "";
      this.appendChild(card);
    }
  }

  customElements.define("receipt-printer-card", ReceiptPrinterCard);

  window.customCards = window.customCards || [];
  window.customCards.push({
    type: "receipt-printer-card",
    name: "Receipt Printer",
    description: "Full UI for the api.py thermal printer service (text, URL, upload).",
  });
})();