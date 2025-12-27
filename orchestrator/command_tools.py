"""MCP tools converted from command templates.

These tools expose command functionality directly via MCP,
replacing the need for markdown command files to be read manually.
"""

from typing import Any

from orchestrator.paths import get_skills_dir


def _load_skill(skill_name: str) -> str:
    """Load a skill's content for reference."""
    skill_file = get_skills_dir() / skill_name / "SKILL.md"
    if skill_file.exists():
        return skill_file.read_text()
    return ""


# =============================================================================
# Data Engineering Tools
# =============================================================================


def create_pipeline(
    source: str,
    target: str,
    name: str = "pipeline",
    incremental: bool = False,
    schedule: str | None = None,
    with_tests: bool = True,
) -> dict[str, Any]:
    """Generate data pipeline boilerplate for ETL/ELT workflows.

    Creates a complete pipeline structure with extraction, transformation,
    and loading components based on the specified source and target.

    Args:
        source: Data source type (api, s3, postgresql, mysql, files)
        target: Data target type (snowflake, redshift, s3, postgresql)
        name: Pipeline name for the directory
        incremental: Generate incremental loading logic with watermarks
        schedule: Cron expression for Airflow DAG (e.g., "0 6 * * *")
        with_tests: Include pytest test files

    Returns:
        Pipeline structure with file templates and next steps
    """
    # Load data pipeline patterns for reference
    patterns = _load_skill("data-pipeline-patterns")

    # Define file structure
    files = {
        f"{name}/src/__init__.py": "",
        f"{name}/src/config.py": _generate_config_template(source, target),
        f"{name}/src/extract.py": _generate_extract_template(source),
        f"{name}/src/transform.py": _generate_transform_template(),
        f"{name}/src/load.py": _generate_load_template(target, incremental),
        f"{name}/config/config.yaml": _generate_config_yaml(source, target),
        f"{name}/requirements.txt": _generate_requirements(source, target),
    }

    if with_tests:
        files.update({
            f"{name}/tests/__init__.py": "",
            f"{name}/tests/test_extract.py": _generate_test_template("extract"),
            f"{name}/tests/test_transform.py": _generate_test_template("transform"),
            f"{name}/tests/test_load.py": _generate_test_template("load"),
        })

    if schedule:
        files[f"{name}/dags/{name}_dag.py"] = _generate_dag_template(name, schedule)

    return {
        "success": True,
        "pipeline_name": name,
        "source": source,
        "target": target,
        "pattern": "incremental" if incremental else "full_refresh",
        "files": files,
        "file_count": len(files),
        "patterns_reference": patterns[:500] if patterns else None,
        "next_steps": [
            f"1. Review generated files in {name}/",
            "2. Configure credentials in config/config.yaml",
            "3. Install dependencies: pip install -r requirements.txt",
            "4. Run tests: pytest tests/",
            f"5. Execute: python -m {name}.src.main" if not schedule else f"5. Deploy DAG to Airflow",
        ],
    }


def _generate_config_template(source: str, target: str) -> str:
    return f'''"""Pipeline configuration."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Pipeline settings from environment."""

    # Source: {source}
    source_connection: str = ""

    # Target: {target}
    target_connection: str = ""

    # Processing
    batch_size: int = 10000
    retry_attempts: int = 3

    class Config:
        env_file = ".env"


settings = Settings()
'''


