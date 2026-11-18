import pathlib
import sys
import types
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))
from llm import get_llm


class LLMFactoryTests(unittest.TestCase):
    def test_bedrock_model_region_and_timeouts(self):
        constructor = MagicMock()
        integration = types.ModuleType("langchain_aws")
        integration.ChatBedrockConverse = constructor
        config_module = types.ModuleType("botocore.config")
        config_module.Config = MagicMock()
        with patch.dict(sys.modules, {"langchain_aws": integration, "botocore.config": config_module}), \
                patch.dict("os.environ", {"LLM_PROVIDER": "bedrock_converse", "LLM_MODEL": "",
                                          "AWS_REGION": "us-west-2"}, clear=True):
            self.assertIs(get_llm(), constructor.return_value)
        arguments = constructor.call_args.kwargs
        self.assertEqual(arguments["model_id"], "us.anthropic.claude-haiku-4-5-20251001-v1:0")
        self.assertEqual(arguments["region_name"], "us-west-2")
        self.assertEqual(arguments["max_tokens"], 2048)
        config_module.Config.assert_called_once_with(connect_timeout=10, read_timeout=30,
                                                      retries={"total_max_attempts": 2, "mode": "standard"})

    def test_existing_provider_unchanged(self):
        with patch.dict("os.environ", {"LLM_PROVIDER": "openai", "LLM_MODEL": "gpt-4o-mini"}, clear=True), \
                patch("llm.init_chat_model") as constructor:
            get_llm()
        constructor.assert_called_once_with("gpt-4o-mini", model_provider="openai", temperature=0.0)
