#!/usr/bin/env python3
import os
import json
import yaml
import openai
import argparse
from pathlib import Path
import sys

# Configuration paths
STATIC_REF_DIR = Path("static-ref")
REPO_DOCS_DIR = Path("repo-docs/open-webui-docs")
GENERATED_DIR = Path("generated")

# Ensure the generated directory exists
GENERATED_DIR.mkdir(exist_ok=True)

def load_env_vars():
    """Load OpenAI API key from .env file if it exists"""
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    if key == "OPENAI_API_KEY":
                        # Remove quotes if present
                        value = value.strip('"\'')
                        os.environ[key] = value
                        return value
    return None

def get_openai_key():
    """Get OpenAI API key from environment or user input"""
    api_key = os.environ.get("OPENAI_API_KEY") or load_env_vars()
    
    if not api_key:
        print("OpenAI API key not found in environment or .env file.")
        api_key = input("Please enter your OpenAI API key: ").strip()
        os.environ["OPENAI_API_KEY"] = api_key
        
    return api_key

def load_documentation():
    """Load documentation from static reference or repo docs"""
    env_vars_content = ""
    sample_compose_content = ""
    
    # Try static reference first (default)
    env_vars_path = STATIC_REF_DIR / "env-variables.md"
    sample_compose_path = STATIC_REF_DIR / "sample-docker-compose.yaml"
    
    if env_vars_path.exists() and sample_compose_path.exists():
        with open(env_vars_path, 'r') as f:
            env_vars_content = f.read()
        with open(sample_compose_path, 'r') as f:
            sample_compose_content = f.read()
    else:
        # Fall back to repo docs
        env_vars_path = REPO_DOCS_DIR / "docs/getting-started/env-configuration.md"
        sample_compose_path = REPO_DOCS_DIR / "docs/getting-started/installation/docker-compose.md"
        
        if env_vars_path.exists():
            with open(env_vars_path, 'r') as f:
                env_vars_content = f.read()
        
        if sample_compose_path.exists():
            with open(sample_compose_path, 'r') as f:
                sample_compose_content = f.read()
    
    return env_vars_content, sample_compose_content

def generate_docker_compose(api_key, reference_source="static", env_vars_in_file=True):
    """Generate Docker Compose file using OpenAI"""
    openai.api_key = api_key
    
    # Load documentation
    env_vars_content, sample_compose_content = load_documentation()
    
    # Initial system prompt
    system_prompt = f"""You are an expert on OpenWebUI configuration and Docker Compose. 
Your task is to help the user generate a customized Docker Compose file for OpenWebUI.
You should ask the user a series of questions about their preferences for:
1. Database configuration (SQLite or PostgreSQL)
2. Vector database for RAG (Chroma, Milvus, Qdrant, OpenSearch, PGVector)
3. Additional services like Redis
4. Authentication options
5. API integrations
6. Other customizations

Based on their answers, you'll generate a complete Docker Compose file with all necessary services and volumes.
You'll also generate environment variables, which can be either embedded in the Docker Compose file or in a separate .env.generated file.

Here's reference documentation on OpenWebUI environment variables:
{env_vars_content[:4000]}... [truncated]

Here's a sample Docker Compose file for OpenWebUI:
{sample_compose_content[:2000]}... [truncated]
"""

    # Start conversation with the user
    messages = [{"role": "system", "content": system_prompt}]
    
    # Initial message to user
    initial_message = """I'll help you generate a customized Docker Compose file for OpenWebUI. 
I'll ask you a series of questions about your preferences, and then generate the appropriate configuration.

First, would you prefer to have environment variables embedded directly in the Docker Compose file, or in a separate .env.generated file?"""
    
    messages.append({"role": "assistant", "content": initial_message})
    print("AI: " + initial_message)
    
    # Main conversation loop
    while True:
        user_input = input("\nYou: ")
        
        if user_input.lower() in ['exit', 'quit', 'q']:
            print("Exiting generator.")
            break
        
        messages.append({"role": "user", "content": user_input})
        
        try:
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=messages,
                max_tokens=1500
            )
            
            ai_response = response.choices[0].message.content
            messages.append({"role": "assistant", "content": ai_response})
            print("\nAI: " + ai_response)
            
            # Check if we've gathered enough information to generate the Docker Compose file
            if "I'll now generate your Docker Compose file" in ai_response:
                # Generate the final Docker Compose file
                final_prompt = """Based on our conversation, please generate:
1. A complete Docker Compose file for OpenWebUI with all the configurations we discussed
2. Environment variables (either embedded or in a separate file as requested)

Format your response as follows:
```docker-compose
# Docker Compose content here
```

If environment variables should be in a separate file:
```env
# Environment variables content here
```

Make sure to include all necessary services, volumes, and environment variables based on the user's preferences."""
                
                messages.append({"role": "user", "content": final_prompt})
                
                response = openai.chat.completions.create(
                    model="gpt-4",
                    messages=messages,
                    max_tokens=2000
                )
                
                generation_response = response.choices[0].message.content
                
                # Extract Docker Compose content
                docker_compose_content = ""
                env_content = ""
                
                if "```docker-compose" in generation_response:
                    docker_compose_parts = generation_response.split("```docker-compose")
                    if len(docker_compose_parts) > 1:
                        docker_compose_content = docker_compose_parts[1].split("```")[0].strip()
                
                if "```env" in generation_response:
                    env_parts = generation_response.split("```env")
                    if len(env_parts) > 1:
                        env_content = env_parts[1].split("```")[0].strip()
                
                # If no Docker Compose content was found, try alternative format
                if not docker_compose_content and "```yaml" in generation_response:
                    yaml_parts = generation_response.split("```yaml")
                    if len(yaml_parts) > 1:
                        docker_compose_content = yaml_parts[1].split("```")[0].strip()
                
                # Save Docker Compose file
                docker_compose_path = GENERATED_DIR / "docker-compose.yaml"
                with open(docker_compose_path, 'w') as f:
                    f.write(docker_compose_content)
                
                # Save environment variables if needed
                if env_content:
                    env_path = GENERATED_DIR / ".env.generated"
                    with open(env_path, 'w') as f:
                        f.write(env_content)
                    print(f"\nEnvironment variables saved to {env_path}")
                
                print(f"\nDocker Compose file generated at {docker_compose_path}")
                print("\nTo start your OpenWebUI stack, run:")
                print(f"cd {GENERATED_DIR} && docker-compose up -d")
                
                # Ask if the user wants to see the generated files
                show_files = input("\nWould you like to see the generated files? (yes/no): ")
                if show_files.lower() in ['yes', 'y']:
                    print("\n--- Docker Compose File ---")
                    print(docker_compose_content)
                    
                    if env_content:
                        print("\n--- Environment Variables ---")
                        print(env_content)
                
                break
            
        except Exception as e:
            print(f"Error: {e}")
            break

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Generate Docker Compose for OpenWebUI")
    parser.add_argument("--reference", choices=["static", "repo-docs"], default="static",
                        help="Reference source to use (static or repo-docs)")
    parser.add_argument("--env-in-file", action="store_true", 
                        help="Store environment variables in a separate file")
    args = parser.parse_args()
    
    print("OpenWebUI Docker Compose Generator")
    print("----------------------------------")
    
    # Get OpenAI API key
    api_key = get_openai_key()
    
    if not api_key:
        print("Error: OpenAI API key is required.")
        sys.exit(1)
    
    # Generate Docker Compose
    generate_docker_compose(api_key, args.reference, args.env_in_file)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nGenerator interrupted. Exiting.")
        sys.exit(0)
