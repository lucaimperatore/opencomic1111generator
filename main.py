import asyncio
import os
import json
import webbrowser
from random import randrange
import argparse
from group_chat import image_validation,image_comparison
import utils
import generator
from speech_baloon import add_comic_rectangle
import shutil
import logging
logger = logging.getLogger(__name__)
import time

async def main():
    """
    Main function
    """

    # parsing command line arguments
    parser = argparse.ArgumentParser(
                    prog='Comic1111 Generator',
                    description='It generates comic images with stable diffusion applying comic speeches according face detection',
                    epilog='Choose an opiton and run again')
    
    parser.add_argument('-in', '--input', type=str, default="plot.json") 
    parser.add_argument('--speach', action=argparse.BooleanOptionalAction,default=True)
    parser.add_argument('--web', action=argparse.BooleanOptionalAction,default=True)
    parser.add_argument('--single', action=argparse.BooleanOptionalAction)
    parser.add_argument('--online', action=argparse.BooleanOptionalAction,default=False)
    parser.add_argument('--debug', action=argparse.BooleanOptionalAction,default=False)
    parser.add_argument('--pdf', action=argparse.BooleanOptionalAction,default=False)
    args = parser.parse_args()

    if utils.get_directory_from_path(str(args.input)):
        
        log_filename=utils.get_directory_from_path(str(args.input))+'/comic1111_'+utils.get_file_name_from_path(str(args.input))+str(time.time())+'.log'
        
    else:
        print("LOCAL FOLDER ...")
        log_filename='comic1111_'+utils.get_file_name_from_path(str(args.input))+str(time.time())+'.log'

    print('log_filename',log_filename)

    logging.basicConfig(
    filename=log_filename,
    format='%(asctime)-8s %(message)s',
    level=logging.ERROR,
    datefmt='%Y-%m-%d %H:%M:%S')

    logger.error(" ---------------------------  Comic1111 Generator ------------------------- ")

    print(args.input)
    logger.error("args.input: "+args.input)
    
    # loads the plot json with the story
    plot = utils.loadPlot(args.input)

    if plot['seed'] != "":
        seed = plot['seed']
    else:
        seed = randrange(4294967294)
    
    logger.error("seed: "+str(seed))
    
    # output dictionary to create panels.json file that will be use by index.html file
    # to show the comic strip
    out = {}
    # array to store images paths
    out_panels = []

    out['seed'] = str(seed)
    out['title'] = plot['title']
    out['abstract'] = plot['abstract']
    out['plot'] = args.input

    # print("characters",plot['characters'])
    logger.error("characters: "+str(plot['characters']))

    if plot:
        i=0
        for panel in plot['panels']:
            i=i+1

            generated_img_path, sd_payload,nospeach_img_path = generator.comic_generator(i,panel,plot['characters'],seed)

            if i == 1:
                out['sd_payload'] = sd_payload

            out_panels.append({'img':generated_img_path,'prompt':sd_payload['prompt']})

            # we save the original prompt in case we had to rollback
            sd_prompt_ori = sd_payload['prompt']

            # print("out_panels",out_panels)

            if args.online:
                print("ONLINE image check.....")
                logger.error("ONLINE image check.....")

                new_prompt, revisor_decision = await image_validation(img_url=nospeach_img_path,character_definition=panel['characters'][0],image_prompt=panel['description'].rstrip(".").replace(panel['characters'][0], ""))
                
                print("ONLINE revisor_decision: ",revisor_decision)
                logger.error("ONLINE revisor_decision: "+revisor_decision)
                
                print("new prompt: ",new_prompt)
                logger.error("new prompt: " +new_prompt)

                if 'DECLINE' in revisor_decision:
                    print('Recived a DECLINE review, starting new image generation...')

                    removed_extension = nospeach_img_path.replace(".png","")

                    original_image = removed_extension+"_ori.png"

                    shutil.move(nospeach_img_path, original_image)

                    # we save the original description in case we had to rollback
                    original_description = panel['description']

                    panel['description'] = new_prompt

                    logger.error("Generate new image...")
                    # we generate image with a new prompt
                    generated_img_path, sd_payload,nospeach_img_path = generator.comic_generator(i,panel,plot['characters'],seed)

                    logger.error("Start to compare images...")
                    # we compare the old and the new image to choose wich better fits the prompt
                    comparison_result = await image_comparison(ori_img_url=original_image,new_img_url=nospeach_img_path,character_definition=panel['characters'][0],image_prompt=original_description.rstrip(".").replace(panel['characters'][0], ""))

                    if 'DECLINE' in comparison_result:
                        logger.error("New image DECLINED!")
                        # rollback to the first image
                        panel['description'] = original_description

                        removed_extension = nospeach_img_path.replace(".png","")

                        new_image = removed_extension+"_new.png"

                        shutil.move(nospeach_img_path, new_image)
                        shutil.move(original_image, nospeach_img_path)
                        shutil.copy(nospeach_img_path,generated_img_path)                    

                    else:
                        logger.error("New image ACCEPTED!")
                        # accept the new one
                        out_panels[i-1] = {'img':generated_img_path,'prompt':sd_payload['prompt']}


                if 'APPROVE' in revisor_decision:
                    print('Recived an APPROVE from reviewer')
                    logger.error("Recived an APPROVE from reviewer")
            
            if args.single:
                # generates only the first image
                break

        out['panels'] = out_panels

        ## here we add speech baloons
        j=0
        for panel in plot['panels']:
            j=j+1
            if args.speach and panel['dialogues'][0]['text'] != "":
                # this version accepts ony one character per time
                nospeach_img_path = "nospeach-img/panel"+str(j)+".png"
                target_img_path = "panels-img/panel"+str(j)+".png"
                add_comic_rectangle(nospeach_img_path,target_img_path,panel['dialogues'][0]['text'],args.debug)
                if args.single:
                    # generates only the first image
                    break

        if args.pdf:
            utils.generate_latex_file(out,args.debug)

        with open("panels.json", "w", encoding="utf-8") as outfile:
            outfile.write('data=`'+json.dumps(out, sort_keys=False, indent=None, separators=(",", ":"))+'`')
            outfile.close()

    print("Opening comic on default web browser.")
    if args.debug and args.web:
        webbrowser.open('file://' + os.path.realpath("debug.html"))
    elif args.web:
        webbrowser.open('file://' + os.path.realpath("index.html"))

if __name__ == "__main__":
    asyncio.run(main())