def _generate_extract_template(source: str) -> str:
    extractors = {
        "api": '''"""Extract data from REST API."""
import requests
from typing import Iterator


def extract(endpoint: str, params: dict = None) -> Iterator[dict]:
    """Extract data from API with pagination."""
    while endpoint:
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        data = response.json()

        yield from data.get("results", [data])

        endpoint = data.get("next")
        params = None  # Pagination URL includes params
''',
        "s3": '''"""Extract data from S3."""
import boto3
from typing import Iterator
import pandas as pd


def extract(bucket: str, prefix: str) -> Iterator[pd.DataFrame]:
    """Extract data from S3 bucket."""
    s3 = boto3.client("s3")
    paginator = s3.get_paginator("list_objects_v2")

    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            response = s3.get_object(Bucket=bucket, Key=obj["Key"])
            yield pd.read_parquet(response["Body"])
''',
        "postgresql": '''"""Extract data from PostgreSQL."""
import psycopg2
from typing import Iterator


def extract(query: str, connection_string: str, batch_size: int = 10000) -> Iterator[list]:
    """Extract data from PostgreSQL in batches."""
    with psycopg2.connect(connection_string) as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            while True:
                batch = cur.fetchmany(batch_size)
                if not batch:
                    break
                yield batch
''',
    }
    return extractors.get(source, extractors["api"])


def _generate_transform_template() -> str:
    return '''"""Transform extracted data."""
import pandas as pd


def transform(data: pd.DataFrame) -> pd.DataFrame:
    """Apply transformations to data."""
    df = data.copy()

    # Add your transformations here
    # Example:
    # df["created_at"] = pd.to_datetime(df["created_at"])
    # df = df.dropna(subset=["required_column"])

    return df
'''


def _generate_load_template(target: str, incremental: bool) -> str:
    mode = "append" if incremental else "replace"
    loaders = {
        "snowflake": f'''"""Load data to Snowflake."""
import pandas as pd
from snowflake.connector import connect
from snowflake.connector.pandas_tools import write_pandas


def load(df: pd.DataFrame, table: str, connection_params: dict) -> int:
    """Load dataframe to Snowflake table."""
    with connect(**connection_params) as conn:
        success, nchunks, nrows, _ = write_pandas(
            conn, df, table,
            auto_create_table=True,
            overwrite={"mode" == "replace"}
        )
        return nrows if success else 0
''',
        "s3": f'''"""Load data to S3."""
import boto3
import pandas as pd
from datetime import datetime


def load(df: pd.DataFrame, bucket: str, prefix: str) -> str:
    """Load dataframe to S3 as parquet."""
    s3 = boto3.client("s3")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    key = f"{{prefix}}/{{timestamp}}.parquet"

    buffer = df.to_parquet()
    s3.put_object(Bucket=bucket, Key=key, Body=buffer)

    return f"s3://{{bucket}}/{{key}}"
''',
    }
    return loaders.get(target, loaders["s3"])


def _generate_config_yaml(source: str, target: str) -> str:
    return f'''# Pipeline Configuration
pipeline:
  name: data_pipeline
  version: "1.0"

source:
  type: {source}
  # Add source-specific configuration

target:
  type: {target}
  # Add target-specific configuration

processing:
  batch_size: 10000
  retry_attempts: 3
'''


def _generate_requirements(source: str, target: str) -> str:
    deps = ["pydantic-settings>=2.0", "pandas>=2.0", "pytest>=7.0"]

    source_deps = {
        "api": ["requests>=2.28"],
        "s3": ["boto3>=1.26", "pyarrow>=12.0"],
        "postgresql": ["psycopg2-binary>=2.9"],
        "mysql": ["mysql-connector-python>=8.0"],
    }

    target_deps = {
        "snowflake": ["snowflake-connector-python[pandas]>=3.0"],
        "redshift": ["redshift-connector>=2.0"],
        "s3": ["boto3>=1.26", "pyarrow>=12.0"],
        "postgresql": ["psycopg2-binary>=2.9"],
    }

    deps.extend(source_deps.get(source, []))
    deps.extend(target_deps.get(target, []))

    return "\n".join(sorted(set(deps)))


def _generate_test_template(module: str) -> str:
    return f'''"""Tests for {module} module."""
import pytest


class Test{module.title()}:
    """Test {module} functionality."""

    def test_{module}_basic(self):
        """Test basic {module} operation."""
        # TODO: Implement test
        assert True

    def test_{module}_error_handling(self):
        """Test {module} error handling."""
        # TODO: Implement test
        assert True
'''


