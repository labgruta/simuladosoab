"""Atribui a matéria de cada questão.

Os cadernos não dizem a matéria, mas cada prova traz as matérias em blocos contíguos,
numa ordem fixa e com quantidades definidas pelo edital da época. Por isso a
classificação é uma segmentação: dado o modelo da época (ordem + tamanho esperado de cada
bloco), uma programação dinâmica escolhe onde cada bloco começa, combinando a pontuação por
palavras-chave (lexico.py) com uma penalidade por fugir do tamanho esperado.
"""
import math

from lexico import MATERIAS, pontuar

SIGLAS = {
    "etica": "ET", "filosofia": "FI", "constitucional": "CO", "dh": "DH", "internacional": "IN",
    "tributario": "TR", "administrativo": "AD", "ambiental": "AM", "civil": "CI", "eca": "EC",
    "consumidor": "CS", "empresarial": "EM", "proc_civil": "PC", "penal": "PE", "proc_penal": "PP",
    "previdenciario": "PV", "financeiro": "FN", "eleitoral": "EL", "trabalho": "TB", "proc_trabalho": "PT",
}
_POR_SIGLA = {v: k for k, v in SIGLAS.items()}


def _modelo(spec):
    """"ET8 FI2 ..." -> (ordem das matérias, {matéria: questões esperadas})"""
    toks = spec.split()
    return [_POR_SIGLA[t[:2]] for t in toks], {_POR_SIGLA[t[:2]]: int(t[2:]) for t in toks}


# Modelos por época, deduzidos da própria sequência das provas. Quando há mais de um,
# fica o que explica melhor a prova.
MODELOS = {
    "2010.2": [_modelo("CO10 AD10 CI10 PC10 TB8 PT7 PE8 PP7 TR10 ET10 EM2 IN2 EC2 AM2 CS2")],
    "2010.3": [_modelo("AD8 CI12 PC10 CO8 EM6 ET9 PE9 PP6 TB9 PT6 TR6 AM4 CS1 EC3 IN2 FI1"),
               _modelo("AD8 CI12 PC10 CO8 EM6 ET9 PE9 PP6 TB9 PT6 TR6 AM3 EC3 CS2 IN2")],
    # IV a VII
    "E1": [_modelo("ET12 DH3 CO7 IN2 EC2 AD6 CI7 PC6 CS2 EM5 TR4 AM2 PE6 PP5 TB6 PT5"),
           _modelo("ET12 CO7 DH3 IN2 EC2 AD6 CI7 PC6 CS2 EM5 TR4 AM2 PE6 PP5 TB6 PT5")],
    # VIII e IX
    "E2": [_modelo("ET12 CO7 DH3 IN2 TR4 AD6 AM2 CI7 EC2 CS2 EM5 PC6 PE6 PP5 TB6 PT5"),
           _modelo("ET12 DH3 CO7 IN2 TR4 AD6 AM2 CI7 EC2 CS2 EM5 PC6 PE6 PP5 TB6 PT5")],
    # X a XXII: entra Filosofia
    "E3": [_modelo("ET10 FI2 CO7 DH3 IN2 TR4 AD6 AM2 CI7 EC2 CS2 EM5 PC6 PE6 PP5 TB6 PT5")],
    # XXIII a XXXVII: Ética cai para 8
    "E4": [_modelo("ET8 FI2 CO7 DH2 IN2 TR5 AD6 AM2 CI7 EC2 CS2 EM5 PC7 PE6 PP6 TB6 PT5")],
    # 38º em diante: entram Eleitoral, Financeiro e Previdenciário
    "E5": [_modelo("ET8 FI2 CO6 DH2 EL2 IN2 FN2 TR5 AD5 AM2 CI6 EC2 CS2 EM4 PC6 PE6 PP6 PV2 TB5 PT5")],
}


def epoca(exame):
    if exame.startswith("2010"):
        return exame
    n = int(exame)
    return "E1" if n <= 7 else "E2" if n <= 9 else "E3" if n <= 22 else "E4" if n <= 37 else "E5"


def _log_probabilidades(questoes, temperatura=2.0):
    """Para cada questão, log-probabilidade (softmax) de cada matéria a partir das palavras-chave."""
    out = []
    for q in questoes:
        s = pontuar(q["stem"] + " " + " ".join(q["alts"].values()))
        m = max(s.values())
        z = math.log(sum(math.exp((v - m) / temperatura) for v in s.values()))
        out.append({k: (v - m) / temperatura - z for k, v in s.items()})
    return out


def _segmentar(lp, ordem, esperado, peso):
    """Melhor divisão das questões em blocos contíguos na ordem dada. Retorna (pontuação, rótulos)."""
    n_q, neg = len(lp), -1e9
    acum = {m: [0.0] for m in ordem}
    for m in ordem:
        for e in lp:
            acum[m].append(acum[m][-1] + e[m])
    dp = [[neg] * (n_q + 1) for _ in range(len(ordem) + 1)]
    volta = [[0] * (n_q + 1) for _ in range(len(ordem) + 1)]
    dp[0][0] = 0
    for k, m in enumerate(ordem, 1):
        for i in range(n_q + 1):
            melhor, melhor_n = neg, 0
            for n in range(0, min(i, 16) + 1):
                p = dp[k - 1][i - n]
                if p <= neg / 2:
                    continue
                # bloco vazio custa como se faltassem todas as questões esperadas
                penal = -peso * esperado[m] if n == 0 else -peso * abs(n - esperado[m])
                v = p + acum[m][i] - acum[m][i - n] + penal
                if v > melhor:
                    melhor, melhor_n = v, n
            dp[k][i], volta[k][i] = melhor, melhor_n
    rotulos, i = [None] * n_q, n_q
    for k in range(len(ordem), 0, -1):
        n = volta[k][i]
        for j in range(i - n, i):
            rotulos[j] = ordem[k - 1]
        i -= n
    return dp[len(ordem)][n_q], rotulos


def classificar(exame, questoes):
    """Lista com a matéria de cada questão, na ordem do caderno."""
    lp = _log_probabilidades(questoes)
    peso = 0.3 if exame.startswith("2010") else 1.0
    melhor = None
    for ordem, esperado in MODELOS[epoca(exame)]:
        pont, rotulos = _segmentar(lp, ordem, esperado, peso)
        if melhor is None or pont > melhor[0]:
            melhor = (pont, rotulos)
    return melhor[1]


def resumo(rotulos):
    """"ET8 FI2 CO6 ..." — tamanho de cada bloco, para conferência."""
    blocos = []
    for m in rotulos:
        if blocos and blocos[-1][0] == m:
            blocos[-1][1] += 1
        else:
            blocos.append([m, 1])
    return " ".join(f"{SIGLAS[m]}{n}" for m, n in blocos)


assert set(SIGLAS) == set(MATERIAS)
