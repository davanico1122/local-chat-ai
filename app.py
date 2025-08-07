import gradio as gr
import ollama
from threading import Lock

# Configuration
DEFAULT_MODEL = "phi3:mini"
MODEL_OPTIONS = [
    "phi3:mini",       # 3.8B (Lightning fast)
    "deepseek-coder",  # 6.7B (Code specialized)
    "llama3:8b",       # 8B (Balanced)
    "mistral",         # 7B (Multilingual)
]
MAX_HISTORY = 10  # Limit context length
STREAMING = True  # Real-time responses

# Thread-safe history management
chat_history = []
history_lock = Lock()

def generate_response(message, model_name, system_prompt):
    """Streaming response generator with context management"""
    global chat_history
    
    # Format messages with system prompt
    messages = [{"role": "system", "content": system_prompt}] if system_prompt else []
    
    with history_lock:
        # Add last N exchanges to context
        for human, ai in chat_history[-MAX_HISTORY:]:
            messages.extend([
                {"role": "user", "content": human},
                {"role": "assistant", "content": ai}
            ])
        messages.append({"role": "user", "content": message})
    
    # Stream response chunks
    stream = ollama.chat(
        model=model_name,
        messages=messages,
        stream=STREAMING,
        options={'num_ctx': 4096}  # Optimized context size
    )
    
    full_response = ""
    for chunk in stream:
        content = chunk['message']['content']
        full_response += content
        yield full_response
    
    # Update history
    with history_lock:
        chat_history.append((message, full_response))

def clear_history():
    """Reset chat history"""
    global chat_history
    with history_lock:
        chat_history = []
    return None, ""

# UI Components
with gr.Blocks(
    title=" LightLocal AI",
    theme=gr.themes.Glass(),
    css="footer {visibility: hidden}"
) as app:
    gr.Markdown("# <center> LightLocal AI</center>")
    gr.Markdown("### <center>Ultra-Fast Offline Chat</center>")
    
    with gr.Row():
        model_selector = gr.Dropdown(
            label="Model",
            choices=MODEL_OPTIONS,
            value=DEFAULT_MODEL,
            scale=2
        )
        system_prompt = gr.Textbox(
            label="System Prompt",
            placeholder="(Optional) Guide AI behavior...",
            scale=3
        )
    
    chatbot = gr.Chatbot(height=400, avatar_images=("", ""))
    msg = gr.Textbox(label="Your Message", placeholder="Type message...")
    
    with gr.Row():
        submit_btn = gr.Button("Send", variant="primary")
        clear_btn = gr.Button("Clear History", variant="stop")
    
    # Event handlers
    msg.submit(
        lambda m, mod, sys: generate_response(m, mod, sys),
        [msg, model_selector, system_prompt],
        chatbot
    ).then(lambda: "", None, msg)
    
    submit_btn.click(
        lambda m, mod, sys: generate_response(m, mod, sys),
        [msg, model_selector, system_prompt],
        chatbot
    ).then(lambda: "", None, msg)
    
    clear_btn.click(
        clear_history,
        inputs=None,
        outputs=[chatbot, msg]
    )

# Launch optimized server
if __name__ == "__main__":
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_api=False,
        enable_queue=True
    )
