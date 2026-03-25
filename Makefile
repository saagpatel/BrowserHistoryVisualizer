SHELL        := /bin/bash
PROJECT_DIR  := $(shell pwd)
VENV         := $(PROJECT_DIR)/backend/venv
VENV_BIN     := $(VENV)/bin
PLIST_DIR    := $(HOME)/Library/LaunchAgents
LOG_DIR      := $(HOME)/Library/Logs/bhv

# Detect nginx via Homebrew
NGINX_BIN    := $(shell brew --prefix nginx 2>/dev/null)/bin/nginx
NGINX_PREFIX := $(shell brew --prefix nginx 2>/dev/null)
NGINX_ETC    := $(shell brew --prefix 2>/dev/null)/etc/nginx

.PHONY: install uninstall build dev logs refresh open status check-deps

install: check-deps build
	mkdir -p $(LOG_DIR) $(PROJECT_DIR)/nginx/logs
	# Substitute paths into nginx config
	sed -e "s|__PROJECT_DIR__|$(PROJECT_DIR)|g" \
	    -e "s|__NGINX_PREFIX__|$(NGINX_PREFIX)|g" \
	    -e "s|__NGINX_ETC__|$(NGINX_ETC)|g" \
	    nginx/bhv.conf > nginx/bhv.conf.installed
	# Substitute paths into plists and load
	@for svc in com.bhv.server com.bhv.pipeline com.bhv.nginx; do \
	    sed -e "s|__PROJECT_DIR__|$(PROJECT_DIR)|g" \
	        -e "s|__VENV_BIN__|$(VENV_BIN)|g" \
	        -e "s|__NGINX_BIN__|$(NGINX_BIN)|g" \
	        -e "s|__NGINX_PREFIX__|$(NGINX_PREFIX)|g" \
	        -e "s|__LOG_DIR__|$(LOG_DIR)|g" \
	        -e "s|__ANTHROPIC_API_KEY__|$(ANTHROPIC_API_KEY)|g" \
	        launchd/$$svc.plist > $(PLIST_DIR)/$$svc.plist; \
	    launchctl load $(PLIST_DIR)/$$svc.plist; \
	    echo "  loaded $$svc"; \
	done
	@echo ""
	@echo "BHV installed. Run: make open"

uninstall:
	@for svc in com.bhv.server com.bhv.pipeline com.bhv.nginx; do \
	    launchctl unload $(PLIST_DIR)/$$svc.plist 2>/dev/null || true; \
	    rm -f $(PLIST_DIR)/$$svc.plist; \
	    echo "  unloaded $$svc"; \
	done
	rm -f nginx/bhv.conf.installed
	@echo "BHV services removed."

check-deps:
	@if ! brew list nginx &>/dev/null; then \
	    echo "nginx not found — installing via Homebrew..."; \
	    brew install nginx; \
	else \
	    echo "nginx: $(NGINX_BIN)"; \
	fi
	@if [ ! -d "$(VENV)" ]; then \
	    echo "Creating Python venv..."; \
	    python3 -m venv $(VENV); \
	    $(VENV_BIN)/pip install -r backend/requirements.txt; \
	fi
	@if [ ! -d "frontend/node_modules" ]; then \
	    echo "Installing frontend dependencies..."; \
	    cd frontend && npm install; \
	fi

build:
	cd frontend && npm run build
	@echo "Frontend built -> frontend/dist/"

dev:
	@# Dev mode: uvicorn --reload + Vite :5173 with /api proxy. No nginx.
	(cd backend && source $(VENV)/bin/activate && \
	    uvicorn main:app --host 127.0.0.1 --port 8000 --reload) &
	(cd frontend && npm run dev) &
	@echo "Dev: http://localhost:5173"
	@wait

logs:
	tail -f $(LOG_DIR)/server.log \
	         $(PROJECT_DIR)/nginx/logs/error.log \
	         $(PROJECT_DIR)/nginx/logs/access.log

refresh:
	curl -s -X POST http://127.0.0.1:8000/api/refresh | python3 -m json.tool

open:
	open http://localhost:8080

status:
	@echo "=== launchd ===" && launchctl list | grep bhv || echo "  (none loaded)"
	@echo "=== ports ===" && lsof -i :8080 -i :8000 | grep LISTEN || echo "  (none)"
