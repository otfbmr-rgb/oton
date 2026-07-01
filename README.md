# Garami

Editor gráfico moderno em Python, inspirado em conceitos de aplicativos profissionais de desenho.

## Como executar

```bash
python main.py
```

## Funcionalidades atuais

- Caneta
- Linha
- Retângulo
- Elipse
- Texto
- Borracha
- Desfazer
- Limpar tela
- Salvar e abrir projetos

## Changelog

- Corrigido: leitura segura de opções do Canvas (evita erros ao ler `font`/`width`).
- Corrigido: seleção e preenchimento agora ignoram elementos de grade/handles/background.
- Melhorado: parsing numérico de `width` agora aceita valores como "3.0".
- Novo: edição de texto por duplo-clique no canvas.
