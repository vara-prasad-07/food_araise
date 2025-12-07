import os
import json
import io
import gradio as gr
import httpx
from loguru import logger

# Setup logging for the UI
logger.add("ui_debug.log", rotation="10 MB")

NGROK_SAMPLE = "https://sleepier-cammy-prejudiciable.ngrok-free.dev"
DEFAULT_API_BASE = os.getenv("API_BASE_URL", NGROK_SAMPLE)


def _format_table(payload: dict) -> str:
    """Create a nutrition-label style markdown table from API payload."""
    if not payload or "items" not in payload:
        return ""

    lines = ["### Nutrition Facts", ""]
    total = payload.get("total_calories_estimate", "")
    if total:
        lines.append(f"**Total Calories:** {total}")
        lines.append("")

    lines.append("| Item | Calories | Protein | Carbs | Fats | Confidence |")
    lines.append("| --- | --- | --- | --- | --- | --- |")

    for item in payload.get("items", []):
        nut = item.get("nutrition", {})
        lines.append(
            f"| {item.get('name','')} | {nut.get('calories','')} | {nut.get('protein','')} | {nut.get('carbs','')} | {nut.get('fats','')} | {item.get('confidence','')} |"
        )

    if payload.get("dietary_warnings"):
        lines.append("")
        lines.append("**Warnings:** " + ", ".join(payload["dietary_warnings"]))

    return "\n".join(lines)


async def call_api(image, deep_search: bool, api_base_url: str):
    if image is None:
        return "Please upload an image.", ""

    # Normalize base url
    api_base = api_base_url.rstrip("/") or DEFAULT_API_BASE
    url = f"{api_base}/api/v1/food/analyze"

    try:
        # Convert PIL image to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format="JPEG")
        image_bytes = img_byte_arr.getvalue()

        files = {"file": ("upload.jpg", image_bytes, "image/jpeg")}
        data = {"deep_search": str(deep_search).lower()}

        logger.info(f"Calling API at {url} (deep_search={deep_search})")
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, files=files, data=data)
            if resp.status_code != 200:
                logger.error(f"API error {resp.status_code}: {resp.text}")
                return f"HTTP {resp.status_code}: {resp.text}", ""
            payload = resp.json()
            return json.dumps(payload, indent=2), _format_table(payload)
    except Exception as e:
        logger.error(f"UI Error: {e}")
        return f"Error: {str(e)}", ""


# Create Gradio Interface
with gr.Blocks(title="Food Agent Tester 🍎") as demo:
    gr.Markdown("# 🍎 Enterprise Food Agent Tester")
    gr.Markdown("Test the running FastAPI server via `/api/v1/food/analyze`. Upload an image and optionally toggle deep search. Output shows JSON and a nutrition-style table.")

    api_base_url = gr.Textbox(label="API Base URL", value=DEFAULT_API_BASE, info="Default: API_BASE_URL env or sample ngrok URL")
    sample_btn = gr.Button("Use sample ngrok URL", variant="secondary")

    with gr.Row():
        with gr.Column():
            input_img = gr.Image(type="pil", label="Upload Food Image")
            deep_search = gr.Checkbox(label="Deep search (slower, higher accuracy)", value=False)
            btn = gr.Button("Analyze", variant="primary")

        with gr.Column():
            output_json = gr.Code(language="json", label="Analysis Result (raw JSON)")
            output_table = gr.Markdown(label="Nutrition Facts")

    btn.click(call_api, inputs=[input_img, deep_search, api_base_url], outputs=[output_json, output_table])
    sample_btn.click(fn=lambda: NGROK_SAMPLE, outputs=api_base_url)


if __name__ == "__main__":
    demo.launch()
