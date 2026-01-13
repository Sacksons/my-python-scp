import psycopg2
import os
from sshtunnel import SSHTunnelForwarder
from sqlmodel import SQLModel, create_engine, Session

sshtunnel.SSH_TIMEOUT = 10.0
sshtunnel.TUNNEL_TIMEOUT = 10.0

postgres_hostname = "sackson-1234.postgres.pythonanywhere-services.com"  # Replace with your hostname
postgres_host_port = 1234  # Replace with your port

with SSHTunnelForwarder(
    ('ssh.pythonanywhere.com'),
    ssh_username='sackson',  # Your PythonAnywhere username
    ssh_password='your_pythonanywhere_password',  # Website login password (store securely, e.g., via env vars)
    remote_bind_address=(postgres_hostname, postgres_host_port)
) as tunnel:
    # Connect using psycopg2 or any Postgres library
    connection = psycopg2.connect(
        user='your_postgres_user',  # Postgres-specific username
        password='your_postgres_password',
        host='127.0.0.1', 
        port=tunnel.local_bind_port,
        database='your_database_name',
    )
    # For SQLModel integration (migrate from SQLite)
    engine = create_engine(f"postgresql://your_postgres_user:your_postgres_password@127.0.0.1:{tunnel.local_bind_port}/your_database_name")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        # Perform queries, e.g., session.add(YourModel(...)); session.commit()
    connection.close()
    # Environment variables for security (set in .env or os.environ)
    PA_USERNAME = os.environ.get('PA_USERNAME', 'sackson')
    PA_PASSWORD = os.environ.get('PA_PASSWORD')
    PG_HOST = os.environ.get('PG_HOST', 'sackson-1234.postgres.pythonanywhere-services.com')  # Your hostname
    PG_PORT = int(os.environ.get('PG_PORT', 1234))  # Your port
    PG_USER = os.environ.get('PG_USER')
    PG_PASS = os.environ.get('PG_PASS')
    PG_DB = os.environ.get('PG_DB')

    with SSHTunnelForwarder(
            ('ssh.pythonanywhere.com'),
            ssh_username=PA_USERNAME,
            ssh_password=PA_PASSWORD,
            remote_bind_address=(PG_HOST, PG_PORT)
    ) as tunnel:
        engine = create_engine(f"postgresql://{PG_USER}:{PG_PASS}@127.0.0.1:{tunnel.local_bind_port}/{PG_DB}")
        # Use engine for sessions or queries