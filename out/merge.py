import os
import glob
import pandas as pd
from time import time
from pathlib import Path
from datetime import datetime


extension = 'csv'
all_filenames = [i for i in glob.glob('*.{}'.format(extension))]


def merge(label, *args):
    total = 0
    t = time()
    timestamp = datetime.fromtimestamp(t).strftime('_%Y%m%d')
    # for each in [*args]:
    #     each_pattern = each.split('_')
    #     count = each_pattern[3]
    #     total += int(count)

    print(total)
    filenames = [*args]
    combined_csv = pd.concat([pd.read_csv(f) for f in filenames])
    filename = '{}.csv'.format(label)
    combined_csv.to_csv(filename, index=False, encoding='utf-8-sig')

    if Path(filename).exists():
        for each in [*args]:
            Path(each).unlink()

merge('',
      'high_demand_polish_market.csv',
      'low_demand_polish_market.csv',
      )
