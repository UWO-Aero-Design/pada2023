from sklearn.mixture import GaussianMixture
from sklearn.clusters import KMeans

class Cluster:
    cluser_count = None

    def __init__(self, cluser_count: int):
        self.cluser_count = cluser_count
        self.kmeans = KMeans(n_clusters=self.cluser_count, random_state=0)

    
    def cluster(self, points: list):
        self.kmeans.fit(points)
        print(self.kmeans.intertia_)