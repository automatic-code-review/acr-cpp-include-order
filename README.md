# acr-cpp-include-order

Arquivo config.json

- message
    - Referente a mensagem em si que ira adicionar no merge
    - Essa mensagem é por arquivo
    - Contem as seguintes chanves
    - ${FILE_PATH} para o caminho do arquivo
    - ${ORDERED} ordem correta
- regexOrder
    - Lista de objetos referente a ordenação
    - orderType
        - Tipo de ordenação
        - individual significa que vai ordenar agrupando cada regex
        - group significa que ira juntar todos os includes de todos os regex desse objeto, e depois ordenar
    - regex
        - Lista de regex

```json
{
  "message": "Ordenação de includes esta incorreta no arquivo ${FILE_PATH}<br>Ordenação correta é:<br><br>${ORDERED}",
  "regexOrder": [
    {
      "orderType": "individual",
      "regex": [
      ]
    },
    {
      "orderType": "group",
      "regex": [
      ]
    }
  ]
}
```

## Como rodar o teste unitario

Opcao recomendada (com venv):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tests -p "test_*.py" -q
```

Para sair do ambiente virtual:

```bash
deactivate
```

Opcao sem venv (usando Python do sistema):

```bash
/usr/bin/python3 -m unittest discover -s tests -p "test_*.py" -q
```

Esse comando executa todos os arquivos de teste dentro de `tests/` que comecam com `test_`.
