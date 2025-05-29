#!/usr/bin/env python3
"""
Basic Kubernetes tools for interacting with Kubernetes clusters using a specified kubeconfig file.

This module provides functions to:
1. List pods in a namespace with their status information
2. List deployments in a namespace with their status information
3. Rollout restart deployments in a namespace
4. Get logs from pods in a deployment

These functions are designed to be used programmatically by both humans and LLM agents.
"""

import os
import sys
import datetime
from kubernetes import client, config

# Get kubeconfig path from environment variable with fallback to default path
KUBECONFIG_PATH = "C:/Users/mandapak/Desktop/wslk3s.yaml"


def list_pods_in_namespace(namespace="default"):
    """
    Lists all pods in a specified Kubernetes namespace using the kubeconfig from KUBECONFIG env var.
    
    Args:
        namespace (str): Kubernetes namespace name (defaults to 'default')
        
    Returns:
        list: List of pod information dictionaries containing name, status, and IP
        
    Example:
        >>> pods = list_pods_in_namespace('kube-system')
        >>> for pod in pods:
        >>>     print(f"Pod: {pod['name']}, Status: {pod['status']}")
    """
    
    try:
        # Check if kubeconfig file exists
        if not os.path.isfile(KUBECONFIG_PATH):
            print(f"Error: Kubeconfig file not found at {KUBECONFIG_PATH}")
            return []
        
        # Load kubeconfig from specified path
        config.load_kube_config(config_file=KUBECONFIG_PATH)
        
        # Create API client
        v1 = client.CoreV1Api()
        
        try:
            # Call API to get pods in the namespace
            pod_list = v1.list_namespaced_pod(namespace=namespace)
            
            # Format results
            pods = []
            for pod in pod_list.items:
                pod_info = {
                    "name": pod.metadata.name,
                    "status": pod.status.phase,
                    "ip": pod.status.pod_ip
                }
                pods.append(pod_info)
            
            return pods
            
        except client.rest.ApiException as e:
            if e.status == 404:
                print(f"Error: Namespace '{namespace}' not found")
            else:
                print(f"API Error: {e}")
            return []
    
    except Exception as e:
        print(f"Error: {e}")
        return []


def list_deployments_in_namespace(namespace="default"):
    """
    Lists all deployments in a specified Kubernetes namespace with status information.
    
    This function connects to a Kubernetes cluster using the kubeconfig from KUBECONFIG env var
    and retrieves detailed information about all deployments in the specified namespace,
    including their readiness status.
    
    Args:
        namespace (str): Kubernetes namespace name (defaults to 'default')
        
    Returns:
        list: List of deployment information dictionaries containing:
            - name: Name of the deployment
            - ready_replicas: Number of ready replicas
            - total_replicas: Total desired replicas
            - available_replicas: Number of available replicas
            - up_to_date_replicas: Number of up-to-date replicas
            - image: Container images used by the deployment (list)
            - age_minutes: Age of the deployment in minutes (float)
            - is_healthy: Boolean indicating if all replicas are ready and available
            
    Example:
        >>> deployments = list_deployments_in_namespace('/path/to/kubeconfig', 'default')
        >>> for deploy in deployments:
        >>>     print(f"Deployment: {deploy['name']}, Ready: {deploy['ready_replicas']}/{deploy['total_replicas']}")
    """
    try:
        # Check if kubeconfig file exists
        if not os.path.isfile(KUBECONFIG_PATH):
            print(f"Error: Kubeconfig file not found at {KUBECONFIG_PATH}")
            return []
        
        # Load kubeconfig from specified path
        config.load_kube_config(config_file=KUBECONFIG_PATH)
        
        # Create API client
        apps_v1 = client.AppsV1Api()
        
        try:
            # Call API to get deployments in the namespace
            deployment_list = apps_v1.list_namespaced_deployment(namespace=namespace)
            
            # Format results
            deployments = []
            for deployment in deployment_list.items:
                # Extract container images
                images = []
                if deployment.spec and deployment.spec.template and deployment.spec.template.spec:
                    for container in deployment.spec.template.spec.containers:
                        images.append(container.image)
                
                # Calculate age in minutes
                age_minutes = 0
                if deployment.metadata.creation_timestamp:
                    now = datetime.datetime.now(deployment.metadata.creation_timestamp.tzinfo)
                    age_seconds = (now - deployment.metadata.creation_timestamp).total_seconds()
                    age_minutes = age_seconds / 60  # Convert to minutes
                
                # Extract replica information
                total_replicas = deployment.spec.replicas if deployment.spec else 0
                ready_replicas = deployment.status.ready_replicas if deployment.status else 0
                available_replicas = deployment.status.available_replicas if deployment.status else 0
                up_to_date_replicas = deployment.status.updated_replicas if deployment.status else 0
                
                # Check if deployment is considered healthy
                is_healthy = (ready_replicas is not None and 
                             ready_replicas == total_replicas and 
                             available_replicas is not None and 
                             available_replicas == total_replicas)
                
                deployment_info = {
                    "name": deployment.metadata.name,
                    "ready_replicas": ready_replicas or 0,
                    "total_replicas": total_replicas,
                    "available_replicas": available_replicas or 0,
                    "up_to_date_replicas": up_to_date_replicas or 0,
                    "image": images,
                    "age_minutes": round(age_minutes, 1),  # Round to 1 decimal place for readability
                    "is_healthy": is_healthy
                }
                deployments.append(deployment_info)
            
            return deployments
            
        except client.rest.ApiException as e:
            if e.status == 404:
                print(f"Error: Namespace '{namespace}' not found")
            else:
                print(f"API Error: {e}")
            return []
    
    except Exception as e:
        print(f"Error: {e}")
        return []


