# Ambiente Docker y Kubernetes en Shekina

## ¿Por qué usar Docker y Kubernetes?
- Permiten aislar y reproducir servicios como bases de datos, APIs y validadores.
- Facilitan el despliegue, escalado y pruebas de integración.
- Kubernetes permite orquestar múltiples contenedores y servicios en clústeres.

## Ejemplo de docker-compose.yml
```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15
    restart: always
    environment:
      POSTGRES_USER: shekina
      POSTGRES_PASSWORD: shekina_pass
      POSTGRES_DB: shekina_db
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
  rips_validator:
    build: ./docker/rips_validator
    depends_on:
      - postgres
    ports:
      - "8080:8080"
volumes:
  pgdata:
```

## Integración con Kubernetes
- Puedes convertir los servicios de docker-compose en archivos YAML para Kubernetes (`Deployment`, `Service`, `PersistentVolume`).
- Usa herramientas como `kompose` para migrar de docker-compose a Kubernetes.
- Documenta los manifiestos y comandos en esta sección.

## Comandos útiles
- Levantar servicios: `docker-compose up -d`
- Detener servicios: `docker-compose down`
- Ver logs: `docker-compose logs`

## Documenta aquí tus servicios y flujos de integración.
