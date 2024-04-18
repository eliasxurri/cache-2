import grpc
from concurrent import futures
import redis
import psycopg2
import time
import hashlib
import logging
import book_service_pb2
import book_service_pb2_grpc

# Configuración del logger
logging.basicConfig(level=logging.INFO, filename='server_logs.log', format='%(asctime)s - %(levelname)s - %(message)s')

class BookService(book_service_pb2_grpc.BookServiceServicer):
    def __init__(self, cache_type):
        # Conexión a PostgreSQL
        self.db = psycopg2.connect(
            dbname="bookdb",
            user="postgres",
            password="marcianito100",
            host="localhost",
            port="5432"
        )
        
        # Configuración según el tipo de caché
        if cache_type == 'classic':
            self.cache = redis.Redis(host='localhost', port=6379)
        elif cache_type == 'partitioned':
            self.cache_nodes = [
                redis.Redis(host='localhost', port=6380),
                redis.Redis(host='localhost', port=6381),
                redis.Redis(host='localhost', port=6382),
            ]
        elif cache_type == 'replicated':
            self.cache_master = redis.Redis(host='localhost', port=6383)
            self.cache_slaves = [
                redis.Redis(host='localhost', port=6384),
                redis.Redis(host='localhost', port=6385),
            ]

    def get_cache_node(self, key):
        """ Simple hash function to choose a Redis node for partitioned cache """
        node_index = int(hashlib.md5(key.encode()).hexdigest(), 16) % len(self.cache_nodes)
        return self.cache_nodes[node_index]

    def GetBookDetails(self, request, context):
        start_time = time.time()
        item_id = str(request.item_id)
        item_data = None
        cache_hit = False

        # Retrieve from cache based on the cache type
        if hasattr(self, 'cache'):
            item_data = self.cache.get(item_id)
        elif hasattr(self, 'cache_nodes'):
            cache_node = self.get_cache_node(item_id)
            item_data = cache_node.get(item_id)
        elif hasattr(self, 'cache_master'):
            for slave in self.cache_slaves:
                item_data = slave.get(item_id)
                if item_data:
                    cache_hit = True
                    break
            if item_data is None:
                item_data = self.cache_master.get(item_id)

        if item_data:
            cache_hit = True

        # If not in cache, fetch from database and update cache
        if item_data is None:
            with self.db.cursor() as cur:
                cur.execute("SELECT user_id, progress FROM books WHERE item_id = %s", (item_id,))
                result = cur.fetchone()
                if result:
                    user_id, progress = result
                    item_data = f"{user_id} {progress}"
                    # Update cache based on the cache type
                    if hasattr(self, 'cache'):
                        self.cache.set(item_id, item_data)
                    elif hasattr(self, 'cache_nodes'):
                        cache_node = self.get_cache_node(item_id)
                        cache_node.set(item_id, item_data)
                    elif hasattr(self, 'cache_master'):
                        self.cache_master.set(item_id, item_data)
                else:
                    return book_service_pb2.GetBookDetailsResponse(user_id=0, progress=0, db_latency=0)

        end_time = time.time()
        db_latency = end_time - start_time
        user_id, progress = map(int, item_data.split())

        # Log the hit rate and response time
        if cache_hit:
            logging.info(f"Cache hit for item_id {item_id}. Response time: {db_latency:.5f}s")
        else:
            logging.info(f"Cache miss for item_id {item_id}. Data fetched from DB. Response time: {db_latency:.5f}s")

        return book_service_pb2.GetBookDetailsResponse(user_id=user_id, progress=progress, db_latency=db_latency)

def serve(cache_type):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    book_service_pb2_grpc.add_BookServiceServicer_to_server(BookService(cache_type), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    import sys
    cache_type = sys.argv[1] if len(sys.argv) > 1 else 'classic'
    serve(cache_type)
