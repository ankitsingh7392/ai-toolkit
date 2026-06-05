.PHONY: up down build logs test seed clean

up:
	cp -n .env.example .env 2>/dev/null || true
	docker compose up --build -d
	@echo "Backend:  http://localhost:8000/docs"
	@echo "Frontend: http://localhost:3000"
	@echo "Flower:   http://localhost:5555"

down:
	docker compose down

build:
	docker compose build --no-cache

logs:
	docker compose logs -f backend worker

test:
	@echo "Sending sample Jenkins payload..."
	cd tests && python simulate_jenkins.py

seed:
	cd tests && python simulate_jenkins.py --runs=5

clean:
	docker compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
