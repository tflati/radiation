from django.shortcuts import render
from django.http import HttpResponse
import json
import os
import sys
import glob

import rpy2
import rpy2.robjects as robjects
import rpy2.robjects.packages as rpackages
import datetime
from django.core.cache import cache
from django.conf.locale import bg

def create_new_image(url, width="100px"):
    return {
            "type": "image",
            "data": {
                "url": url,
                "width": width
            }
        }
def create_new_paragraph(text, inline=False):
    return {
        "type": "paragraph",
        "data": {
            "value": text
        },
        "inline": inline
    }
    
def create_new_text(text, inline=False):
    return {
        "type": "text",
        "label": text
    }
    
def create_new_link(url, text, tooltip="", target="_blank"):
    return {
        "type": "link",
        "title": tooltip,
        "target": target,
        "url": url,
        "label": text
    }

def create_linkable_image(img_url, target_url, tooltip="", width="100px"):
    return {
        "type": "linkable_image",
        "data": {
            "title": tooltip,
            "width": width,
            "url": img_url,
            "link": target_url
        }
    }
    
def create_new_button(text, url, tooltip=None, img=None, img_height=None, icon=None, icon_color=None, icon_modifiers=None, color=None):
    button =  {
        "type": "button",
        "action": "link",
        "label": text,
        "data": {
            "url": url,
        }
    }
    
    if color is not None:
        button["color"] = color
    
    if tooltip is not None:
        button["title"] = tooltip
    
    if img is not None:
        button["data"]["image"] = img
        if img_height is not None: button["data"]["height"] = img_height
        
    if icon is not None:
        button["data"]["icon"] = icon
        if icon_color is not None: button["data"]["color"] = icon_color
        if icon_modifiers is not None: button["data"]["modifiers"] = icon_modifiers
        
    
    return button
    
def create_new_multi_element(layout=None, alignment=None):
    multi = {
        "type": "multi",
        "elements": []
    }
    
    if layout is not None: multi["layout"] = layout
    if alignment is not None: multi["layout_align"] = alignment
    
    return multi
    
def add_element_to_multi_element(multielement, element):
    multielement["elements"].append(element)
    
def convert_bytes(number):
    if number is None: return "Unknown size"
        
    sizes = ["B", "KB", "MB", "GB", "TB"]
    s = float(number)
    i = 0;
    while s >= 1024 and i < len(sizes):
        s = s / 1024
        i += 1

    #return "{0:.2f} {}".format(s, sizes[i])
    return "{0:.2f}".format(s) + " " + sizes[i]

BASE_BGE_DIR = os.path.dirname(__file__) + "/Ballgown_Extractor/"
BASE_DATA_DIR = os.path.dirname(__file__) + "/data/"

