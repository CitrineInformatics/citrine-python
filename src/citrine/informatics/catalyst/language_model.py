from gemd.enumeration.base_enumeration import BaseEnumeration


class LanguageModelChoice(BaseEnumeration):
    """The options for which model to use to answer a query."""

    GPT_35_TURBO = "gpt-3.5-turbo"
    GPT_35_TURBO_16K = "gpt-3.5-turbo-16k"
    GPT_4 = "gpt-4"
    GPT_4_32K = "gpt-4-32k"
