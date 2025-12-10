# app/gradio_app.py
import os
import json
import uuid
import tempfile
from typing import Tuple, Optional

import gradio as gr
import logging  # NEW

# NEW: basic logger setup
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Import your chain, models and memory
from src.chain import DeterministicChain
from src.models import MockClient, LLMClient
from src.memory import ShortTermMemory

# Try to import openai if user wants real model (optional)
try:
    from openai import OpenAI
    
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    OPENAI_AVAILABLE = True
except Exception:
    OPENAI_AVAILABLE = False

# Helper: OpenAI client wrapper (optional)
class OpenAIClient(LLMClient):
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        logger.debug("Initializing OpenAIClient with model=%s", model)
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OpenAI API key not found in env")
            raise RuntimeError("OpenAI API key not found.")
        self.model = model

    def generate(self, system: str, user: str, temperature: float = 0.1) -> str:
        logger.info("OpenAIClient.generate called (temp=%s)", temperature)
        # Use Chat Completions; adjust per provider if needed
        resp = client.chat.completions.create(model=self.model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature)
        # Extract text
        text = resp.choices[0].message.content
        logger.debug("OpenAIClient.generate got %d chars", len(text or ""))
        return text

# App-level memory and default client
GLOBAL_MEMORY = ShortTermMemory(max_len=4)

def build_chain(client_name: str, temperature: float) -> DeterministicChain:
    logger.info("build_chain called with client_name=%s, temperature=%s", client_name, temperature)
    # Choose client
    if client_name == "openai":
        if not OPENAI_AVAILABLE:
            logger.error("OpenAI SDK not available in environment")
            raise RuntimeError("OpenAI SDK not available in environment.")
        client = OpenAIClient(model="gpt-4o-mini")  # change model as desired
        client.generate = lambda system, user, temperature=temperature: OpenAIClient().generate(system, user, temperature)
        logger.debug("Using OpenAIClient")
    else:
        logger.debug("Using MockClient")
        # MockClient returns an instructive placeholder if used; change per-run via response_inject
        # We'll use MockClient with a simple default response that mirrors schema (for demo)
        demo_response = json.dumps({
            "name": "Demo Startup",
            "summary": "Demo summary; limited data.",
            "market": {"size_estimate": "unknown", "top_markets": [], "competitors": []},
            "product": {"category": "demo", "differentiation": "unknown"},
            "business_model": {"revenue_streams": [], "monetization_risks": []},
            "team": {"founders_count": "unknown", "strengths": [], "gaps": []},
            "risks": [],
            "recommendation": {"invest": "hold", "rationale": "insufficient data"},
            "assumptions": ["demo"]
        })
        client = MockClient(demo_response)
    chain = DeterministicChain(llm_client=client, memory=GLOBAL_MEMORY)
    logger.debug("DeterministicChain instance created")
    return chain

# UI helpers
def run_chain_and_format(user_input: str, model_choice: str, temperature: float, session_id: str):
    logger.info(
        "run_chain_and_format called model=%s, temp=%s, session_id=%s",
        model_choice, temperature, session_id,
    )
    logger.debug("User input (first 200 chars): %s", (user_input or "")[:200])
    try:
        chain = build_chain(client_name=model_choice, temperature=temperature)
    except Exception as e:
        logger.exception("Failed to build LLM client")
        return {"error": True, "message": f"Failed to build LLM client: {e}"}, "", "", session_id

    ok, result = chain.run(user_input, session_id=session_id)
    logger.info("chain.run finished ok=%s", ok)
    if not ok:
        logger.warning("Chain failed with result=%s", result)
        error_box = json.dumps(result, indent=2)
        return {"error": True, "message": "Chain failed", "detail": error_box}, "", "", session_id

    # result is pydantic model; convert to dict
    try:
        out_dict = result.dict()
        logger.debug("Converted result to dict with keys=%s", list(out_dict.keys()))
    except Exception:
        logger.debug("Result not a Pydantic model; using raw dict if possible")
        out_dict = result if isinstance(result, dict) else {}

    pretty_json = json.dumps(out_dict, indent=2)
    logger.debug("pretty_json length=%d", len(pretty_json))

    # create a temp file for download
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w")
    tmp.write(pretty_json)
    tmp.flush()
    tmp.close()
    download_path = tmp.name
    logger.info("Result JSON written to %s", download_path)

    return {"error": False}, pretty_json, download_path, session_id

# Gradio UI layout
with gr.Blocks(title="Startup Analyst AI", css=".output-json {white-space: pre-wrap;}") as demo:
    # Session id (hidden, auto-generated)
    session_id_input = gr.Textbox(value=str(uuid.uuid4()), label="Session ID (auto)", visible=False)

    with gr.Row():
        with gr.Column(scale=3):
            user_input = gr.Textbox(lines=6, placeholder="Paste startup description here...", label="User Input")
            with gr.Row():
                model_choice = gr.Radio(choices=["mock", "openai"], value="mock", label="Model")
                temp_slider = gr.Slider(minimum=0.0, maximum=1.0, value=0.1, step=0.05, label="Temperature")
                run_btn = gr.Button("Analyze")
            # Chat / JSON output area
            output_area = gr.Markdown("", elem_id="output_markdown")
            json_output = gr.Textbox(label="JSON Output", interactive=False, lines=20)
            download_btn = gr.File(label="Download JSON", visible=False)

        with gr.Column(scale=1):
            system_preview = gr.Textbox(label="System Prompt (Role + Behavior + Style + Output Format)", lines=20, value="")
            memory_view = gr.Textbox(label="Short-term Memory (last entries)", lines=20, value="")

    error_box = gr.HTML("", visible=False)

    # Update system preview on load
    def get_system_preview():
        from src.prompts.role import ROLE_PROMPT
        from src.prompts.behavior import BEHAVIOR_PROMPT
        from src.prompts.style import STYLE_PROMPT
        from src.prompts.output_format import OUTPUT_FORMAT_PROMPT
        return "\n\n".join([ROLE_PROMPT.strip(), BEHAVIOR_PROMPT.strip(), STYLE_PROMPT.strip(), OUTPUT_FORMAT_PROMPT.strip()])

    system_preview.value = get_system_preview()

    def on_run(user_text, model_choice_val, temperature_val, session_id_val):
        logger.info("on_run called for session_id=%s", session_id_val)
        logger.debug(
            "on_run params: model=%s, temp=%s, user_text_len=%d",
            model_choice_val, temperature_val, len(user_text or "")
        )
        if not user_text or user_text.strip() == "":
            logger.warning("on_run received empty user_text")
            return gr.update(visible=True, value="<div style='color:red'>Please enter startup description.</div>"), "", None, session_id_val
        result_info, pretty_json, download_path, sid = run_chain_and_format(
            user_text, model_choice_val, temperature_val, session_id_val
        )
        if result_info.get("error"):
            logger.error("Error from run_chain_and_format: %s", result_info)
            error_html = f"<div style='color:red'><b>Error:</b> {result_info.get('message')}<pre>{result_info.get('detail','')}</pre></div>"
            return error_html, "", None, sid
        logger.info("on_run success; returning JSON and download path")
        return "", pretty_json, download_path, sid

    run_btn.click(on_run, inputs=[user_input, model_choice, temp_slider, session_id_input],
                  outputs=[error_box, json_output, download_btn, session_id_input])

demo.launch(server_name="0.0.0.0", share=False)