# Create your views here.
def dataset_overview(request):
    
    filename = BASE_DATA_DIR + "project.json"
    dataset = json.loads(open(filename, "r").read())
    
    map = {}
    for experiment in dataset["projects"]:
        bioproject_id = experiment["dataset"]["bioproject_id"]
        if bioproject_id not in map:
            map[bioproject_id] = {
                    "size": 0,
                    "genome": None,
                    "experiments": 0,
                    "paper_id": set(),
                    "platform": set(),
                    "samples": 0,
                }

        data = map[bioproject_id]
        
        data["experiments"] += 1
        dataset = experiment["dataset"]
        size = dataset["size"]
        organism = dataset["genome"]
        paper_id = dataset["paper_id"] if "paper_id" in dataset else None
        platform = dataset["platform"]
        samples = len(dataset["sample_ids"].split("\n"))
        
        data["size"] += size
        if paper_id is not None:
            data["paper_id"].add(paper_id)
        data["platform"].add(platform)
        data["samples"] += samples
        data["organism"] = organism
    
    rows = []
    for bioproject_id in map:
        data = map[bioproject_id]
        print("DATA", data)
        row = []
        
        row.append(create_new_link("https://www.ncbi.nlm.nih.gov/bioproject/" + bioproject_id, bioproject_id, tooltip="See this BioProject within NCBI ("+bioproject_id+")"))
        row.append(create_new_text(data["samples"]))
        
        sample_cell = create_new_multi_element(alignment="center center")
        add_element_to_multi_element(sample_cell, create_new_text(data["experiments"]))
        add_element_to_multi_element(sample_cell, create_new_button("See detail", url="bioproject/"+ bioproject_id))
        row.append(sample_cell)
        row.append(create_new_text(convert_bytes(data["size"])))
        row.append(create_new_text(data["organism"]))
        
        if data["paper_id"]:
            paper_links = []
            for paper_id in data["paper_id"]:
                paper_links.append(create_linkable_image("imgs/paper.png", "https://www.ncbi.nlm.nih.gov/pubmed/" + paper_id, width="50px", tooltip="See this paper within Pubmed ("+paper_id+")"))
            row.append(paper_links[0])
        else:
            row.append(create_new_text("No paper available"))
                
        platforms = []
        for platform in data["platform"]:
            platforms.append(create_new_text(platform))
        row.append(platforms[0])

        rows.append(row)
    
    header = ["BioProject ID", "Number of samples", "Experiments", "Size", "Organism", "Paper ID", "Platform"]
    response = {"total": len(rows), "header": header, "items": rows}
    
    return HttpResponse(json.dumps(response))

def clear_cache(request):
    cache.clear()
    return HttpResponse("OK")

import threading
lock = threading.Lock()

def init():
    
    base = rpackages.importr("base")
    base.source(BASE_BGE_DIR + "definitions.R")
    
    return base

def get_header():
    return [
        {
            "label": "result_id",
            "title": "Result ID",
            "tooltip": "Result ID",
            "filters": {
                "title": "Result ID filters:",
                "list": [
                    {
                        "type": "select",
                        "key": "result_id",
                        "title": "Select a result ID:",
                        "placeholder": "",
                        "operators": "LIKE",
                        "chosen_value": ""
                    }
                ]
            }
        },
        {
            "label": "gene",
            "title": "Coverage",
            "tooltip": "Gene symbol",
            "filters": {
                "title": "gene symbol filters:",
                "list": [
                    {
                        "type": "select",
                        "key": "gene_symbol",
                        "title": "Select a gene symbol:",
                        "placeholder": "",
                        "operators": "LIKE",
                        "chosen_value": ""
                    }
                ]
            }
        },
        {
            "label": "geneID",
            "title": "FPKM",
            "tooltip": "gene ID",
            "filters": {
                "title": "Gene ID filters:",
                "list": [
                    {
                        "type": "select",
                        "key": "geneID",
                        "title": "Select a gene ID:",
                        "placeholder": "",
                        "operators": "LIKE",
                        "chosen_value": ""
                    }
                ]
            }
        }
    ]
    
def search_by_gene_symbol(request):
    print(str(datetime.datetime.now()))

    data = json.loads(request.body.decode('utf-8'))
#     data = {}
    print(data)
    
    bioproject = data["bioproject"]
    gene_symbol = data["gene_name_sy"]
#     gene_symbol = "DUSP6"
    
    offset = 0
    limit = 10
    
    if "offset" in data: offset = data["offset"]
    if "limit" in data: limit = data["limit"]
    
    rows = []

    with lock:
        basedir = BASE_DATA_DIR + bioproject + "/"
        bg = get_ballgown_object(basedir + "bg.RData")
        SearchByGene = robjects.r("SearchByGene")
        results = SearchByGene(gene_symbol, bg)
    
    # Make the call
    print(results, len(results), results.names, results[0])
    
    total = len(results)
    
    header = []
    for colname in ["Sample ID", "FPKM value"]:
        header.append({
            "label": colname,
            "title": colname,
            "tooltip": colname,
            "filters": {
                "title": colname + " filters:",
                "list": [
                    {
                        "type": "select",
                        "key": colname,
                        "title": "Select a "+colname+":",
                        "placeholder": "",
                        "operators": "LIKE",
                        "chosen_value": ""
                    }
                ]
            }
        })
    
    for i in range(total):
        row_dict = {}
        
        sample_id = results.names[i].replace("FPKM.", "")
        sample_id = results.names[i].replace("trimmed_", "")
        value = results[i]
        
        row_dict["Sample ID"] = [{
            "type": "text",
            "label": str(sample_id),
            "color": "black"
        }]
        
        row_dict["FPKM value"] = [{
            "type": "text",
            "label": str(value),
            "color": "black"
        }]
        
        rows.append(row_dict)
    
    response = {"structure": {"field_list": header}, "total": total, "hits": rows}
    
    return HttpResponse(json.dumps(response))

