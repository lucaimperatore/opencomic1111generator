# comic1111generator

An Automatic1111 comic panel images generator with multiagent chat image validation system

![panel1](examples/panel1.png)
![panel2](examples/panel2.png)

you can find a complete comic generation example in [comic sample](examples/fumetto_answer_agent_rag_1749715128.247098.pdf)

## Setup

developed and tested with python 3.10.9 on Kubuntu 24.10 use of Python virtualenv is encouraged. 

### Pre req

In order to use comic1111generator you need:

* **automatic1111** (tested on v 1.10.1 installation) https://github.com/AUTOMATIC1111/stable-diffusion-webui . In order to get the things running you have to run it with --api option
* **gemma3** a simple way to obtain it is with **ollama**

### Activate virtual env and install requirements

Create a virtual environment named .venv

```python -m venv .venv```

Activate the environment

```source .venv/bin/activate```

Install a package

```pip install -r requirements.txt```

Deactivate the environment

```deactivate```

## Run

### run for help

    .venv/bin/python main.py --help

### basic usage

    .venv/bin/python main.py -in plot.json

### comic to pdf mode

    .venv/bin/python main.py -in plot.json --pdf

### debug mode

    .venv/bin/python main.py -in plot.json --debug

### multiagent chat validation

    .venv/bin/python main.py -in plot.json --online

## Stable diffusion models

The program was tested with either stable diffusion 1.5 and XL models:

* juggernautXL_juggXIByRundiffusion.safetensors (with LoRA ComicStyleXL)
* mistoonAnime_v30.safetensors
* dreamshaper_8.safetensors
* anythingV3_fp16
* arthemyComics_v70
* flat2DAnimerge_v45Sharp
* toonyou_beta6

you can find usage examples in [config.yaml](config.yaml) file

### Character stabilization

Character stabilization and customization was reached with LoRA made with Kohya ss https://github.com/bmaltais/kohya_ss