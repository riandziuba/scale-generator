# Scale Generator

Aplicação web para geração automática de escalas de pessoas, com suporte a indisponibilidades, dias extras e ensaios.

## Funcionalidades

- **Cadastro de pessoas** — Gerencie a lista de possíveis escalados
- **Indisponibilidades** — Registre dias em que cada pessoa não pode participar
- **Escalas de Domingo** — Gere automaticamente para todos os domingos de um período
- **Dias Extras** — Adicione dias avulsos com descrição personalizada
- **Reescalonamento inteligente** — Evita repetir a mesma pessoa entre semanas consecutivas; se não houver disponíveis, repete
- **Ensaios** — Vincule um ensaio a cada escala, com data/horário independentes e responsável
- **Relatórios** — Exporte em PDF (impressão) ou PNG

## Como usar

### Desenvolvimento (com Python)

```bash
cd scale-generator
pip3 install flask
python3 app.py
```

Acesse http://localhost:5500

### Executável (sem Python)

#### macOS

Abra `dist/scale-generator.app`

O banco de dados fica em `~/.scale-generator/escala.db`.

#### Windows

1. Instale Python e PyInstaller em um PC com Windows
2. Execute `build_windows.bat`
3. O executável estará em `dist/scale-generator.exe`

## Build manual

```bash
# macOS (aplicativo)
python3 -m PyInstaller --windowed \
  --name "scale-generator" \
  --add-data "templates:templates" \
  --add-data "static:static" \
  --hidden-import flask \
  --hidden-import sqlite3 \
  --collect-submodules flask \
  app.py

# macOS (único arquivo)
python3 -m PyInstaller --onefile --windowed \
  --name "scale-generator" \
  --add-data "templates:templates" \
  --add-data "static:static" \
  --hidden-import flask \
  --hidden-import sqlite3 \
  --collect-submodules flask \
  app.py
```

## Estrutura

```
scale-generator/
├── app.py               # Servidor Flask + API
├── templates/
│   └── index.html       # Interface web
├── static/
│   ├── i18n.js          # Traduções PT/EN
│   ├── api.js           # Helpers compartilhados (fetch, toast, escHtml)
│   ├── people.js        # CRUD de pessoas
│   ├── unavailability.js# CRUD de indisponibilidades
│   ├── scales.js        # Geração/CRUD de escalas
│   ├── rehearsals.js    # Modal e lista de ensaios
│   ├── reports.js       # Relatórios PDF/PNG
│   ├── script.js        # Bootstrap (abas, idioma, init)
│   └── style.css        # Estilos
├── test_app.py          # Testes automatizados (pytest)
├── build_mac.sh         # Build macOS (arquivo único)
├── build_app_mac.sh     # Build macOS (.app)
├── build_windows.bat    # Build Windows (.exe)
├── CODE_REVIEW.md       # Revisão de código
└── README.md
```

## API

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/pessoas` | Lista pessoas |
| POST | `/api/pessoas` | Cadastra pessoa |
| DELETE | `/api/pessoas/:id` | Exclui pessoa |
| GET | `/api/indisponibilidades` | Lista indisponibilidades |
| POST | `/api/indisponibilidades` | Adiciona indisponibilidade |
| DELETE | `/api/indisponibilidades/:id` | Remove indisponibilidade |
| POST | `/api/escalas/gerar` | Gera escalas de domingo |
| GET | `/api/escalas` | Lista todas as escalas |
| DELETE | `/api/escalas/:id` | Exclui escala |
| POST | `/api/escalas/:id/regenerar` | Reatribui pessoas |
| POST | `/api/escalas/extra` | Adiciona dia extra |
| POST | `/api/ensaios` | Cria/atualiza ensaio |
| GET | `/api/ensaios` | Lista ensaios |
| DELETE | `/api/ensaios/:id` | Exclui ensaio |