def see_gene_isoforms(request):
    print(str(datetime.datetime.now()))

    data = json.loads(request.body.decode('utf-8'))
#     data = {}
    print(data)
    
    bioproject = data["bioproject"]
    gene_symbol = data["gene_name_sy"]
#     gene_symbol = "DUSP6"
    
    offset = 0
    limit = 10
    
    if "offset" in data: offset = data["offset"]
    if "limit" in data: limit = data["limit"]
    
    rows = []

    with lock:
        dir = BASE_DATA_DIR + bioproject + "/"
        bg = get_ballgown_object(dir + "bg.RData")
        results = robjects.r("SearchGeneIsoforms")(gene_symbol, bg)
        if results is rpy2.rinterface.NULL: return HttpResponse(json.dumps(empty_table()))
        
    response = to_table(results, offset, limit)

    return HttpResponse(json.dumps(response))

def search_by_transcript_symbol(request):
    print(str(datetime.datetime.now()))

    data = json.loads(request.body.decode('utf-8'))
    print(data)
    
    bioproject = data["bioproject"]
    transcript_symbol = data["transcript_name_sy"]
    
    offset = 0
    limit = 10
    
    if "offset" in data: offset = data["offset"]
    if "limit" in data: limit = data["limit"]
    
    with lock:
        dir = BASE_DATA_DIR + bioproject + "/"
        bg = get_ballgown_object(dir + "bg.RData")
        SearchByTranscript = robjects.r("SearchByTranscript")
        results = SearchByTranscript(transcript_symbol, bg)
    
    response = to_table(results, offset, limit)
    
    return HttpResponse(json.dumps(response))

def search_by_feature(request):
    print(str(datetime.datetime.now()))

    data = json.loads(request.body.decode('utf-8'))
    print(data)
    
    bioproject = data["bioproject"]
    gene_symbol = data["gene_name_sy"]
    feature = data["feature"]
    
    offset = 0
    limit = 10
    
    if "offset" in data: offset = data["offset"]
    if "limit" in data: limit = data["limit"]
    
    with lock:
        dir = BASE_DATA_DIR + bioproject + "/"
        bg = get_ballgown_object(dir + "bg.RData")
        search = robjects.r("SearchByFeature")
        results = search(gene_symbol, feature, bg)
    
    response = to_table(results, offset, limit)
    
    return HttpResponse(json.dumps(response))

def search_by_condition(request):
    
    data = json.loads(request.body.decode('utf-8'))
    print(data)
    
    conditions = []
    for x in range(1, 6):
        conditionId = "condition"+str(x)
        conditionValueId = "condition_value"+str(x)
        
        if conditionId in data:
            condition = data[conditionId]
            if condition == "ALL": continue
            
            condition_value = data[conditionValueId]    
            conditions.append(condition + "=='" + str(condition_value)+ "'")
    final_conditions = " & ".join(conditions)
    
    bioproject = data["bioproject"]
    gene = data["gene_name_sy"]
    
    offset = 0
    limit = 10
    
    if "offset" in data: offset = data["offset"]
    if "limit" in data: limit = data["limit"]
    
    print("QUERY", final_conditions, gene)
    
    with lock:
        dir = BASE_DATA_DIR + bioproject + "/"
        bg = get_ballgown_object(dir + "bg.RData")
        results = robjects.r("SearchByCondition")(final_conditions, gene, bg)
        if results is rpy2.rinterface.NULL: return HttpResponse(json.dumps(empty_table()))
    
    response = to_table(results, offset, limit)
    
