## @ Utils Commands
requirements: ## Update requirements.txt
	poetry export --without  dev --output requirements.txt --without-hashes

lint: ## Run autoformatting and linting
	poetry run ruff check ./ --fix