## Running the Project
```bash
docker compose up --build
```

## Important Notes for AI Assistant

### Development Workflow
- **Auto-reload enabled**: The service automatically reloads on each code edit within the Docker container
- **Check logs in `logs/` folder**: Instead of running commands directly, check the logs folder for server status and errors
- **Server runs on port 9000**: Access the application at http://localhost:9000

### Project Structure
- `app.py` - FastAPI backend
- `templates/index.html` - Frontend
- `logs/` - Application logs folder
- `docker-compose.yml` - Docker container configuration