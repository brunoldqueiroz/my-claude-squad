"""Tests for command_tools module."""

import pytest
from orchestrator.command_tools import (
    create_pipeline,
    analyze_query,
    analyze_data,
    create_dockerfile,
    create_k8s_manifest,
    scaffold_rag,
    scaffold_mcp_server,
    generate_commit_message,
    lookup_docs,
)


class TestCreatePipeline:
    """Tests for create_pipeline function."""

    def test_basic_pipeline(self):
        """Test creating a basic pipeline."""
        result = create_pipeline(source="api", target="snowflake")

        assert result["success"] is True
        assert result["source"] == "api"
        assert result["target"] == "snowflake"
        assert result["pipeline_name"] == "pipeline"
        assert result["pattern"] == "full_refresh"
        assert len(result["files"]) > 0
        assert "next_steps" in result

    def test_pipeline_with_custom_name(self):
        """Test pipeline with custom name."""
        result = create_pipeline(source="s3", target="redshift", name="my_etl")

        assert result["pipeline_name"] == "my_etl"
        assert "my_etl/src/extract.py" in result["files"]
        assert "my_etl/src/transform.py" in result["files"]
        assert "my_etl/src/load.py" in result["files"]

    def test_incremental_pipeline(self):
        """Test incremental pipeline pattern."""
        result = create_pipeline(source="postgresql", target="s3", incremental=True)

        assert result["pattern"] == "incremental"

    def test_pipeline_with_schedule(self):
        """Test pipeline with Airflow DAG schedule."""
        result = create_pipeline(
            source="api", target="snowflake",
            name="daily_etl", schedule="0 6 * * *"
        )

        assert "daily_etl/dags/daily_etl_dag.py" in result["files"]
        dag_content = result["files"]["daily_etl/dags/daily_etl_dag.py"]
        assert "schedule_interval" in dag_content
        assert "0 6 * * *" in dag_content

    def test_pipeline_without_tests(self):
        """Test pipeline without test files."""
        result = create_pipeline(source="api", target="s3", with_tests=False)

        test_files = [k for k in result["files"].keys() if "test_" in k]
        assert len(test_files) == 0

    def test_pipeline_with_tests(self):
        """Test pipeline with test files."""
        result = create_pipeline(source="api", target="s3", with_tests=True)

        assert "pipeline/tests/test_extract.py" in result["files"]
        assert "pipeline/tests/test_transform.py" in result["files"]
        assert "pipeline/tests/test_load.py" in result["files"]

    def test_pipeline_requirements_source_deps(self):
        """Test pipeline requirements include source dependencies."""
        result = create_pipeline(source="postgresql", target="snowflake")

        reqs = result["files"]["pipeline/requirements.txt"]
        assert "psycopg2" in reqs

    def test_pipeline_requirements_target_deps(self):
        """Test pipeline requirements include target dependencies."""
        result = create_pipeline(source="api", target="snowflake")

        reqs = result["files"]["pipeline/requirements.txt"]
        assert "snowflake-connector-python" in reqs

    def test_pipeline_file_count(self):
        """Test that file_count matches actual files."""
        result = create_pipeline(source="api", target="s3")

        assert result["file_count"] == len(result["files"])


class TestAnalyzeQuery:
    """Tests for analyze_query function."""

    def test_detect_select_star(self):
        """Test detection of SELECT * usage."""
        result = analyze_query("SELECT * FROM orders")

        assert result["success"] is True
        issues = [i for i in result["issues"] if i["title"] == "SELECT * usage"]
        assert len(issues) == 1
        assert issues[0]["severity"] == "medium"

    def test_detect_function_on_column(self):
        """Test detection of functions on columns in WHERE."""
        result = analyze_query("SELECT id FROM orders WHERE YEAR(created_at) = 2024")

        issues = [i for i in result["issues"] if "Function" in i["title"]]
        assert len(issues) >= 1
        assert issues[0]["severity"] == "high"

    def test_detect_missing_where(self):
        """Test detection of missing WHERE clause."""
        result = analyze_query("SELECT id, name FROM users")

        issues = [i for i in result["issues"] if i["title"] == "No WHERE clause"]
        assert len(issues) == 1

    def test_detect_distinct(self):
        """Test detection of DISTINCT usage."""
        result = analyze_query("SELECT DISTINCT customer_id FROM orders")

        issues = [i for i in result["issues"] if i["title"] == "DISTINCT usage"]
        assert len(issues) == 1

    def test_detect_or_conditions(self):
        """Test detection of OR conditions."""
        result = analyze_query("SELECT * FROM orders WHERE status = 'active' OR status = 'pending'")

        issues = [i for i in result["issues"] if i["title"] == "OR conditions"]
        assert len(issues) == 1

    def test_clean_query_no_issues(self):
        """Test a well-structured query has fewer issues."""
        result = analyze_query("SELECT id, name FROM users WHERE status = 'active'")

        # Should not have SELECT * or missing WHERE issues
        issues_titles = [i["title"] for i in result["issues"]]
        assert "SELECT * usage" not in issues_titles
        assert "No WHERE clause" not in issues_titles

    def test_query_preview_truncation(self):
        """Test long query preview is truncated."""
        long_query = "SELECT " + ", ".join([f"col{i}" for i in range(100)]) + " FROM table"
        result = analyze_query(long_query)

        assert len(result["query_preview"]) <= 203  # 200 + "..."

    def test_suggestions_always_present(self):
        """Test that suggestions are always provided."""
        result = analyze_query("SELECT id FROM table")

        assert len(result["suggestions"]) > 0
        assert len(result["next_steps"]) > 0


