## @ Utils Commands
requirements: ## Update requirements.txt
	poetry export --without  dev --output requirements.txt --without-hashes

lint: ## Run autoformatting and linting
	uv run ruff format && uv run ruff check ./ --fix