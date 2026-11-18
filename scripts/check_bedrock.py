"""Check configuration privately; --invoke sends one small structured-output request."""
import argparse
import os
import pathlib
import sys

from dotenv import load_dotenv
from pydantic import BaseModel

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
load_dotenv(ROOT / ".env")

from llm import get_llm


class ConnectionReply(BaseModel):
    status: str


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--invoke", action="store_true")
    args = parser.parse_args()
    bearer = bool(os.getenv("AWS_BEARER_TOKEN_BEDROCK", "").strip())
    pair = bool(os.getenv("AWS_ACCESS_KEY_ID", "").strip() and
                os.getenv("AWS_SECRET_ACCESS_KEY", "").strip())
    print("Bedrock API key configured:", bearer)
    print("AWS access-key pair configured:", pair)
    print("Session token configured:", bool(os.getenv("AWS_SESSION_TOKEN", "").strip()))
    if os.getenv("LLM_PROVIDER") != "bedrock_converse":
        parser.exit(1, "Set LLM_PROVIDER=bedrock_converse in the local .env.\n")
    if not bearer and not pair:
        parser.exit(1, "Fill one credential option in the local .env; do not share it in chat.\n")
    if not args.invoke:
        print("Configuration present. No AWS request sent; authentication is not yet verified.")
        return
    try:
        reply = get_llm().with_structured_output(ConnectionReply, include_raw=True).invoke(
            [("system", "Respond with status equal to ok."), ("user", "Connection test.")])
        if reply["parsed"] is None or reply["parsed"].status.lower() != "ok":
            parser.exit(1, "Model replied but structured-output validation failed.\n")
        print("Bedrock structured-output connection: OK")
        print("Token usage:", getattr(reply["raw"], "usage_metadata", None))
    except Exception as error:
        response = getattr(error, "response", {})
        code = response.get("Error", {}).get("Code", type(error).__name__)
        message = response.get("Error", {}).get("Message", "")
        for name in ["AWS_BEARER_TOKEN_BEDROCK", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN"]:
            value = os.getenv(name)
            if value:
                message = message.replace(value, "[REDACTED]")
        if message:
            print("AWS reason:", message)
        parser.exit(1, f"Connection failed: {code}. Verify credentials, region, model access and quota.\n")


if __name__ == "__main__":
    main()