def _generate_dag_template(name: str, schedule: str) -> str:
    return f'''"""Airflow DAG for {name} pipeline."""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator


default_args = {{
    "owner": "data-team",
    "depends_on_past": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
}}

with DAG(
    dag_id="{name}",
    default_args=default_args,
    description="{name} data pipeline",
    schedule_interval="{schedule}",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["data-pipeline"],
) as dag:

    def run_extract():
        from {name}.src.extract import extract
        # TODO: Implement extraction

    def run_transform():
        from {name}.src.transform import transform
        # TODO: Implement transformation

    def run_load():
        from {name}.src.load import load
        # TODO: Implement loading

    extract_task = PythonOperator(task_id="extract", python_callable=run_extract)
    transform_task = PythonOperator(task_id="transform", python_callable=run_transform)
    load_task = PythonOperator(task_id="load", python_callable=run_load)

    extract_task >> transform_task >> load_task
'''


def analyze_query(sql: str) -> dict[str, Any]:
    """Analyze SQL query and provide optimization recommendations.

    Checks for common anti-patterns including index issues, join problems,
    query structure issues, and performance concerns.

    Args:
        sql: SQL query to analyze (or description of slow query)

    Returns:
        Analysis with issues found and optimization suggestions
    """
    # Load SQL optimization patterns
    patterns = _load_skill("sql-optimization")

    issues = []
    suggestions = []

    sql_upper = sql.upper()
    sql_lower = sql.lower()

    # Check for SELECT *
    if "SELECT *" in sql_upper:
        issues.append({
            "severity": "medium",
            "category": "query_structure",
            "title": "SELECT * usage",
            "description": "Selecting all columns can cause unnecessary data transfer",
            "suggestion": "Specify only the columns you need",
        })

    # Check for functions on columns in WHERE
    function_patterns = ["YEAR(", "MONTH(", "DATE(", "UPPER(", "LOWER(", "TRIM("]
    for func in function_patterns:
        if func in sql_upper and "WHERE" in sql_upper:
            issues.append({
                "severity": "high",
                "category": "index_usage",
                "title": f"Function {func[:-1]} on column",
                "description": "Functions on columns prevent index usage",
                "suggestion": "Use range predicates or computed columns instead",
            })

    # Check for NOT IN with subquery
    if "NOT IN" in sql_upper and "SELECT" in sql_upper.split("NOT IN")[1][:50] if "NOT IN" in sql_upper else False:
        issues.append({
            "severity": "medium",
            "category": "query_structure",
            "title": "NOT IN with subquery",
            "description": "NOT IN with NULLs can cause unexpected results",
            "suggestion": "Use NOT EXISTS or LEFT JOIN ... WHERE IS NULL instead",
        })

    # Check for missing WHERE
    if "WHERE" not in sql_upper and ("SELECT" in sql_upper and "FROM" in sql_upper):
        issues.append({
            "severity": "low",
            "category": "performance",
            "title": "No WHERE clause",
            "description": "Query may scan entire table",
            "suggestion": "Add appropriate filters if not all rows are needed",
        })

    # Check for DISTINCT
    if "DISTINCT" in sql_upper:
        issues.append({
            "severity": "low",
            "category": "query_structure",
            "title": "DISTINCT usage",
            "description": "DISTINCT requires sorting and may indicate data issues",
            "suggestion": "Review if DISTINCT is necessary or fix upstream duplicates",
        })

    # Check for OR conditions
    if " OR " in sql_upper:
        issues.append({
            "severity": "medium",
            "category": "index_usage",
            "title": "OR conditions",
            "description": "OR conditions may prevent index usage",
            "suggestion": "Consider UNION ALL for separate conditions",
        })

    # General suggestions
    suggestions = [
        "Review execution plan with EXPLAIN ANALYZE",
        "Check if indexes exist on filtered columns",
        "Consider query caching for repeated queries",
        "Verify statistics are up to date",
    ]

    return {
        "success": True,
        "query_preview": sql[:200] + "..." if len(sql) > 200 else sql,
        "issues_found": len(issues),
        "issues": issues,
        "suggestions": suggestions,
        "patterns_reference": patterns[:500] if patterns else None,
        "next_steps": [
            "1. Address high-severity issues first",
            "2. Run EXPLAIN ANALYZE on the query",
            "3. Compare performance before and after changes",
            "4. Test with production-like data volumes",
        ],
    }