class TestAnalyzeData:
    """Tests for analyze_data function."""

    def test_basic_analysis_request(self):
        """Test basic data analysis request."""
        result = analyze_data("/path/to/data.csv")

        assert result["success"] is True
        assert result["action"] == "analyze_data_file"
        assert result["path"] == "/path/to/data.csv"
        assert result["sample_size"] == 1000

    def test_custom_sample_size(self):
        """Test custom sample size."""
        result = analyze_data("/path/to/data.parquet", sample_size=500)

        assert result["sample_size"] == 500

    def test_instructions_included(self):
        """Test that analysis instructions are included."""
        result = analyze_data("/data.json")

        assert "Schema Analysis" in result["instructions"]
        assert "Data Quality" in result["instructions"]
        assert "Statistical Summary" in result["instructions"]

    def test_output_format_schema(self):
        """Test that output format is specified."""
        result = analyze_data("/data.csv")

        assert "schema" in result["output_format"]
        assert "quality" in result["output_format"]
        assert "statistics" in result["output_format"]


class TestCreateDockerfile:
    """Tests for create_dockerfile function."""

    def test_python_dockerfile(self):
        """Test Python Dockerfile generation."""
        result = create_dockerfile(project_type="python")

        assert result["success"] is True
        assert result["project_type"] == "python"
        assert "Dockerfile" in result["files"]
        assert ".dockerignore" in result["files"]
        assert "docker-compose.yml" in result["files"]

    def test_python_dockerfile_content(self):
        """Test Python Dockerfile has proper content."""
        result = create_dockerfile(project_type="python", python_version="3.12")

        dockerfile = result["files"]["Dockerfile"]
        assert "python:3.12-slim" in dockerfile
        assert "FROM" in dockerfile
        assert "HEALTHCHECK" in dockerfile
        assert "useradd" in dockerfile  # Non-root user

    def test_node_dockerfile(self):
        """Test Node.js Dockerfile generation."""
        result = create_dockerfile(project_type="node")

        assert result["project_type"] == "node"
        dockerfile = result["files"]["Dockerfile"]
        assert "node:" in dockerfile
        assert "npm" in dockerfile

    def test_unsupported_project_type(self):
        """Test unsupported project type."""
        result = create_dockerfile(project_type="rust")

        assert result["success"] is True
        assert "# Unsupported" in result["files"]["Dockerfile"]

    def test_dockerignore_content(self):
        """Test .dockerignore has expected content."""
        result = create_dockerfile()

        dockerignore = result["files"][".dockerignore"]
        assert ".git" in dockerignore
        assert "__pycache__" in dockerignore
        assert ".venv" in dockerignore

    def test_features_listed(self):
        """Test that features are listed."""
        result = create_dockerfile()

        assert len(result["features"]) > 0
        assert "Multi-stage build" in result["features"][0]


