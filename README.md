# price-scout

Comparador de preços pela linha de comando. Informe um produto e um CEP e o `price-scout` busca o produto nos sites de e-commerce configurados. Ele escolhe, em cada site, a oferta mais barata considerando **preço + frete** para o CEP, e mostra tudo numa tabela, com a melhor opção destacada.

## Instalação

Requer [uv](https://docs.astral.sh/uv/). O uv instala o Python 3.13+ se precisar.

```bash
uv sync
uv run playwright install chromium
```

## Uso

```bash
uv run price-scout "fone bluetooth" 01310-100
```

```text
Buscando "fone bluetooth" para o CEP 01310-100 em 6 sites...

┏━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┓
┃ Site           ┃ Oferta                     ┃    Preço ┃    Frete ┃    Total ┃ Status            ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━┩
│ Amazon         │ Fone De Ouvido Bluetooth … │  R$ 6,99 │ R$ 22,91 │ R$ 29,90 │ OK                │
│ Americanas     │ Fone de Ouvido Bluetooth … │ R$ 79,90 │   Grátis │ R$ 79,90 │ OK                │
│ Magazine Luiza │ —                          │        — │        — │        — │ Bloqueado         │
│ Mercado Livre  │ —                          │        — │        — │        — │ Bloqueado         │
│ Shopee         │ —                          │        — │        — │        — │ Bloqueado         │
│ Submarino      │ —                          │        — │        — │        — │ Site indisponível │
└────────────────┴────────────────────────────┴──────────┴──────────┴──────────┴───────────────────┘

Melhor opção: Amazon — Fone De Ouvido Bluetooth 5.0 ...
Total: R$ 29,90 (R$ 6,99 + frete R$ 22,91)
Link: https://www.amazon.com.br/dp/...
```

Opções:

| Opção | Descrição |
|---|---|
| `--sites ARQUIVO` | Usa outro arquivo de sites (padrão: `sites.toml`) |
| `--verbose` | Mostra o motivo técnico das falhas de cada site |
| `-h`, `--ajuda` | Mostra a ajuda |

Códigos de saída: `0` quando encontrou alguma oferta, `1` quando nenhum site retornou oferta, `2` para erro de uso (CEP inválido, arquivo de sites com problema, navegador não instalado).

## Como a comparação funciona

- Só entram ofertas cujo título contém **todas** as palavras buscadas. Acessórios como "Capa para …" ou "Cabo p/ …" são descartados.
- Em cada site, o frete é cotado para as 5 ofertas de menor preço, e fica a de menor **preço + frete**.
- O frete é o de entrega padrão para o CEP. Retirada na loja, cupons e promoções condicionais (como "grátis no seu primeiro pedido" ou Prime) não contam. Nesses casos o frete aparece como "Indisponível", e a oferta não concorre à melhor opção.

## Sites

Os sites consultados ficam em `sites.toml`. Para desativar um site, sem apagá-lo, use `enabled = false`:

```toml
[[sites]]
id = "shopee"
name = "Shopee"
enabled = false
```

Situação de cada site hoje (setembro de 2026):

| Site | Suporte |
|---|---|
| Americanas | Completo: busca e frete por CEP |
| Amazon | Completo. Muitas ofertas mostram só frete grátis condicional ("primeiro pedido") e aparecem com "Frete indisponível" |
| Mercado Livre, Magazine Luiza, Shopee | Pedem verificação anti-robô e aparecem como "Bloqueado" |
| Submarino | O endereço não resolve mais; aparece como "Site indisponível" ou "Tempo esgotado" |

Um `id` que a aplicação não conhece aparece como "Não suportado". Adicionar um site novo exige escrever um adaptador em `src/price_scout/adapters/`.

## Testes

```bash
uv run pytest            # testes offline (unitários e de integração)
uv run pytest -m live    # consulta os sites reais
```