def analyze_data(
    path: str,
    sample_size: int = 1000,
) -> dict[str, Any]:
    """Profile and analyze a dataset for quality and patterns.

    Returns analysis structure that Claude Code should use to examine
    the data file and provide profiling results.

    Args:
        path: Path to the data file (CSV, Parquet, JSON)
        sample_size: Number of rows to sample for analysis

    Returns:
        Analysis template and instructions for data profiling
    """
    return {
        "success": True,
        "action": "analyze_data_file",
        "path": path,
        "sample_size": sample_size,
        "instructions": """Analyze the data file and report:

1. **Schema Analysis**:
   - Column names and inferred types
   - Nullable columns

2. **Data Quality**:
   - Missing value counts per column
   - Duplicate row count
   - Outlier detection for numeric columns

3. **Statistical Summary**:
   - Numeric columns: min, max, mean, median, std
   - Categorical columns: unique values, top 5 values

4. **Data Patterns**:
   - Date/time columns: range, gaps
   - ID columns: uniqueness, format
   - Relationships between columns

5. **Recommendations**:
   - Data cleaning suggestions
   - Schema improvements
   - Potential data quality rules""",
        "output_format": {
            "schema": [{"column": "str", "dtype": "str", "nullable": "bool"}],
            "quality": {
                "missing_values": {"column": "count"},
                "duplicates": "int",
                "outliers": {"column": ["values"]},
            },
            "statistics": {"column": {"min": "", "max": "", "mean": "", "unique": ""}},
            "recommendations": ["list of suggestions"],
        },
    }


# =============================================================================
# DevOps Tools
# =============================================================================


def create_dockerfile(
    project_type: str = "python",
    optimize_for: str = "size",
    python_version: str = "3.11",
    include_dev: bool = False,
) -> dict[str, Any]:
    """Create optimized Dockerfile for a project.

    Generates a multi-stage Dockerfile with best practices including
    layer caching, non-root user, and health checks.

    Args:
        project_type: Type of project (python, node, java)
        optimize_for: Optimization target (size, speed)
        python_version: Python version for base image
        include_dev: Include development tools

    Returns:
        Dockerfile content and related files
    """
    if project_type == "python":
        dockerfile = f'''# Build stage
FROM python:{python_version}-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Runtime stage
FROM python:{python_version}-slim

WORKDIR /app

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser

# Copy dependencies from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Add local bin to PATH
ENV PATH=/home/appuser/.local/bin:$PATH

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Default command
CMD ["python", "-m", "app.main"]
'''
    elif project_type == "node":
        dockerfile = '''# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci --only=production

# Runtime stage
FROM node:20-alpine

WORKDIR /app

# Create non-root user
RUN addgroup -g 1001 -S nodejs && adduser -S nodejs -u 1001

# Copy dependencies
COPY --from=builder /app/node_modules ./node_modules
COPY --chown=nodejs:nodejs . .

USER nodejs

HEALTHCHECK --interval=30s CMD wget -q --spider http://localhost:3000/health || exit 1

CMD ["node", "src/index.js"]
'''
    else:
        dockerfile = "# Unsupported project type"

    dockerignore = '''# Git
.git
.gitignore

# Python
__pycache__
*.pyc
*.pyo
.pytest_cache
.venv
venv
.env*

# IDE
.vscode
.idea

# Build artifacts
dist
build
*.egg-info

# Documentation
docs
*.md
!README.md

# Tests
tests
test_*

# Other
.DS_Store
*.log
'''

    compose = f'''version: "3.8"

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - LOG_LEVEL=info
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
'''

    return {
        "success": True,
        "project_type": project_type,
        "optimization": optimize_for,
        "files": {
            "Dockerfile": dockerfile,
            ".dockerignore": dockerignore,
            "docker-compose.yml": compose,
        },
        "features": [
            "Multi-stage build for smaller image",
            "Layer caching for faster builds",
            "Non-root user for security",
            "Health check configured",
            "Production-ready defaults",
        ],
        "next_steps": [
            "1. Review and customize the Dockerfile",
            "2. Build: docker build -t myapp .",
            "3. Run: docker run -p 8000:8000 myapp",
            "4. Or use: docker-compose up",
        ],
    }


