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

    def update_cache_with_mru(self, cache, item_id, data):
        # Almacenar datos con timestamp para MRU
        timestamp = int(time.time())
        data_with_timestamp = f"{data}|{timestamp}"
        cache.set(item_id, data_with_timestamp)

        # Eliminar la clave más recientemente usada (MRU)
        all_keys = cache.keys('*')
        latest_time = 0
        most_recent_key = None
        for key in all_keys:
            _, key_timestamp = cache.get(key).decode().split('|')
            if int(key_timestamp) > latest_time:
                latest_time = int(key_timestamp)
                most_recent_key = key
        if most_recent_key:
            cache.delete(most_recent_key)
            logging.info(f"Removed most recently used key {most_recent_key.decode()} from cache under MRU policy.")

    def get_data_from_cache(self, cache, item_id):
        # Recuperar datos y actualizar timestamp
        data_with_timestamp = cache.get(item_id)
        if data_with_timestamp:
            data, _ = data_with_timestamp.decode().split('|')
            return data
        return None

    def GetBookDetails(self, request, context):
        item_id = str(request.item_id)
        cache_hit = False

        # Determinar qué caché usar
        cache = self.cache if hasattr(self, 'cache') else self.get_cache_node(item_id) if hasattr(self, 'cache_nodes') else self.cache_master

        # Intentar recuperar del caché
        item_data = self.get_data_from_cache(cache, item_id)
        cache_hit = item_data is not None

        # Si no está en caché, buscar en DB y actualizar caché
        if item_data is None:
            with self.db.cursor() as cur:
                cur.execute("SELECT user_id, progress FROM books WHERE item_id = %s", (item_id,))
                result = cur.fetchone()
                if result:
                    user_id, progress = result
                    item_data = f"{user_id} {progress}"
                    self.update_cache_with_mru(cache, item_id, item_data)
                else:
                    return book_service_pb2.GetBookDetailsResponse(user_id=0, progress=0, db_latency=0)

        end_time = time.time()
        db_latency = end_time - time.time()
        user_id, progress = map(int, item_data.split())

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
