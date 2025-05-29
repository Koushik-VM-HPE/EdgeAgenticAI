from langgraph.prebuilt import create_react_agent
from langchain_ollama import ChatOllama
from langchain_core.tools import StructuredTool
from utils import extract_ai_message_content

# Import Kubernetes tools directly
from basicTools import (
    list_pods_in_namespace,
    list_deployments_in_namespace,
    rollout_restart_deployment,
    get_deployment_logs
)

model = ChatOllama(
    model = "mistral-nemo:12b",
)

def check_weather(location: str) -> str:
    '''Return the weather forecast for the specified location.'''
    return f"It's always sunny in {location}, about 40 Celsius."

# Create structured tools for LangChain - using the imported functions directly
tools = [
    StructuredTool.from_function(check_weather),
    StructuredTool.from_function(list_pods_in_namespace),
    StructuredTool.from_function(list_deployments_in_namespace),
    StructuredTool.from_function(rollout_restart_deployment),
    StructuredTool.from_function(get_deployment_logs),
]

graph = create_react_agent(
    model,
    tools=tools,
    prompt="""You are a helpful assistant with Kubernetes management capabilities.
You can check the weather and interact with Kubernetes clusters using the provided tools:

1. check_weather(location): Get the weather for a location.
2. list_pods_in_namespace(namespace="default"): List all pods in a K8s namespace.
3. list_deployments_in_namespace(namespace="default"): List all deployments in a K8s namespace.
4. rollout_restart_deployment(deployment_name, namespace="default"): Restart a K8s deployment. can be used during any temporary issues.
5. get_deployment_logs(deployment_name, namespace="default", hours=1, tail_lines=None): Get logs from all pods in a deployment.

""",
)

# Example usage
if __name__ == "__main__":
    # You can modify this to test different prompts
    # inputs = {"messages": [{"role": "user", "content": "check the status of 'infinite-pod' deployment in the 'default' namespace, please check the logs of the deployment to be sure that everything is running smoothly. In case of any issue restart the deployment with the given tools and see if that improves the situation."}]}
    inputs = {"messages": [{"role": "user", "content": "rollout restart the dpeloyment with name 'infinite-pod' in default using the tools provided"}]}


    # Store all chunks to extract the final response
    chunks = []
    for chunk in graph.stream(inputs, stream_mode="updates"):
        print(chunk)
        chunks.append(chunk)
    
    # Extract and print just the final AI response
    final_response = None
    for chunk in reversed(chunks):
        if 'agent' in chunk:
            final_response = extract_ai_message_content(chunk)
            if final_response:
                break
    
    # Print the final response in a clean format
    if final_response:
        print("\n===== FINAL RESPONSE =====")
        print(final_response)
        print("=========================\n")
    else:
        print("No response was generated.")

