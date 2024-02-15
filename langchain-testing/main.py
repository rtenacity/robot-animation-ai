import boto3
from dotenv import load_dotenv
from langchain.schema import HumanMessage
from langchain_community.chat_models import BedrockChat

load_dotenv()

client = boto3.client("bedrock-runtime")

chat = BedrockChat(model_id="meta.llama2-13b-chat-v1")

messages = [
    HumanMessage(
        content="Translate this sentence from English to French. I love programming."
    )
]

print(chat(messages))