#     preferential_order = ["chr", "start", "end", "strand", "gene"]
#     header = response["structure"]["field_list"]
#     rows = response["hits"]
#     header.sort(key=lambda x: preferential_order.index(x["label"]) if x["label"] in preferential_order else sys.maxsize)
    
    return HttpResponse(json.dumps(response))

def search_by_diff_fold_expr(request):

    data = json.loads(request.body.decode('utf-8'))
    print(data)
    
    feature = data["feature"]
    covariate = data["covariate"]
    
    conditions = []
    for x in range(1, 6):
        conditionId = "condition"+str(x)
        conditionValueId = "condition_value"+str(x)
        
        if conditionId in data:
            condition = data[conditionId]
            if condition == "ALL": continue
            
            condition_value = data[conditionValueId]    
            conditions.append(condition + "=='" + str(condition_value)+ "'")
    final_conditions = " & ".join(conditions)
    
    bioproject = data["bioproject"]
    covariance = float(data["covariance"]) if data["covariance"] != "ALL" else 1
    pvalue = float(data["pvalue"]) if data["pvalue"] != "ALL" else 0.05
    qvalue = float(data["qvalue"]) if data["qvalue"] != "ALL" else 0.05
    min_fold_change = float(data["min_fold_change"]) if data["min_fold_change"] != "ALL" else 2
    
    offset = 0
    limit = 10
    
    if "offset" in data: offset = data["offset"]
    if "limit" in data: limit = data["limit"]
    
    print("QUERY", final_conditions, covariate, feature)
    
    with lock:
        dir = BASE_DATA_DIR + bioproject + "/"
        bg = get_ballgown_object(dir + "bg.RData")
        results = robjects.r("SearchByDiffFoldExpr")(final_conditions, covariate, feature, bg)
        if results is rpy2.rinterface.NULL: return HttpResponse(json.dumps(empty_table()))
        
        results = robjects.r("StatsFiltering")(results, qvalue, pvalue, min_fold_change)
        if results is rpy2.rinterface.NULL: return HttpResponse(json.dumps(empty_table()))
    
    response = to_table(results, offset, limit)
    
    preferential_order = ["chr", "start", "end", "strand", "gene_id", "gene_name"]
    header = response["structure"]["field_list"]
    rows = response["hits"]
    header.sort(key=lambda x: preferential_order.index(x["label"]) if x["label"] in preferential_order else sys.maxsize)
#     for row in rows:
#         if "gene_name" in row:
#             cell = row["gene_name"]
#             elem = cell[0]
#             gene = elem["label"]
#             cell[0] = create_new_link("https://www.genecards.org/cgi-bin/carddisp.pl?gene="+gene, gene)
    
    return HttpResponse(json.dumps(response))

def gene_plotter(request):
    print(str(datetime.datetime.now()))

    data = json.loads(request.body.decode('utf-8'))
    print(data)
    
    bioproject = data["bioproject"]
    gene_symbol = data["gene_name_sy"]
    measure = data["measure"]
    covariate = data["covariate"]

#     gene_symbol = "DUSP11"
#     measure = "FPKM"
#     covariate = "time_h"
    
    offset = 0
    limit = 10
    
    if "offset" in data: offset = data["offset"]
    if "limit" in data: limit = data["limit"]

    basedir = os.path.dirname(__file__) + "/../../material/imgs/temp/"
    if not os.path.exists(basedir):
        os.makedirs(basedir)
        
    with lock:
        dir = BASE_DATA_DIR + bioproject + "/"
        bg = get_ballgown_object(dir + "bg.RData")
        results = robjects.r("Gene_Plotter_By_Group")(gene_symbol, measure, covariate, basedir, bg)
        if results is rpy2.rinterface.NULL: return HttpResponse(json.dumps(empty_table()))
    
    print(results)
    print(type(results))
    print(results.names)