def create_k8s_manifest(
    app_name: str,
    replicas: int = 2,
    port: int = 8000,
    image: str = "app:latest",
    resources_preset: str = "small",
) -> dict[str, Any]:
    """Generate Kubernetes manifests for an application.

    Creates Deployment, Service, ConfigMap, and HorizontalPodAutoscaler
    with production-ready defaults.

    Args:
        app_name: Name of the application
        replicas: Number of replicas
        port: Container port
        image: Docker image to deploy
        resources_preset: Resource preset (small, medium, large)

    Returns:
        Kubernetes manifest files
    """
    resource_presets = {
        "small": {"cpu": "100m", "memory": "128Mi", "cpu_limit": "500m", "memory_limit": "512Mi"},
        "medium": {"cpu": "250m", "memory": "256Mi", "cpu_limit": "1000m", "memory_limit": "1Gi"},
        "large": {"cpu": "500m", "memory": "512Mi", "cpu_limit": "2000m", "memory_limit": "2Gi"},
    }
    resources = resource_presets.get(resources_preset, resource_presets["small"])

    deployment = f'''apiVersion: apps/v1
kind: Deployment
metadata:
  name: {app_name}
  labels:
    app: {app_name}
spec:
  replicas: {replicas}
  selector:
    matchLabels:
      app: {app_name}
  template:
    metadata:
      labels:
        app: {app_name}
    spec:
      containers:
      - name: {app_name}
        image: {image}
        ports:
        - containerPort: {port}
        resources:
          requests:
            cpu: "{resources['cpu']}"
            memory: "{resources['memory']}"
          limits:
            cpu: "{resources['cpu_limit']}"
            memory: "{resources['memory_limit']}"
        livenessProbe:
          httpGet:
            path: /health
            port: {port}
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: {port}
          initialDelaySeconds: 5
          periodSeconds: 5
        envFrom:
        - configMapRef:
            name: {app_name}-config
'''

    service = f'''apiVersion: v1
kind: Service
metadata:
  name: {app_name}
spec:
  selector:
    app: {app_name}
  ports:
  - port: 80
    targetPort: {port}
  type: ClusterIP
'''

    configmap = f'''apiVersion: v1
kind: ConfigMap
metadata:
  name: {app_name}-config
data:
  LOG_LEVEL: "info"
  # Add more configuration here
'''

    hpa = f'''apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {app_name}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {app_name}
  minReplicas: {replicas}
  maxReplicas: {replicas * 5}
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
'''

    kustomization = f'''apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - deployment.yaml
  - service.yaml
  - configmap.yaml
  - hpa.yaml

commonLabels:
  app.kubernetes.io/name: {app_name}
  app.kubernetes.io/managed-by: kustomize
'''

    return {
        "success": True,
        "app_name": app_name,
        "files": {
            "k8s/deployment.yaml": deployment,
            "k8s/service.yaml": service,
            "k8s/configmap.yaml": configmap,
            "k8s/hpa.yaml": hpa,
            "k8s/kustomization.yaml": kustomization,
        },
        "resources": resources,
        "next_steps": [
            "1. Review and customize manifests in k8s/",
            "2. Apply: kubectl apply -k k8s/",
            "3. Check status: kubectl get pods -l app=" + app_name,
            "4. View logs: kubectl logs -l app=" + app_name,
        ],
    }


# =============================================================================
# AI Engineering Tools
# =============================================================================


