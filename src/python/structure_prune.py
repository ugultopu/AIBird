from numpy import array
from sklearn.cluster import KMeans
from sklearn.metrics import pairwise_distances_argmin_min

def structure_prune(k, export_data):
    kmeans = KMeans(n_clusters=k).fit(array(export_data))
    return ( pairwise_distances_argmin_min(kmeans.cluster_centers_, export_data),
             kmeans.labels_,
             kmeans.cluster_centers_ )
