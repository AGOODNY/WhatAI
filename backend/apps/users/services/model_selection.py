from django.core.exceptions import ObjectDoesNotExist

from config.llm_models import DEFAULT_LLM_MODEL, normalize_llm_model


def get_user_llm_model(user):
    try:
        selected_model = user.profile.llm_model
    except (AttributeError, ObjectDoesNotExist):
        selected_model = DEFAULT_LLM_MODEL

    return normalize_llm_model(selected_model)
