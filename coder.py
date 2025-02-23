import json
import time
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from cerebras.cloud.sdk import Cerebras

class CerebrasEndpoint:
  def __init__(self):
    print("Creating Cerebras client...")
    self.client = Cerebras(api_key=os.environ.get("CEREBRAS_API_KEY"))
    self.model = "llama3.3-70b"

  def chat(self, messages):
    response = self.client.chat.completions.create(messages=messages, model=self.model)
    return response.choices[0].message.content

cerebras_endpoint = CerebrasEndpoint()

class ChatRequestHandler(BaseHTTPRequestHandler):
  protocol_version = "HTTP/1.1"

  def do_POST(self):
    content_length = int(self.headers.get("Content-Length", 0))
    post_data = json.loads(self.rfile.read(content_length))
    messages = [{"role": "system", "content": post_data.get("system_prompt", "")}] + post_data.get("messages", [])
    stream = post_data.get("stream", False)
    
    response_data = cerebras_endpoint.chat(messages)
    completion_id = f"chatcmpl-{int(time.time())}"
    print(post_data)
    
    if stream:
      self.send_response(200)
      self.send_header("Content-Type", "text/event-stream")
      self.send_header("Cache-Control", "no-cache")
      self.send_header("Connection", "keep-alive")
      self.end_headers()

      message = json.dumps({
        "id": completion_id,
        "model": "default",
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "choices": [{"index": 0, "delta": {"role": "assistant", "content": response_data}, "finish_reason": None}],
      })
      self.wfile.write(f"data: {message}\n\n".encode("utf-8"))
      self.wfile.flush()
      
      end_message = json.dumps({
        "id": completion_id,
        "model": "default",
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
      })
      self.wfile.write(f"data: {end_message}\n\n".encode("utf-8"))
      self.wfile.flush()
    else:
      self.send_response(200)
      self.send_header("Content-Type", "application/json")
      self.end_headers()
      self.wfile.write(json.dumps({
        "id": completion_id,
        "model": "default",
        "object": "chat.completion",
        "created": int(time.time()),
        "choices": [{"index": 0, "message": {"role": "assistant", "content": response_data}, "finish_reason": "stop"}],
      }).encode("utf-8"))

    self.send_header('Connection', 'close')

if __name__ == "__main__":
  server_address = ("", 8000)
  print("Starting server...")
  HTTPServer(server_address, ChatRequestHandler).serve_forever()
