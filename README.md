Sentinela Apolo · v1.0.0

O Sentinela Apolo é um sistema de monitoramento de rede óptica (FTTx) com foco em:

detecção de quedas PPPoE e eventos críticos (por OLT/SLOT/PON/CTO);

alertas hierárquicos e registros de incidentes;

recuperações de assinantes com filtro por eventos críticos;

painel web responsivo com abas (Avisos, Logs de Sistema, Detalhamento) e sons para eventos críticos.
(O APP ALERTAMENTO NÃO TEM FUNCIONALIADES NA VERSÃO ATUAL)

Usuário ──> NGINX (frontend-proxy)
              │
              ▼
        Django (Gunicorn)
       ├── App Login 
       ├── App Monitoramento  ─┬─ Endpoints JSON (avisos, logs, detalhamento)
       │                       └─ Management Command: monitorador_de_rede.py
       				   └─ API de incidentes/status de queda
       └── App upload_csv (dados OLT/ONU)*
              │
              ▼
           PostgreSQL

           ▲
           │ (SSH/CLI Juniper)
           └── monitorador_de_rede coleta "show subscribers..." e grava em DB



* Em alguns setups, o modelo Onu/ Olt pode estar em Monitoramento.models — adapte conforme seu repositório.


Principais funcionalidades

Coleta periódica de assinantes ativos via SSH no concentrador PPPoE (Juniper).

Cálculo de diferença (diff) entre leituras para detectar quedas e recuperações.

Hierarquia de alerta por OLT/SLOT/PON/CTO.

Filtro de recuperação: só gera avisos de reconexão para logins que participaram de quedas críticas anteriores.

Alertas sonoros somente para eventos críticos.

Frontend responsivo com Bootstrap/Font Awesome e autoatualização por fetch() a cada 5s.


Estrutura de pastas e arquivos (papéis)
Raiz do projeto

docker-compose.yml
Orquestra os serviços:

db: PostgreSQL (volume persistente);

django-web: app Django (Gunicorn + entrypoint que faz collectstatic, migrate e inicia o monitorador_de_rede);

frontend-proxy: NGINX como reverse proxy (porta 8001 → 80 dentro do container).
Inclui healthcheck para django-web.

nginx.conf
Configura o NGINX:

upstream django-server apontando para django-web:8000;

server_name para o seu subdomínio;

rota /static/ servida diretamente do volume montado;

proxy_pass das demais requisições para o Django.

requirements.txt
Dependências Python (Django, DRF opcional, Paramiko, django-recaptcha, etc).

entrypoint.prod.sh (caso exista no repo)
Script usado pelo serviço django-web para:

aguardar o banco; 2) rodar collectstatic; 3) migrate; 4) (opcional) iniciar o comando de monitoramento; 5) subir Gunicorn.

.env
Variáveis de ambiente (não versionar):
POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT, TZ, RECAPTCHA_SITE_KEY, etc.


Projeto Django (SentinelaApolo/)

SentinelaApolo/settings.py
Configurações principais:

ALLOWED_HOSTS, DEBUG, TIME_ZONE, USE_TZ;

Banco PostgreSQL via django-environ;

STATIC_ROOT/STATIC_URL para NGINX servir os estáticos;

INSTALLED_APPS: Login, Monitoramento, upload_csv (se usado), captcha;

reCAPTCHA (RECAPTCHA_PUBLIC_KEY, RECAPTCHA_PRIVATE_KEY);

parâmetro de negócio: MONITORAMENTO_MIN_DROP.

SentinelaApolo/urls.py
Roteamento de alto nível:

raiz → Login.urls (tela de login);

/monitoramento/ → Monitoramento.urls (painel e APIs);

/captcha/ → rotas do django-recaptcha (se necessário).

SentinelaApolo/wsgi.py
Ponto de entrada WSGI (usado pelo Gunicorn).

App Login/

Login/views.py

login_view: renderiza o form de login, valida reCAPTCHA (via Login/forms.py), autentica e redireciona para home/painel.

logout_view: finaliza sessão e redireciona para login.

Login/forms.py

LoginForm: campos username, password , com clean() chamando authenticate().

Login/urls.py

'' → login_view;

'logout/' → logout_view.

Login/templates/login/login.html
Template do login, com CSRF e widget do reCAPTCHA (V2 checkbox, tipicamente).


App Monitoramento/

Monitoramento/management/commands/monitorador_de_rede.py
Coração do monitoramento. Faz:

Conexão SSH (Paramiko) ao concentrador PPPoE (Juniper):

show subscribers count

show subscribers | display json

Diferença entre leituras: se diff >= MONITORAMENTO_MIN_DROP, registra queda crítica.

Monta hierarquia por OLT/SLOT/PON/CTO a partir do modelo Onu.

Recuperações: somente para logins que participaram de quedas críticas (evita “ruído”).

Cria Alertas (texto consolidado) + salva hierarchy_data em JSON.



Usa log_to_db() (em Monitoramento/utils.py) para registrar em SystemLog/NetworkAlert com timezone.localtime.

Monitoramento/models.py
Modelos centrais:

SystemLog: logs internos (INFO/WARNING/ERROR/DEBUG).

NetworkAlert: avisos de monitoramento (inclui hierarchy_data em JSON).

Alert: alertas agregados de desconexões (mensagem + hierarquia).

SubscriberSnapshot, DisconnectionRecord, DisconnectionAnalysis: apoio a históricos/análises.

Onu/Olt (se residirem aqui; em alguns projetos ficam no upload_csv.models).

