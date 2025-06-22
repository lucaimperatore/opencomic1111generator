"""
Reapply speaches to images
"""

import utils
from speech_baloon import add_comic_rectangle

# input_path = "/home/luca/Scaricati/stories_2/gpt-4o/llama_index_hierarchical_multi_agent_rag.json"
input_path = "plot.json"
# loads the plot json with the story
plot = utils.loadPlot(input_path)

## here we add speech baloons
j=0
for panel in plot['panels']:
    j=j+1
    if panel['dialogues'][0]['text'] != "":
        # this version accepts ony one character per time
        nospeach_img_path = "nospeach-img/panel"+str(j)+".png"
        target_img_path = "panels-img/panel"+str(j)+".png"
        add_comic_rectangle(nospeach_img_path,target_img_path,panel['dialogues'][0]['text'],False)
        