#     print(results[results.names[0]])
#     print(results[results.names[1]])
#     print(results[results.names[2]])
#     print(results[results.names[3]])
#     print(type(results[0]))
#     print(results[0])
#     print(results[1])
#     print(results[2])
#     print(results[3])
    
    transcripts = results[0]
    chromosomes = results[1]
    starts = results[2]
    ends = results[3]
    
    print("CHROMOSOMES", chromosomes)
    print("STARTS", starts)
    print("ENDS", ends)
    chromosome = chromosomes[0]
    min_start = min(starts)
    max_end = max(ends)
    print(chromosome, min_start, max_end)
    
    filename = results[4][0]
    if os.path.exists(filename):
        os.rename(filename, basedir + filename)
        
        response = create_new_image("imgs/temp/" + filename, "100%")
        
        return HttpResponse(json.dumps(response))
    else:
        return HttpResponse(json.dumps(create_error_message(filename)))
    
def empty_table():
    return {"structure": {"field_list": []}, "total": 0, "hits": []}

def to_table(results, offset, limit):
    total = results.nrow
    
    rows = []
    header = []
    n = results.ncol
    
    i = -1
    for result in results.iter_row():
        i += 1
        if i < offset: continue
        if len(rows) >= limit: break
        
        row_dict = {}
        
        colnames = result.colnames
        
        for i in range(0, n):
            item = result[i]
            colname = colnames[i]
            colname = simplify_column(colname)
            
            if hasattr(item, 'levels'):
                value = str(item.levels[item[0]-1])
            else:
                value = item[0]
            
            if value is rpy2.rinterface.NA_Character:
                value = "N/A"
            
            row_dict[colname] = [{
                "type": "text",
                "label": value,
                "color": "black"
            }]
        
        rows.append(row_dict)
    
    header = []
    for colname in results.colnames:
        colname = colname
        colname = simplify_column(colname)
        
        header.append({
            "label": colname,
            "title": colname,
            "tooltip": colname,
            "filters": {
                "title": colname + " filters:",
                "list": [
                    {
                        "type": "select",
                        "key": colname,
                        "title": "Select a "+colname+":",
                        "placeholder": "",
                        "operators": "LIKE",
                        "chosen_value": ""
                    }
                ]
            }
        })
        
    response = {"structure": {"field_list": header}, "total": total, "hits": rows}
    
    return response

def simplify_column(column):
    return column.replace("trimmed_", "")

def get_ballgown_object(path):
    
    bg = cache.get(path)
    if bg is None:
        print("OBJECT 'BG' NOT FOUND IN CACHE", path)
        base = init()
        base.load(path)
        bg = robjects.r("bg")
        print("ADDING OBJECT 'BG' INTO CACHE", path)
        cache.set(path, bg, None)
    else:
        print("OBJECT 'BG' FOUND IN CACHE", path)
        
    return bg

def create_entry(id, label, img=None):
    entry = {"id": id, "label": label}
    if img is not None:
        entry["img"] = img
        
    return entry

def get_projects(request):
    results = []
    for dir in glob.glob(os.path.dirname(__file__) + "/data/*"):
        if os.path.isdir(dir):
            name = os.path.basename(dir)
            results.append(create_entry(name, name, "imgs/project.png"))
        
    return HttpResponse(json.dumps(results))

def simple_genes(request):
    print("SIMPLE GENES")
    return HttpResponse(json.dumps("SIMPLE GENES"))

def genes(request, bioproject, prefix = ""):
    print("GENES WITH PREFIX", bioproject, prefix)
    
    with lock:
        basedir = BASE_DATA_DIR + bioproject + "/"
        bg = get_ballgown_object(basedir + "bg.RData")
        getGenes = robjects.r("getGenes")
        all_genes = getGenes(bg)
    
    response = []
    
    genes = set()
    for gene_id in all_genes:
        id = str(gene_id)
        if prefix not in id: continue
        if len(genes) >= 50: break
        
        genes.add(id)
    
    for gene in sorted(genes):
        response.append({"id": gene, "label": gene, "img": "imgs/gene-icon.png"})
        
    if len(response) > 1:
        response.insert(0, {"id": "ALL", "label": "Include any gene", "img": "imgs/gene-icon.png"})
    
    return HttpResponse(json.dumps(response))

