import logging as log

from numpy import array
from pprint import pformat
from sklearn.cluster import KMeans
from sklearn.metrics import pairwise_distances_argmin_min

def structure_prune(k, column_vectors):
    log.info(f'column vectors are:\n{pformat(column_vectors)}')
    vectors_as_numpy_array = array(column_vectors)
    log.info(f'column vectors as numpy array are:\n{pformat(vectors_as_numpy_array)}')
    kmeans = KMeans(n_clusters=k).fit(vectors_as_numpy_array)
    return ( pairwise_distances_argmin_min(kmeans.cluster_centers_, vectors_as_numpy_array),
             kmeans.labels_,
             kmeans.cluster_centers_ )
