import gradio as gr
import asyncio
from app.core.vision import analyze_food_image_with_search
from loguru import logger
import json

# Setup logging for the UI
logger.add("ui_debug.log", rotation="10 MB")

async def process_image(image):
    if image is None:
        return "Please upload an image."
    
    try:
        # Convert numpy/PIL image from Gradio to bytes
        import io
        from PIL import Image
        
        # Gradio passes a PIL Image by default with type="pil"
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG')
        image_bytes = img_byte_arr.getvalue()
        
        logger.info("Starting analysis from UI...")
        result = await analyze_food_image_with_search(image_bytes)
        
        # Format JSON as pretty string
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"UI Error: {e}")
        return f"Error: {str(e)}"

# Create Gradio Interface
with gr.Blocks(title="Food Agent Tester 🍎") as demo:
    gr.Markdown("# 🍎 Enterprise Food Agent Tester")
    gr.Markdown("Upload a food image to test the `Identify -> Search -> Synthesize` pipeline.")
    
    with gr.Row():
        with gr.Column():
            input_img = gr.Image(type="pil", label="Upload Food Image")
            btn = gr.Button("Analyze", variant="primary")
        
        with gr.Column():
            output_json = gr.Code(language="json", label="Analysis Result")
    
    btn.click(process_image, inputs=input_img, outputs=output_json)

if __name__ == "__main__":
    demo.launch()
