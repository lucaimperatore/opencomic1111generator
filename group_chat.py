import asyncio

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base import TaskResult
from autogen_agentchat.conditions import ExternalTermination, TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_core import CancellationToken
from autogen_ext.models.ollama import OllamaChatCompletionClient
from autogen_agentchat.messages import MultiModalMessage,TextMessage
from autogen_core import Image as AGImage
from PIL import Image
import json
import utils
import logging
logger = logging.getLogger(__name__)

# load the configuration
config = utils.load_configuration()

model_client = OllamaChatCompletionClient(
    model=config['llm_model']['model'],
    model_info=config['llm_model']['model_info'],
    host=config['llm_model']['host'] + ":" + str(config['llm_model']['port'])
)

# Create the primary agent.
primary_agent = AssistantAgent(
    "reviewer",
    model_client=model_client,
    system_message="You are an image reviewer, say that your name is Bob",
)

# Create the critic agent.
critic_agent = AssistantAgent(
    "critic",
    model_client=model_client,
    system_message="you are a critic which responds modifying the original prompt to better fit the image",
)

# Ai prompt specialist
ai_specialist = AssistantAgent(
    "specialist",
    model_client=model_client,
    system_message="you are an ai prompt specialist that uses the critic suggestions and responds only with an improved version of the given prompt based on the critic feedback",
)
# revisor agent
revisor_agent = AssistantAgent(
    "revisor",
    model_client=model_client,
    system_message="You are a revisor, respond 'APPROVE' if the image perfectly fits the given prompt or 'DECLINE' if the key elements of the scene are missing and the overall impression is not good"
)

# Define a termination condition that stops the task if the critic approves.
text_termination = TextMentionTermination('APPROVE') | TextMentionTermination('DECLINE')

# Create a team with the primary and critic agents.
team = RoundRobinGroupChat([primary_agent, critic_agent,ai_specialist,revisor_agent], termination_condition=text_termination)

async def image_validation(img_url,character_definition,image_prompt) -> str:
    pil_image = Image.open(img_url)
    img = AGImage(pil_image)
    primary_agent_message1 = MultiModalMessage(content=["Can you watch this image an keep in mind what it represents?", img], source="User")
    primary_agent_message2 = TextMessage(content="Does it represents this character definition: "+character_definition, source="User")

    critic_agent_message1 = MultiModalMessage(content=["This is the image object of the discussion.", img], source="User")
    
    ai_specialist_message1 = TextMessage(content="The original prompt is: "+image_prompt, source="User")
    ai_specialist_message2 = TextMessage(content="Your response must be an enhanced version for stable diffusion of the given prompt and must not be longer than 65 token", source="User")
    ai_specialist_message3 = TextMessage(content="the prompt is intended for a comic image", source="User")
    ai_specialist_message4 = TextMessage(content="you have to surround with round brackets the tokens you consider more important", source="User")
    ai_specialist_message5 = TextMessage(content="your reply must be a json with a field named prompt and nothing else. no personal comments or ratings only the json", source="User")
    
    revisor_message1 = TextMessage(content="you must reply only with one word: APPROVE or DECLINE", source="User")
    
    await team.reset()  # Reset the team for a new task.
    response1 = await primary_agent.on_messages(
        [primary_agent_message1,primary_agent_message2],
        cancellation_token=CancellationToken(),
    )
    response2 = await critic_agent.on_messages(
        [critic_agent_message1],
        cancellation_token=CancellationToken(),
    )
    response3 = await ai_specialist.on_messages(
        [ai_specialist_message1,ai_specialist_message2,ai_specialist_message3,ai_specialist_message4,ai_specialist_message5],
        cancellation_token=CancellationToken(),
    )
    response4 = await revisor_agent.on_messages(
        [revisor_message1],
        cancellation_token=CancellationToken(),
    )
    # print(response.inner_messages)
    # print(response.chat_message)
    # await Console(team.run_stream(task="discuss if the image seen by Bob suits on the following prompt, providing a rate from 1 to 10: Professor Thompson is sitting at his desk, wearing his glasses and red shirt, with a stack of comic books behind him"))  # Stream the messages to the console.
    revisor_decision = "APPROVE"
    new_prompt = image_prompt
    result = await team.run(task="discuss if the image seen by Bob suits the following prompt: "+character_definition+" "+image_prompt)
    for message in result.messages:
        # print(message)
        print("("+message.source + ") --> "+ message.content)
        logger.error("("+message.source + ") --> "+ message.content)
        if message.source == "specialist":
            print("------------------------------")
            logger.error("------------------------------")
            new_prompt = json.loads(message.content.replace("```json","").replace("```",""))['prompt']
            print(json.loads(message.content.replace("```json","").replace("```",""))['prompt'])
            logger.error(json.loads(message.content.replace("```json","").replace("```",""))['prompt'])
            print("------------------------------")
            logger.error("------------------------------")
        if message.source == "revisor":
            print("------------------------------")
            logger.error("------------------------------")
            print(message.content)
            logger.error(message.content)
            revisor_decision = message.content
            print("------------------------------")
            logger.error("------------------------------")
    return (new_prompt if "DECLINE" in revisor_decision else image_prompt) , revisor_decision