Monitoramento/views.py
Endpoints protegidos por @login_required:

iniciar_monitoramento (POST/thread): dispara o comando de monitoramento (quando usado);

get_system_logs: retorna JSON dos SystemLog;

get_network_alerts: retorna JSON de NetworkAlert (com hierarchy_data);

get_logs: retorna JSON de Alert;

home_view: renderiza o painel (monitoramento.html).

Monitoramento/templates/monitoramento.html
Painel (Bootstrap/Font Awesome) com sidebar e abas:

Avisos: tabela preenchida via fetch('/monitoramento/network-alerts/');

Logs de Sistema: fetch('/monitoramento/system-logs/');

Detalhamento: tabela construída a partir de hierarchy_data (OLT/SLOT/PON/CTO, usuários).
Atualiza a cada 5s. Inclui alarme sonoro somente quando o nível/critério é crítico (implementado via JS).

Monitoramento/utils.py

log_to_db(kind, level, message, detail, hierarchy_data): utilitário padronizado para gravar logs/alertas com timezone.localtime, evitando duplicações e garantindo consistência.

Monitoramento/urls.py
Rotas do app:

'' ou 'home/' → painel;

'network-alerts/', 'system-logs/', 'logs/' → APIs JSON para o frontend.


App Monitoramento/

Monitoramento/management/commands/monitorador_de_rede.py
Coração do monitoramento. Faz:

Conexão SSH (Paramiko) ao concentrador PPPoE (Juniper):

show subscribers count

show subscribers | display json

Diferença entre leituras: se diff >= MONITORAMENTO_MIN_DROP, registra queda crítica.

Monta hierarquia por OLT/SLOT/PON/CTO a partir do modelo Onu.

Recuperações: somente para logins que participaram de quedas críticas (evita “ruído”).

Cria Alertas (texto consolidado) + salva hierarchy_data em JSON.



Usa log_to_db() (em Monitoramento/utils.py) para registrar em SystemLog/NetworkAlert com timezone.localtime.

Monitoramento/models.py
Modelos centrais:

SystemLog: logs internos (INFO/WARNING/ERROR/DEBUG).

NetworkAlert: avisos de monitoramento (inclui hierarchy_data em JSON).

Alert: alertas agregados de desconexões (mensagem + hierarquia).

SubscriberSnapshot, DisconnectionRecord, DisconnectionAnalysis: apoio a históricos/análises.

Onu/Olt (se residirem aqui; em alguns projetos ficam no upload_csv.models).

Monitoramento/views.py
Endpoints protegidos por @login_required:

iniciar_monitoramento (POST/thread): dispara o comando de monitoramento (quando usado);

get_system_logs: retorna JSON dos SystemLog;

get_network_alerts: retorna JSON de NetworkAlert (com hierarchy_data);

get_logs: retorna JSON de Alert;

home_view: renderiza o painel (monitoramento.html).

Monitoramento/templates/monitoramento.html
Painel (Bootstrap/Font Awesome) com sidebar e abas:

Avisos: tabela preenchida via fetch('/monitoramento/network-alerts/');

Logs de Sistema: fetch('/monitoramento/system-logs/');

Detalhamento: tabela construída a partir de hierarchy_data (OLT/SLOT/PON/CTO, usuários).
Atualiza a cada 5s. Inclui alarme sonoro somente quando o nível/critério é crítico (implementado via JS).

Monitoramento/utils.py

log_to_db(kind, level, message, detail, hierarchy_data): utilitário padronizado para gravar logs/alertas com timezone.localtime, evitando duplicações e garantindo consistência.

Monitoramento/urls.py
Rotas do app:

'' ou 'home/' → painel;

'network-alerts/', 'system-logs/', 'logs/' → APIs JSON para o frontend.

Fluxo de dados (resumo)

Monitorador (monitorador_de_rede.py) conecta no Juniper, lê assinantes e conta ativos.

Calcula o diff vs. leitura anterior:

diff >= MIN_DROP → queda crítica (gera NetworkAlert + Alert com hierarquia).

Recuperações: apenas para logins que participaram de alguma queda crítica recente.

Frontend atualiza a cada 5s:

Abas consomem JSON dos endpoints e re-renderizam as tabelas.

Som só toca para níveis críticos.



Configuração essencial

Variáveis de ambiente (.env)

POSTGRES_DB=...
POSTGRES_USER=...
POSTGRES_PASSWORD=...
POSTGRES_HOST=db
POSTGRES_PORT=5432
TZ=America/Sao_Paulo

RECAPTCHA_SITE_KEY=...
RECAPTCHA_PRIVATE_KEY=...


Django (settings.py)

ALLOWED_HOSTS com seu domínio/subdomínio;

CSRF_TRUSTED_ORIGINS incluindo o host do proxy (http://seu_dominio);

INSTALLED_APPS inclui "captcha" para o reCAPTCHA;

MONITORAMENTO_MIN_DROP = 4 (ajuste conforme política de alarme).

Nginx (nginx.conf)

server_name sentinela.seu_dominio...;

location /static/ apontando para o volume;

proxy_pass http://django-server;.

Docker Compose (docker-compose.yml)

Garanta que frontend-proxy depende de django-web com condition: service_healthy;

django-web expõe 8000 e roda Gunicorn.

Observações de segurança

Nunca versione chaves/segredos (.env, SECRET_KEY, senhas SSH).

Use TLS/HTTPS (certbot/letsencrypt) no NGINX em produção.

Mantenha DEBUG=False e ALLOWED_HOSTS corretos.

Restrinja acesso SSH e rotas sensíveis.
