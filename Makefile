COMPOSE_FILE=docker-compose.yml
DOCKER_COMPOSE=docker-compose -f $(COMPOSE_FILE)

default: build

#================================================================================
# Managing the Docker environment (Building and Starting)
#================================================================================
build: ## Build all Docker images
	@echo "Building Chatbot images"
	@$(DOCKER_COMPOSE) build

start-attached: ## Start the server in attached mode
	@echo "${GREEN}Starting Chatbot in attached mode${RESET}"
	$(DOCKER_COMPOSE) up

#==============================================
# Application management commands
#==============================================

makemigrations: ## Create migrations using the Django `makemigrations` management command
	$(DOCKER_COMPOSE) run --rm web python manage.py makemigrations

migrate: ## Run migrations using the Django `migrate` management command
	$(DOCKER_COMPOSE) run --rm web python manage.py migrate

create-superuser: ## Create a new superuser using the Django `createsuperuser` management command
	$(DOCKER_COMPOSE) run --rm web python manage.py createsuperuser
	
test: ## Run automated tests
	$(DOCKER_COMPOSE) run --rm web python manage.py test
