import os
from dotenv import load_dotenv
from langchain_community.vectorstores import Cassandra
from langchain.indexes.vectorstore import VectorStoreIndexWrapper
from langchain_openai import OpenAI, OpenAIEmbeddings
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider

# Load environment variables from the .env file
load_dotenv()

def setup():
    # Load environment variables
    astra_db_secure_bundle_path = os.getenv('ASTRA_DB_SECURE_BUNDLE_PATH')
    astra_db_application_token = os.getenv('ASTRA_DB_APPLICATION_TOKEN')
    astra_db_client_id = os.getenv('ASTRA_DB_CLIENT_ID')
    astra_client_secret = os.getenv('ASTRA_CLIENT_SECRET')
    astra_db_keyspace = os.getenv('ASTRA_DB_KEYSPACE')
    open_ai_key = os.getenv('OPEN_AI_KEY')

    cloud_config = {'secure_connect_bundle': astra_db_secure_bundle_path}
    auth_provider = PlainTextAuthProvider(astra_db_client_id, astra_client_secret)
    cluster = Cluster(cloud=cloud_config, auth_provider=auth_provider)
    astraSession = cluster.connect()
    astraSession.set_keyspace(astra_db_keyspace)

    try:
        row = astraSession.execute("SELECT release_version FROM system.local").one()
        if row:
            print(f"Connected to Cassandra. Release version: {row[0]}")
        else:
            print("No rows returned, connection might be faulty.")
    except Exception as e:
        print(f"Connection failed: {e}")

    # Initialize the language model and embedding model
    llm = OpenAI(api_key=open_ai_key)
    myEmbedding = OpenAIEmbeddings(api_key=open_ai_key)

    # Initialize Cassandra vector store
    myCassandraVStore = Cassandra(
        embedding=myEmbedding,
        session=astraSession,
        keyspace=astra_db_keyspace,
        table_name="odd"
    )

    # vectorIndex = VectorStoreIndexWrapper(vectorstore=myCassandraVStore)

    return myCassandraVStore, llm

def clear_db(astraSession):
    try:
        astraSession.execute("TRUNCATE TABLE odd")
        #print("Table truncated successfully.")
    except Exception as e:
        print(f"Failed to truncate table: {e}")

# Function to read text files
def read_text_files(file_paths):
    texts = []
    for file_path in file_paths:
        with open(file_path, 'r') as file:
            texts.append(file.read())
    return texts
