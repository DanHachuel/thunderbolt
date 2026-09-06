from __future__ import annotations

from html import escape
from typing import Any

import streamlit as st


BILIBILI_CARDS: tuple[tuple[str, int, bool, tuple[tuple[str, str, str, str], ...]], ...] = (
    (
        "Validação de Procura",
        70,
        True,
        (
            ("Tecto dos concorrentes", "A medir", "> 500k views", "A verificar"),
            ("Volume de pesquisa", "A medir", "Procura crescente", "A verificar"),
            ("Tráfego de pesquisa", "A medir", "15–30%", "A verificar"),
            ("Diagnóstico", "Validar antes de produzir", "Nicho validado", "A verificar"),
        ),
    ),
    (
        "Thumbnail",
        70,
        True,
        (
            ("CTR", "A medir", "> 6%", "A verificar"),
            ("Contraste", "Alto contraste", "Fundo escuro + cor viva", "Meta"),
            ("Texto", "3–5 palavras", "Legível no telemóvel", "Meta"),
            ("Elementos Bilibili", "ACG quando adequado", "Visual expressivo", "Meta"),
        ),
    ),
    (
        "Título e Intenção",
        70,
        True,
        (
            ("Estrutura", "Curiosity · Clarity · Context", "Promessa clara", "Meta"),
            ("Keyword principal", "No início", "Pesquisa Bilibili", "Meta"),
            ("CTR + retenção", "A medir", "CTR alto sem queda brusca", "A verificar"),
            ("Formato", "Why / How to / VS", "Intenção explícita", "Meta"),
        ),
    ),
    (
        "Hook e Retenção",
        70,
        False,
        (
            ("Retenção aos 15s", "A medir", "> 50%", "A verificar"),
            ("Retenção aos 30s", "A medir", "> 70%", "A verificar"),
            ("Método", "Clímax primeiro", "Resultado antes da introdução", "Meta"),
            ("Abertura", "Sem introdução longa", "Primeiro frame forte", "Meta"),
        ),
    ),
    (
        "Ritmo e Edição",
        70,
        False,
        (
            ("Pattern interrupt", "A cada 5–8s", "Sem imagens estáticas > 4s", "Meta"),
            ("Quedas intermédias", "A medir", "Quedas pequenas", "A verificar"),
            ("Texto danmaku", "Usar com intenção", "Comentários sobrepostos", "Meta"),
            ("Cadência visual", "A medir", "Plateau de retenção", "A verificar"),
        ),
    ),
    (
        "Engagement 三连",
        70,
        False,
        (
            ("三连率", "A medir", "> 4%", "A verificar"),
            ("Likes + Coins + Favorites", "Três cliques", "Sinal de qualidade", "Meta"),
            ("Danmaku", "A medir", "> 5/min", "A verificar"),
            ("Comentários", "A medir", "> 1/100 views", "A verificar"),
        ),
    ),
    (
        "Tráfego e Algoritmo",
        70,
        False,
        (
            ("Recommendation 推荐", "A medir", "40–60%", "A verificar"),
            ("Search 搜索", "A medir", "15–30%", "A verificar"),
            ("Followers 粉丝", "A medir", "10–30%", "A verificar"),
            ("External 外部", "A medir", "< 10%", "A verificar"),
        ),
    ),
    (
        "Conversão e Saúde",
        70,
        False,
        (
            ("Conversão em followers", "A medir", "> 1%", "A verificar"),
            ("Fan Playback", "A medir", "40–60%", "A verificar"),
            ("Novos viewers", "A medir", "> 20%", "A verificar"),
            ("Abandono mensal", "A medir", "< 5%", "A verificar"),
        ),
    ),
)


def _card_html(card: tuple[str, int, bool, tuple[tuple[str, str, str, str], ...]]) -> str:
    title, score, featured, rows = card
    row_html = "".join(
        f'<tr><td>{escape(label)}</td><td><b>{escape(value)}</b></td><td>{escape(target)}</td>'
        f'<td><span style="color:#94a3b8;font-weight:700;">● {escape(status)}</span></td></tr>'
        for label, value, target, status in rows
    )
    height = "350px" if featured else "280px"
    title_size = "19px" if featured else "16px"
    score_size = "38px" if featured else "30px"
    return (
        f'<div style="min-height:{height};border:1px solid #2b3b52;border-radius:14px;padding:16px;'
        f'background:linear-gradient(145deg,#111c2b,#0b121c);box-shadow:0 8px 22px rgba(0,0,0,.16);">'
        f'<div style="font-size:11px;font-weight:800;letter-spacing:.08em;color:#7dd3fc;text-transform:uppercase;">BILIBILI GROWTH</div>'
        f'<div style="font-size:{title_size};font-weight:750;color:#f8fafc;margin-top:8px;">{escape(title)}</div>'
        f'<div style="display:flex;align-items:baseline;gap:5px;margin:8px 0 10px;">'
        f'<span style="font-size:{score_size};font-weight:850;color:#22c55e;">{score}</span>'
        f'<span style="font-size:13px;color:#94a3b8;">/100 · meta do agente</span></div>'
        f'<div style="overflow-x:auto;"><table style="width:100%;border-collapse:collapse;font-size:11px;color:#cbd5e1;">'
        f'<thead><tr><th style="text-align:left;padding:5px 3px;border-bottom:1px solid #334155;">KPI</th>'
        f'<th style="text-align:left;padding:5px 3px;border-bottom:1px solid #334155;">Valor</th>'
        f'<th style="text-align:left;padding:5px 3px;border-bottom:1px solid #334155;">Meta</th>'
        f'<th style="text-align:left;padding:5px 3px;border-bottom:1px solid #334155;">Estado</th></tr></thead>'
        f'<tbody>{row_html}</tbody></table></div></div>'
    )