def scaffold_rag(
    name: str,
    vectordb: str = "chromadb",
    framework: str = "langchain",
    embedding_model: str = "text-embedding-3-small",
) -> dict[str, Any]:
    """Generate RAG application boilerplate.

    Creates a complete RAG application structure with vector database
    integration, document ingestion, and retrieval chain.

    Args:
        name: Application name
        vectordb: Vector database (chromadb, qdrant, weaviate, pgvector)
        framework: RAG framework (langchain, llamaindex)
        embedding_model: Embedding model to use

    Returns:
        RAG application scaffold with all necessary files
    """
    # Load AI engineering patterns
    patterns = _load_skill("ai-engineering-patterns")

    config_py = f'''"""RAG Application Configuration."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Embedding
    embedding_model: str = "{embedding_model}"
    openai_api_key: str = ""

    # Vector DB
    vectordb_url: str = "http://localhost:6333"
    collection_name: str = "documents"

    # Chunking
    chunk_size: int = 512
    chunk_overlap: int = 50

    # Retrieval
    top_k: int = 5

    # LLM
    llm_model: str = "gpt-4o-mini"
    temperature: float = 0.0

    class Config:
        env_file = ".env"


settings = Settings()
'''

    if framework == "langchain":
        chain_py = '''"""RAG Chain Implementation with LangChain."""
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI
from .config import settings
from .vectorstore import get_vectorstore


def create_rag_chain():
    """Create RAG chain with retrieval."""
    vectorstore = get_vectorstore()
    retriever = vectorstore.as_retriever(
        search_kwargs={"k": settings.top_k}
    )

    llm = ChatOpenAI(
        model=settings.llm_model,
        temperature=settings.temperature,
    )

    chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
    )

    return chain


def query(question: str) -> dict:
    """Query the RAG system."""
    chain = create_rag_chain()
    result = chain.invoke({"query": question})

    return {
        "answer": result["result"],
        "sources": [doc.metadata for doc in result["source_documents"]],
    }
'''
    else:  # llamaindex
        chain_py = '''"""RAG Chain Implementation with LlamaIndex."""
from llama_index.core import VectorStoreIndex, Settings
from llama_index.llms.openai import OpenAI
from .config import settings
from .vectorstore import get_vectorstore


def create_rag_engine():
    """Create RAG query engine."""
    Settings.llm = OpenAI(
        model=settings.llm_model,
        temperature=settings.temperature,
    )

    vectorstore = get_vectorstore()
    index = VectorStoreIndex.from_vector_store(vectorstore)

    return index.as_query_engine(similarity_top_k=settings.top_k)


def query(question: str) -> dict:
    """Query the RAG system."""
    engine = create_rag_engine()
    response = engine.query(question)

    return {
        "answer": str(response),
        "sources": [node.metadata for node in response.source_nodes],
    }
'''

    vectorstore_templates = {
        "chromadb": '''"""ChromaDB Vector Store."""
import chromadb
from chromadb.config import Settings as ChromaSettings
from .config import settings


def get_vectorstore():
    """Get ChromaDB client and collection."""
    client = chromadb.Client(ChromaSettings(
        anonymized_telemetry=False,
        persist_directory="./.chroma"
    ))

    collection = client.get_or_create_collection(
        name=settings.collection_name,
    )

    return collection
''',
        "qdrant": '''"""Qdrant Vector Store."""
from qdrant_client import QdrantClient
from .config import settings


def get_vectorstore():
    """Get Qdrant client."""
    client = QdrantClient(url=settings.vectordb_url)
    return client
''',
    }

    ingestion_py = '''"""Document Ingestion Pipeline."""
from pathlib import Path
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    DirectoryLoader,
    TextLoader,
    PyPDFLoader,
)
from .config import settings
from .embeddings import get_embeddings
from .vectorstore import get_vectorstore


def ingest_documents(directory: str) -> int:
    """Ingest documents from a directory."""
    # Load documents
    loader = DirectoryLoader(
        directory,
        glob="**/*",
        loader_cls=TextLoader,
        show_progress=True,
    )
    documents = loader.load()

    # Split into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    chunks = splitter.split_documents(documents)

    # Get embeddings and store
    embeddings = get_embeddings()
    vectorstore = get_vectorstore()

    # Add to vectorstore
    vectorstore.add_documents(chunks)

    return len(chunks)
'''

    requirements = {
        "langchain": f'''langchain>=0.1.0
langchain-openai>=0.0.5
langchain-community>=0.0.10
{"chromadb>=0.4.0" if vectordb == "chromadb" else ""}
{"qdrant-client>=1.7.0" if vectordb == "qdrant" else ""}
pydantic-settings>=2.0
python-dotenv>=1.0.0
pypdf>=3.0.0
''',
        "llamaindex": f'''llama-index>=0.10.0
llama-index-llms-openai>=0.1.0
{"llama-index-vector-stores-chroma>=0.1.0" if vectordb == "chromadb" else ""}
{"llama-index-vector-stores-qdrant>=0.1.0" if vectordb == "qdrant" else ""}
pydantic-settings>=2.0
python-dotenv>=1.0.0
''',
    }

    return {
        "success": True,
        "name": name,
        "framework": framework,
        "vectordb": vectordb,
        "files": {
            f"{name}/src/__init__.py": "",
            f"{name}/src/config.py": config_py,
            f"{name}/src/chain.py": chain_py,
            f"{name}/src/vectorstore.py": vectorstore_templates.get(vectordb, vectorstore_templates["chromadb"]),
            f"{name}/src/ingestion.py": ingestion_py,
            f"{name}/src/embeddings.py": '''"""Embedding model configuration."""
from langchain_openai import OpenAIEmbeddings
from .config import settings


def get_embeddings():
    """Get embedding model."""
    return OpenAIEmbeddings(model=settings.embedding_model)
''',
            f"{name}/scripts/ingest.py": '''"""Ingestion script."""
import sys
from src.ingestion import ingest_documents

if __name__ == "__main__":
    directory = sys.argv[1] if len(sys.argv) > 1 else "data"
    count = ingest_documents(directory)
    print(f"Ingested {count} chunks")
''',
            f"{name}/scripts/query.py": '''"""Interactive query script."""
from src.chain import query

if __name__ == "__main__":
    print("RAG Query Interface (type 'exit' to quit)")
    while True:
        question = input("\\nQuestion: ")
        if question.lower() == "exit":
            break
        result = query(question)
        print(f"\\nAnswer: {result['answer']}")
        print(f"Sources: {result['sources']}")
''',
            f"{name}/data/.gitkeep": "",
            f"{name}/requirements.txt": requirements.get(framework, requirements["langchain"]),
            f"{name}/.env.example": f'''OPENAI_API_KEY=sk-...
EMBEDDING_MODEL={embedding_model}
VECTORDB_URL=http://localhost:6333
''',
        },
        "patterns_reference": patterns[:300] if patterns else None,
        "next_steps": [
            f"1. cd {name} && pip install -r requirements.txt",
            "2. Copy .env.example to .env and configure",
            "3. Add documents to data/",
            "4. Run: python scripts/ingest.py",
            "5. Query: python scripts/query.py",
        ],
    }


