# ComfyUI REST API Documentation

Welcome to the developer documentation for the **ComfyUI REST API Gateway**. 

This documentation hub provides everything you need to interface programmatically with the local ComfyUI Stable Diffusion engine.

![Architecture Banner](assets/banner.jpg)

## Navigation

- 🚀 **[Starting the Servers](starting-servers.md)**: Guide on how to boot the ComfyUI core, REST API, and MCP Client using the integrated script.
- 🧭 **[Getting Started / Usage Guide](usage.md)**: Learn how to format payloads and test the endpoints using cURL.
- 🏗️ **[System Architecture](architecture.md)**: Understand how the API safely interacts with ComfyUI's internal graph loop and websocket streams.
- 🧠 **[Choosing the Right Model](models-context.md)**: A deep dive into all supported Checkpoint models (DreamShaper, Juggernaut, RealVis), their optimal sampling steps, and CFG constraints.
- 📜 **[MDX Reference](rest-api.mdx)**: React-compatible API reference for advanced site generators.

## OpenAPI Spec
The complete API schema is available in [openapi.json](openapi.json). You can import this directly into Postman or Insomnia to automatically generate your HTTP client requests.
