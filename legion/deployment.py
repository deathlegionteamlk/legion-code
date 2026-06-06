import os


class Deployer:
    def __init__(self, project_name: str = "legion-app"):
        self.project_name = project_name

    def generate_dockerfile(self, output_path: str = "Dockerfile", base_image: str = "python:3.11-slim") -> str:
        content = f"""FROM {base_image}
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "run.py"]
"""
        with open(output_path, "w") as f:
            f.write(content)
        return output_path

    def generate_docker_compose(self, output_path: str = "docker-compose.yml", services: dict = None) -> str:
        if services is None:
            services = {
                "app": {
                    "build": ".",
                    "ports": ["8080:8080"],
                    "volumes": [".:/app"],
                    "environment": ["OPENROUTER_API_KEY=${OPENROUTER_API_KEY}"],
                }
            }
        lines = [f"version: '3.8'", "services:"]
        for name, config in services.items():
            lines.append(f"  {name}:")
            for key, value in config.items():
                if isinstance(value, list):
                    lines.append(f"    {key}:")
                    for item in value:
                        lines.append(f"      - {item}")
                elif isinstance(value, dict):
                    lines.append(f"    {key}:")
                    for k, v in value.items():
                        lines.append(f"      {k}: {v}")
                else:
                    lines.append(f"    {key}: {value}")
        content = "\n".join(lines) + "\n"
        with open(output_path, "w") as f:
            f.write(content)
        return output_path

    def generate_systemd_service(self, output_path: str = "", user: str = "root") -> str:
        if not output_path:
            output_path = f"/etc/systemd/system/{self.project_name}.service"
        content = f"""[Unit]
Description={self.project_name} - Legion Code Agent
After=network.target

[Service]
Type=simple
User={user}
WorkingDirectory=/app
ExecStart=/usr/bin/python /app/run.py --interactive
Restart=on-failure
RestartSec=5
Environment=OPENROUTER_API_KEY=your_key_here

[Install]
WantedBy=multi-user.target
"""
        with open(output_path, "w") as f:
            f.write(content)
        return output_path

    def generate_railway_config(self, output_path: str = "railway.json") -> str:
        content = json.dumps({
            "build": {"builder": "NIXPACKS", "buildCommand": "pip install -r requirements.txt"},
            "deploy": {"startCommand": "python run.py", "healthcheckPath": "/", "restartPolicyType": "ON_FAILURE"}
        }, indent=2)
        with open(output_path, "w") as f:
            f.write(content)
        return output_path