class TestCreateK8sManifest:
    """Tests for create_k8s_manifest function."""

    def test_basic_manifest(self):
        """Test basic Kubernetes manifest generation."""
        result = create_k8s_manifest(app_name="myapp")

        assert result["success"] is True
        assert result["app_name"] == "myapp"
        assert "k8s/deployment.yaml" in result["files"]
        assert "k8s/service.yaml" in result["files"]
        assert "k8s/configmap.yaml" in result["files"]
        assert "k8s/hpa.yaml" in result["files"]
        assert "k8s/kustomization.yaml" in result["files"]

    def test_deployment_content(self):
        """Test deployment YAML content."""
        result = create_k8s_manifest(app_name="testapp", replicas=3)

        deployment = result["files"]["k8s/deployment.yaml"]
        assert "replicas: 3" in deployment
        assert "testapp" in deployment
        assert "livenessProbe" in deployment
        assert "readinessProbe" in deployment

    def test_custom_port(self):
        """Test custom port in manifest."""
        result = create_k8s_manifest(app_name="api", port=3000)

        deployment = result["files"]["k8s/deployment.yaml"]
        assert "containerPort: 3000" in deployment

    def test_custom_image(self):
        """Test custom image in manifest."""
        result = create_k8s_manifest(app_name="myapp", image="registry.io/myapp:v1")

        deployment = result["files"]["k8s/deployment.yaml"]
        assert "registry.io/myapp:v1" in deployment

    def test_resource_presets_small(self):
        """Test small resource preset."""
        result = create_k8s_manifest(app_name="myapp", resources_preset="small")

        assert result["resources"]["cpu"] == "100m"
        assert result["resources"]["memory"] == "128Mi"

    def test_resource_presets_medium(self):
        """Test medium resource preset."""
        result = create_k8s_manifest(app_name="myapp", resources_preset="medium")

        assert result["resources"]["cpu"] == "250m"
        assert result["resources"]["memory"] == "256Mi"

    def test_resource_presets_large(self):
        """Test large resource preset."""
        result = create_k8s_manifest(app_name="myapp", resources_preset="large")

        assert result["resources"]["cpu"] == "500m"
        assert result["resources"]["memory"] == "512Mi"

    def test_hpa_scaling(self):
        """Test HPA autoscaling configuration."""
        result = create_k8s_manifest(app_name="myapp", replicas=2)

        hpa = result["files"]["k8s/hpa.yaml"]
        assert "minReplicas: 2" in hpa
        assert "maxReplicas: 10" in hpa  # 2 * 5


class TestScaffoldRag:
    """Tests for scaffold_rag function."""

    def test_basic_rag_scaffold(self):
        """Test basic RAG scaffold generation."""
        result = scaffold_rag(name="my_rag")

        assert result["success"] is True
        assert result["name"] == "my_rag"
        assert result["framework"] == "langchain"
        assert result["vectordb"] == "chromadb"

    def test_rag_files_created(self):
        """Test RAG scaffold creates expected files."""
        result = scaffold_rag(name="docbot")

        assert "docbot/src/config.py" in result["files"]
        assert "docbot/src/chain.py" in result["files"]
        assert "docbot/src/vectorstore.py" in result["files"]
        assert "docbot/src/ingestion.py" in result["files"]
        assert "docbot/requirements.txt" in result["files"]

    def test_rag_with_qdrant(self):
        """Test RAG scaffold with Qdrant."""
        result = scaffold_rag(name="qa", vectordb="qdrant")

        assert result["vectordb"] == "qdrant"
        vectorstore = result["files"]["qa/src/vectorstore.py"]
        assert "QdrantClient" in vectorstore

    def test_rag_with_llamaindex(self):
        """Test RAG scaffold with LlamaIndex."""
        result = scaffold_rag(name="bot", framework="llamaindex")

        assert result["framework"] == "llamaindex"
        chain = result["files"]["bot/src/chain.py"]
        assert "llama_index" in chain

    def test_rag_config_embedding_model(self):
        """Test RAG config uses specified embedding model."""
        result = scaffold_rag(name="test", embedding_model="text-embedding-ada-002")

        config = result["files"]["test/src/config.py"]
        assert "text-embedding-ada-002" in config

    def test_rag_scripts_included(self):
        """Test RAG scaffold includes helper scripts."""
        result = scaffold_rag(name="rag")

        assert "rag/scripts/ingest.py" in result["files"]
        assert "rag/scripts/query.py" in result["files"]


