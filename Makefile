#variaveis
POETRY = poetry run
RUFF = $(POETRY) ruff

#.PHONY indica alvo falso, com isso ao executar o comando não
# há confusão cajo exista um arquivo com o mesmo nome do comando

# ruff executar linting
.PHONY: lint
lint: 
	$(RUFF) check .

# ruff auto correção
.PHONY: fix
fix:
	$(RUFF) check --fix .

# ruff formatar código 
.PHONY: format
format:
	$(RUFF) format .

# verificando tipos com mypy
.PHONY: typecheck
typecheck:
	$(POETRY) mypy . 

# comando make, executa ambos: lint, format e typecheck
.PHONY: all
all:
	make lint format typecheck sec

# instalar dependências com o Poetry
.PHONY: install
install:
	poetry install

# ativar ambiente vitual com Poetry
.PHONY: venv
venv:
	poetry env activate

# desativar ambiente virtual com Poetry
.PHONY: deactivate venv
deactivate:
	deactivate

# instalar e ativar pre-commit
.PHONY: pre-commit
pre-commit:
	$(POETRY) pre-commit install

# comandos para segurança do código com pip-audit
.PHONY: sec
sec:
	pip-audit
