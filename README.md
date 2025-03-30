# OWUI-Docker-Compose-Generation-Agent

An AI-powered tool for generating customized Docker Compose files for Open WebUI.

## Overview

This tool helps you generate a tailored Docker Compose configuration for Open WebUI using a conversational AI interface. It leverages OpenAI's GPT models to provide an intelligent, guided experience for creating your custom deployment.

## Features

- Fully conversational AI-driven configuration process
- Customizable database options (SQLite or PostgreSQL)
- Vector database selection for RAG (Chroma, Milvus, Qdrant, OpenSearch, PGVector)
- Support for additional services like Redis
- Authentication configuration options
- API integration settings
- Flexible environment variable handling (embedded or separate file)
- Complete Docker Compose generation with all necessary services and volumes

## Prerequisites

- Python 3.7+
- Docker and Docker Compose
- OpenAI API key

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/OWUI-Docker-Compose-Generation-Agent.git
   cd OWUI-Docker-Compose-Generation-Agent
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your OpenAI API key in a `.env` file:
   ```
   OPENAI_API_KEY=your-api-key-here
   ```

4. Make the generator script executable:
   ```
   chmod +x generate.py
   ```

## Usage

Run the generator:

```
python generate.py
```

Follow the conversational prompts to describe your preferred configuration. The AI will ask you about:

1. Environment variable placement (embedded or separate file)
2. Database preferences (SQLite or PostgreSQL)
3. Vector database selection for RAG
4. Additional services like Redis
5. Authentication options
6. API integrations
7. Other customizations

Once the conversation is complete, the tool will generate:
- `generated/docker-compose.yaml` - Your customized Docker Compose file
- `generated/.env.generated` - Environment variables file (if requested)

## Command Line Options

```
python generate.py --reference repo-docs  # Use repo docs instead of static reference
python generate.py --env-in-file          # Default to separate env file
```

## Running Your Open WebUI Deployment

After generating the configuration files, start your deployment with:

```
cd generated
docker-compose up -d
```

## References

This tool uses documentation from:
- Static reference files in the `static-ref` directory
- Open WebUI documentation in the `repo-docs/open-webui-docs` directory (added as a Git submodule)
