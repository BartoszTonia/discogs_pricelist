import pandas as pd
from lib.convert import prepare_df
from lib.methods import plot, value_counts_for, seller_count_for, bargain_count_for

pd.set_option('display.max_columns', 15)
pd.set_option('display.width', 1600)

df = prepare_df('out/Electronic_PL_sample_database.csv')
df = df[df.bargain_label == 'very nice']
df = df[df.ships_from != 'United States']

print(df['id'].count())

# df = df[df['start'] > (df['med'] + 0.50)]  # will show rare and highly wanted records
# df = df[df['for_sale'] < 15]
# df = df[df['want'] > 100]

print_view = [
    'start', 'med', 'title', 'high', 'price', 'discount', 'seller',
    'ratio', 'for_sale', 'want', 'ships_from', 'url'
]

print(df[print_view].sort_values(by='discount', ascending=False).head(10))

plot_view = ['title', 'price', 'start', 'med', 'high', 'discount', 'ratio', 'seller', 'hi-med']
plot(df, plot_view, 'discount', ascend=False, head=30 )


value_counts_for('bargain_label', df)
value_counts_for('label', df, head=6)
value_counts_for('condition', df)
value_counts_for('seller', df)

seller_count_for('very nice', df)

bargain_count_for('best', df)

print(df[df['hi-low'] == 0]['id'].count(), '- one-time sale in history')
print(df[df['last_sold'] == 'never sold']['id'].count(), '- no sale history')
print(df[df['price'] == 0]['id'].count(), '- broken address')
print('Avg rating', round(df['avg_rating'].mean(), 2))
print('Ratio:', round(df['ratio'].mean(), 2))
