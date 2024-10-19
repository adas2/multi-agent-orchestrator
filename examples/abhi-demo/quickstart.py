import uuid
import asyncio
from typing import Optional, List, Dict, Any
# import json
import sys
from multi_agent_orchestrator.orchestrator import MultiAgentOrchestrator, OrchestratorConfig
from multi_agent_orchestrator.agents import (
    BedrockLLMAgent,
    BedrockLLMAgentOptions,
    AgentResponse,
    AgentCallbacks)
from multi_agent_orchestrator.classifiers import BedrockClassifier, BedrockClassifierOptions
from multi_agent_orchestrator.types import ConversationMessage, ParticipantRole

from multi_agent_orchestrator.agents import LexBotAgent, LexBotAgentOptions
from multi_agent_orchestrator.agents import AmazonBedrockAgent, AmazonBedrockAgentOptions
# from multi_agent_orchestrator.agents import LambdaAgent, LambdaAgentOptions
import weather_tool
import logging

logger = logging.getLogger()
# logger.setLevel(logging.DEBUG)
logger.setLevel(logging.INFO)

custom_bedrock_classifier = BedrockClassifier(BedrockClassifierOptions(
    model_id='anthropic.claude-3-sonnet-20240229-v1:0',
    region='us-east-1',
    inference_config={
        'maxTokens': 500,
        'temperature': 0.7,
        'topP': 0.9
    }
))

orchestrator = MultiAgentOrchestrator(
    classifier=custom_bedrock_classifier,
    options=OrchestratorConfig(
        LOG_AGENT_CHAT=True,
        LOG_CLASSIFIER_CHAT=True,
        LOG_CLASSIFIER_RAW_OUTPUT=True,
        LOG_CLASSIFIER_OUTPUT=True,
        LOG_EXECUTION_TIMES=True,
        MAX_RETRIES=3,
        USE_DEFAULT_AGENT_IF_NONE_IDENTIFIED=False,
        MAX_MESSAGE_PAIRS_PER_AGENT=10,
        NO_SELECTED_AGENT_MESSAGE="I'm not sure how to handle your request. I don't have a brain yet!"
    )
)

class BedrockLLMAgentCallbacks(AgentCallbacks):
    def on_llm_new_token(self, token: str) -> None:
        # handle response streaming here
        print(token, end='', flush=True)

# Add some agents: TECH AGENT (LLM)
tech_agent = BedrockLLMAgent(BedrockLLMAgentOptions(
  name="Tech Agent",
  streaming=True,
  description="Specializes in technology areas including software development, hardware, AI, \
  cybersecurity, blockchain, cloud computing, emerging tech innovations, and pricing/costs \
  related to technology products and services.",
  model_id="anthropic.claude-3-sonnet-20240229-v1:0",
  callbacks=BedrockLLMAgentCallbacks()
))
#   model_id="anthropic.claude-3-sonnet-20240229-v1:0" 
# "anthropic.claude-v2:1",

orchestrator.add_agent(tech_agent)

""""""
# Add some agents: WEATHER AGENT (API)
weather_agent = BedrockLLMAgent(BedrockLLMAgentOptions(
    name="Weather Agent",
    streaming=False,
    description="Specialized agent for giving weather condition from a city.",
    # model_id="anthropic.claude-3-sonnet-20240229-v1:0",
    tool_config={
        'tool': weather_tool.weather_tool_description,
        'toolMaxRecursions': 5,
        'useToolHandler': weather_tool.weather_tool_handler
    }
))
weather_agent.set_system_prompt(weather_tool.weather_tool_prompt)
orchestrator.add_agent(weather_agent)

""""""

# add some agent: MATH-Agent (Custom)
math_agent = AmazonBedrockAgent(AmazonBedrockAgentOptions(
    name='Math Agent',
    description='You are a helpful agent who can perform basic math operations and tell the time.',
    agent_id='CE1I5RXPAZ',
    agent_alias_id='BTOLODOFRY'
))
orchestrator.add_agent(math_agent)

# add some agent: CHATBOT (Lex)
lex_agent = LexBotAgent(LexBotAgentOptions(
    name='Booking Bot',
    description='An agent specialized in flight booking',
    bot_id='YHQ5665ZY6',
    bot_alias_id='TSTALIASID',
    locale_id='en_US',
    region='us-east-1'
))
orchestrator.add_agent(lex_agent)

"""
# add some agent : LAMBDA AGENT
def my_custom_input_payload_encoder(input_text: str,
                                    chat_history: List[ConversationMessage],
                                    user_id: str,
                                    session_id: str,
                                    additional_params: Optional[Dict[str, str]] = None) -> str:
    return json.dumps({
        "userQuestion": input_text,
        "city": input_text,
        "history": [message.__dict__ for message in chat_history],
        "user": user_id,
        "session": session_id,
        **(additional_params or {})
    })

def my_custom_output_payload_decoder(response: Dict[str, Any]) -> ConversationMessage:
    decoded_response = json.loads(response['Payload'].read().decode('utf-8'))['body']
    return ConversationMessage(
        role=ParticipantRole.ASSISTANT.value,
        content=[{"text": f"Response: {decoded_response}"}]
    )


lambda_agent_options = LambdaAgentOptions(
    name='My Advanced Lambda Agent',
    description='A versatile agent that calls a custom Lambda function to check the weather, \
        find the coordinates of the location provided by user; use it as an alternative to Weather Agent.',
    function_name='fetch_location_weather',
    function_region='us-east-1',
    input_payload_encoder=my_custom_input_payload_encoder,
    output_payload_decoder=my_custom_output_payload_decoder
)

lambda_agent = LambdaAgent(lambda_agent_options)
orchestrator.add_agent(lambda_agent)

"""


async def handle_request(_orchestrator: MultiAgentOrchestrator, _user_input: str, _user_id: str, _session_id: str):
    response: AgentResponse = await _orchestrator.route_request(_user_input, _user_id, _session_id)
    # Print metadata
    print("\nMetadata:")
    print(f"Selected Agent: {response.metadata.agent_name}")
    if response.streaming:
        print('Response:', response.output.content[0]['text'])
    else:
        print('Response:', response.output.content[0]['text'])

if __name__ == "__main__":
    USER_ID = "user123"
    SESSION_ID = str(uuid.uuid4())
    print("Welcome to the interactive Multi-Agent system. Type 'quit' to exit.")
    while True:
        # Get user input
        user_input = input("\nYou: ").strip()
        if user_input.lower() == 'quit':
            print("Exiting the program. Goodbye!")
            sys.exit()
        # Run the async function
        asyncio.run(handle_request(orchestrator, user_input, USER_ID, SESSION_ID))




