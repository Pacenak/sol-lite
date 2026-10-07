# Model Layer

`ModelManager` resolves named profiles from `config/models.yaml`. The provider boundary is implemented by the Ollama adapter.

Models are configurable rather than hard-coded into the agent architecture. Missing models are diagnosed rather than silently substituted.
