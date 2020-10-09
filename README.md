## ..:: Discogs pricelist ::..

## Technology stack :snake:

Name |  Version |

| [Python](https://www.python.org/) | 3.6 |

## Features
- Scrape best quality records and analyze them in search of best bargains!

## How 

Check out these Jupyter notebooks below, where I explain the logic behind scraping engine, cleaning data
and present some example data analysis using `pandas` and `matplotlib`

- <a href="https://nbviewer.jupyter.org/github/BartoszTonia/discogs_pricelist/blob/master/jupyter_notebooks/scraping_engine.ipynb"> Scraping Engine </a>
- <a href="https://nbviewer.jupyter.org/github/BartoszTonia/discogs_pricelist/blob/master/jupyter_notebooks/convert.ipynb"> Convertion into database </a>
- <a href="https://nbviewer.jupyter.org/github/BartoszTonia/discogs_pricelist/blob/master/jupyter_notebooks/show.ipynb"> Final Analysis </a>

## Prerequisites :coffee:

You will need the following things properly installed on your machine.

* python3
* pip3
```
apt-get install python3-pip
```

## Installation :books:
1. Install all dependencies using ``` pip3 install -r requirements.txt ```

2. Discogs account required! Open file dprice.py and fill your developer token (line 17)
Get your token at https://www.discogs.com/settings/developers

## Run
Run search
``` angular2
python3 dprice.py 
```
Run preview of database
```angular2
python3 show.py
```
## ToDo

- write unit tests
