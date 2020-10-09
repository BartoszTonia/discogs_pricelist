import pandas as pd
from time import time

columns = "id", "title", "price", "ratio", 'start', 'avg_rating', 'rating_count', "low", "med", "high", "want", \
          "have", "seller", "ships_from", "label", "last_sold", "for_sale", "url", "styles", 'comment', 'condition'

ratio_with_label = [(0, 0.01, 'error'), (0.01, 0.85, 'very nice'), (0.85, 1.15, 'good'),
             (1.15, 1.6, 'expensive'), (1.6, 2.2, 'overpriced'), (2.2, 1000, 'greedy')]


def prepare_df( temp ):
    s_time = time()
    df = pd.read_csv(temp, encoding='utf-8')
    print(len(df.index))
    
    df['hi-low'] = df['high'] - df['low']
    df['discount'] = df['med'] - df['price']
    df['hi-med'] = df['high'] - df['med']

    df = df[df['price'] != 0]
    df = df[df['hi-low'] != 0]
    df = df[df['last_sold'] != 'never_sold']
    
    for i in ratio_with_label:
        df.loc[(df['ratio'] > i[0]) & (df['ratio'] <= i[1]), 'bargain_label'] = i[2]
        
    print(' >>> % s ' % (round((time() - s_time), 4)))
    return df


def create_db( df, location ):
    try:
        df.to_csv(location, index=True)
        print('File was successfully created -- {}'.format(location))
    except ValueError:
        print("Empty file, not created -- {}".format(location), ValueError)
        pass

    
def scale(df, column):
    return (df[column] - df[column].min()) / (df[column].max() - df[column].min())

