---
lab3_genai_diff:
  instrumentation: "opentelemetry-instrumentation-genai-openai 1.2b0; OpenTelemetry SDK 1.45.0; JSON file exporter 0.66b0"
  spec_ref: semantic-conventions@v1.41.1
  attributes:
    - {name: gen_ai.operation.name, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.provider.name, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.request.model, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.request.max_tokens, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.response.finish_reasons, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.response.model, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.response.id, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.usage.input_tokens, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.usage.output_tokens, emitted: true, in_spec: true, stability: development}
---
<!-- ai-generated: 100% - compared a real local Qwen span against the published OpenTelemetry GenAI semantic conventions -->

# What the library emits, against the spec

The captured span is a real chat-completion request made through the OpenAI-compatible Ollama API. The instrumentation emitted nine GenAI attributes, and each is defined in the selected semantic-conventions release with development stability. Model, provider, operation, response identity, finish reason, and token usage are represented. Message contents were not captured, which avoids copying prompt or completion text into telemetry. The attributes are still experimental, so dashboards should treat their names and semantics as version-sensitive rather than as a permanent contract.
