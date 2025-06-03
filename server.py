from flask import Flask, request, jsonify
import requests
import time
import threading
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

# Server configuration
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8002"))

# Agent registry - stores active agents
agents = {}  # {agent_id: {host, port, last_heartbeat, capabilities}}

@app.route("/register", methods=["POST"])
def register_agent():
    """Register a new agent with the server"""
    data = request.json
    agent_id = data.get("agent_id")
    host = data.get("host")
    port = data.get("port")
    capabilities = data.get("capabilities", [])
    
    if not agent_id or not host or not port:
        return jsonify({"success": False, "error": "Missing required fields"}), 400
    
    agents[agent_id] = {
        "host": host,
        "port": port,
        "last_heartbeat": time.time(),
        "capabilities": capabilities,
        "status": "active"
    }
    
    print(f"✅ Agent {agent_id} registered: {host}:{port}")
    return jsonify({"success": True, "message": f"Agent {agent_id} registered successfully"})

@app.route("/heartbeat", methods=["POST"])
def receive_heartbeat():
    """Receive heartbeat from agents"""
    data = request.json
    agent_id = data.get("agent_id")
    timestamp = data.get("timestamp")
    
    if agent_id in agents:
        agents[agent_id]["last_heartbeat"] = timestamp
        agents[agent_id]["status"] = "active"
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": "Agent not registered"}), 404

@app.route("/agents", methods=["GET"])
def list_agents():
    """List all registered agents and their status"""
    current_time = time.time()
    agent_list = []
    
    for agent_id, info in agents.items():
        # Consider agent dead if no heartbeat for 60 seconds
        is_alive = (current_time - info["last_heartbeat"]) < 60
        status = "active" if is_alive else "inactive"
        
        agent_list.append({
            "agent_id": agent_id,
            "host": info["host"],
            "port": info["port"],
            "status": status,
            "last_heartbeat": info["last_heartbeat"],
            "capabilities": info["capabilities"]
        })
    
    return jsonify({"agents": agent_list})

@app.route("/exec", methods=["POST"])
def dispatch_command():
    """Dispatch command to specific agent (main endpoint for clients)"""
    data = request.json
    agent_id = data.get("agent_id")
    cmd = data.get("cmd", "")
    cmd_type = data.get("type", "shell")
    
    if not agent_id:
        return jsonify({"success": False, "result": "❌ Agent ID required"}), 400
    
    if not cmd:
        return jsonify({"success": False, "result": "❌ Command required"}), 400
    
    # Check if agent exists and is alive
    if agent_id not in agents:
        return jsonify({"success": False, "result": f"❌ Agent {agent_id} not found"}), 404
    
    agent_info = agents[agent_id]
    current_time = time.time()
    is_alive = (current_time - agent_info["last_heartbeat"]) < 60
    
    if not is_alive:
        return jsonify({"success": False, "result": f"❌ Agent {agent_id} is not responding"}), 503
    
    # Forward command to agent
    agent_url = f"http://{agent_info['host']}:{agent_info['port']}/exec"
    
    try:
        response = requests.post(agent_url, json={"cmd": cmd, "type": cmd_type}, timeout=30)
        
        if response.status_code == 200:
            agent_response = response.json()
            return jsonify(agent_response)
        else:
            return jsonify({
                "success": False, 
                "result": f"❌ Agent {agent_id} returned error: {response.status_code}"
            })
    
    except requests.exceptions.Timeout:
        return jsonify({
            "success": False, 
            "result": f"❌ Timeout when contacting agent {agent_id}"
        })
    except requests.exceptions.ConnectionError:
        return jsonify({
            "success": False, 
            "result": f"❌ Cannot connect to agent {agent_id}"
        })
    except Exception as e:
        return jsonify({
            "success": False, 
            "result": f"❌ Error forwarding to agent {agent_id}: {str(e)}"
        })

@app.route("/health", methods=["GET"])
def health_check():
    """Server health check"""
    active_agents = sum(1 for agent_id, info in agents.items() 
                       if (time.time() - info["last_heartbeat"]) < 60)
    
    return jsonify({
        "server_status": "healthy",
        "timestamp": time.time(),
        "total_agents": len(agents),
        "active_agents": active_agents,
        "registered_agents": list(agents.keys())
    })

@app.route("/broadcast", methods=["POST"])
def broadcast_command():
    """Broadcast command to all active agents"""
    data = request.json
    cmd = data.get("cmd", "")
    cmd_type = data.get("type", "shell")
    
    if not cmd:
        return jsonify({"success": False, "result": "❌ Command required"}), 400
    
    current_time = time.time()
    results = {}
    
    for agent_id, agent_info in agents.items():
        # Only send to alive agents
        is_alive = (current_time - agent_info["last_heartbeat"]) < 60
        if not is_alive:
            results[agent_id] = {"success": False, "result": f"❌ Agent {agent_id} is not responding"}
            continue
        
        agent_url = f"http://{agent_info['host']}:{agent_info['port']}/exec"
        
        try:
            response = requests.post(agent_url, json={"cmd": cmd, "type": cmd_type}, timeout=15)
            if response.status_code == 200:
                results[agent_id] = response.json()
            else:
                results[agent_id] = {"success": False, "result": f"Error: {response.status_code}"}
        except Exception as e:
            results[agent_id] = {"success": False, "result": f"Error: {str(e)}"}
    
    return jsonify({"broadcast_results": results})

def cleanup_dead_agents():
    """Periodically remove agents that haven't sent heartbeat"""
    while True:
        current_time = time.time()
        dead_agents = []
        
        for agent_id, info in agents.items():
            if (current_time - info["last_heartbeat"]) > 120:  # 2 minutes timeout
                dead_agents.append(agent_id)
        
        for agent_id in dead_agents:
            del agents[agent_id]
            print(f"🗑️ Removed dead agent: {agent_id}")
        
        time.sleep(60)  # Run cleanup every minute

if __name__ == "__main__":
    print(f"🖥️ Starting Server on {SERVER_HOST}:{SERVER_PORT}")
    
    # Start cleanup thread
    cleanup_thread = threading.Thread(target=cleanup_dead_agents)
    cleanup_thread.daemon = True
    cleanup_thread.start()
    
    # Start Flask app
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=False)