def rollout_restart_deployment(deployment_name, namespace="default"):
    """
    Performs a rollout restart on a specified Kubernetes deployment.
    
    This function performs the equivalent of 'kubectl rollout restart deployment/{name}',
    causing the deployment to gradually restart all its pods with new instances. This is
    useful for picking up configuration changes without changing the deployment spec.
    
    Args:
        deployment_name (str): Name of the deployment to restart
        namespace (str): Kubernetes namespace containing the deployment (defaults to 'default')
        
    Returns:
        dict: Result of the operation containing:
            - success: Boolean indicating if the restart was successfully initiated
            - message: Descriptive message about the operation result
            - deployment_name: Name of the targeted deployment
            - namespace: Namespace of the targeted deployment
            
    Example:
        >>> result = rollout_restart_deployment('/path/to/kubeconfig', 'my-app', 'default')
        >>> if result['success']:
        >>>     print(f"Successfully restarted deployment: {result['message']}")
        >>> else:
        >>>     print(f"Failed to restart deployment: {result['message']}")
    """
    try:
        # Check if kubeconfig file exists
        if not os.path.isfile(KUBECONFIG_PATH):
            return {
                "success": False,
                "message": f"Kubeconfig file not found at {KUBECONFIG_PATH}",
                "deployment_name": deployment_name,
                "namespace": namespace
            }
        
        # Load kubeconfig from specified path
        config.load_kube_config(config_file=KUBECONFIG_PATH)
        
        # Create API client
        apps_v1 = client.AppsV1Api()
        
        try:
            # First, get the deployment to verify it exists
            deployment = apps_v1.read_namespaced_deployment(name=deployment_name, namespace=namespace)
            
            # To perform a rollout restart, we need to add or update a restart annotation
            # Patch body with annotation update
            now = datetime.datetime.utcnow().isoformat() + "Z"  # RFC3339 format
            patch_body = {
                "spec": {
                    "template": {
                        "metadata": {
                            "annotations": {
                                "kubectl.kubernetes.io/restartedAt": now
                            }
                        }
                    }
                }
            }
            
            # Apply the patch to restart the deployment
            result = apps_v1.patch_namespaced_deployment(
                name=deployment_name,
                namespace=namespace,
                body=patch_body
            )
            
            # Return success information
            return {
                "success": True,
                "message": f"Deployment '{deployment_name}' in namespace '{namespace}' rollout restart initiated",
                "deployment_name": deployment_name, 
                "namespace": namespace
            }
            
        except client.rest.ApiException as e:
            if e.status == 404:
                return {
                    "success": False,
                    "message": f"Deployment '{deployment_name}' not found in namespace '{namespace}'",
                    "deployment_name": deployment_name,
                    "namespace": namespace
                }
            else:
                return {
                    "success": False,
                    "message": f"API Error: {e}",
                    "deployment_name": deployment_name,
                    "namespace": namespace
                }
    
    except Exception as e:
        return {
            "success": False,
            "message": f"Error: {e}",
            "deployment_name": deployment_name,
            "namespace": namespace
        }


