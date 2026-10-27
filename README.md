# serra-anuncios-midia

Artes dos anúncios da Serra Montenegro Advocacia (Meta Ads). Hospedagem pública das imagens para a Meta buscar.

Repositório operado por automação (tarefa semanal do Claude). Não guarda dado de cliente.

- `lotes/AAAA-MM-DD/` — artes da semana (6 JPGs) + `anuncios.json`. Escrito pela skill `serra-anuncio-arte`.
- `historico/estado.json` — estado vivo dos anúncios (gancho, estilo, gasto, conversas). Escrito pela skill `serra-meta-ads`.
- `historico/AAAA-MM-DD.md` — registro de cada execução semanal: o que foi visto, decidido e por quê.
- `motor/render_anuncio.py` — motor que desenha as artes.
- `fontes/` — Newsreader e Inter (SIL Open Font License, ver OFL-*.txt).