def features(request):
    
    response = []
    
    response.insert(0, {"id": "ALL", "label": "Include any feature", "img": "imgs/transcript-icon.png"})
    for feature in ["Exon", "Intron", "Trans"]:
        response.append({"id": feature.lower(), "label": feature, "img": "imgs/transcript-icon.png"})
    
    return HttpResponse(json.dumps(response))

def transcripts(request, bioproject, prefix = ""):
    
    with lock:
        basedir = BASE_DATA_DIR + bioproject + "/"
        bg = get_ballgown_object(basedir + "bg.RData")
        fx = robjects.r("getTranscript")
        all_transcripts = fx(bg)
    
    response = []
    
    response.insert(0, {"id": "ALL", "label": "Include any transcript", "img": "imgs/gene-icon.png"})
    transcripts = set()
    for transcript_id in all_transcripts:
        id = str(transcript_id)
        if prefix not in id: continue
        if len(transcripts) >= 50: break
        
        transcripts.add(id)
    
    for transcript in sorted(transcripts):
        response.append({"id": transcript, "label": transcript, "img": "imgs/gene-icon.png"})
    
    return HttpResponse(json.dumps(response))

def covariates(request, bioproject):
    
    with lock:
        basedir = BASE_DATA_DIR + bioproject + "/"
        bg = get_ballgown_object(basedir + "bg.RData")
        fx = robjects.r("getCovariates")
        phenodata = fx(bg)
    
    response = []
    
    response.insert(0, {"id": "ALL", "label": "Include any covariate", "img": "imgs/covariate.png"})
    covariates = set()
    for col_name in phenodata.colnames:
        if col_name == "ids": continue
        covariates.add(col_name)
    
    for covariate in covariates:
        response.append({"id": covariate, "label": covariate, "img": "imgs/covariate.png"})
    
    return HttpResponse(json.dumps(response))

def measures(request):
    
    response = []
    
    response.insert(0, {"id": "ALL", "label": "Include any measure", "img": "imgs/measure.png"})
    for measure in ["FPKM", "Cov"]:
        response.append({"id": measure, "label": measure, "img": "imgs/measure.png"})
    
    return HttpResponse(json.dumps(response))

def covariate_values(request, bioproject, covariate):
    
    with lock:
        basedir = BASE_DATA_DIR + bioproject + "/"
        bg = get_ballgown_object(basedir + "bg.RData")
        fx = robjects.r("getCovariates")
        phenodata = fx(bg)
    
    covariates = {}
    for colname in phenodata.colnames:
        index = phenodata.colnames.index(colname)
        
        values = set()
        for result in phenodata.iter_row():
            x = result[index]
            
            if hasattr(x, 'levels'):
                value = str(x.levels[x[0]-1])
            else:
                value = x[0]
    
            values.add(value)
        
        response = []
        
        for value in values:
            response.append({"id": value, "label": value, "img": "imgs/covariate.png"})
            
        covariates[colname] = response
    
    index = phenodata.colnames.index(covariate)
    if index < 0:
        return HttpResponse(json.dumps("No such covariate ({}) in data.".format(covariate)))
    
    values = set()
    for result in phenodata.iter_row():
        x = result[index]
        
        if hasattr(x, 'levels'):
            value = str(x.levels[x[0]-1])
        else:
            value = x[0]

        values.add(value)
    
    response = []
    
    for value in values:
        response.append({"id": value, "label": value, "img": "imgs/covariate.png"})
    
    return HttpResponse(json.dumps(response))

def downloads(request):
    return HttpResponse(json.dumps(empty_table()))