team2 = RoundRobinGroupChat([primary_agent, critic_agent,revisor_agent], termination_condition=text_termination)

async def image_comparison(ori_img_url,new_img_url,character_definition,image_prompt) -> str:
    pil_image_ori = Image.open(ori_img_url)
    pil_image_new = Image.open(new_img_url)
    img_ori = AGImage(pil_image_ori)
    img_new = AGImage(pil_image_new)

    primary_agent_message1 = MultiModalMessage(content=["This is the original image, keep in mind what it represents?", img_ori], source="User")
    primary_agent_message2 = MultiModalMessage(content=["This is the new image, keep in mind what it represents?", img_new], source="User")
    primary_agent_message3 = TextMessage(content="This is the character definition you must see in the picture: "+character_definition, source="User")

    critic_agent_message1 = MultiModalMessage(content=["This is the original image object of the discussion.", img_ori], source="User")
    critic_agent_message2 = MultiModalMessage(content=["This is the new image object of the discussion.", img_new], source="User")
    
    revisor_message1 = TextMessage(content="you must reply only with APPROVE if the new image is better or DECLINE if the original image is better", source="User")
    
    await team2.reset()  # Reset the team for a new task.

    response1 = await primary_agent.on_messages(
        [primary_agent_message1,primary_agent_message2,primary_agent_message3],
        cancellation_token=CancellationToken(),
    )

    response2 = await critic_agent.on_messages(
        [critic_agent_message1,critic_agent_message2],
        cancellation_token=CancellationToken(),
    )
    
    response3 = await revisor_agent.on_messages(
        [revisor_message1],
        cancellation_token=CancellationToken(),
    )
    # print(response.inner_messages)
    # print(response.chat_message)
    # await Console(team.run_stream(task="discuss if the image seen by Bob suits on the following prompt, providing a rate from 1 to 10: Professor Thompson is sitting at his desk, wearing his glasses and red shirt, with a stack of comic books behind him"))  # Stream the messages to the console.
    revisor_decision = "APPROVE"
    result = await team2.run(task="discuss which of the two images seen by Bob represents better the following prompt: "+image_prompt)
    for message in result.messages:
        # print(message)
        print("("+message.source + ") --> "+ message.content)
        logger.error("("+message.source + ") --> "+ message.content)
        if message.source == "revisor":
            print("------------------------------")
            logger.error("------------------------------")
            print(message.content)
            logger.error(message.content)
            revisor_decision = message.content
            print("------------------------------")
            logger.error("------------------------------")
    return revisor_decision

team3 = RoundRobinGroupChat([primary_agent, critic_agent,ai_specialist,revisor_agent], termination_condition=text_termination)

async def dress_comparison(ori_img_url,new_img_url,character_definition,image_prompt) -> str:
    pil_image_ori = Image.open(ori_img_url)
    pil_image_new = Image.open(new_img_url)
    img_ori = AGImage(pil_image_ori)
    img_new = AGImage(pil_image_new)

    primary_agent_message1 = MultiModalMessage(content=["This is the original image, keep in mind what it represents?", img_ori], source="User")
    primary_agent_message2 = MultiModalMessage(content=["This is the new image, keep in mind what it represents?", img_new], source="User")
    primary_agent_message3 = TextMessage(content="This is the character definition you must see in the picture: "+character_definition, source="User")

    critic_agent_message1 = MultiModalMessage(content=["This is the original image object of the discussion.", img_ori], source="User")
    critic_agent_message2 = MultiModalMessage(content=["This is the new image object of the discussion.", img_new], source="User")

    ai_specialist_message1 = TextMessage(content="The original prompt is: "+image_prompt, source="User")
    ai_specialist_message2 = TextMessage(content="Your response must be an enhanced version for stable diffusion of the given prompt and must not be longer than 65 token", source="User")
    ai_specialist_message3 = TextMessage(content="the prompt is intended for a comic image", source="User")
    ai_specialist_message4 = TextMessage(content="you have to surround with round brackets the tokens you consider more important", source="User")
    ai_specialist_message5 = TextMessage(content="your reply must be a json with a field named prompt and nothing else. no personal comments or ratings only the json", source="User")
    
    revisor_message1 = TextMessage(content="you must reply only with APPROVE", source="User")
    
    await team3.reset()  # Reset the team for a new task.

    response1 = await primary_agent.on_messages(
        [primary_agent_message1,primary_agent_message2,primary_agent_message3],
        cancellation_token=CancellationToken(),
    )

    response2 = await critic_agent.on_messages(
        [critic_agent_message1,critic_agent_message2],
        cancellation_token=CancellationToken(),
    )
    response3 = await ai_specialist.on_messages(
        [ai_specialist_message1,ai_specialist_message2,ai_specialist_message3,ai_specialist_message4,ai_specialist_message5],
        cancellation_token=CancellationToken(),
    )
    
    response4 = await revisor_agent.on_messages(
        [revisor_message1],
        cancellation_token=CancellationToken(),
    )
    # print(response.inner_messages)
    # print(response.chat_message)
    # await Console(team.run_stream(task="discuss if the image seen by Bob suits on the following prompt, providing a rate from 1 to 10: Professor Thompson is sitting at his desk, wearing his glasses and red shirt, with a stack of comic books behind him"))  # Stream the messages to the console.
    revisor_decision = "APPROVE"
    result = await team3.run(task="discuss how to change the dresses details of the character in the new image seen by Bob to be more similar to the original one. ")
    for message in result.messages:
        # print(message)
        print("("+message.source + ") --> "+ message.content)
        logger.error("("+message.source + ") --> "+ message.content)
        if message.source == "specialist":
            print("------------------------------")
            logger.error("------------------------------")
            new_prompt = json.loads(message.content.replace("```json","").replace("```",""))['prompt']
            print(json.loads(message.content.replace("```json","").replace("```",""))['prompt'])
            logger.error(json.loads(message.content.replace("```json","").replace("```",""))['prompt'])
            print("------------------------------")
            logger.error("------------------------------")
        if message.source == "revisor":
            print("------------------------------")
            logger.error("------------------------------")
            print(message.content)
            logger.error(message.content)
            revisor_decision = message.content
            print("------------------------------")
            logger.error("------------------------------")
    return revisor_decision