def scaffold_mcp_server(
    name: str,
    tools: list[str],
    transport: str = "stdio",
) -> dict[str, Any]:
    """Generate MCP server template.

    Creates a FastMCP server with specified tools.

    Args:
        name: Server name
        tools: List of tool names to create
        transport: Transport type (stdio, http)

    Returns:
        MCP server scaffold with tool stubs
    """
    tool_definitions = ""
    for tool in tools:
        tool_definitions += f'''

@mcp.tool()
def {tool}() -> dict:
    """TODO: Implement {tool} tool.

    Returns:
        Tool result
    """
    return {{"status": "not_implemented", "tool": "{tool}"}}
'''

    server_py = f'''"""MCP Server: {name}"""
from fastmcp import FastMCP

mcp = FastMCP("{name}")

{tool_definitions}


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
'''

    pyproject = f'''[project]
name = "{name}"
version = "0.1.0"
description = "MCP Server for {name}"
requires-python = ">=3.11"
dependencies = [
    "fastmcp>=2.0",
]

[project.scripts]
{name} = "{name.replace("-", "_")}.server:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
'''

    return {
        "success": True,
        "name": name,
        "tools": tools,
        "files": {
            f"{name}/{name.replace('-', '_')}/__init__.py": "",
            f"{name}/{name.replace('-', '_')}/server.py": server_py,
            f"{name}/pyproject.toml": pyproject,
        },
        "next_steps": [
            f"1. cd {name}",
            "2. uv sync",
            f"3. claude mcp add {name} uv run {name}",
            "4. Implement your tools in server.py",
        ],
    }


