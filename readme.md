# gRPC Redis Caching for Book Service

Este repositorio contiene la implementación de un sistema de servicio de libros utilizando gRPC, que incorpora varias configuraciones de caché en Redis para optimizar el rendimiento de consultas frecuentes.

## Estructura del Proyecto

A continuación, se describe la estructura del repositorio y el propósito de cada archivo y directorio:

- `cache-distribuido.py`: Script del servidor que implementa la lógica del servicio gRPC con opciones de caché distribuido.
- `client.py`: Cliente gRPC para interactuar con el servidor y realizar pruebas de rendimiento.
- `interactions.csv`: Datos de muestra que contienen `item_id`s utilizados para pruebas de carga y funcionalidad.
- `server_logs.log`: Archivo de registro que almacena los logs de rendimiento y operaciones del servidor.

### Directorio `redis-config`
Configuraciones específicas de Redis para cada tipo de caché:
- `classic/redis_classic_LRU.conf`: Configuración de Redis para caché clásico con política LRU.
- `partitioned/node_638X/redis.conf`: Configuración para nodos individuales en un caché particionado.
- `replicated/`: Contiene configuraciones para un nodo maestro y dos esclavos en un caché replicado.