class TestScaffoldMcpServer:
    """Tests for scaffold_mcp_server function."""

    def test_basic_mcp_scaffold(self):
        """Test basic MCP server scaffold."""
        result = scaffold_mcp_server(name="my-mcp", tools=["search", "fetch"])

        assert result["success"] is True
        assert result["name"] == "my-mcp"
        assert result["tools"] == ["search", "fetch"]

    def test_mcp_server_file_structure(self):
        """Test MCP server file structure."""
        result = scaffold_mcp_server(name="test-mcp", tools=["query"])

        assert "test-mcp/test_mcp/server.py" in result["files"]
        assert "test-mcp/pyproject.toml" in result["files"]
        assert "test-mcp/test_mcp/__init__.py" in result["files"]

    def test_mcp_server_tools_defined(self):
        """Test MCP server has tool definitions."""
        result = scaffold_mcp_server(name="api-mcp", tools=["get_data", "post_data"])

        server = result["files"]["api-mcp/api_mcp/server.py"]
        assert "@mcp.tool()" in server
        assert "def get_data" in server
        assert "def post_data" in server

    def test_mcp_pyproject_content(self):
        """Test MCP pyproject.toml content."""
        result = scaffold_mcp_server(name="demo-mcp", tools=["test"])

        pyproject = result["files"]["demo-mcp/pyproject.toml"]
        assert 'name = "demo-mcp"' in pyproject
        assert "fastmcp" in pyproject


class TestGenerateCommitMessage:
    """Tests for generate_commit_message function."""

    def test_basic_commit_message(self):
        """Test basic commit message generation."""
        result = generate_commit_message(
            changes_summary="Add user authentication",
            change_type="feat"
        )

        assert result["success"] is True
        assert result["commit_message"] == "feat: Add user authentication"
        assert result["type"] == "feat"

    def test_commit_message_with_scope(self):
        """Test commit message with scope."""
        result = generate_commit_message(
            changes_summary="Fix login bug",
            change_type="fix",
            scope="auth"
        )

        assert result["commit_message"] == "fix(auth): Fix login bug"
        assert result["scope"] == "auth"

    def test_breaking_change(self):
        """Test breaking change commit message."""
        result = generate_commit_message(
            changes_summary="Remove deprecated API",
            change_type="feat",
            breaking=True
        )

        assert result["commit_message"].startswith("feat!:")
        assert result["breaking"] is True

    def test_breaking_change_with_scope(self):
        """Test breaking change with scope."""
        result = generate_commit_message(
            changes_summary="Change API response format",
            change_type="feat",
            scope="api",
            breaking=True
        )

        assert result["commit_message"].startswith("feat(api)!:")

    def test_invalid_change_type(self):
        """Test invalid change type defaults to chore."""
        result = generate_commit_message(
            changes_summary="Miscellaneous update",
            change_type="invalid"
        )

        assert result["type"] == "chore"

    def test_long_summary_truncation(self):
        """Test long summary is truncated properly."""
        long_summary = "A" * 100
        result = generate_commit_message(changes_summary=long_summary)

        # Subject line should be truncated
        lines = result["commit_message"].split("\n")
        assert len(lines[0]) <= 80  # type: + subject

    def test_warning_about_ai_attribution(self):
        """Test warning about AI attribution is present."""
        result = generate_commit_message(changes_summary="Update docs")

        assert "AI attribution" in result["warning"]
        assert "Co-Authored-By" in result["warning"]

    def test_all_valid_change_types(self):
        """Test all valid change types are accepted."""
        valid_types = ["feat", "fix", "docs", "style", "refactor", "perf", "test", "build", "ci", "chore"]

        for change_type in valid_types:
            result = generate_commit_message(
                changes_summary="test",
                change_type=change_type
            )
            assert result["type"] == change_type


class TestLookupDocs:
    """Tests for lookup_docs function."""

    def test_basic_lookup(self):
        """Test basic documentation lookup."""
        result = lookup_docs(library="pandas")

        assert result["success"] is True
        assert result["library"] == "pandas"
        assert result["action"] == "lookup_documentation"

    def test_lookup_with_topic(self):
        """Test documentation lookup with topic."""
        result = lookup_docs(library="react", topic="hooks")

        assert result["library"] == "react"
        assert result["topic"] == "hooks"
        assert "hooks" in result["instructions"]

    def test_mcp_tools_referenced(self):
        """Test that MCP tools are referenced."""
        result = lookup_docs(library="numpy")

        assert "mcp__upstash-context7-mcp__resolve-library-id" in result["mcp_tools"]
        assert "mcp__upstash-context7-mcp__get-library-docs" in result["mcp_tools"]
        assert "mcp__exa__get_code_context_exa" in result["mcp_tools"]

    def test_instructions_contain_library_name(self):
        """Test instructions contain the library name."""
        result = lookup_docs(library="tensorflow")

        assert "tensorflow" in result["instructions"]
