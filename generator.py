import requests
import base64
import utils
import logging
logger = logging.getLogger(__name__)

def comic_generator(index,prompt,characters,seed):
    """
    Interacts with stable diffusion in order to generate images
    """

    # load the configuration
    config = utils.load_configuration()

    # Define the URL and the payload to send.
    url = config['sd_url']

    # lora that gives comic style to images
    base_prompt = config['base_prompt']

    characters_models = config['characters_models']
    # characters_models = {"Professor Thompson":"<lora:lucaia_v1-5:1.3> (lucaia, man, black hair, beard)","Elisa":"<lora:elisaia_v1-5:1.3> (elisaia, girl, little)"}

    characters_dict = {}
    for character in characters:
        characters_dict[character['name']] = character['description'].rstrip(".")

    # uso solo il primo personaggio
    
    final_prompt = base_prompt +", "+ characters_models[prompt['characters'][0]].rstrip(".") +", "+ characters_dict[prompt['characters'][0]] + ", " + prompt['description'].rstrip(".").replace(prompt['characters'][0], "")
    # final_prompt = characters_models[prompt['characters'][0]].rstrip(".") +", "+ characters_dict[prompt['characters'][0]] + ", " + prompt['description'].rstrip(".").replace(prompt['characters'][0], "")

    print("prompt: ",final_prompt)
    logger.error("prompt: "+final_prompt)

    sd_payload = config['sd_payload']

    sd_payload['prompt'] = final_prompt
    sd_payload['seed'] = seed

    # Send payload to URL through the API.
    response = requests.post(url=f'{url}/sdapi/v1/txt2img', json=sd_payload)
    r = response.json()

    # print("Response parameters: ",r['parameters'])
    # print("Response info: ",r['info'])

    print("Generated: panel"+str(index)+".png")
    logger.error("Generated: panel"+str(index)+".png")

    current_img_path = "panels-img/panel"+str(index)+".png"
    nospeach_img_path = "nospeach-img/panel"+str(index)+".png"

    # Decode and save the image.
    with open(current_img_path, 'wb') as f:
        f.write(base64.b64decode(r['images'][0]))
    # We laso want to to save the original image widthout speach
    with open(nospeach_img_path, 'wb') as f:
        f.write(base64.b64decode(r['images'][0]))

    return current_img_path,sd_payload,nospeach_img_path
