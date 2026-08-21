---
repo: architecture
path: docs/architecture/aw-app-google-cloud.md
source: generated
edited: false
checksum: sha256:1ba9f71b16140f78c7590d85b750670a744425ceda7f0d7eb5b5fa1db9dbe730
---
# Google Cloud CLI

- **repo**: aw-app-google-cloud
- **layer**: app
- **technologies**: python
- **health** (derived): planned

Installs the Google Cloud CLI (`gcloud`) into the workspace and provides a settings panel for project/account defaults and optional service-account JSON setup.

## Connections
- `http` → **aw-workspace** — routes mounted at /api/apps/google-cloud

## MCP tools
_none exposed_

## Requirements
### A chave de service-account passa por disco mas o arquivo é sempre removido
- Given um JSON de service-account salvo nas settings, e o `gcloud auth activate-service-account` só aceita a chave via --key-file, nunca por stdin
- When a ativação escreve um arquivo temporário e o remove (repos/aw-app-google-cloud/google_cloud_app/gcloud_configure.py::activate_service_account:44, mkstemp:55 e o unlink no finally:73)
- Then o arquivo é apagado mesmo quando o gcloud falha e sobe GcloudConfigureError, porque o unlink está no finally e não no caminho feliz — sem isso toda tentativa fracassada deixaria uma chave privada legível em /tmp, que é o pior lugar possível para ela ficar justamente porque ninguém volta lá olhar depois de um erro. FileNotFoundError no unlink é engolido de propósito, para não mascarar a exceção real que estava subindo
- intended_status: `not_implemented` · derived health: `not_implemented`
- tests: `repos/aw-app-google-cloud/tests/test_gcloud_configure.py` (passing)

### JSON de service-account inválido ou sem client_email é rejeitado antes de tocar o disco
- Given alguém cola no campo de service-account um texto que não é JSON, ou um JSON válido que não é uma chave de service-account
- When o parse e a extração do client_email acontecem antes do mkstemp (repos/aw-app-google-cloud/google_cloud_app/gcloud_configure.py::activate_service_account:46-53)
- Then sobe GcloudConfigureError com a razão e nenhum arquivo temporário chega a ser criado — a ordem importa: validar depois de escrever significaria criar e ter que limpar um arquivo para uma entrada que nunca teve chance. O client_email vem de dentro do próprio JSON e não de um campo separado, então o e-mail passado ao gcloud não pode divergir da chave que o acompanha
- intended_status: `not_implemented` · derived health: `not_implemented`
- tests: `repos/aw-app-google-cloud/tests/test_gcloud_configure.py` (passing)

### A autenticação é aplicada antes das defaults de projeto e região
- Given um save que traz de uma vez a chave de service-account e as defaults (project, account, compute/region, compute/zone)
- When apply_settings executa (repos/aw-app-google-cloud/google_cloud_app/gcloud_configure.py::apply_settings:82): a ativação da conta é o bloco 85-87, o laço de config_set vem depois, na linha 89
- Then "auth/service_account" entra em applied antes de qualquer chave de config, e os nomes são traduzidos por _FIELD_TO_GCLOUD_KEY (gcloud_configure.py:15) — gcloud_compute_region vira compute/region, com barra, que é a sintaxe de seção da gcloud. A ordem não é cosmética: `gcloud config set` grava na configuração da conta ativa, então aplicar as defaults antes de trocar de conta as escreveria no perfil errado
- intended_status: `not_implemented` · derived health: `not_implemented`
- tests: `repos/aw-app-google-cloud/tests/test_gcloud_configure.py` (passing)

### Logout limpa o cofre e não revoga a conta gcloud local
- Given um service-account ativado e defaults gravadas, e a pessoa clica em Logout
- When a rota apaga os cinco campos do cofre (repos/aw-app-google-cloud/google_cloud_app/plugin.py::GoogleCloudAppPlugin._build_routes.logout:109)
- Then o cofre fica vazio e o activate seguinte não tem o que reaplicar, mas a credencial que a gcloud já guardou no perfil local continua ativa — revogação está declaradamente fora de escopo desta rota (plugin.py:111-114). Vale enxergar isso como o que é: para um service-account a diferença entre "esqueci a chave" e "revoguei a chave" é grande, e este botão só faz a primeira. ATENÇÃO: nenhum teste cobre logout neste app, diferente do aw-app-aws, que cobre
- intended_status: `not_implemented` · derived health: `not_implemented`
- tests: _none linked_