def render_growth_bilibili() -> None:
    st.title("Analista Bilibili")
    st.caption("Como o agente opera e reporta: procura, click funnel, retenção, engagement 三连 e saúde da audiência Bilibili.")
    st.info("Esta aba define o protocolo e o dashboard de reporte do agente. Os valores privados são preenchidos quando os dados autorizados do Bilibili Studio estiverem disponíveis; não são inventados a partir de páginas públicas.")

    summary_col, status_col = st.columns([3.25, 1], gap="large")
    with summary_col:
        st.markdown(
            '<div style="border:1px solid #263447;border-radius:12px;padding:18px;margin:12px 0 20px;'
            'background:#101722;display:flex;align-items:center;justify-content:space-between;min-height:76px;">'
            '<div><div style="font-size:13px;color:#94a3b8;text-transform:uppercase;letter-spacing:.08em;">Estado do agente</div>'
            '<div style="font-size:18px;font-weight:700;margin-top:5px;">Pronto para auditoria Bilibili</div></div>'
            '<div style="font-size:18px;font-weight:800;color:#22c55e;">PROTOCOLO ACTIVO</div></div>',
            unsafe_allow_html=True,
        )
    with status_col:
        st.write("")
        st.button("ANALISAR CANAL", disabled=True, use_container_width=True, key="growth_bilibili_analyse_disabled")
        st.caption("A ligação ao Studio será usada quando autorizada.")

    st.subheader("Dashboard de Growth")
    st.caption("Os três pilares críticos aparecem primeiro; os cinco blocos operacionais completam o diagnóstico. Verde: referência de execução · Cinzento: dado a verificar no Studio.")
    st.markdown('<div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin:14px 0 18px;">' + "".join(_card_html(card) for card in BILIBILI_CARDS[:3]) + '</div>', unsafe_allow_html=True)
    st.markdown('<div style="display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px;margin:0 0 18px;">' + "".join(_card_html(card) for card in BILIBILI_CARDS[3:]) + '</div>', unsafe_allow_html=True)
    st.caption("Legenda: o agente compara os dados autorizados com as metas Bilibili; quando um dado não existe, apresenta “A verificar” em vez de estimar.")

    st.divider()
    operation_tab, report_tab, monetization_tab = st.tabs(["Como o agente vai operar", "Como vai reportar", "Contexto de monetização"])
    with operation_tab:
        st.subheader("Protocolo de auditoria em 10 passos")
        st.markdown("""
1. **Validar procura:** compara o tecto de concorrentes, pesquisa e origem do tráfego.
2. **Avaliar thumbnail:** verifica CTR, contraste, legibilidade móvel, emoção e elementos ACG quando adequados.
3. **Avaliar título:** cruza CTR com retenção inicial e aplica Curiosity, Clarity e Context.
4. **Verificar engagement:** mede a taxa 三连 (Like + Coin + Favorite), danmaku e qualidade dos comentários.
5. **Diagnosticar hook:** localiza a queda dos primeiros 15–30 segundos e aplica “clímax primeiro”.
6. **Diagnosticar ritmo:** identifica quedas recorrentes e recomenda pattern interrupts a cada 5–8 segundos.
7. **Ler o algoritmo:** compara Recommendation, Search, Followers e External com as metas da plataforma.
8. **Medir conversão:** calcula novos followers por visualização e posiciona a CTA aos 40% do vídeo.
9. **Verificar cadência:** acompanha 1–2 vídeos por semana, consistência e uso de posts/live para comunidade.
10. **Avaliar saúde:** cruza Fan Playback, New Viewer, abandono mensal e sinais moonshot.
""")
    with report_tab:
        st.subheader("Formato do reporte entregue pelo agente")
        st.markdown("""
O agente reporta sempre em cinco blocos: **projecção financeira e contexto**, **resumo dos dez pilares**, **Top 3 prioridades accionáveis**, **estratégia de longo prazo** e **checklist dos próximos passos**. Cada KPI recebe valor observado, meta, estado e origem do dado.

As três prioridades são escolhidas por impacto: primeiro **Thumbnail + Título**, depois **retenção e engagement**, e só depois produção ou expansão. O relatório distingue claramente `DADO OBSERVADO`, `A VERIFICAR` e `RECOMENDAÇÃO`, sem transformar uma meta em resultado real.

> Regra de reporte: um vídeo com conteúdo forte, mas sem click funnel, não é considerado optimizado. O agente corrige primeiro a combinação thumbnail + título e acompanha a evolução no ciclo seguinte.
""")
        st.markdown("**Checklist padrão:** validar nicho · corrigir as últimas 5 thumbnails · reescrever títulos · cortar a introdução · inserir prompt danmaku · publicar em dia fixo · rever analytics em 30 dias.")
    with monetization_tab:
        st.subheader("Referências internas usadas pelo agente")
        st.markdown("""
A projecção considera Video Incentive Program, Charging, Paid Subscriptions e Huahuo. O cálculo interno é: `Playbacks × Base Rate × Zone Multiplier × Quality Multiplier + Ad Revenue + Tips + Subscriptions`.

Para o diagnóstico inicial, o agente acompanha originalidade do conteúdo, verificação de identidade, estado da conta, direitos ≥ 3, score de crédito ≥ 80 e os limiares de audiência definidos no material Bilibili. Estes itens são **contexto de elegibilidade**, não promessa de rendimento.

Os sinais moonshot acompanhados são densidade de danmaku (> 5 por minuto), crescimento do Search Index (+20% mensal), Long-tail Traffic (> 30%), Shares (> 1%) e Collect Rate (> 5%).
""")
