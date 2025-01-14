import uuid
from qdrant_client import QdrantClient, models
from utils.embeddings import Embeddings
from config.prompt import search_prompt
from utils.backend import retry_request
from config.qdrant_config import create_vectors_config
from fastembed.sparse.bm25 import Bm25

bm25_embedding_model = Bm25("Qdrant/bm25")


class Qdrant:
    def __init__(self, qdrant_url, qdrant_api_key, inferless_token):
        """
        Initialize the Qdrant client with the provided URL, API key, and Inferless token.

        Args:
            qdrant_url (str): The URL of the Qdrant server.
            qdrant_api_key (str): The API key for the Qdrant server.
            inferless_token (str): The Inferless token for embeddings.
        """
        self.client = QdrantClient(qdrant_url, api_key=qdrant_api_key)
        self.embeddings = Embeddings(inferless_token)

    def create_collection(self, collection_name, nlp_embeddings, code_embeddings):
        """
        Create a new collection in Qdrant with the provided name and embeddings.

        Args:
            collection_name (str): The name of the new collection.
            nlp_embeddings (np.array): The NLP embeddings for the collection.
            code_embeddings (np.array): The code embeddings for the collection.

        Returns:
            str: The name of the created collection.
        """
        vectors_config = create_vectors_config(nlp_embeddings.shape[1], code_embeddings.shape[1])

        self.client.create_collection(collection_name=collection_name, vectors_config=vectors_config)
        return collection_name

    def list_collections(self):
        """
        List all collections in the Qdrant server.

        Returns:
            list[str]: The list of collection names.
        """
        collections = self.client.get_collections()
        collection_list = [collection.name for collection in collections.collections]
        return collection_list

    def upload_points(self, collection_name, structures, nlp_embeddings, code_embeddings):
        """
        Upload points to a collection in the Qdrant server.

        Args:
            collection_name (str): The name of the collection to upload to.
            structures (list): The structures of the points to upload.
            nlp_embeddings (np.array): The NLP embeddings of the points.
            code_embeddings (np.array): The code embeddings of the points.
        """
        points = [
            models.PointStruct(
                id=uuid.uuid4().hex,
                vector={
                    "text": text_embedding,
                    "code": code_embedding,
                },
                payload=structure,
            )
            for text_embedding, code_embedding, structure in zip(nlp_embeddings, code_embeddings, structures)
        ]
        self.client.upload_points(
            collection_name,
            points=points,
            batch_size=64,
        )

    def search_groups_text(self, collection_name, vectors, limit=5):
        """
        Search for groups in a collection using text vectors.

        Args:
            collection_name (str): The name of the collection to search in.
            vectors (np.array): The text vectors to search with.

        Returns:
            SearchGroupsResponse: The search results.
        """
        results = self.client.search_groups(
            collection_name,
            query_vector=("text", vectors),
            group_by="context.file_path",
            limit=limit,
            group_size=1,
        )
        return results

    def search_points_code(self, collection_name, vectors, limit=5):
        """
        Search for points in a collection using code vectors.

        Args:
            collection_name (str): The name of the collection to search in.
            vectors (np.array): The code vectors to search with.
            limit (int): The maximum number of results to return.

        Returns:
            List[PointStruct]: The search results.
        """
        results = self.client.search(
            collection_name,
            query_vector=("code", vectors),
            limit=limit,
        )
        return results

    def search_points_text(self, collection_name, vectors, limit=5):
        """
        Search for points in a collection using text vectors.

        Args:
            collection_name (str): The name of the collection to search in.
            vectors (np.array): The text vectors to search with.
            limit (int): The maximum number of results to return.

        Returns:
            List[PointStruct]: The search results.
        """
        results = self.client.search(
            collection_name,
            query_vector=("text", vectors),
            limit=limit,
        )
        return results

    def search_groups_code(self, collection_name, vectors, limit=5):
        """
        Search for groups in a collection using code vectors.

        Args:
            collection_name (str): The name of the collection to search in.
            vectors (np.array): The code vectors to search with.

        Returns:
            SearchGroupsResponse: The search results.
        """
        results = self.client.search_groups(
            collection_name,
            query_vector=("code", vectors),
            group_by="context.file_path",
            limit=limit,
            group_size=1,
        )
        print(results)
        return results

    def hybrid_search_points_text(self, collection_name, dense_vector, sparse_vector, limit=10):
        """
        Search for points in a collection using text vectors.

        Args:
            collection_name (str): The name of the collection to search in.
            vectors (np.array): The text vectors to search with.
            limit (int): The maximum number of results to return.

        Returns:
            List[PointStruct]: The search results.
        """
        prefetch = [
            models.Prefetch(
                query=dense_vector,
                using="text",
                limit=20,
            ),
            models.Prefetch(
                query=models.SparseVector(**sparse_vector.as_object()),
                using="bm25_text",
                limit=20,
            ),
        ]
        try:
            results = self.client.query_points(
                collection_name,
                prefetch=prefetch,
                query=models.FusionQuery(
                    fusion=models.Fusion.RRF,
                ),
                with_payload=True,
                limit=limit,
            )
            return results
        except Exception as e:
            print(f"Error in query_points: {str(e)}")
            return None

    def hybrid_search_points_code(self, collection_name, dense_vector, sparse_vector, limit=10):
        """
        Search for points in a collection using text vectors.

        Args:
            collection_name (str): The name of the collection to search in.
            vectors (np.array): The text vectors to search with.
            limit (int): The maximum number of results to return.

        Returns:
            List[PointStruct]: The search results.
        """
        prefetch = [
            models.Prefetch(
                query=dense_vector,
                using="text",
                limit=20,
            ),
            models.Prefetch(
                query=models.SparseVector(**sparse_vector.as_object()),
                using="bm25_text",
                limit=20,
            ),
        ]
        try:
            results = self.client.query_points(
                collection_name,
                prefetch=prefetch,
                query=models.FusionQuery(
                    fusion=models.Fusion.RRF,
                ),
                with_payload=True,
                limit=limit,
            )
            return results
        except Exception as e:
            print(f"Error in query_points: {str(e)}")
            return None

    def process_results(self, results):
        """
        Process search results into a dictionary format.

        Args:
            results: The search results to process.

        Returns:
            list[dict]: The processed results.
        """
        processed_results = []
        for group in results.groups:
            group_dict = {
                "id": group.id,
                "hits": [
                    {
                        "id": hit.id,
                        "version": hit.version,
                        "score": hit.score,
                        "payload": hit.payload,
                        "vector": hit.vector,
                        "shard_key": hit.shard_key,
                    }
                    for hit in group.hits
                ],
            }
            processed_results.append(group_dict)
        return processed_results

    def get_analytics_platform_filepaths(self, collection, analytics_platform):
        """
        This function retrieves similar data points based on a query from a given collection in Qdrant using text and code embeddings.

        Args:
        - collection: The collection to search for similar points.
        - analytics_platform: The analytics_platform related to the query. For example analytics_platform = 'mixpanel' if the query is
          related to mixpanel.

        Returns:
        - results_dict: A list of dictionaries containing information about the similar points found, including id, version, score, payload, vector,
          and shard key.
        """

        query = search_prompt.get(analytics_platform, "")
        print(f"Query: {query}")

        text_query_vector = self.embeddings.encode_text(shape=1, texts=[query])["outputs"][0]["data"]
        print(f"Text query vector: {text_query_vector[:5]}...")  # Printing first 5 elements

        code_query_vector = self.embeddings.encode_code(shape=1, codes=[query])["outputs"][0]["data"]
        print(f"Code query vector: {code_query_vector[:5]}...")  # Printing first 5 elements
        try:
            text_results = retry_request(self.search_groups_text, collection, vectors=text_query_vector)
            print(f"Text results: {text_results}")
        except Exception as e:
            print(f"Error in text search: {str(e)}")

        try:
            code_results = retry_request(self.search_groups_code, collection, vectors=code_query_vector)
            print(f"Code results: {code_results}")
        except Exception as e:
            print(f"Error in code search: {str(e)}")

        results_dict = self.process_results(text_results) + self.process_results(code_results)
        print(f"Combined results: {results_dict}")

        # Extract filepaths with scores above 0.5
        analytics_filepaths = []
        print(f"Initialized analytics_filepaths: {analytics_filepaths}")
        for result in results_dict:
            if result["hits"][0]["score"] > 0.5:
                analytics_filepaths.append(result["id"])
        return analytics_filepaths

    def search(self, query, collection):
        """
        Search for similar data points in a collection using text and code embeddings.

        Args:
        - query: The query to search for similar points.
        - collection: The collection to search for similar points.

        Returns:
        - list[dict]: A list of dictionaries containing information about the similar points found, including id, version, score, payload, vector,
          and shard key.
        """
        text_query_vector = self.embeddings.encode_text(shape=1, texts=[query])["outputs"][0]["data"]
        code_query_vector = self.embeddings.encode_code(shape=1, codes=[query])["outputs"][0]["data"]

        text_results = self.search_points_text(collection, vectors=text_query_vector, limit=2)
        code_results = self.search_points_code(collection, vectors=code_query_vector, limit=2)

        def process_points(points):
            return [{"score": point.score, "payload": point.payload} for point in points]

        results = process_points(text_results) + process_points(code_results)
        passages = sorted(results, key=lambda x: x["score"], reverse=True)
        return [passage["payload"] for passage in passages]