### batch test ####
# in order to use load plot or load panel import them from utils
#
# asyncio.run(image_validation(img_url="panels-img/panel8.png",character_definition="Professor Thompson is a man and A passionate and experienced writer, wearing glasses and a red shirt",image_prompt="Professor Thompson is sitting at his desk, wearing his glasses and red shirt, with a stack of comic books behind him"))
# asyncio.run(image_validation(img_url="/home/luca/Documenti/Tesi/comic1111generator/test/panel1.png",character_definition="Professor Thompson is a man and A passionate and experienced writer, wearing glasses and a red shirt",image_prompt="Professor Thompson is sitting at his desk, wearing his glasses and red shirt, with a stack of comic books behind him"))
# async def batch_test():
#     plot = loadPlot()
#     # print(plot)
#     panels = loadPanels()
#     # print(panels)
#     plot['seed'] = panels['seed']
#     if plot:
#         i=0
#         for panel in plot['panels']:
#             print("Analyzing image --> ",panels['panels'][i]['img'])
#             plot['panels'][i]['description'] = await image_validation(img_url=panels['panels'][i]['img'],character_definition=panel['characters'][0],image_prompt=panel['description'].rstrip(".").replace(panel['characters'][0], ""))
#             i=i+1
#         with open("plot2.json", "w", encoding="utf-8") as outfile:
#             outfile.write(json.dumps(plot, separators=(",", ":")))
#             outfile.close()

# asyncio.run(batch_test())

##### IMAGE COMPARISON #####
# ori_img_url,new_img_url,character_definition,image_prompt
# asyncio.run(image_comparison(ori_img_url="panels-img/panel72.png",new_img_url="panels-img/panel7.png",character_definition="Professor Thompson is a man and A passionate and experienced writer, wearing glasses and a red shirt",image_prompt="Professor Thompson is sitting at his desk, wearing his glasses and red shirt, with a stack of comic books behind him"))
# asyncio.run(image_comparison(ori_img_url="nospeach-img/panel1_ori.png",new_img_url="nospeach-img/panel1.png",character_definition="Professor Thompson is a man and A passionate and experienced writer, wearing glasses and a red shirt",image_prompt="Professor Thompson shows a character design sheet."))

##### DRES COMPARISON #####
# ori_img_url,new_img_url,character_definition,image_prompt
#asyncio.run(dress_comparison(ori_img_url="panels-img/panel7.png",new_img_url="panels-img/panel9.png",character_definition="Professor Thompson is a man and A passionate and experienced writer, wearing glasses and a red shirt",image_prompt="Professor Thompson is sitting at his desk, wearing his glasses and red shirt, with a stack of comic books behind him"))
# asyncio.run(image_comparison(ori_img_url="nospeach-img/panel1_ori.png",new_img_url="nospeach-img/panel1.png",character_definition="Professor Thompson is a man and A passionate and experienced writer, wearing glasses and a red shirt",image_prompt="Professor Thompson shows a character design sheet."))


#export GGML_CUDA_ENABLE_UNIFIED_MEMORY=1