def get_deployment_logs(deployment_name, namespace="default", hours=1, tail_lines=None):
    """
    Gets logs from all pods in a specified deployment for the past specified hours.
    
    This function identifies all pods belonging to a deployment and fetches their logs,
    making it easier to troubleshoot issues with specific deployments.
    
    Args:
        deployment_name (str): Name of the deployment
        namespace (str): Kubernetes namespace containing the deployment (defaults to 'default')
        hours (int): Number of hours of logs to retrieve (defaults to 1)
        tail_lines (int, optional): If specified, return only the last N lines of logs
        
    Returns:
        dict: Result containing:
            - success: Boolean indicating if logs were successfully retrieved
            - message: Descriptive message about the operation
            - logs: Dictionary mapping pod names to their logs
            - deployment_name: Name of the targeted deployment
            - namespace: Namespace of the targeted deployment
            
    Example:
        >>> result = get_deployment_logs('my-web-app', 'default', 2)
        >>> if result['success']:
        >>>     for pod_name, log in result['logs'].items():
        >>>         print(f"=== Logs for {pod_name} ===")
        >>>         print(log)
    """
    try:
        # Check if kubeconfig file exists
        if not os.path.isfile(KUBECONFIG_PATH):
            return {
                "success": False,
                "message": f"Kubeconfig file not found at {KUBECONFIG_PATH}",
                "logs": {},
                "deployment_name": deployment_name,
                "namespace": namespace
            }
        
        # Load kubeconfig from specified path
        config.load_kube_config(config_file=KUBECONFIG_PATH)
        
        # Create API clients
        apps_v1 = client.AppsV1Api()
        core_v1 = client.CoreV1Api()
        
        try:
            # First, get the deployment to verify it exists and get its selector
            deployment = apps_v1.read_namespaced_deployment(
                name=deployment_name, 
                namespace=namespace
            )
            
            # Extract the selector labels from the deployment
            selector = deployment.spec.selector.match_labels
            label_selector = ",".join([f"{k}={v}" for k, v in selector.items()])
            
            # Find all pods matching the deployment selector
            pods = core_v1.list_namespaced_pod(
                namespace=namespace,
                label_selector=label_selector
            )
            
            if not pods.items:
                return {
                    "success": False,
                    "message": f"No pods found for deployment '{deployment_name}' in namespace '{namespace}'",
                    "logs": {},
                    "deployment_name": deployment_name,
                    "namespace": namespace
                }
            
            # Calculate the timestamp for N hours ago
            since_seconds = int(hours * 3600)  # Convert hours to seconds
            
            # Get logs for each pod
            logs_dict = {}
            for pod in pods.items:
                try:
                    pod_logs = core_v1.read_namespaced_pod_log(
                        name=pod.metadata.name,
                        namespace=namespace,
                        since_seconds=since_seconds,
                        tail_lines=tail_lines
                    )
                    logs_dict[pod.metadata.name] = pod_logs
                except client.rest.ApiException as e:
                    logs_dict[pod.metadata.name] = f"Error retrieving logs: {e}"
            
            return {
                "success": True,
                "message": f"Retrieved logs for {len(logs_dict)} pods in deployment '{deployment_name}'",
                "logs": logs_dict,
                "deployment_name": deployment_name,
                "namespace": namespace
            }
            
        except client.rest.ApiException as e:
            if e.status == 404:
                return {
                    "success": False,
                    "message": f"Deployment '{deployment_name}' not found in namespace '{namespace}'",
                    "logs": {},
                    "deployment_name": deployment_name,
                    "namespace": namespace
                }
            else:
                return {
                    "success": False,
                    "message": f"API Error: {e}",
                    "logs": {},
                    "deployment_name": deployment_name,
                    "namespace": namespace
                }
    
    except Exception as e:
        return {
            "success": False,
            "message": f"Error: {e}",
            "logs": {},
            "deployment_name": deployment_name,
            "namespace": namespace
        }