# =============================================================================
# Documentation Tools
# =============================================================================


def generate_commit_message(
    changes_summary: str,
    change_type: str = "feat",
    scope: str | None = None,
    breaking: bool = False,
) -> dict[str, Any]:
    """Generate a conventional commit message.

    IMPORTANT: Never includes AI attribution, "Generated by Claude",
    or any Co-Authored-By headers.

    Args:
        changes_summary: Description of changes made
        change_type: Type (feat, fix, docs, style, refactor, perf, test, build, ci, chore)
        scope: Optional scope (e.g., api, auth, db)
        breaking: Whether this is a breaking change

    Returns:
        Formatted commit message ready for git commit
    """
    valid_types = ["feat", "fix", "docs", "style", "refactor", "perf", "test", "build", "ci", "chore"]

    if change_type not in valid_types:
        change_type = "chore"

    # Build commit message
    prefix = change_type
    if scope:
        prefix = f"{change_type}({scope})"
    if breaking:
        prefix = f"{prefix}!"

    # Clean up the summary
    summary = changes_summary.strip()
    if len(summary) > 72:
        # Split into subject and body
        subject = summary[:69] + "..."
        body = summary
    else:
        subject = summary
        body = None

    commit_message = f"{prefix}: {subject}"
    if body and body != subject:
        commit_message += f"\n\n{body}"

    return {
        "success": True,
        "commit_message": commit_message,
        "type": change_type,
        "scope": scope,
        "breaking": breaking,
        "instructions": [
            "Copy the commit message above",
            "Run: git commit -m '<message>'",
            "Or use heredoc for multi-line messages",
        ],
        "warning": "DO NOT add AI attribution or Co-Authored-By headers",
    }


# =============================================================================
# Research Tools
# =============================================================================


def lookup_docs(library: str, topic: str | None = None) -> dict[str, Any]:
    """Look up documentation for a library or tool.

    Returns instructions for using Context7 and Exa MCPs to find
    up-to-date documentation.

    Args:
        library: Library or framework name
        topic: Specific topic to focus on

    Returns:
        Instructions for documentation lookup
    """
    return {
        "success": True,
        "library": library,
        "topic": topic,
        "action": "lookup_documentation",
        "instructions": f"""Look up documentation for '{library}'{f" focusing on '{topic}'" if topic else ""}:

1. **Use Context7 MCP** (preferred for official docs):
   - First: mcp__upstash-context7-mcp__resolve-library-id(libraryName="{library}")
   - Then: mcp__upstash-context7-mcp__get-library-docs(context7CompatibleLibraryID=<id>{f', topic="{topic}"' if topic else ""})

2. **Use Exa MCP** (for code examples):
   - mcp__exa__get_code_context_exa(query="{library}{f' {topic}' if topic else ''} example code")

3. **Combine results** to provide comprehensive answer with:
   - Official documentation excerpts
   - Code examples
   - Best practices
   - Common pitfalls""",
        "mcp_tools": [
            "mcp__upstash-context7-mcp__resolve-library-id",
            "mcp__upstash-context7-mcp__get-library-docs",
            "mcp__exa__get_code_context_exa",
        ],
    }
