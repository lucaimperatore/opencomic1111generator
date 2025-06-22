import json
from pylatex import (
    Document,
    NoEscape,
    Package,
    Command,
    LongTable,
    Section
)
import os

import subprocess
import time
import yaml

def loadPlot(plotFileName = "plot.json"):
    """
    Loads plot data from a JSON file.

    Args:
        plotFileName (str, optional): The name of the JSON file to load. Defaults to "plot.json".

    Returns:
        dict: A dictionary containing the loaded JSON data, or None if an error occurred.
    """
    try:
        # Opening JSON file
        f = open(plotFileName)

        # returns JSON object as a dictionary
        data = json.load(f)
        print('Loaded plot file: '+plotFileName)

        # Closing file
        f.close()

    except FileNotFoundError:
        print(f"Error: File 'plotFileName' not found.")
    except PermissionError:
        print(f"Error: Permission denied to open 'plotFileName'.")
    except Exception as e: #Catch any other exception
        print(f"An unexpected error occurred: {e}")

    return data

def json_to_latex(json_data, doc):
    """
    Recursively converts JSON data to LaTeX format and adds it to the document.
    Args:
        json_data (dict, required): the dict to convert 
        doc (Document, required): the latex document
    
    """
    if isinstance(json_data, dict):
        for key, value in json_data.items():
            with doc.create(Section(str(key))):
                json_to_latex(value, doc)
    elif isinstance(json_data, list):
        doc.append(NoEscape(r'\begin{itemize}'))
        for item in json_data:
            doc.append(NoEscape(r'\item '))
            json_to_latex(item, doc)
        doc.append(NoEscape(r'\end{itemize}'))
    else:
        doc.append(str(json_data))


def get_directory_from_path(file_path):
  """
  Return the directory name from a given path
  Args:
    file_path (string,requred): file path
  """
  if not isinstance(file_path, str):
    return None 

  return os.path.dirname(file_path)

def get_file_name_from_path(file_path):
  """
  Return the file name name from a given path removing .json extension
  Args:
    file_path (string,requred): file path
  """
  if not isinstance(file_path, str):
    return None
  return os.path.basename(file_path).replace(".json","")

def generate_latex_file(out,isDebug):
    """
    Return the file name name from a given path removing .json extension
    Args:
        out (dict,requred): dict with the generated image reference and panels details
        isDebug (boolean,requred): influience the visitbility of som kind of data in the pdf for debug purpose
    """
    geometry_options = {"a4paper": True,"margin": "1in"}
    doc = Document(geometry_options=geometry_options)
    
    doc.preamble.append(Command('title', out["title"]))

    doc.packages.append(Package('graphicx'))
    doc.packages.append(Package('indentfirst'))

    doc.append(Command('maketitle'))

    doc.append(NoEscape('\\noindent'))
    doc.append(NoEscape('\\textbf{Abstract:} '))
    doc.append(str(out["abstract"]))
    doc.append(NoEscape('\\newline')) 
    doc.append(NoEscape('\\textbf{Plot:} '))
    doc.append(str(out["plot"]))
    doc.append(NoEscape('\\newline')) 
    doc.append(NoEscape('\\textbf{Seed:} '))
    doc.append(str(out["seed"]))
    doc.append(NoEscape('\\newline')) 
    doc.append(NoEscape('\\textbf{Model:} '))
    doc.append(str(out['sd_payload']['override_settings']['sd_model_checkpoint']))
    doc.append(NoEscape('\\newline')) 
    doc.append(NoEscape('\\textbf{Steps:} '))
    doc.append(str(out['sd_payload']['steps']))
    doc.append(NoEscape('\\newline')) 
    doc.append(NoEscape('\\textbf{HrFix:} '))
    enable_hr = 'True' if 'enable_hr' in out['sd_payload'].keys() else 'False'
    doc.append(enable_hr)
    doc.append(NoEscape('\\newline')) 
    doc.append(NoEscape('\\textbf{Refiner:} '))
    refiner_checkpoint = out['sd_payload']['refiner_checkpoint'] if 'refiner_checkpoint' in out['sd_payload'].keys() else 'False'
    doc.append(refiner_checkpoint)
    doc.append(NoEscape('\\newline')) 
     
    with doc.create(LongTable("|c|c|")) as data_table:
        data_table.add_hline()
        if len(out['panels']) > 0:
            i=0
            isEven = True if len(out['panels']) % 2 == 0 else False 
            temp_img =["",""]
            for panel in out['panels']:
                i = i + 1
                if len(out['panels']) == 1:
                    data_table.add_row([NoEscape('\\includegraphics[width=0.45\\textwidth]{'+panel["img"]+'}'),""])
                    break
                # se è l'ultima pagina e le pagine sono diapari rimane un soilo pannello a sx
                if not isEven and i == len(out['panels']):
                    data_table.add_row([NoEscape('\\includegraphics[width=0.45\\textwidth]{'+panel["img"]+'}'),""])
                
                # se non siamo in fondo e i è dispari mi salvo la foto per dopo
                if i < len(out['panels']) and i % 2 != 0:
                    temp_img[0] = NoEscape('\\includegraphics[width=0.45\\textwidth]{'+panel["img"]+'}')
                # se non siamo in fondo e i è pari aggiungo la riga
                if i <= len(out['panels']) and i % 2 == 0:
                    temp_img[1] = NoEscape('\\includegraphics[width=0.45\\textwidth]{'+panel["img"]+'}')
                    data_table.add_row(temp_img)
        data_table.add_hline()

    if isDebug:
        with doc.create(Section("JSON Data")):
            json_to_latex(json.dumps(out), doc)

        with doc.create(Section("Prompts")):
            doc.append(NoEscape(r'\begin{enumerate}'))
            for panel in out['panels']:
                doc.append(NoEscape(r'\item '))
                doc.append(str(panel))
            doc.append(NoEscape(r'\end{enumerate}'))

    doc.generate_pdf("fumetto", clean_tex=False)

    if get_directory_from_path(str(out["plot"])):
        subprocess.run(["pdflatex","-f","-jobname=fumetto_"+get_file_name_from_path(str(out["plot"]))+"_"+str(time.time()),"-output-directory="+get_directory_from_path(str(out["plot"])), "fumetto.tex"]) 
    else:
        print("CARTELLA LOCALE")
        subprocess.run(["pdflatex","-f","-jobname=fumetto_"+get_file_name_from_path(str(out["plot"]))+"_"+str(time.time()), "fumetto.tex"])


def load_configuration():
   with open("config.yaml", "r") as yamlfile:
    data = yaml.load(yamlfile, Loader=yaml.FullLoader)
    print("Config read successful")
    return data