if __name__ == "__main__":
    # Example usage
    if "--help" in sys.argv or "-h" in sys.argv:
        print("Usage: python basicTools.py <KUBECONFIG_PATH> <command> [namespace] [deployment_name]")
        print("\nDescription: Kubernetes utility tools for working with clusters")
        print("\nCommands:")
        print("  list-pods       List pods in a namespace")
        print("  list-deploy     List deployments in a namespace")
        print("  restart-deploy  Rollout restart a deployment (requires deployment_name)")
        print("  get-logs        Get logs from pods in a deployment (requires deployment_name)")
        print("\nArguments:")
        print("  <KUBECONFIG_PATH>   Path to your kubeconfig file")
        print("  <command>           Command to execute (list-pods, list-deploy, restart-deploy, get-logs)")
        print("  [namespace]         Kubernetes namespace (default is 'default')")
        print("  [deployment_name]   Name of deployment (required for restart-deploy and get-logs commands)")
        print("\nExamples:")
        print("  python basicTools.py ~/.kube/config list-pods kube-system")
        print("  python basicTools.py ~/.kube/config list-deploy default")
        print("  python basicTools.py ~/.kube/config restart-deploy default my-deployment")
        print("  python basicTools.py ~/.kube/config get-logs default my-deployment")
        sys.exit(0)
    
    # Parse command-line arguments
    kubeconfig = sys.argv[1] if len(sys.argv) >= 2 else None
    command = sys.argv[2] if len(sys.argv) >= 3 else None
    namespace = sys.argv[3] if len(sys.argv) >= 4 else "default"
    deployment_name = sys.argv[4] if len(sys.argv) >= 5 else None
    
    if not kubeconfig or not command:
        print("Usage: python basicTools.py <KUBECONFIG_PATH> <command> [namespace] [deployment_name]")
        print("For more information, use --help")
        sys.exit(1)
    
    # Execute the appropriate command
    if command == "list-pods" or command == "pods":
        pods = list_pods_in_namespace(kubeconfig, namespace)
        print(f"Found {len(pods)} pods in namespace '{namespace}':")
        for pod in pods:
            print(f"Pod: {pod['name']}, Status: {pod['status']}, IP: {pod['ip'] or 'None'}")
    
    elif command == "list-deploy" or command == "list-deployment" or command == "deployments":
        deployments = list_deployments_in_namespace(kubeconfig, namespace)
        print(f"Found {len(deployments)} deployments in namespace '{namespace}':")
        for deploy in deployments:
            status = "HEALTHY" if deploy['is_healthy'] else "UNHEALTHY"
            age_str = f"{deploy['age_minutes']} minutes"
            print(f"Deployment: {deploy['name']}, Ready: {deploy['ready_replicas']}/{deploy['total_replicas']} [{status}], Age: {age_str}")
            print(f"  Images: {', '.join(deploy['image'])}")
    elif command == "restart-deploy" or command == "restart":
        if not deployment_name:
            print("Error: Missing deployment name for restart-deploy command")
            print("Usage: python basicTools.py <KUBECONFIG_PATH> restart-deploy <namespace> <deployment_name>")
            sys.exit(1)
        
        result = rollout_restart_deployment(deployment_name, namespace)
        if result['success']:
            print(f"Success: {result['message']}")
        else:
            print(f"Failed: {result['message']}")
    
    elif command == "get-logs" or command == "logs":
        if not deployment_name:
            print("Error: Missing deployment name for get-logs command")
            print("Usage: python basicTools.py <KUBECONFIG_PATH> get-logs <namespace> <deployment_name>")
            sys.exit(1)
        
        result = get_deployment_logs(kubeconfig, deployment_name, namespace)
        if result['success']:
            for pod_name, log in result['logs'].items():
                print(f"=== Logs for {pod_name} ===")
                print(log)
        else:
            print(f"Failed to get logs: {result['message']}")
    
    else:
        print(f"Unknown command: {command}")
        print("Supported commands: list-pods, list-deploy, restart-deploy, get-logs")
        print("For more information, use --help")
        sys.exit(1)
