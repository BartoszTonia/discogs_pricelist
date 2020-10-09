import seaborn as sns
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import numpy as np
from sklearn.cluster import KMeans

plt.rcParams["figure.figsize"] = [12, 6]


# Label counts for column filter
def value_counts_for( label, df, head=5 ):
    load = df[label].value_counts().head(head)
    return print(load, ' >> counts for', label, '\n')


def seller_count_for( pricing, df ):
    load = df[df['bargain_label'] == pricing]['seller'].value_counts().head(5)
    return print(load, ' <<< seller counts for >', pricing, '< bargain_label', '\n')


def bargain_count_for( seller, df ):
    load = df[df['seller'] == seller]['bargain_label'].value_counts()
    return load, print(load, '<<< bargain_label counts for seller >', seller, '<\n')


def number_of_unique_labels_for( label, df ):
    load = df[label].count()
    unique = df[label].nunique()
    return load, print('Column', label, 'has', load, 'entries with ', unique, 'unique labels')


def plot( df, cols, sort_by, kind='line', head=100, ascend=True ):
    df[cols].sort_values(by=sort_by, ascending=ascend).head(head).plot(kind=kind, x='seller', figsize=(12, 7))
    plt.title(sort_by)
    plt.xlabel(sort_by)
    plt.ylabel('EUR  /  for sale')
    plt.show()


def scatter_with_trend(df, X_col, y_col):
    X = np.array(df[X_col]).reshape(-1, 1)
    y = np.array(df[y_col])

    from sklearn.model_selection import train_test_split
    x_train, x_test, y_train, y_test = train_test_split(X, y, test_size=1 / 3, random_state=0)

    regress = LinearRegression().fit(x_train, y_train)

    plt.scatter(x_train, y_train, color='yellow')
    plt.scatter(x_test, y_test, color='red')
    plt.plot(x_train, regress.predict(x_train), color='yellow')
    plt.plot(x_test, regress.predict(x_test), color='blue')
    plt.show()


def show_corr(df):
    plt.figure(figsize=(8, 5))
    sns.heatmap(df.corr(), annot=True, cmap=plt.cm.Reds)
    plt.title('Dataset Correlation')
    return plt.show()


def print_inertia(X):
    inertia = []
    for i in range(1, 10):
        kmeans = KMeans(n_clusters=i, max_iter=100, n_init=10, random_state=1)
        kmeans.fit(X)
        inertia.append(kmeans.inertia_)
    plt.plot(inertia)
    plt.show()


def k_means(df, column_choice, n_clusters=5):
    X = np.array(df[column_choice])
    # print_inertia(X)
    kmeans = KMeans(n_clusters=n_clusters, max_iter=100, n_init=10, random_state=0)
    ymeans = kmeans.fit_predict(X)
    # plt.scatter(X[1], X[2])
    df.plot(x=column_choice[0], y=column_choice[1], kind='scatter')
    plt.scatter(kmeans.cluster_centers_[:, 0], kmeans.cluster_centers_[:, 1], c='black')
    plt.show()