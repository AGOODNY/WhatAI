DEFAULT_LLM_MODEL = "deepseek-v4-flash"

AVAILABLE_LLM_MODELS = (
    "deepseek-v4-flash",
    "deepseek-v4-pro",
)

LLM_MODEL_CHOICES = tuple((model, model) for model in AVAILABLE_LLM_MODELS)


def is_supported_llm_model(model):
    return model in AVAILABLE_LLM_MODELS


def normalize_llm_model(model):
    return model if is_supported_llm_model(model) else DEFAULT_LLM_MODEL
