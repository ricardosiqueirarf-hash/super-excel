# Super Excel

Planilha web construída com **HTML, CSS, JavaScript, Flask e HyperFormula**. Funciona localmente e pode ser publicada em serviços que executem aplicações Python, como Render, Railway, Fly.io ou qualquer servidor com Docker.

## Recursos

- Grade com 60 linhas e 26 colunas.
- Barra de fórmulas e referências A1.
- Motor de cálculo HyperFormula 3.3.0 em português do Brasil.
- 30 fórmulas principais, incluindo `SOMA`, `SE`, `SOMASES`, `PROCX`, `FILTRO`, `ÚNICO` e `CLASSIFICAR`.
- Colar intervalos copiados do Excel.
- Desfazer e refazer.
- Autosave no navegador.
- Persistência no servidor usando SQLite.
- Importação e exportação em JSON.
- Execução local, Gunicorn, Render e Docker.

## Executar localmente

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Linux/macOS:

```bash
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Abra `http://localhost:5000`.

## Executar como servidor de produção

```bash
pip install -r requirements.txt
gunicorn --bind 0.0.0.0:8000 app:app
```

Abra `http://localhost:8000`.

## Executar com Docker

```bash
docker build -t super-excel .
docker run --rm -p 8000:8000 super-excel
```

## Publicar no Render

O arquivo `render.yaml` já define o build, o comando de inicialização e o health check. Crie um Blueprint no Render apontando para este repositório.

Para manter as planilhas após recriações do serviço, configure um disco persistente e defina:

```text
SUPER_EXCEL_DATA_DIR=/var/data
```

## Fórmulas

Use `;` como separador de argumentos e `,` como separador decimal.

```excel
=SOMA(A1:A10)
=SE(B2>=1000;"Meta atingida";"Abaixo da meta")
=SOMASES(E2:E20;D2:D20;"Pago";C2:C20;"Fortaleza")
=PROCX(A2;F2:F20;H2:H20;"Não encontrado")
=ÚNICO(B2:B20)
=CLASSIFICAR(A2:D20;4;-1)
```

`MÉDIASES`, `CONCAT`, `FILTRO`, `ÚNICO`, `CLASSIFICAR` e `TEXTO` possuem extensões registradas no HyperFormula para completar a compatibilidade solicitada. As funções dinâmicas ocupam uma área de saída na grade.

## Licença do HyperFormula

Este projeto inicializa o HyperFormula com a chave `gpl-v3`. Ao distribuir uma aplicação incompatível com a GPLv3, avalie a licença comercial do HyperFormula.
