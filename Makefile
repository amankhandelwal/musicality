BACKEND_DIR := backend
FRONTEND_DIR := frontend

.PHONY: start-be start-fe stop

start-be:
	cd $(BACKEND_DIR) && uv run uvicorn app.main:app --reload --port 8000

start-fe:
	cd $(FRONTEND_DIR) && npm run dev

stop:
	@pkill -f "uvicorn app.main:app" 2>/dev/null || true
	@pkill -f "vite.*musicality" 2>/dev/null || true
	@echo "Stopped."
