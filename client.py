import grpc
import pandas as pd
import time
import book_service_pb2
import book_service_pb2_grpc

def run_client(cache_type):
    # Establecer la dirección del servidor gRPC
    channel = grpc.insecure_channel('localhost:50051')
    stub = book_service_pb2_grpc.BookServiceStub(channel)

    # Cargar datos desde el archivo CSV
    df = pd.read_csv('interactions.csv')

    # Extraer los item_id únicos para evitar solicitudes duplicadas
    item_ids = df['item_id']
    # Realizar solicitudes al servidor gRPC y medir el tiempo de respuesta
    start_time = time.time()
    for item_id in item_ids:
        try:
            response = stub.GetBookDetails(book_service_pb2.GetBookDetailsRequest(item_id=item_id))
            print(f"Item ID: {item_id}, User ID: {response.user_id}, Progress: {response.progress}%")
        except grpc.RpcError as e:
            print(f"GRPC Error: {str(e)}")
    end_time = time.time()

    # Calcular el tiempo total tomado
    total_time = end_time - start_time
    print(f"Total time for {len(item_ids)} requests with {cache_type} cache: {total_time:.5f}s")

if __name__ == '__main__':
    import sys
    cache_type = sys.argv[1] if len(sys.argv) > 1 else 'classic'
    print(f"Running client for {cache_type} cache...")
    run_client(cache_type)
