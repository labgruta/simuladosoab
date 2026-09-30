"""Temas dentro de cada matéria, para identificar os assuntos que mais caem.

Cada questão recebe o tema com mais evidências (ver atribuir_temas). Os temas "mais recorrentes" de uma matéria são os mais frequentes,
somados até cobrir COBERTURA das questões da matéria.
"""
import math
import re

COBERTURA = 0.6

TEMAS = {
    "etica": [
        ("honorarios", "Honorários advocatícios", r"honorári|tabela de honorários|quota litis|cláusula quota"),
        ("inscricao", "Inscrição, licença e cancelamento", r"inscrição|inscrever|inscrit[oa]s? (principal|suplementar)|estagiári|estágio|carteira|cartão de identidade|licença|cancelamento|exame de ordem|bacharel|transferência"),
        ("incompat", "Incompatibilidades e impedimentos", r"incompatib|impediment|impedid[oa]|exercer a advocacia.{0,40}(cargo|função)|servidor.{0,40}advog|militar|magistrad|policial"),
        ("sociedade", "Sociedade de advogados", r"sociedade (individual|unipessoal)? ?de advog|sociedade unipessoal|sócio|advogados? associad|razão social|registro da sociedade"),
        ("infracoes", "Infrações e sanções disciplinares", r"infração|infrações|censura|suspensão|exclusão|advertência|multa|sanção|sanções|punid|reabilitação"),
        ("processo_disc", "Processo disciplinar", r"processo disciplinar|Tribunal de Ética|representação|instrução|relator|prescrição da pretensão punitiva|revisão do processo|recurso.{0,40}(Conselho|Tribunal de Ética)|poder de punir"),
        ("prerrogativas", "Direitos e prerrogativas", r"prerrogativ|direitos do advogado|inviolabilidade|sala de Estado[- ]Maior|desagravo|vista dos autos|examinar.{0,30}autos|ingressar livremente|preso em flagrante|busca e apreensão.{0,40}escritório|imunidade profissional|retirar-se"),
        ("publicidade", "Publicidade profissional", r"publicidade|anúnci|propaganda|redes sociais|internet|site|divulga|mala direta|captação de clientela|patrocín|placa|outdoor|marketing|entrevista"),
        ("sigilo", "Sigilo profissional", r"sigilo|segredo profissional|confidencial|depor como testemunha"),
        ("cliente", "Relação com o cliente e mandato", r"mandato|procuração|renúncia|renunciar|substabelec|revogação|conflito de interesses|patrocin(ar|ou) .{0,30}(parte contrária|ambas)|cliente|confiança"),
        ("orgaos_oab", "Órgãos da OAB e eleições", r"Conselho Federal|Conselho Seccional|Seccional|Subseç|Caixa de Assistência|eleiç|chapa|diretoria|mandato.{0,20}(conselheiro|diretor)|anuidade|contribuiç|Presidente da OAB|Exame de Ordem.{0,30}(Conselho|regulament)"),
        ("adv_empregado", "Advogado empregado e advocacia pública", r"advogado empregado|empregado.{0,40}advog|relação de emprego|jornada|advocacia pública|procurador|dedicação exclusiva|salário mínimo profissional"),
    ],
    "filosofia": [
        ("positivismo", "Positivismo jurídico (Kelsen, Hart, Bobbio)", r"Kelsen|Hart\b|Bobbio|positivis|norma fundamental|teoria pura|regra de reconhecimento|ordenamento"),
        ("justica", "Teorias da justiça (Aristóteles, Rawls)", r"Aristóteles|Rawls|justiça distributiva|justiça corretiva|equidade|véu da ignorância|Nicômaco|Sandel|Nozick|utilitaris|Bentham|Stuart Mill"),
        ("jusnatural", "Jusnaturalismo e contratualismo", r"jusnatural|direito natural|Tomás de Aquino|Agostinho|Grócio|Hobbes|Locke|Rousseau|contrato social|estado de natureza|Pufendorf|Cícero"),
        ("pospositiv", "Princípios e pós-positivismo (Dworkin, Alexy)", r"Dworkin|Alexy|princípio|ponderação|pós-positiv|Radbruch|Habermas|Perelman|argumentação|Viehweg|tópica"),
        ("hermeneutica", "Interpretação e hermenêutica", r"interpretaç|hermenêutic|lacuna|analogia|Savigny|Ihering|Engisch|Miguel Reale|tridimensional|antinomia"),
        ("modernos", "Kant, Hegel, Marx e Weber", r"Kant|Hegel|Marx|Weber|Maquiavel|Montesquieu|Arendt|Foucault|Luhmann|Durkheim|Nietzsche|Schmitt"),
    ],
    "constitucional": [
        ("controle", "Controle de constitucionalidade", r"controle de constitucionalidade|inconstitucional|ADI\b|ADC\b|ADPF|ação direta|arguição de descumprimento|cláusula de reserva de plenário|efeitos? (vinculante|erga omnes)|modulação|controle difuso|controle concentrado|recurso extraordinário"),
        ("direitos_fund", "Direitos e garantias fundamentais", r"direitos? fundamenta|dignidade|igualdade|liberdade de|direito à (vida|privacidade|intimidade)|inviolabilidade do domicílio|sigilo|direito de reunião|associação|propriedade|direito adquirido|devido processo|contraditório|direitos sociais|educação|saúde"),
        ("remedios", "Remédios constitucionais", r"habeas corpus|habeas data|mandado de segurança|mandado de injunção|ação popular|ação civil pública"),
        ("org_estado", "Organização do Estado e competências", r"competência (legislativa|privativa|concorrente|comum|da União|dos Estados|dos Municípios)|União|Estado-membro|Estados-membros|Municípi|Distrito Federal|federa|intervenção|autonomia|repartição de competências|bens da União|Território"),
        ("legislativo", "Poder Legislativo e processo legislativo", r"Congresso|Senado|Câmara dos Deputados|Deputad|Senador|parlamentar|imunidade parlamentar|CPI|comissão parlamentar|medida provisória|processo legislativo|projeto de lei|lei complementar|emenda|veto|sanção|Tribunal de Contas|decreto legislativo|iniciativa"),
        ("executivo", "Poder Executivo", r"Presidente da República|Vice-Presidente|Ministro de Estado|crime de responsabilidade|impeachment|Governador|Prefeito|decreto autônomo|Conselho da República"),
        ("judiciario", "Poder Judiciário e funções essenciais", r"Poder Judiciário|STF|Supremo|STJ|CNJ|Conselho Nacional de Justiça|magistra|juiz|tribunal|Ministério Público|Defensoria|Advocacia-Geral|súmula vinculante|reclamação|quinto constitucional|precatório"),
        ("nacionalidade", "Nacionalidade e direitos políticos", r"nacionalidade|brasileiro nato|naturaliza|estrangeir|extradição|direitos políticos|elegib|inelegib|alistamento|voto|sufrágio|cassação|perda.{0,20}mandato"),
        ("ordem_social", "Ordem social e econômica", r"ordem econômica|ordem social|seguridade|previdência|meio ambiente|família|criança|índio|indígena|cultura|desporto|comunicação social|ciência e tecnologia|política urbana|reforma agrária|sistema financeiro"),
        ("poder_const", "Poder constituinte e emendas", r"poder constituinte|constituinte originário|emenda constitucional|cláusula pétrea|limites ao poder de reforma|mutação constitucional|recepção|repristinação|desconstitucionalização|eficácia das normas"),
    ],
    "dh": [
        ("interamericano", "Sistema interamericano", r"interamerican|Convenção Americana|Pacto de San José|San José da Costa Rica|OEA|Protocolo de San Salvador|Belém do Pará"),
        ("global", "Sistema global (ONU)", r"ONU|Nações Unidas|Declaração Universal|Pacto Internacional|Conselho de Direitos Humanos|relator(a)? especial|Comitê|Alto Comissariado|Revisão Periódica"),
        ("incorporacao", "Tratados de DH no direito brasileiro", r"supralegal|emenda constitucional|status|incorpora|§ ?3º|hierarquia|controle de convencionalidade|incidente de deslocamento|federalização"),
        ("vulneraveis", "Grupos vulneráveis", r"deficiência|idos[oa]|igualdade racial|racism|negr|quilombol|indígen|povos|mulher|violência doméstica|Maria da Penha|LGBT|travesti|transexual|gênero|orientação sexual|refugiad|migrante|criança|população em situação de rua"),
        ("tortura", "Tortura, escravidão e tráfico de pessoas", r"tortura|escrav|trabalho análogo|tráfico de pessoas|desaparecimento forçado|tratamento (cruel|degradante)"),
    ],
    "internacional": [
        ("tratados", "Tratados internacionais", r"tratado|Convenção de Viena|ratifica|reserva|denúncia|vigência internacional|referendo do Congresso|jus cogens|costume internacional"),
        ("dipr", "Direito internacional privado (LINDB)", r"LINDB|Lei de Introdução|lei aplicável|domicílio|elemento de conexão|regras de conexão|conflito de leis|contrato internacional|casamento.{0,40}exterior|sucessão.{0,40}(exterior|estrangeir)|bens situados"),
        ("cooperacao", "Cooperação jurídica internacional", r"carta rogatória|homologação|sentença estrangeira|exequatur|auxílio direto|cooperação jurídica|STJ|citação.{0,30}exterior|sequestro internacional|Haia"),
        ("migracao", "Nacionalidade, migração e extradição", r"extradição|expulsão|deportação|repatriação|asilo|refúgio|refugiad|apátrida|migra|visto|naturaliza|nacionalidade"),
        ("organizacoes", "Organizações e tribunais internacionais", r"Organização Mundial do Comércio|OMC|Mercosul|ONU|Conselho de Segurança|Corte Internacional|Tribunal Penal Internacional|Estatuto de Roma|organização internacional|União Europeia|Bretton Woods|FMI|OIT"),
        ("imunidade", "Imunidades e agentes diplomáticos", r"imunidade|diplomát|cônsul|consular|embaixad|Estado estrangeiro|missão diplomática"),
    ],
    "tributario": [
        ("limitacoes", "Princípios e imunidades tributárias", r"imunidade|anterioridade|noventena|legalidade|irretroatividade|isonomia|confisco|capacidade contributiva|limitações ao poder de tributar|templos|livros|partidos políticos|imunidade recíproca"),
        ("especies", "Espécies tributárias e competência", r"taxa|contribuição de melhoria|empréstimo compulsório|contribuição (social|de intervenção|especial)|CIDE|competência tributária|espécies tributárias|tributo|preço público|tarifa"),
        ("impostos", "Impostos em espécie", r"ICMS|IPI|ISS|IPTU|IPVA|ITBI|ITCMD|ITR|IOF|imposto (de|sobre) renda|IRPF|IRPJ|imposto sobre|IBS|CBS|imposto seletivo|alíquota|base de cálculo"),
        ("credito", "Obrigação e crédito tributário", r"fato gerador|obrigação tributária|lançamento|crédito tributário|suspensão da exigibilidade|extinção do crédito|exclusão do crédito|isenção|anistia|decadência|prescrição|parcelamento|compensação|moratória|depósito do montante|pagamento|remissão|transação|consignação"),
        ("responsabilidade", "Responsabilidade tributária", r"responsabilidade|responsável|substituição tributária|sucess(or|ão)|solidari|sócio|administrador|terceiros|adquirente|redirecionamento|denúncia espontânea"),
        ("processo_trib", "Processo tributário e execução fiscal", r"execução fiscal|embargos à execução|mandado de segurança|ação anulatória|repetição de indébito|ação declaratória|consignação em pagamento|certidão|dívida ativa|CDA|exceção de pré-executividade|garantia|penhora|medida cautelar fiscal"),
    ],
    "administrativo": [
        ("licitacoes", "Licitações e contratos", r"licitaç|Lei nº 14\.133|Lei nº 8\.666|pregão|concorrência|dispensa|inexigib|contrato administrativo|contratad[oa]|edital|reequilíbrio|cláusulas exorbitantes|diálogo competitivo"),
        ("servidores", "Agentes e servidores públicos", r"servidor|servidores|Lei nº 8\.112|cargo|concurso público|estabilidade|estágio probatório|acumulação|aposentadoria|remuneração|vencimento|agente público|nomeação|exoneração|demissão|disponibilidade|reintegração"),
        ("improbidade", "Improbidade administrativa", r"improbidade|Lei nº 8\.429|enriquecimento ilícito|lesão ao erário|ato ímprobo"),
        ("responsabilidade", "Responsabilidade civil do Estado", r"responsabilidade civil do Estado|responsabilidade (objetiva|subjetiva)|§ ?6º|indeniza|dano|ação regressiva|risco administrativo|omissão estatal"),
        ("atos", "Atos administrativos", r"ato administrativo|atos administrativos|anulação|revogação|convalida|discricionári|vinculad|motivação|motivo|mérito administrativo|autoexecutoriedade|presunção de legitimidade|cassação|autotutela|licença|autorização|permissão"),
        ("organizacao", "Organização administrativa", r"autarquia|fundação pública|empresa pública|sociedade de economia mista|agência reguladora|agência executiva|consórcio público|administração (direta|indireta)|descentraliza|desconcentra|organizaç(ão|ões) social|OSCIP|terceiro setor|estatais|Lei nº 13\.303"),
        ("servicos", "Serviços públicos e concessões", r"serviço público|serviços públicos|concessão|concessionári|permissionári|parceria público|PPP|tarifa|delegação|encampação|caducidade"),
        ("intervencao", "Intervenção na propriedade e bens públicos", r"desapropria|tombamento|servidão administrativa|requisição|ocupação temporária|limitação administrativa|bens públicos|bem público|afetação|imóvel público|usucapião"),
        ("processo_adm", "Processo administrativo e controle", r"processo administrativo|Lei nº 9\.784|recurso administrativo|controle|Tribunal de Contas|Lei Anticorrupção|Lei nº 12\.846|acordo de leniência|poder de polícia|poder hierárquico|poder disciplinar|poder regulamentar|abuso de poder|prescrição"),
    ],
    "ambiental": [
        ("licenciamento", "Licenciamento e estudo de impacto", r"licenciamento|licença (prévia|de instalação|de operação|ambiental)|EIA|RIMA|estudo (prévio )?de impacto|impacto ambiental|audiência pública|Lei Complementar nº 140|órgão licenciador"),
        ("responsabilidade", "Responsabilidade ambiental", r"responsabilidade|dano ambiental|Lei nº 9\.605|crime ambiental|infração administrativa|sanç|multa|reparação|poluidor-pagador|propter rem|desconsideração|termo de ajustamento|ação civil pública"),
        ("areas_protegidas", "Áreas protegidas e Código Florestal", r"unidade de conservação|SNUC|Lei nº 9\.985|Código Florestal|Lei nº 12\.651|área de preservação permanente|APP|reserva legal|Mata Atlântica|vegetação|parque|reserva extrativista|floresta"),
        ("competencia", "Competência e princípios ambientais", r"competência|princípio|precaução|prevenção|desenvolvimento sustentável|art\. 225|Política Nacional do Meio Ambiente|Lei nº 6\.938|SISNAMA|CONAMA|função socioambiental"),
        ("recursos", "Recursos hídricos, resíduos e poluição", r"recursos hídricos|água|resíduos sólidos|logística reversa|saneamento|poluição|agrotóxic|mineração|patrimônio genético|biodiversidade|fauna|pesca|mudança do clima"),
    ],
    "civil": [
        ("parte_geral", "Parte geral (pessoas, bens, negócio jurídico)", r"personalidade|capacidade|incapa|curatela|ausência|pessoa jurídica|desconsideração|domicílio|bens (móveis|imóveis|públicos)|negócio jurídico|nulidade|anulabilidade|anulável|nulo|erro|dolo|coação|lesão|estado de perigo|fraude contra credores|simulação|condição|termo|encargo|direitos da personalidade|nome"),
        ("prescricao", "Prescrição e decadência", r"prescrição|prescricional|decadência|decadencial|prazo prescricional|interrupção da prescrição"),
        ("obrigacoes", "Obrigações", r"obrigaç|credor|devedor|adimplemento|inadimplemento|pagamento|mora|juros|cláusula penal|arras|dação|novação|compensação|remissão|consignação|sub-rogação|solidariedade|solidári|cessão de crédito|assunção de dívida|perdas e danos"),
        ("contratos", "Contratos", r"contrato|contratante|compra e venda|locação|locatári|locador|doação|mútuo|comodato|fiança|fiador|empreitada|seguro|prestação de serviço|transporte|corretagem|evicção|vícios redibitórios|resolução|onerosidade excessiva|boa-fé|promessa de compra|Lei nº 8\.245"),
        ("resp_civil", "Responsabilidade civil", r"responsabilidade civil|dano moral|danos morais|dano material|indenizaç|ato ilícito|culpa|nexo|responsabilidade objetiva|abuso de direito|lucros cessantes|dano estético|perda de uma chance"),
        ("reais", "Posse, propriedade e direitos reais", r"posse|possuidor|possessóri|propriedade|proprietári|usucapião|condomínio|vizinhança|servidão|usufruto|uso|habitação|superfície|hipoteca|penhor|anticrese|alienação fiduciária|direito real|direitos reais|registro de imóveis|laje|multipropriedade|imóvel"),
        ("familia", "Família", r"casamento|cônjuge|união estável|companheir|regime de bens|comunhão|separação|divórcio|alimentos|pensão alimentícia|poder familiar|guarda|filiação|paternidade|parentesco|adoção|tutela|bem de família|alienação parental"),
        ("sucessoes", "Sucessões", r"herança|herdeir|sucessão|sucessões|testamento|testador|legado|legatári|inventário|partilha|legítima|colação|deserdação|indignidade|codicilo|espólio|meação|renúncia à herança"),
    ],
    "eca": [
        ("ato_infracional", "Ato infracional e medidas socioeducativas", r"ato infracional|medida socioeducativa|medidas socioeducativas|internação|semiliberdade|liberdade assistida|prestação de serviços à comunidade|advertência|remissão|apreensão|SINASE|adolescente infrator"),
        ("familia_subst", "Família substituta, adoção e guarda", r"adoção|adotante|adotand|guarda|tutela|família substituta|família extensa|acolhimento|cadastro|destituição do poder familiar|perda.{0,20}poder familiar|suspensão do poder familiar|apadrinhamento|adoção internacional"),
        ("direitos", "Direitos fundamentais da criança", r"direito à (vida|saúde|educação|convivência)|educação|escola|saúde|vacina|trabalho.{0,30}(adolescente|menor)|aprendiz|profissionaliza|convivência familiar|lazer|castigo físico|viagem|autorização para viajar|prevenção"),
        ("rede_protecao", "Conselho Tutelar e Justiça da Infância", r"Conselho Tutelar|conselheiro tutelar|Justiça da Infância|Vara da Infância|juiz da infância|Ministério Público|medida de proteção|medidas de proteção|entidade de atendimento|conselho de direitos|procedimento|recurso|competência"),
        ("crimes_eca", "Crimes e infrações administrativas", r"crime|infração administrativa|pornografia|venda de bebida|hospedar|corrupção de menores|submeter.{0,30}vexame|exploração sexual"),
    ],
    "consumidor": [
        ("responsabilidade", "Responsabilidade por fato e vício", r"fato do produto|fato do serviço|vício|defeito|acidente de consumo|recall|responsabilidade|solidári|comerciante|fabricante|prazo (decadencial|prescricional)|reclamar|garantia|substituição do produto|abatimento"),
        ("praticas", "Oferta, publicidade e práticas abusivas", r"oferta|publicidade|propaganda|enganosa|abusiva|prática abusiva|práticas abusivas|venda casada|cobrança|cadastro|banco de dados|negativa|SPC|Serasa|informação|preço|orçamento|amostra grátis"),
        ("contratos_cons", "Proteção contratual", r"cláusula|contrato de adesão|arrependimento|direito de arrependimento|sete dias|fora do estabelecimento|internet|nulidade|revisão|superendividamento|crédito|financiamento|plano de saúde|seguro"),
        ("defesa_juizo", "Defesa do consumidor em juízo", r"ação coletiva|ações coletivas|interesses? (difusos|coletivos|individuais homogêneos)|inversão do ônus|ônus da prova|coisa julgada|legitimidade|Ministério Público|associação|PROCON|Defensoria|foro|competência|desconsideração"),
        ("conceitos", "Relação de consumo (conceitos)", r"consumidor (por equiparação|bystander|equiparado)|destinatário final|relação de consumo|conceito de (consumidor|fornecedor)|fornecedor|vulnerabilidade|hipossuficiência|pessoa jurídica.{0,40}consumidor|serviço bancário|instituição financeira"),
    ],
    "empresarial": [
        ("societario", "Direito societário", r"sociedade|sócio|quotas?|cotas?|ações|acionista|assembleia|administrador|conselho de administração|capital social|dissolução|retirada|exclusão de sócio|limitada|anônima|contrato social|estatuto social|debênture|dividendo|incorporação|fusão|cisão|cooperativa|conta de participação"),
        ("falencia", "Falência e recuperação", r"falência|falid|recuperação (judicial|extrajudicial)|Lei nº 11\.101|administrador judicial|credores|classificação dos créditos|plano de recuperação|assembleia de credores|habilitação|massa falida|concordata"),
        ("titulos", "Títulos de crédito", r"título de crédito|títulos de crédito|cheque|nota promissória|letra de câmbio|duplicata|endosso|endossatári|aval|avalista|protesto|cambial|sacad|emitente|cédula de crédito|conhecimento de depósito"),
        ("empresario", "Empresário, registro e estabelecimento", r"empresári|empresa|Junta Comercial|registro|nome empresarial|estabelecimento|trespasse|ponto empresarial|microempresa|empresa de pequeno porte|EIRELI|MEI|escrituração|livros|preposto|gerente|capacidade"),
        ("propriedade_ind", "Propriedade industrial", r"marca|patente|desenho industrial|INPI|Lei nº 9\.279|propriedade industrial|invenção|modelo de utilidade|indicação geográfica|concorrência desleal"),
        ("contratos_emp", "Contratos empresariais", r"contrato de (agência|distribuição|comissão|representação|franquia|leasing|arrendamento mercantil|faturização|factoring|alienação fiduciária)|franquia|representação comercial|contratos? empresaria|arrendamento mercantil|shopping"),
    ],
    "proc_civil": [
        ("recursos", "Recursos", r"recurso|apelação|agravo|embargos de declaração|recurso especial|recurso extraordinário|embargos de divergência|recurso ordinário|efeito (suspensivo|devolutivo)|preparo|reexame|remessa necessária|tribunal"),
        ("execucao", "Execução e cumprimento de sentença", r"execução|executad|exequente|cumprimento de sentença|título executivo|penhora|impenhorab|embargos à execução|impugnação ao cumprimento|expropriação|adjudicação|leilão|alienação judicial|devedor|prisão civil|alimentos"),
        ("tutela", "Tutela provisória", r"tutela (provisória|de urgência|da evidência|antecipada|cautelar)|liminar|estabiliza|periculum|perigo de dano|arresto|sequestro"),
        ("procedimento", "Procedimento comum e sentença", r"petição inicial|emenda da inicial|indeferimento|contestação|reconvenção|revelia|audiência de conciliação|saneamento|julgamento antecipado|improcedência liminar|sentença|coisa julgada|prova|perícia|testemunha|ônus da prova|depoimento|ação rescisória"),
        ("competencia", "Jurisdição e competência", r"competência|incompetência|foro|juízo|conexão|continência|prevenção|conflito de competência|jurisdição|cooperação nacional|arbitragem|convenção de arbitragem"),
        ("partes", "Partes, litisconsórcio e terceiros", r"litisconsórcio|litisconsorte|intervenção de terceiros|assistência|assistente|denunciação da lide|chamamento ao processo|amicus curiae|incidente de desconsideração|legitimidade|substituição processual|capacidade processual|advogado|Ministério Público|Defensoria|gratuidade|honorários|sucumbência"),
        ("especiais", "Procedimentos especiais", r"ação (possessória|monitória|de consignação|de exigir contas|de usucapião|de divisão|de demarcação|de alimentos|de família|de dissolução)|possessóri|monitória|inventário|embargos de terceiro|procedimento especial|interdição|curatela|habilitação|restauração de autos"),
        ("coletivos", "Juizados, MS e processos coletivos", r"Juizado|Lei nº 9\.099|mandado de segurança|ação civil pública|ação popular|processo coletivo|IRDR|incidente de resolução|incidente de assunção|precedente|repetitivo|reclamação"),
        ("atos", "Atos processuais, prazos e nulidades", r"prazo|intimação|citação|contagem|dias úteis|preclusão|nulidade|negócio jurídico processual|calendário processual|ato processual|atos processuais|suspensão do processo|extinção do processo"),
    ],
    "penal": [
        ("teoria_crime", "Teoria do crime", r"dolo|doloso|culpa|culposo|tentativa|consumação|desistência voluntária|arrependimento (eficaz|posterior)|crime impossível|erro (de tipo|de proibição|sobre)|legítima defesa|estado de necessidade|estrito cumprimento|exercício regular|excludente|ilicitude|culpabilidade|imputabilidade|inimputável|embriaguez|coação|obediência hierárquica|concurso de (agentes|pessoas)|partícipe|coautor|nexo causal|omissão|insignificância|iter criminis|princípio"),
        ("pena", "Aplicação e execução da pena", r"pena|dosimetria|agravante|atenuante|causa de (aumento|diminuição)|regime (inicial|fechado|semiaberto|aberto)|substituição|restritiva de direitos|multa|sursis|suspensão condicional da pena|livramento condicional|concurso (material|formal)|crime continuado|reincid|medida de segurança|progressão|remição|detração|efeitos da condenação"),
        ("punibilidade", "Extinção da punibilidade e prescrição", r"extinção da punibilidade|prescrição|decadência|perempção|perdão judicial|renúncia|abolitio|anistia|graça|indulto|retroatividade|lei penal no tempo|lei mais benéfica"),
        ("contra_pessoa", "Crimes contra a pessoa", r"homicídio|feminicídio|infanticídio|aborto|lesão corporal|induzimento|instigação|auxílio ao suicídio|omissão de socorro|maus-tratos|calúnia|difamação|injúria|ameaça|sequestro|cárcere privado|constrangimento ilegal|violação de domicílio|perseguição|stalking"),
        ("patrimonio", "Crimes contra o patrimônio", r"furto|roubo|latrocínio|extorsão|estelionato|apropriação indébita|receptação|dano|usurpação|fraude|esbulho"),
        ("adm_publica", "Crimes contra a Administração Pública e a fé pública", r"peculato|corrupção|concussão|prevaricação|condescendência|advocacia administrativa|desacato|desobediência|resistência|tráfico de influência|contrabando|descaminho|falsidade|falsificação|moeda falsa|uso de documento falso|denunciação caluniosa|falso testemunho|fraude processual|coação no curso"),
        ("especial", "Legislação penal especial", r"Lei de Drogas|Lei nº 11\.343|tráfico|entorpecente|arma|Estatuto do Desarmamento|Lei nº 10\.826|trânsito|Código de Trânsito|embriaguez ao volante|hediondo|Maria da Penha|violência doméstica|abuso de autoridade|lavagem|organização criminosa|tortura|crimes ambientais|crimes contra o consumidor|Lei nº 9\.099|racismo|ECA"),
        ("dignidade_sexual", "Crimes contra a dignidade sexual", r"estupro|estupro de vulnerável|importunação sexual|assédio sexual|violação sexual|favorecimento da prostituição|dignidade sexual|registro não autorizado"),
    ],
    "proc_penal": [
        ("inquerito_acao", "Inquérito e ação penal", r"inquérito|investigação|autoridade policial|delegado|indiciamento|arquivamento|denúncia|queixa|ação penal|representação do ofendido|requisição|acordo de não persecução|ANPP|trancamento|justa causa|assistente de acusação|ação penal privada|perempção"),
        ("prisoes", "Prisões e medidas cautelares", r"prisão (preventiva|temporária|em flagrante|domiciliar)|flagrante|audiência de custódia|liberdade provisória|fiança|medida cautelar|medidas cautelares|monitoração|relaxamento|revogação da prisão"),
        ("provas", "Provas", r"prova|provas|perícia|exame de corpo de delito|interrogatório|testemunha|confissão|reconhecimento de pessoas|busca e apreensão|interceptação|cadeia de custódia|ilícita|colaboração premiada|acareação|documento"),
        ("competencia", "Competência e jurisdição", r"competência|incompetência|foro por prerrogativa|Justiça Federal|Justiça Estadual|Justiça Militar|conexão|continência|desaforamento|juiz natural|prevenção"),
        ("procedimentos", "Procedimentos e Tribunal do Júri", r"Júri|Tribunal do Júri|pronúncia|impronúncia|absolvição sumária|desclassificação|quesito|jurado|plenário|procedimento (comum|sumário|sumaríssimo|ordinário)|Juizado Especial Criminal|transação penal|suspensão condicional do processo|Lei nº 9\.099|resposta à acusação|citação|revelia|emendatio|mutatio|sentença"),
        ("recursos", "Recursos, habeas corpus e revisão", r"recurso|apelação|recurso em sentido estrito|embargos|agravo|carta testemunhável|habeas corpus|revisão criminal|mandado de segurança|reformatio|efeito"),
        ("nulidades", "Nulidades", r"nulidade|nulidades|nulo|prejuízo|pas de nullité|cerceamento de defesa"),
        ("execucao_penal", "Execução penal", r"execução penal|Lei de Execução Penal|LEP|progressão|remição|livramento condicional|saída temporária|falta grave|regime disciplinar|agravo em execução|unificação de penas|indulto"),
    ],
    "previdenciario": [
        ("beneficios", "Benefícios previdenciários", r"aposentadoria|pensão por morte|auxílio|benefício por incapacidade|salário-maternidade|salário-família|reabilitação|renda mensal|cálculo do benefício|revisão"),
        ("segurados", "Segurados, carência e custeio", r"segurad|dependente|carência|qualidade de segurado|período de graça|contribuição|contribuinte individual|facultativo|segurado especial|filiação|tempo de contribuição|custeio"),
        ("assistencia", "Assistência social e BPC", r"assistência social|benefício de prestação continuada|BPC|LOAS|miserabilidade|renda per capita|idoso|pessoa com deficiência"),
    ],
    "financeiro": [
        ("orcamento", "Leis orçamentárias", r"orçament|lei orçamentária|LOA|LDO|diretrizes orçamentárias|plano plurianual|PPA|crédito (adicional|suplementar|especial|extraordinário)|emenda parlamentar|vinculação de receita"),
        ("lrf", "Responsabilidade fiscal e despesa", r"Responsabilidade Fiscal|LRF|Lei Complementar nº 101|despesa|despesa com pessoal|limite|renúncia de receita|restos a pagar|empenho|transferências voluntárias|receita corrente líquida"),
        ("credito_publico", "Receita, dívida e precatórios", r"receita|dívida pública|operação de crédito|precatório|requisição de pequeno valor|RPV|fundo|repartição de receitas|fundo de participação|Tribunal de Contas|fiscalização|controle externo"),
    ],
    "eleitoral": [
        ("elegibilidade", "Elegibilidade e inelegibilidade", r"elegib|inelegib|Ficha Limpa|Lei Complementar nº 64|registro de candidatura|condições de elegibilidade|desincompatibilização|domicílio eleitoral|filiação partidária"),
        ("propaganda", "Propaganda e campanha eleitoral", r"propaganda|campanha|pesquisa eleitoral|debate|internet|arrecadação|gastos|prestação de contas|financiamento"),
        ("partidos", "Partidos políticos", r"partido|partidos|federação partidária|coligação|fidelidade partidária|fundo partidário|convenção"),
        ("contencioso", "Ações e crimes eleitorais, Justiça Eleitoral", r"ação de investigação|AIJE|impugnação|recurso contra a expedição|abuso de poder|captação ilícita|crime eleitoral|Justiça Eleitoral|TSE|TRE|juiz eleitoral|cassação|diplomação"),
    ],
    "trabalho": [
        ("relacao_emprego", "Relação de emprego e contrato", r"vínculo|relação de emprego|empregado|empregador|contrato de trabalho|subordinação|pessoalidade|contrato de experiência|prazo determinado|intermitente|teletrabalho|doméstic|aprendiz|grupo econômico|sucessão|pejotização|autônomo|estagiário"),
        ("jornada", "Jornada e descanso", r"jornada|hora extra|horas extras|horas extraordinárias|intervalo|banco de horas|compensação|turno|sobreaviso|prontidão|trabalho noturno|adicional noturno|descanso semanal|repouso|horas in itinere|tempo à disposição|12x36"),
        ("remuneracao", "Salário e remuneração", r"salário|remuneração|gorjeta|comissão|gratificação|equiparação salarial|isonomia salarial|desconto|13º|décimo terceiro|salário-utilidade|in natura|prêmio|diárias|PLR|participação nos lucros"),
        ("rescisao", "Extinção do contrato, estabilidade e FGTS", r"rescisão|dispensa|justa causa|aviso prévio|FGTS|multa de 40%|estabilidade|garantia de emprego|gestante|acidente do trabalho|cipeiro|dirigente sindical|pedido de demissão|rescisão indireta|culpa recíproca|distrato|verbas rescisórias"),
        ("ferias", "Férias", r"férias|abono pecuniário|terço constitucional|férias coletivas"),
        ("terceirizacao", "Terceirização e trabalho temporário", r"terceiriza|tomador|prestadora de serviços|trabalho temporário|Lei nº 6\.019|responsabilidade subsidiária|cooperativa"),
        ("coletivo", "Direito coletivo do trabalho", r"sindicato|sindical|convenção coletiva|acordo coletivo|negociação coletiva|greve|contribuição (sindical|confederativa|assistencial)|negociado sobre o legislado|comissão de representantes|ultratividade"),
        ("saude_seguranca", "Saúde, segurança e adicionais", r"insalubridade|periculosidade|adicional|EPI|equipamento de proteção|acidente|doença ocupacional|CIPA|meio ambiente do trabalho|dano extrapatrimonial|assédio|dano moral"),
        ("alteracao", "Alteração, suspensão e interrupção do contrato", r"alteração contratual|transferência|jus variandi|rebaixamento|reversão|suspensão do contrato|interrupção|licença|afastamento|auxílio-doença|serviço militar"),
    ],
    "proc_trabalho": [
        ("recursos", "Recursos trabalhistas", r"recurso|recurso ordinário|recurso de revista|agravo de instrumento|agravo de petição|embargos (de declaração|no TST)|depósito recursal|preparo|transcendência|efeito devolutivo|juízo de admissibilidade"),
        ("execucao", "Execução trabalhista", r"execução|executad|exequente|penhora|embargos à execução|impugnação à sentença de liquidação|liquidação|cálculos|desconsideração|responsabilidade.{0,20}sócio|praça|leilão|adjudicação|BACEN|SISBAJUD|precatório|prescrição intercorrente"),
        ("procedimento", "Procedimento, audiência e provas", r"audiência|revelia|confissão|preposto|arquivamento|sumaríssimo|rito|conciliação|proposta de acordo|testemunha|prova|perícia|ônus da prova|contestação|reconvenção|petição inicial|emenda|valor da causa|pedido líquido|exceção de incompetência|sentença"),
        ("competencia", "Competência da Justiça do Trabalho", r"competência|incompetência|Justiça do Trabalho|Justiça Comum|Justiça Federal|foro|localidade|conflito de competência|jurisdição"),
        ("acoes_especiais", "Ações especiais e acordos", r"ação rescisória|mandado de segurança|dissídio coletivo|ação de cumprimento|inquérito para apuração de falta grave|consignação em pagamento|ação anulatória|homologação de acordo extrajudicial|acordo extrajudicial|habeas corpus|ação civil pública|tutela provisória|tutela de urgência"),
        ("custas_honorarios", "Custas, honorários e gratuidade", r"custas|honorários|sucumbência|gratuidade|justiça gratuita|assistência judiciária|jus postulandi|litigância de má-fé|multa"),
        ("prazos_nulidades", "Prazos, prescrição e nulidades", r"prazo|prescrição|nulidade|notificação|intimação|citação|contagem|dias úteis|recesso|férias forenses|preclusão"),
    ],
}

