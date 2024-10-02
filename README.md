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
