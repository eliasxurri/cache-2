import grpc
from concurrent import futures
import redis
import psycopg2
import time
import book_service_pb2
import book_service_pb2_grpc

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
            self.cache = {
                'node1': redis.Redis(host='localhost', port=6380),
                'node2': redis.Redis(host='localhost', port=6381),
                'node3': redis.Redis(host='localhost', port=6382),
            }
        elif cache_type == 'replicated':
            self.cache_master = redis.Redis(host='localhost', port=6383)
            self.cache_slave_1 = redis.Redis(host='localhost', port=6384)
            self.cache_slave_2 = redis.Redis(host='localhost', port=6385)

    def get_data_from_cache(self, item_id):
        if hasattr(self, 'cache'):
            return self.cache.get(item_id)
        elif hasattr(self, 'cache_slave'):
            return self.cache_slave.get(item_id)
        return None

    def update_cache(self, item_id, data):
        if hasattr(self, 'cache'):
            self.cache.set(item_id, data)
        elif hasattr(self, 'cache_master'):
            self.cache_master.set(item_id, data)

    def fetch_data_from_db(self, item_id):
        with self.db.cursor() as cursor:
            cursor.execute("SELECT user_id, progress FROM books WHERE item_id = %s", (item_id,))
            result = cursor.fetchone()
            return result

    def GetBookDetails(self, request, context):
        start_time = time.time()
        item_id = request.item_id
        item_data = self.get_data_from_cache(item_id)

        if item_data is None:
            result = self.fetch_data_from_db(item_id)
            if result:
                user_id, progress = result
                item_data = f"{user_id} {progress}"
                self.update_cache(item_id, item_data)
            else:
                return book_service_pb2.GetBookDetailsResponse(user_id=0, progress=0, db_latency=0)  # Not found

        end_time = time.time()
        db_latency = end_time - start_time
        user_id, progress = map(int, item_data.split())

        return book_service_pb2.GetBookDetailsResponse(user_id=user_id, progress=progress, db_latency=db_latency)

def serve(cache_type):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    book_service_pb2_grpc.add_BookServiceServicer_to_server(BookService(cache_type), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    import sys
    cache_type = sys.argv[1] if len(sys.argv) > 1 else 'classic'
    serve(cache_type)