def _alternativas(padrao):
    """Divide 'a|b(c|d)|e' nas alternativas de nível superior: ['a', 'b(c|d)', 'e']."""
    partes, nivel, atual = [], 0, ""
    for ch in padrao:
        if ch == "(":
            nivel += 1
        elif ch == ")":
            nivel -= 1
        if ch == "|" and nivel == 0:
            partes.append(atual)
            atual = ""
        else:
            atual += ch
    partes.append(atual)
    return partes


_TERMOS = {m: [(tid, re.compile(t, re.I)) for tid, _, p in lista for t in _alternativas(p)] for m, lista in TEMAS.items()}
_NOMES = {m: {tid: nome for tid, nome, _ in lista} for m, lista in TEMAS.items()}


def atribuir_temas(materia, questoes):
    """Grava em cada questão o campo "t" com o tema de maior evidência (ou "outros").

    Cada termo vale log(N/df): termos que aparecem em quase toda questão da matéria
    (ex.: "cliente" em Ética, "pena" em Penal) quase não pesam; termos específicos decidem.
    O enunciado conta em dobro em relação às alternativas.
    """
    termos = _TERMOS.get(materia, [])
    textos = [(q["q"], " ".join(q["a"])) for q in questoes]
    n = len(questoes)
    df = [sum(1 for e, a in textos if r.search(e) or r.search(a)) for _, r in termos]
    peso = [math.log((n + 1) / (d + 1)) for d in df]
    for q, (enun, alts) in zip(questoes, textos):
        pont = {}
        for (tid, r), w in zip(termos, peso):
            k = 2 * len(r.findall(enun)) + len(r.findall(alts))
            if k:
                pont[tid] = pont.get(tid, 0.0) + w * min(k, 4)
        q["t"] = max(pont, key=pont.get) if pont and max(pont.values()) > 0.5 else "outros"


def resumo_de_temas(banco):
    """{matéria: [{id, nome, n, rec}]} com os temas ordenados do mais para o menos frequente."""
    saida = {}
    for materia, questoes in banco.items():
        nomes = _NOMES.get(materia, {})
        contagem = {}
        for q in questoes:
            contagem[q["t"]] = contagem.get(q["t"], 0) + 1
        ordenados = sorted((t for t in contagem if t != "outros"), key=lambda t: -contagem[t])
        total, acum, lista = len(questoes), 0, []
        for tid in ordenados:
            rec = acum < COBERTURA * total or len([x for x in lista if x["rec"]]) < 2
            acum += contagem[tid]
            lista.append({"id": tid, "nome": nomes[tid], "n": contagem[tid], "rec": rec})
        if "outros" in contagem:
            lista.append({"id": "outros", "nome": "Outros temas", "n": contagem["outros"], "rec": False})
        saida[materia] = lista
    return saida
