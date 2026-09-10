<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# keycloak 사용법을 상세하게 알려주세요. 영어로

Keycloak is an open-source identity and access management server that provides single sign-on, OpenID Connect, OAuth 2.0, and SAML support for web apps and APIs. You typically use it by creating a realm, registering clients, creating users/roles, and then wiring your application to Keycloak for login and token-based access control.[^1_1]

## What Keycloak does

Keycloak acts as a separate authentication server, so your applications redirect users to Keycloak for login and then receive signed tokens instead of handling passwords directly. It also supports user federation with LDAP/Active Directory, social login, customizable login/admin/account UIs, two-factor authentication, and session management.[^1_1]

## Core concepts

A few terms matter most when learning Keycloak: a **realm** is an isolated security domain, a **client** is an application or service that uses Keycloak, a **user** is a login identity, and **roles** define permissions. Keycloak also uses **groups**, **client scopes**, **protocol mappers**, and **service accounts** to model more advanced access-control and token-claim behavior.[^1_1]

## Basic setup flow

The usual setup path is: install and start Keycloak, create the initial administrator, open the Admin Console, create a realm, register a client, add users and roles, and then configure your app to use the realm’s OIDC or SAML endpoints. The current documentation says you create the first admin either through the local welcome page or by setting `KC_BOOTSTRAP_ADMIN_USERNAME` and `KC_BOOTSTRAP_ADMIN_PASSWORD` before starting the server.[^1_1]

## Admin Console workflow

Most administration happens in the Admin Console. From there you can switch realms, create new realms, configure realm settings, manage users and roles, adjust login options, set themes, configure email, and control required actions like password reset or email verification.[^1_1]

## Common tasks

Here are the most common tasks you’ll do first:

- Create a realm for your organization or app boundary.[^1_1]
- Create clients for each application that needs login.[^1_1]
- Add users, groups, and roles, then assign roles to users or groups.[^1_1]
- Enable email settings if you want password reset or verification flows.[^1_1]
- Customize login and account themes to match your brand.[^1_1]
- Configure token claims with protocol mappers when your app needs custom user attributes in tokens.[^1_1]


## A practical example

If you are securing a React SPA and a REST API, you usually create one realm, add one public client for the SPA, and configure the API to validate access tokens issued by Keycloak. Users log in through Keycloak, the SPA receives tokens, and the API checks those tokens on each request. Keycloak’s documented support for OpenID Connect and OAuth 2.0 is what makes this pattern straightforward.[^1_1]

## Recommended learning path

If you want to learn Keycloak efficiently, start in this order: Getting Started, Server Installation and Configuration, Securing Applications and Services, and then Server Administration. The official documentation page lists those guides as the main entry points for current Keycloak releases.[^1_1]

If you want, I can give you the next step in English as one of these:

1. “Install Keycloak with Docker and create a realm”
2. “How to integrate Keycloak with Spring Boot”
3. “How to secure a React app and REST API with Keycloak”
<span style="display:none">[^1_10][^1_11][^1_12][^1_13][^1_14][^1_15][^1_2][^1_3][^1_4][^1_5][^1_6][^1_7][^1_8][^1_9]</span>

<div align="center">⁂</div>

[^1_1]: https://www.keycloak.org/documentation

[^1_2]: https://www.keycloak.org/guides

[^1_3]: https://docs.redhat.com/de/documentation/red_hat_build_of_keycloak/26.0/pdf/getting_started_guide/index

[^1_4]: https://docs.redhat.com/ko/documentation/red_hat_build_of_keycloak/24.0/html/getting_started_guide/getting-started-zip-

[^1_5]: https://wjw465150.gitbooks.io/keycloak-documentation/content/getting_started/index.html

[^1_6]: https://dev.to/pierangelo1982/keycloak-setup-and-deployment-guide-4ebg

[^1_7]: https://subscription.packtpub.com/book/cloud-and-networking/9781800562493/2/ch02lvl1sec06/discovering-the-keycloak-admin-and-account-consoles

[^1_8]: https://dev.to/haithamoumer/getting-started-with-keycloak-understanding-the-basics-55bf

[^1_9]: https://docs.redhat.com/ko/documentation/red_hat_build_of_keycloak/26.0/html/server_configuration_guide/configuration-production-

[^1_10]: https://www.keycloak.org/docs/latest/server_admin/index.html

[^1_11]: https://www.youtube.com/watch?v=fvxQ8bW0vO8

[^1_12]: https://access.redhat.com/documentation/es-es/red_hat_build_of_keycloak/24.0/pdf/server_guide/red_hat_build_of_keycloak-24.0-server_guide-en-us.pdf

[^1_13]: https://booiljung.gitbook.io/booil-jung/docs/server_archiecture/keycloak/chapter_03/0309

[^1_14]: https://kc-api.github.io/quick-reference/

[^1_15]: https://manologg.github.io/keycloak-documentation-18.0.2/server_installation/index.html


---

# Keycloak을 Docker로 배포하고 Postgres DB 연동

아래처럼 하면 됩니다. Keycloak은 공식 컨테이너 이미지에서 `KC_DB=postgres`, `KC_DB_URL`, `KC_DB_USERNAME`, `KC_DB_PASSWORD`를 설정해 PostgreSQL에 연결할 수 있고, 개발용이면 `start-dev`, 운영용이면 `start --optimized` 흐름을 권장합니다.[^2_1]

## Docker Compose 예시

```yaml
version: "3.8"

services:
  postgres:
    image: postgres:16
    container_name: keycloak-postgres
    environment:
      POSTGRES_DB: keycloak
      POSTGRES_USER: keycloak
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - keycloak-net

  keycloak:
    image: quay.io/keycloak/keycloak:latest
    container_name: keycloak
    depends_on:
      - postgres
    ports:
      - "8080:8080"
    environment:
      KEYCLOAK_ADMIN: admin
      KEYCLOAK_ADMIN_PASSWORD: admin
      KC_DB: postgres
      KC_DB_URL: jdbc:postgresql://postgres:5432/keycloak
      KC_DB_USERNAME: keycloak
      KC_DB_PASSWORD: password
      KC_HOSTNAME: localhost
      KC_HOSTNAME_STRICT: "false"
      KC_HTTP_ENABLED: "true"
    command: ["start-dev"]
    networks:
      - keycloak-net

volumes:
  postgres_data:

networks:
  keycloak-net:
```

이 구성은 같은 Docker network 안에서 `postgres` 서비스명을 호스트명으로 사용해 Keycloak이 PostgreSQL에 접속하도록 합니다. Keycloak 공식 문서도 컨테이너 실행 시 PostgreSQL용 `KC_DB`, `KC_DB_URL`, `KC_DB_USERNAME`, `KC_DB_PASSWORD` 설정을 예시로 보여줍니다.[^2_1]

## 실행 순서

1. `docker compose up -d`로 PostgreSQL과 Keycloak을 함께 올립니다.[^2_1]
2. 브라우저에서 `http://localhost:8080`에 접속합니다.[^2_1]
3. 초기 관리자 계정으로 로그인합니다. Keycloak은 컨테이너 환경에서 초기 admin 생성을 위해 `KEYCLOAK_ADMIN`과 `KEYCLOAK_ADMIN_PASSWORD`를 요구합니다.[^2_1]
4. Admin Console에서 Realm, Client, User, Role을 생성합니다.[^2_1]

## 운영 배포 시 주의점

개발용 `start-dev`는 빠르게 띄우기 좋지만 운영 환경에서는 사용을 피해야 합니다. 공식 문서는 운영 환경에서는 이미지 빌드 단계에서 최적화한 뒤 `start --optimized`로 실행하고, 메모리 제한도 반드시 설정하라고 안내합니다.[^2_1]

운영용으로는 보통 다음 두 가지를 추가합니다. 첫째, Keycloak 이미지를 미리 빌드해 최적화합니다. 둘째, HTTPS와 hostname 설정을 명확히 넣습니다. 공식 문서의 예시에서도 `KC_DB=postgres`와 함께 `KC_DB_URL`, `KC_DB_USERNAME`, `KC_DB_PASSWORD`, `KC_HOSTNAME`을 사용합니다.[^2_1]

## 바로 쓸 수 있는 운영형 예시

```bash
docker run --name keycloak \
  -p 8080:8080 \
  -e KEYCLOAK_ADMIN=admin \
  -e KEYCLOAK_ADMIN_PASSWORD=admin \
  -e KC_DB=postgres \
  -e KC_DB_URL=jdbc:postgresql://postgres:5432/keycloak \
  -e KC_DB_USERNAME=keycloak \
  -e KC_DB_PASSWORD=password \
  -e KC_HOSTNAME=localhost \
  quay.io/keycloak/keycloak:latest \
  start-dev
```

이 예시는 개발/검증용으로는 충분하지만, 공식 문서 기준으로 운영에서는 `start-dev` 대신 최적화된 이미지와 `start --optimized`를 쓰는 쪽이 맞습니다.[^2_1]

## 자주 생기는 문제

- `localhost`를 DB 주소로 넣으면 컨테이너 내부에서는 자기 자신을 가리키므로 실패합니다. 같은 Compose 네트워크에서는 서비스명 `postgres`를 써야 합니다.[^2_1]
- PostgreSQL 컨테이너가 완전히 올라오기 전에 Keycloak이 먼저 기동하면 초기 연결 실패가 날 수 있습니다. 이 경우 healthcheck 또는 재시도 로직을 추가하는 것이 좋습니다.[^2_1]
- 운영에서는 메모리 제한을 설정해야 합니다. Keycloak 문서는 컨테이너 메모리 기반 힙 계산을 사용하므로 memory limit 설정을 권장합니다.[^2_1]

원하시면 다음 단계로 이어서 드릴 수 있습니다:

1. `docker-compose.yml`를 운영용으로 개선한 버전
2. `Keycloak + Postgres + HTTPS` 구성
3. `Spring Boot`에서 Keycloak 연동 방법
<span style="display:none">[^2_10][^2_11][^2_12][^2_13][^2_14][^2_15][^2_16][^2_2][^2_3][^2_4][^2_5][^2_6][^2_7][^2_8][^2_9]</span>

<div align="center">⁂</div>

[^2_1]: https://www.keycloak.org/documentation

[^2_2]: https://hub.docker.com/r/stibbons31/docker-keycloak-pg

[^2_3]: https://hub.docker.com/layers/gdscyber/keycloak-postgresql/latest/images/sha256-a73f9427dae4928e4a1981a9fb96084cf33e6ad380460ab863b02873a86031a6

[^2_4]: https://hub.docker.com/layers/ayoubouladmaalem/postgres-keycloak-customer/latest/images/sha256-671a678fa062b9939c4ff35bb07743318f775dcffb904b46aef475a610536310

[^2_5]: https://github.com/keycloak/keycloak/discussions/14029

[^2_6]: https://stackoverflow.com/questions/75410699/connecting-keycloak-with-postgres-database

[^2_7]: https://www.keycloak.org/keycloak-benchmark/kubernetes-guide/latest/storage/postgres

[^2_8]: https://forum.keycloak.org/t/getting-keycloak-to-use-postgres-within-docker-compose/23882

[^2_9]: https://www.keycloak.org/server/containers

[^2_10]: https://www.ibm.com/docs/en/doc/4.4.0?topic=credentials-configuring-postgres-keycloak

[^2_11]: https://github.com/andissanayake/ForgeContainer

[^2_12]: https://stackoverflow.com/questions/78101985/keycloak-and-postgres-docker-compose

[^2_13]: https://cloud.tencent.com/developer/ask/sof/107983308

[^2_14]: https://smoh.tistory.com/508

[^2_15]: https://tommypagy.tistory.com/631

[^2_16]: https://velog.io/@minju0426/Keycloak-Postgres-sql-연동-psycopg2


---

# Keycloak 프로덕션 모드 Docker Postgres 설정

프로덕션 모드에서는 **`start-dev`를 쓰지 말고 `kc.sh build`로 최적화한 뒤 `start --optimized`로 실행**하는 구성이 정석입니다. 또한 프로덕션에서는 **`hostname`을 명시해야 하며**, 프록시 뒤에 둘 경우 `proxy-headers` 설정도 같이 맞춰야 합니다.[^3_1][^3_2]

## 권장 구성

프로덕션용 Docker 배포는 보통 다음 흐름입니다.

1. Keycloak 이미지를 빌드 단계에서 최적화합니다.
2. PostgreSQL을 외부 DB로 사용합니다.
3. `hostname`을 고정합니다.
4. 리버스 프록시가 있으면 `proxy-headers`를 설정합니다.[^3_2][^3_1]

## 예시 Containerfile

```dockerfile
FROM quay.io/keycloak/keycloak:latest AS builder
ENV KC_HEALTH_ENABLED=true
ENV KC_METRICS_ENABLED=true
ENV KC_DB=postgres
WORKDIR /opt/keycloak
RUN /opt/keycloak/bin/kc.sh build

FROM quay.io/keycloak/keycloak:latest
COPY --from=builder /opt/keycloak/ /opt/keycloak/
ENV KC_DB=postgres
ENV KC_DB_URL=jdbc:postgresql://postgres:5432/keycloak
ENV KC_DB_USERNAME=keycloak
ENV KC_DB_PASSWORD=change_me
ENV KC_HOSTNAME=https://auth.example.com
ENTRYPOINT ["/opt/keycloak/bin/kc.sh"]
```

공식 문서는 컨테이너 환경에서 PostgreSQL을 사용할 때 `KC_DB=postgres`, `KC_DB_URL`, `KC_DB_USERNAME`, `KC_DB_PASSWORD`를 설정하는 방식과, 최적화된 이미지를 위해 `kc.sh build`를 수행하는 방식을 제시합니다.[^3_1]

## 예시 docker-compose.yml

```yaml
version: "3.8"

services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: keycloak
      POSTGRES_USER: keycloak
      POSTGRES_PASSWORD: change_me
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - kcnet

  keycloak:
    build:
      context: .
      dockerfile: Containerfile
    depends_on:
      - postgres
    ports:
      - "8443:8443"
      - "9000:9000"
    environment:
      KC_DB: postgres
      KC_DB_URL: jdbc:postgresql://postgres:5432/keycloak
      KC_DB_USERNAME: keycloak
      KC_DB_PASSWORD: change_me
      KC_BOOTSTRAP_ADMIN_USERNAME: admin
      KC_BOOTSTRAP_ADMIN_PASSWORD: change_me_admin
      KC_HOSTNAME: https://auth.example.com
      KC_HTTP_ENABLED: "true"
      KC_PROXY_HEADERS: xforwarded
    command: ["start", "--optimized"]
    networks:
      - kcnet

volumes:
  postgres_data:

networks:
  kcnet:
```

Keycloak의 hostname 문서는 프로덕션에서 `--hostname`을 명시하라고 안내하고, 프록시 뒤에서는 `proxy-headers`를 사용해 `Forwarded` 또는 `X-Forwarded-*` 헤더를 신뢰하도록 설정하라고 설명합니다.[^3_2]

## 운영에서 중요한 포인트

- **`start-dev` 대신 `start --optimized` 사용**이 맞습니다.[^3_1]
- **`KC_HOSTNAME`은 전체 URL로 지정**하는 편이 안전합니다. 예: `https://auth.example.com`.[^3_2]
- **프록시가 있으면 `KC_PROXY_HEADERS` 또는 대응 CLI 옵션을 맞춰야** 링크 생성, OIDC discovery, 리다이렉트 URI가 정상 동작합니다.[^3_2]
- **DB 주소는 컨테이너 내부 기준으로 `postgres:5432`처럼 서비스명 기반**으로 써야 합니다.[^3_1]


## 추가로 권장하는 운영 설정

프로덕션에서는 아래도 같이 넣는 경우가 많습니다.

- `KC_HEALTH_ENABLED=true`
- `KC_METRICS_ENABLED=true`
- PostgreSQL 데이터 볼륨 영속화
- Keycloak에 메모리 제한 설정
- TLS는 보통 리버스 프록시에서 종료[^3_1][^3_2]

원하시면 제가 바로 다음으로

1. **Nginx 리버스 프록시 포함한 프로덕션 compose**, 또는
2. **AWS / NCP / 온프레미스 기준 운영 배포 예시**
중 하나로 이어서 정리해드릴게요.
<span style="display:none">[^3_10][^3_11][^3_12][^3_13][^3_14][^3_15][^3_16][^3_17][^3_3][^3_4][^3_5][^3_6][^3_7][^3_8][^3_9]</span>

<div align="center">⁂</div>

[^3_1]: https://www.keycloak.org/documentation

[^3_2]: https://www.keycloak.org/guides

[^3_3]: https://www.keycloak.org/server/containers

[^3_4]: https://docs.redhat.com/en/documentation/red_hat_build_of_keycloak/26.2/html/server_configuration_guide/containers-

[^3_5]: https://github.com/keycloak/keycloak/blob/main/docs/guides/server/containers.adoc

[^3_6]: https://www.keycloak.org/keycloak-benchmark/kubernetes-guide/latest/storage/postgres

[^3_7]: https://kondratovich.work/blog/keycloak

[^3_8]: https://computingforgeeks.com/run-keycloak-server-in-docker/

[^3_9]: https://github.com/keycloak/keycloak/discussions/11856

[^3_10]: https://docs.redhat.com/de/documentation/red_hat_build_of_keycloak/24.0/html/server_guide/containers-

[^3_11]: https://github.com/GoogleCloudPlatform/click-to-deploy/blob/master/docker/keycloak/README.md

[^3_12]: https://www.keycloak.org/server/hostname

[^3_13]: https://whitepro.tistory.com/1012

[^3_14]: https://stackoverflow.com/questions/75082054/keycloak-does-not-use-postgres-database-and-tries-to-connect-h2-database

[^3_15]: https://docs.redhat.com/en/documentation/red_hat_build_of_keycloak/24.0/html/server_guide/hostname-

[^3_16]: https://stackoverflow.com/questions/78683169/keycloak-production-docker-site-able-to-connect-to-postgres-and-run-using-docker

[^3_17]: https://tommypagy.tistory.com/631


---

# keycloak의 postgres를 외부 즉 aws의 ec2내에 제공하는 postgre를 사용합니다. 예를 들면, postgre.a.com 5432 입니다.

AWS EC2 안에 독립된 PostgreSQL이 있고, Keycloak Docker 컨테이너가 그 외부 DB를 사용하도록 만들고 싶으시죠. 핵심은 **Keycloak 쪽에서 `KC_DB_URL`을 `postgre.a.com:5432` 포맷으로 지정**하고, 네트워크·보안 그룹·PostgreSQL 설정을 맞춰주는 것입니다.[^4_1][^4_2]

***

## 1. PostgreSQL 외부 DB 설정 (postgre.a.com)

1. **PostgreSQL DB 생성**
    - DB 이름: `keycloak`
    - 사용자: `keycloak` / `keycloak_admin` 등으로 생성
    - 권한: 해당 DB에 `ALL PRIVILEGES` 부여

```sql
CREATE DATABASE keycloak;
CREATE USER keycloak WITH PASSWORD 'change_me';
GRANT ALL PRIVILEGES ON DATABASE keycloak TO keycloak;
```


[^4_3]

2. **listen_address / pg_hba 설정**
    - `postgresql.conf`에서

```conf
listen_addresses = '*'
port = 5432
```

    - `pg_hba.conf`에 Keycloak 컨테이너가 나올 IP 또는 네트워크 CIDR 추가

```conf
host keycloak keycloak <docker_subnet>/24 md5
```


[^4_3]

3. **AWS EC2 보안그룹**
    - `5432` 포트를 **Keycloak이 올라가는 서버/클러스터의 IP나 CIDR**로 제한해서 오픈.

***

## 2. Keycloak Docker에서 외부 PostgreSQL 사용

PostgreSQL이 `postgre.a.com:5432`에 있고, Keycloak을 Docker에서 실행한다고 가정하면 다음과 같이 설정합니다. 공식 문서에서도 외부 PostgreSQL은 `KC_DB=postgres` + `KC_DB_URL=jdbc:postgresql://주소:5432/DB` 형태로 설정하라고 명시합니다.[^4_2][^4_1]

```bash
docker run -d \
  --name keycloak \
  -p 8080:8080 \
  -e KEYCLOAK_ADMIN=admin \
  -e KEYCLOAK_ADMIN_PASSWORD=change_me_admin \
  -e KC_DB=postgres \
  -e KC_DB_URL=jdbc:postgresql://postgre.a.com:5432/keycloak \
  -e KC_DB_USERNAME=keycloak \
  -e KC_DB_PASSWORD=change_me \
  -e KC_HOSTNAME=https://auth.example.com \
  -e KC_HTTP_ENABLED=true \
  quay.io/keycloak/keycloak:latest \
  start --optimized
```

- `KC_DB_URL`: `jdbc:postgresql://postgre.a.com:5432/keycloak`처럼 외부 호스트명과 포트로 지정합니다.[^4_1]
- `KC_DB_USERNAME` / `KC_DB_PASSWORD`: 위에서 만든 PostgreSQL 계정.
- `KC_HOSTNAME`은 실제 도메인으로 세팅해야 다른 서비스에서 OIDC discovery가 정상적으로 됩니다.[^4_1]

***

## 3. docker-compose 예시 (외부 PostgreSQL)

```yaml
version: "3.8"

services:
  keycloak:
    image: quay.io/keycloak/keycloak:latest
    container_name: keycloak
    ports:
      - "8080:8080"
    environment:
      KC_DB: postgres
      KC_DB_URL: jdbc:postgresql://postgre.a.com:5432/keycloak
      KC_DB_USERNAME: keycloak
      KC_DB_PASSWORD: change_me
      KC_BOOTSTRAP_ADMIN_USERNAME: admin
      KC_BOOTSTRAP_ADMIN_PASSWORD: change_me_admin
      KC_HOSTNAME: https://auth.example.com
      KC_HTTP_ENABLED: "true"
      KC_PROXY_HEADERS: xforwarded
    command: ["start", "--optimized"]
    networks:
      - kcnet

networks:
  kcnet:
```

Keycloak은 컨테이너 안에서 `postgre.a.com`을 DNS로 해석할 수 있어야 하며, Docker 네트워크 설정이 아니라 **컨테이너가 외부 인터넷/EC2 VPC를 통해 해당 주소에 접근 가능**해야 합니다.[^4_4][^4_2]

***

## 4. 주의사항 및 테스트 방법

1. **port 및 네트워크 확인**
    - Keycloak 서버에서 `telnet postgre.a.com 5432` 또는 `psql "postgresql://postgre.a.com:5432/keycloak"`로 접속 가능 여부 확인.
2. **TLS 설정 (선택)**
    - 외부 PostgreSQL이 SSL을 요구하면 JDBC URL에 옵션 추가 가능

```bash
KC_DB_URL=jdbc:postgresql://postgre.a.com:5432/keycloak?sslmode=require
```


[^4_5][^4_1]

3. **프로덕션 보안**
    - `postgre.a.com`은 프라이빗 VPC/ALB/Route53 CNAME 등으로 내부망에서만 접근되도록 구성하는 것이 좋습니다.
    - Keycloak admins는 `KC_HOSTNAME`과 reverse proxy(Let’s Encrypt Termination 등)를 함께 사용해 HTTPS를 처리합니다.[^4_6][^4_7]

***

원하시면 다음 단계로

1. **Keycloak + AWS EC2 PostgreSQL + Nginx reverse proxy + TLS** 구성 예시, 또는
2. **multitenant Keycloak 운영 시 DB/Networking 고려사항**
을 정리해드릴까요?
<span style="display:none">[^4_10][^4_11][^4_12][^4_13][^4_14][^4_15][^4_16][^4_17][^4_18][^4_8][^4_9]</span>

<div align="center">⁂</div>

[^4_1]: https://forum.keycloak.org/t/how-should-kc-db-url-be-formatted-for-postgres/18626

[^4_2]: https://www.keycloak.org/server/containers

[^4_3]: https://alice-secreta.tistory.com/29

[^4_4]: https://www.keycloak.org/keycloak-benchmark/kubernetes-guide/latest/customizing-deployment

[^4_5]: https://blog.devops.dev/deploy-keycloak-v24-to-k8s-cluster-with-helm-83e6714f2888?gi=a5da525ba121

[^4_6]: https://computingforgeeks.com/run-keycloak-server-in-docker/

[^4_7]: https://www.keycloak.org/server/hostname

[^4_8]: https://asknbshwmj.blogspot.com/?page=en-git-tim-herbie-opencloud-helm-1769164924545

[^4_9]: https://github.com/keycloak/keycloak/discussions/14029

[^4_10]: https://stackoverflow.com/questions/66557539/how-to-create-keycloak-with-operator-and-external-database

[^4_11]: https://www.keycloak.org/keycloak-benchmark/kubernetes-guide/latest/storage/postgres

[^4_12]: https://stackoverflow.com/questions/75410699/connecting-keycloak-with-postgres-database

[^4_13]: https://forum.keycloak.org/t/yml-file-format-for-postgres-db/9493

[^4_14]: https://www.youtube.com/watch?v=VHMCpjdRiCs

[^4_15]: https://keycloak.discourse.group/t/how-should-kc-db-url-be-formatted-for-postgres/18626

[^4_16]: https://gist.github.com/s1moe2/b154ff546c5a0025e2f2cac4336fdafb

[^4_17]: https://hub.docker.com/r/stibbons31/docker-keycloak-pg

[^4_18]: https://docs.redhat.com/ko/documentation/red_hat_single_sign-on/7.6/html/server_installation_and_configuration_guide/external_database


---

# 외부 Postgres 연결 시 발생하는 일반적인 오류와 해결법

Keycloak Postgres 연결 SSL 설정 방법
Keycloak 외부 DB 마이그레이션 스크립트 실행
외부 Postgres 사용 시 Keycloak 성능 최적화 팁

Keycloak을 **외부 PostgreSQL(Postgres)에 연결**하고, 동시에 **SSL·마이그레이션·성능 튜닝**까지 염두에 둔 운영 구성은 아래와 같이 정리할 수 있습니다.

***

## 1. 외부 Postgres 연결 시 발생하는 일반적인 오류와 해결법

외부 Postgres(postgre.a.com:5432)를 사용하면 보통 다음 유형의 오류가 자주 발생합니다.[^5_1][^5_2]

### (1) `Connection refused` / `could not connect to server`

```text
FATAL: connection to postgres:5432 refused
```

- **원인**
    - Postgres 서버가 `listen_addresses`를 `'*'`가 아니라 `127.0.0.1`로만 열어둠
    - 보안 그룹/방화벽에서 5432 포트가 막혀 있음
    - DNS(`postgre.a.com`) 해석이 안 됨
- **해결법**
    - `postgresql.conf`에서 `listen_addresses = '*'`
    - `pg_hba.conf`에 Keycloak 서버 IP / CIDR에 `host all all md5` 또는 `host keycloak keycloak ...` 추가
    - AWS EC2 보안그룹에서 `5432` → Keycloak 머신 IP 허용
    - 컨테이너 내부에서 `telnet postgre.a.com 5432` 또는 `psql`로 직접 접속 테스트

[^5_3][^5_2]

***

### (2) `Ident authentication failed` / `SCRAM-SHA-256` 에러

```text
FATAL: Ident authentication failed for user "keycloak"
FATAL: password authentication failed for user "keycloak"
```

- **원인**
    - `pg_hba.conf`가 `peer`/`ident` 모드로 되어 있어, 외부 TCP에서 plain password 인증을 못 받음
- **해결법**
    - `pg_hba.conf`에 다음과 같이 추가

```conf
host keycloak keycloak all md5
# 또는 더 최신 방식
host keycloak keycloak all scram-sha-256
```

    - Postgres 재시작 후 접속 확인
- JDBC 측에서는 `KC_DB_PASSWORD`를 올바르게 설정하고, Postgres 계정에 `CREATE USER ... PASSWORD`를 다시 설정.[^5_1]

***

### (3) Keycloak이 H2 DB를 계속 사용하는 경우

```text
Database 'keycloak' skipped, using default H2
```

- **원인**
    - `KC_DB=postgres` 또는 `db = postgres`가 누락됨
    - `KC_DB_URL`, `KC_DB_USERNAME`, `KC_DB_PASSWORD`가 올바르지 않아 기본 내장 H2로 폴백
- **해결법**
    - Keycloak(`keycloak.conf` 또는 환경변수)에서 반드시 지정

```properties
KC_DB=postgres
KC_DB_URL=jdbc:postgresql://postgre.a.com:5432/keycloak
KC_DB_USERNAME=keycloak
KC_DB_PASSWORD=change_me
```

    - 최초 기동 시 `keycloak` DB가 비어 있어도 Keycloak이 자동으로 스키마를 생성해야 함. 만약 안 되면 Postgres 측에서 `CREATE DATABASE keycloak;`을 먼저 수행.[^5_4][^5_5]

***

## 2. Keycloak Postgres 연결 SSL 설정 방법

외부 Postgres(postgre.a.com)가 **SSL/TLS를 강제**로 사용하도록 설정되어 있다면, Keycloak JDBC 쪽에 옵션을 주는 방식으로 처리합니다. Keycloak은 기본 JDBC 드라이버를 사용하므로, `sslmode` 옵션을 URL에 붙입니다.[^5_6][^5_7]

### (1) 기본 JDBC URL에 SSL 모드 붙이기

```bash
KC_DB_URL=jdbc:postgresql://postgre.a.com:5432/keycloak?sslmode=require
```

- `sslmode` 옵션 예시
    - `prefer` : 가능하면 SSL, 아니면 일반 접속
    - `require` : SSL 없으면 연결 거부 (보통 운영용)
    - `verify-ca` / `verify-full` : CA 인증서·호스트명 검증까지 강제

Keycloak 공식 문서·커뮤니티 답변에서 외부 Postgres 연결 시 `sslmode` 파라미터를 사용하는 방식을 명시하고 있습니다.[^5_6]

### (2) CA 인증서 신뢰가 필요한 경우

Postgres가 자체 CA 인증서를 쓰는 경우, Keycloak 컨테이너 안에 CA 인증서를 넣고, JVM/Truststore를 설정해야 합니다. 예:

- 컨테이너 빌드에서 `cacerts`에 CA 붙이기
- 또는 `keycloak.conf`에 `KC_DB_SSL_CA_CERT` / `KC_DB_SSL_CERT` 옵션을 사용하는 방식 (Quarkus 기반 문서에서 언급됨).[^5_8][^5_7]

> 프로덕션에서는 보통 `sslmode=require` + 외부 Postgres가 Let's Encrypt/CA로 인증된 경우를 사용하고, CA를 컨테이너에 사전에 넣어 두는 방식을 권장합니다.

***

## 3. Keycloak 외부 DB 마이그레이션 스크립트 실행

Keycloak에서의 **외부 DB 마이그레이션(예: H2 → Postgres, 또는 이전 Postgres → 새로운 Postgres)**는 보통 2가지 패턴으로 나뉩니다.[^5_9][^5_10]

### (1) Keycloak 자체 스키마 자동 마이그레이션

- Keycloak을 최초로 외부 DB로 연결할 때, Keycloak 서버가 `keycloak` 스키마에 필요한 테이블을 자동 생성하고 초기화합니다.
- 이미 내부 DB(H2)에서 사용 중이던 Keycloak을 **외부 Postgres로 옮기고 싶다면**:

1. 이전 Keycloak(H2)에서 `export` 또는 `realm export` 수행
2. 새로운 Postgres + Keycloak 구성에서
        - `start` 후 `realm import` / `keycloak.log`를 통해 테이블·데이터 생성 확인
- 이 방식은 **Keycloak이 제공하는 스키마만 마이그레이션**된다.[^5_4][^5_8]


### (2) DB 레이어 직접 마이그레이션 스크립트

외부 DB를 교체하거나, 데이터베이스/클러스터를 이전할 때는:

- **Postgres dump / restore**

```bash
pg_dump -h old-host -U keycloak keycloak > keycloak.sql
psql -h new-postgres.a.com -U keycloak keycloak < keycloak.sql
```


[^5_9]

- dump 복원 후 Keycloak 쪽 `KC_DB_URL`을 새 호스트로 변경하고, Keycloak 재시작 시 DB 스키마 유효성 검사 후 문제 없다면 정상 작동합니다.
- 이 과정에서는 **Keycloak 서버는 변경 없이, DB 스크립트만 실행**하면 되는 구조입니다.[^5_10]

> 만약 스키마 버전이 다르다면 Keycloak 재시작 시 자동 스키마 업그레이드가 수행되며, 이 과정은 Keycloak 로그에서 `Flyway`/`schema` 관련 메시지로 확인 가능합니다.[^5_8][^5_4]

***

## 4. 외부 Postgres 사용 시 Keycloak 성능 최적화 팁

외부 Postgres(postgre.a.com)는 Keycloak의 **콜드 쿼리 성능**을 좌우합니다. 아래는 일반적으로 추천되는 최적화 포인트입니다.[^5_11][^5_12]

### (1) Keycloak 쪽 DB 커넥션 풀 설정

Quarkus/Keycloak 커넥션 풀 설정 (`keycloak.conf` 또는 환경변수)에서 다음과 같이 늘립니다.[^5_11]

```properties
# 쿼리/결정적으로 영향을 주는 설정들
KC_DB_POOL_MAX_SIZE=50
KC_DB_POOL_MIN_SIZE=10
KC_DB_POOL_ACQUIRE_INCREMENT=5
```

- 트래픽이 많을수록 `KC_DB_POOL_MAX_SIZE`를 50~200 정도로 넉넉히 설정하는 것이 일반적입니다.[^5_11]


### (2) PostgreSQL 내부 튜닝

Postgres(postgre.a.com) 쪽에서도 다음을 조정하면 효과가 큽니다.[^5_12][^5_9]

- `max_connections = 500` (Keycloak 인스턴스 * 커넥션 풀 최대값을 감안해 설정)
- `shared_buffers = 16GB`, `effective_cache_size = 48GB` (메모리가 충분하면)
- `work_mem = 32MB`
- `maintenance_work_mem = 1~2GB`
- `checkpoint_completion_target = 0.9`
- `wal_buffers = 16MB`
- `random_page_cost ≈ 1.1` / `effective_io_concurrency`를 SSD 기준으로 튜닝
- `pg_stat_statements` 활성화 → 어떤 쿼리가 병목인지 모니터링

이러한 설정은 Keycloak + Postgres 구성을 다루는 성능 안내 글에서 실제 cnpg/클러스터 기반 구성 예시로 제시되고 있습니다.[^5_12][^5_9]

### (3) 인덱스 및 쿼리 패턴

Keycloak은 기본적으로 자체 인덱스를 생성하지만, 일부 쿼리는 `user_entity`/`user_role_mapping` 테이블에 대해 매우 빈번하게 발생합니다. 필요 시 다음과 같은 커스텀 인덱스를 고려:

```sql
-- 예시 (실제는 Keycloak 스키마 버전에 따라 달라짐)
CREATE INDEX CONCURRENTLY idx_user_entity_email ON user_entity (email);
CREATE INDEX CONCURRENTLY idx_user_role_mapping_role ON user_role_mapping (role_id);
```

이렇게 하면 수십만 사용자 규모에서도 로그인/토큰 발급 시 쿼리 지연이 감소합니다.[^5_11]

### (4) 네트워크와 TLS 오버헤드

- Postgres가 외부 EC2라면, Keycloak 인스턴스와 **같은 리전/VPC**를 사용하고, 가능하면 **내부 프라이빗 IP**로 연결합니다.
- TLS 인증 여부 상관없이, **Postgres와 Keycloak 간 RTT가 낮을수록 로그인 성능이 좋아집니다.**
- 이미지 배포 시 `KC_DB_SSL_MODE=require`로 강제하지만, 불필요한 TLS 인증을 피하기 위해 Postgres 인스턴스는 내부망에서만 접근 가능하도록 설계하는 것이 일반적입니다.[^5_9]

***

## 정리형 선택 가이드 (아키텍트 관점)

- **외부 Postgres(postgre.a.com:5432) 사용 시**
    - Keycloak → `KC_DB_URL`로 외부 주소 + `KC_DB_SSL_MODE=require`
    - Postgres는 `pg_hba` + `listen_addresses` + 방화벽 개방으로 외부 TCP 접속 허용
- **마이그레이션**
    - 이전 DB: `pg_dump` → 새 Postgres `psql` 복원 → `KC_DB_URL` 변경 후 Keycloak 재시작
- **성능**
    - `KC_DB_POOL_*` 설정 수정 + Postgres `shared_buffers`, `work_mem`, `max_connections` 튜닝 + `pg_stat_statements`로 병목 쿼리 모니터링

원하시면 다음 단계에서

1. `Keycloak 26.x + Postgres 16` 기준 실제 `keycloak.conf` 템플릿, 또는
2. `Kubernetes(Helm) + 외부 Postgres` 운영용 values.yaml 예시
을 엔터프라이즈 수준으로 정리해드릴게요.
<span style="display:none">[^5_13][^5_14][^5_15][^5_16][^5_17]</span>

<div align="center">⁂</div>

[^5_1]: https://pharosinfo.tistory.com/entry/Keycloak-postgresql-연동

[^5_2]: https://github.com/keycloak/keycloak/issues/16398

[^5_3]: https://alice-secreta.tistory.com/29

[^5_4]: https://docs.redhat.com/ko/documentation/red_hat_single_sign-on/7.6/html/server_installation_and_configuration_guide/external_database

[^5_5]: https://soojae.tistory.com/48

[^5_6]: https://forum.keycloak.org/t/how-should-kc-db-url-be-formatted-for-postgres/18626

[^5_7]: https://blog.devops.dev/deploy-keycloak-v24-to-k8s-cluster-with-helm-83e6714f2888?gi=a5da525ba121

[^5_8]: https://docs.redhat.com/ko/documentation/red_hat_single_sign-on/7.5/html/server_installation_and_configuration_guide/external_database

[^5_9]: https://velog.io/@bytebliss/Keycloak-고가용성-인증-시스템-구축-가이드

[^5_10]: https://www.reddit.com/r/KeyCloak/comments/1lco5jz/methods_to_move_users_from_keycloak_to_another/

[^5_11]: https://kjbg.tistory.com/entry/Keycloak-13-성능-최적화와-모니터링

[^5_12]: https://www.linkedin.com/posts/jeeunglee_%ED%8A%9C%EB%8B%9D-%EC%97%86%EC%9D%B4-%EC%84%B1%EB%8A%A5-2%EB%B0%B0-postgresql-%EB%A9%94%EB%AA%A8%EB%A6%AC-%EC%84%A4%EC%A0%95-%EC%B5%9C%EC%A0%81%ED%99%94-%EA%B5%AC%EC%B6%95-activity-7424772781470543872-GC1C

[^5_13]: https://velog.io/@bytebliss/keyclock-4

[^5_14]: https://velog.io/@bytebliss/keycloak-이슈-해결-ㄱㄱ

[^5_15]: https://ssmyefrin.tistory.com/111

[^5_16]: https://tommypagy.tistory.com/631

[^5_17]: https://subji.github.io/posts/2020/07/08/keycloak2


---

# 내부 즉 회사내 인증표준 시스템으로 이용하고자 합니다. 아키텍처 관점에서 dmz 내외, waf, nac 등 보안 솔루션을 도려하여 도식화해 주세요.

회사 내부 표준 인증 시스템(기업용 SSO/IdP)으로 Keycloak을 쓰신다면, **Keycloak 자체는 내부망(LAN)에 두고, DMZ에는 WAF·리버스 프록시만 배치**하는 구조가 가장 일반적입니다.  아래에 DMZ·WAF·NAC까지 포함한 레퍼런스 아키텍처를 “도식화에 가까운 텍스트 다이어그램”으로 설명하겠습니다.[^6_1][^6_2]

***

## 1. 전체 보안 존 개념

Keycloak을 기준으로 한 보안 존 구성은 보통 이렇게 나뉩니다.[^6_3][^6_1]

- **인터넷 존**: 사내/외부 사용자가 브라우저·모바일·VPN 클라이언트로 접근
- **외부 DMZ 존**:
    - WAF / L4·L7 로드밸런서
    - 리버스 프록시(예: Nginx/Apache, API Gateway)
- **내부 DMZ 또는 서비스 DMZ 존(선택)**:
    - 사내 포털, B2B API, 외부 노출이 필요한 일부 서비스
- **내부 업무망(LAN)**:
    - Keycloak 클러스터(IdP)
    - 사내 업무 시스템(PMS, ERP, Groupware 등)
    - AD/LDAP, HR 시스템, 사내 DB 등 사용자·권한 소스
- **보안/인증 인프라**:
    - NAC (네트워크 접속 제어)
    - IDS/IPS, SIEM, EDR 등

JANUA의 Keycloak 보호 아키텍처도 비슷하게 **Internet ⇄ FW1 ⇄ DMZ(Reverse Proxy) ⇄ FW2 ⇄ Internal LAN(Keycloak)** 구조를 추천합니다.[^6_1]

***

## 2. 텍스트 아키텍처 다이어그램

### 2-1. 논리 구조 (외부 사용자 기준)

```text
[Internet / 외부 사용자 브라우저]
        |
        v
+--------------------+
|    Perimeter FW    |
+--------------------+
        |
        v
+--------------------+     +-------------------+
|        WAF         | --> |  Web Attack Logs  |
+--------------------+     +-------------------+
        |
        v
+--------------------+
| Reverse Proxy / LB |
| (Nginx, Apache)    |
+--------------------+
        |
    (FW 2, 내부방화벽)
        |
        v
+-----------------------------+
|   Internal Auth Zone        |
|  - Keycloak Cluster (IdP)   |
|  - Redis/Cache (선택)       |
+-----------------------------+
        |
        +------------------+
        |                  |
        v                  v
+----------------+   +---------------------+
| Corp Apps (SP) |   |  AD/LDAP, HR, DB    |
|  ERP, GW, etc. |   | (User/Group Source) |
+----------------+   +---------------------+
```

- 외부 사용자는 **직접 Keycloak에 접속하지 않고**, DMZ의 WAF + Reverse Proxy를 통해서만 접근합니다.[^6_4][^6_1]


### 2-2. 내부 사용자 + NAC까지 포함한 구조

```text
[내부 단말(PC, 노트북, 모바일)]
        |
        v
+-------------------+
|      NAC          |<-----+ 등록되지 않은 단말 차단
+-------------------+      |
        |                  |
        +------------------+
        |
        v
+--------------------+
| Internal Switch/L3 |
+--------------------+
        |
        v
+-----------------------------+
|   Internal Auth Zone        |
|  - Keycloak Cluster         |
|  - Corp Apps (SP)           |
+-----------------------------+
```

- NAC는 **“누가 네트워크에 들어올 수 있는지”**를 통제하고, Keycloak은 **“들어온 단말/사용자가 어떤 시스템에 접근 가능한지”**를 통제하는 역할로 분리됩니다.[^6_5]

***

## 3. DMZ・WAF・Reverse Proxy 역할

### 3-1. DMZ

- 정의: 외부(인터넷)와 내부망 사이에 위치한 반(半) 신뢰 구간.[^6_1]
- 역할:
    - 외부에 노출되는 **도메인/서비스의 끝단**만 배치(WAF, Reverse Proxy, 일부 공개 웹서버)
    - Keycloak·업무 시스템은 DMZ 뒤쪽 내부망에 배치하여 직접 공격면을 줄임


### 3-2. WAF(Web Application Firewall)

- DMZ에서 **첫 관문**으로 배치
- 역할:
    - OWASP Top 10 공격(SQL Injection, XSS 등) 필터링
    - 로그인·토큰 엔드포인트에 대한 Rate Limit
    - Geo-IP, Bot 차단 정책
- 처리 대상:
    - Keycloak의 `/realms/.../protocol/openid-connect/*` 등 인증 엔드포인트 URI를 우선 보호 대상으로 등록[^6_6][^6_1]


### 3-3. Reverse Proxy / API Gateway

Keycloak 공식 문서도 리버스 프록시 뒤에 Keycloak을 두는 구성을 기본으로 설명합니다.[^6_6]

- 역할:
    - **TLS 종료(HTTPS)**
    - URL 라우팅: `/auth` → Keycloak, `/app` → 사내 포털 등
    - `X-Forwarded-*` 헤더 세팅 (Keycloak의 `hostname`·`proxy-headers` 설정과 연계)[^6_4]
- 예시 (Nginx):

```nginx
location /auth {
    proxy_pass https://keycloak.internal.corp:8443;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto https;
    proxy_set_header X-Forwarded-Host $host;
}
```


***

## 4. NAC와 Keycloak 연동 관점

NAC 솔루션(예: 802.1X, Agent 기반 NAC)이 Keycloak과 OIDC로 통합되는 시나리오도 문서에 등장합니다.[^6_5]

- **NAC 역할**:
    - 단말 인증 (MAC, Agent, 802.1X)
    - 허용된 단말만 사내 VLAN에 붙게 함
- **Keycloak 역할**:
    - 사용자의 SSO 로그인, MFA, RBAC
    - NAC 관리 콘솔/포털에 접속할 때 OIDC/SAML IdP로 동작 (NAC 관리자·사용자 계정 SSO)[^6_5]

이렇게 두 시스템을 구분하면:

- 내부 단말이 먼저 **NAC를 통과해야** 내부망에 IP 할당
- 그 다음에 사용자가 브라우저로 **Keycloak을 통해 각 시스템에 로그인**
- NAC는 “네트워크 레벨의 접근 제어”, Keycloak은 “애플리케이션 레벨의 인증/인가”

***

## 5. 권장 아키텍처 옵션 비교

아래는 Keycloak을 어디에 둘지에 따라 자주 논의되는 패턴입니다.[^6_7][^6_2][^6_1]


| 패턴 | Keycloak 위치 | 장점 | 단점 |
| :-- | :-- | :-- | :-- |
| A | DMZ 내부 | 외부 접근시 홉이 적어 단순, 레이턴시 낮음 [^6_7] | DMZ가 뚫리면 IdP가 직접 노출, 보안 부담 큼 |
| B | 내부망, DMZ에는 Reverse Proxy만 | Keycloak 직접 노출 없음, 관리·백업·모니터링 용이 [^6_1] | DMZ–내부 간 FW 규칙·프록시 설정 필요 |
| C | 내부망 2중화(Region A/B 또는 2 클러스터), DMZ는 글로벌 LB | 가용성·DR에 유리, 대규모 엔터프라이즈 패턴 [^6_8][^6_9] | 설계·운영 복잡, 네트워크 설계와 DNS 전략 필요 |

대부분의 **사내 표준 인증 시스템** 용도라면 **B 패턴(내부망 배치 + DMZ Reverse Proxy)**가 현실적입니다.[^6_1]

***

## 6. 보안·운영 측면 필수 체크리스트

아키텍처 설계 시 꼭 고려해야 하는 항목들입니다.[^6_10][^6_3][^6_1]

- **Keycloak Admin Console**
    - 외부에서는 절대 보이지 않도록, 내부망 전용 도메인/포트 사용 (`hostname-admin` 별도 설정도 가능)[^6_4]
- **네트워크 분리**
    - DMZ ↔ 내부망 사이에 별도의 방화벽 정책
    - Keycloak ↔ AD/LDAP/DB 간 포트만 최소 허용 (LDAPS, Postgres, etc.)[^6_7]
- **로그 \& 모니터링**
    - WAF, Reverse Proxy, Keycloak, NAC, 애플리케이션 로그를 SIEM으로 집계
    - 비정상 로그인·Brute force 패턴 탐지[^6_3]
- **Zero Trust 지향**
    - “내부망이라고 다 신뢰하지 않는다”는 관점에서, 내부 애플리케이션도 전부 Keycloak/OIDC로 보호
    - 서비스 간 호출도 mTLS/API Gateway+Keycloak 토큰 검증 사용[^6_8][^6_3]

***

여기까지가 “회사 내 표준 인증 시스템”으로 쓰는 Keycloak의 전형적인 DMZ/WAF/NAC 포함 아키텍처입니다. 실제로는 **사내 시스템이 대부분 웹인지, VPN/VDI까지 포함하는지에 따라** 상세 구성이 많이 달라지는데요,

현재 환경이

1) 대부분 **웹 기반 사내 시스템(포털, 그룹웨어, ERP 등)** 위주인지,
2) 아니면 **VPN/VDI·개발자 플랫폼 등까지 아우르는 광범위 SSO**가 목표인지
어느 쪽에 더 가깝나요?
<span style="display:none">[^6_11][^6_12][^6_13][^6_14][^6_15]</span>

<div align="center">⁂</div>

[^6_1]: https://www.janua.fr/protecting-keycloak-redhat-sso-with-a-reverse-proxy/

[^6_2]: https://dev.to/mayormaier/architecting-a-keycloak-deployment-in-aws-2id4

[^6_3]: https://www.slideshare.net/slideshow/understanding-zero-trust-architecture-with-keycloak/286227817

[^6_4]: https://github.com/keycloak/keycloak/discussions/34712

[^6_5]: https://docs.genians.com/nac/5.0/release/ko/authentication/integrate-external/oidc-keycloak.html

[^6_6]: https://www.keycloak.org/server/reverseproxy

[^6_7]: https://www.reddit.com/r/KeyCloak/comments/1ivk5ld/keycloak_in_dmz_with_no_userdata_in_local/

[^6_8]: https://www.keycloak.org/high-availability/multi-cluster/deploy-keycloak-kubernetes

[^6_9]: https://www.youtube.com/watch?v=y1yE7Rd3lGE

[^6_10]: https://www.oloid.com/blog/enterprise-sso

[^6_11]: https://docs.github.com/ko/enterprise-server@3.15/admin/managing-iam/using-saml-for-enterprise-iam/configuring-saml-single-sign-on-for-your-enterprise

[^6_12]: https://nginxstore.com/blog/keycloak/자습서-keycloak-설치-구성/

[^6_13]: https://frontegg.com/guides/enterprise-sso

[^6_14]: https://support.catonetworks.com/hc/en-us/articles/26243212522141-Configuring-Keycloak-SSO

[^6_15]: https://blog.logto.io/ko/enterprise-sso


---

# 개발자 플랫폼과 API GW 통합이 가장 중요합니다

For a developer platform where the API gateway is central, a good pattern is: **Keycloak as the enterprise IdP in the internal zone, and every API/app behind the API Gateway trusts Keycloak-issued tokens**.  Below is an architecture-style explanation focusing on dev experience and gateway integration.[^7_1][^7_2]

***

## 1. Big picture: “API-first IdP” model

In this model, Keycloak is treated as an **API‑first identity platform**: all developers and services integrate via OIDC/OAuth flows and standardized tokens.[^7_3][^7_4]

High‑level flow:

1. Developer or client app calls the **API Gateway**.
2. API Gateway checks for a JWT/OAuth2 access token issued by Keycloak.
3. If missing or invalid, the gateway redirects the user (or returns 401) and the client obtains a token from Keycloak.
4. Once a valid token is present, the gateway forwards the request to backend services, optionally adding identity/role information from the token to headers.[^7_5][^7_1]

This keeps authentication and authorization centralized, while API routing, throttling, and monitoring stay in the gateway.[^7_6][^7_5]

***

## 2. Network \& security layout with API GW

Combining the DMZ layout we discussed with an API gateway–centric view, you can picture the zones like this.[^7_2][^7_7]

```text
[External devs / apps / partners]         [Internal devs / CI/CD / tools]
             |                                         |
             v                                         v
      +--------------+                         +--------------+
      |   Internet   |                         |  Corp LAN    |
      +--------------+                         +--------------+
             |                                         |
             v                                         v
      +------------------+                      +------------------+
      |   Perimeter FW   |                      |   Internal FW    |
      +------------------+                      +------------------+
             |                                         |
             v                                         v
      +------------------+                      +------------------+
      |       WAF        |   (optional)        |  Internal WAF    |
      +------------------+                      +------------------+
             |                                         |
             +------------------+----------------------+
                                v
                     +----------------------+
                     |   API Gateway (DMZ)  |
                     |  - Authz policies    |
                     |  - Rate limiting     |
                     +----------+-----------+
                                |
                         (FW rule: 443)
                                |
                                v
           +----------------------------------------+
           |     Internal Auth & Services Zone      |
           |  - Keycloak Cluster (IdP)             |
           |  - Developer Portal / API Catalog     |
           |  - CI/CD, Git, Registry, etc.         |
           |  - Backend microservices / APIs       |
           +----------------+----------------------+
                            |
                            v
                    +------------------+
                    |  AD/LDAP / HR    |
                    |  User store      |
                    +------------------+
```

Key points:

- The **API Gateway sits in the DMZ** and is the single entry point for all API traffic.[^7_5][^7_1]
- **Keycloak stays inside the internal zone**; only the gateway and internal apps talk to it directly.
- The developer platform (portal, docs, token self‑service) also lives in the internal or “trusted” zone and uses Keycloak for SSO.[^7_8][^7_6]

***

## 3. How the API Gateway integrates with Keycloak

Most enterprise gateways (Kong, Apigee, NGINX, Spring Cloud Gateway, etc.) support OIDC/OAuth2. Conceptually they all do similar things.[^7_1][^7_5]

### 3.1 Token validation in the gateway

- Configure the gateway with:
    - Keycloak **issuer URL**: `https://auth.company.com/realms/my-realm`
    - **JWKS endpoint**: `.../protocol/openid-connect/certs`
    - Accepted **audience/client IDs** (API clients)[^7_9][^7_10]
- For each API route, apply an “OAuth2/JWT” plugin or policy:
    - Require Bearer token in `Authorization` header.
    - Validate signature against Keycloak JWKS.
    - Check expiry, audience, and optionally scopes/roles.[^7_1]

If validation fails, the gateway returns **401/403** and may include a `WWW-Authenticate` header to guide clients to the correct Keycloak realm.[^7_4]

### 3.2 AuthN + AuthZ split

A widely-used pattern is:

- **Authentication**: Keycloak issues tokens.
- **Coarse-grained authorization**: API Gateway checks scopes/roles in the token (e.g. `role:developer`, `scope:api:read`).[^7_1]
- **Fine-grained authorization**: backend services apply domain-specific rules (project ownership, resource-level ACLs).

This keeps your gateway policies relatively simple, but still centralizes “who can even reach this API family.”[^7_11]

***

## 4. Developer platform view

From developers’ perspective, they mostly interact with:

1. **Developer portal** (API catalog, docs, onboarding).
2. **Keycloak** (for SSO and API credentials).
3. **API Gateway** (as the runtime endpoint and rate limiting layer).[^7_12][^7_6]

### 4.1 Onboarding \& identity model for developers

A clean model is:

- Developers log in to the **dev portal** using Keycloak (SSO).
- Devs are assigned to **groups** and **roles** in Keycloak:
    - `dev-team-a`, `dev-team-b`
    - `api-owner`, `api-consumer`, `platform-admin`[^7_13][^7_4]
- The developer portal uses Keycloak’s **Admin APIs** (with a service account) to:
    - Register or approve **API clients** (machine-to-machine accounts).
    - Attach API scopes/roles to those clients.
- The API gateway trusts those client credentials (client credentials flow) or user tokens (authorization code flow) issued by Keycloak.[^7_10][^7_3]


### 4.2 Typical flows

- **User → UI → API** (Authorization Code w/ PKCE):

1. SPA/Web app redirects user to Keycloak login.
2. User gets tokens.
3. SPA calls API through the gateway using the access token.
- **Service → Service** (Client Credentials):

1. Backend service obtains token from Keycloak using client credentials.
2. Calls API Gateway with Bearer token.
3. Gateway validates token and forwards.[^7_4][^7_5]

This covers both developer‑facing UIs and machine integrations.

***

## 5. Where NAC and internal dev tools fit

Because you care about developer platforms, you likely have things like Git, CI/CD, artifact registries, k8s dashboards, etc.

- **NAC** ensures only authorized devices can join engineering networks (Wi-Fi/LAN).
- Once on the network, devs authenticate to:
    - Git, CI/CD, registries, internal dashboards — all via **Keycloak SSO**.
    - API Gateway–fronted internal APIs, again using Keycloak tokens.[^7_14][^7_15]

In some NAC products, the NAC admin UI itself can use Keycloak as an OIDC IdP, so even **admin access to NAC is SSO’d**.[^7_14]

***

## 6. API Governance \& multi‑team developer experience

For a developer platform, **governance without killing autonomy** is key. Modern API gateway articles call this “adaptive API governance.”[^7_12][^7_11]

Common patterns:

- **Central policies in the Gateway**:
    - Enforce that every public API route:
        - uses TLS,
        - has some form of Keycloak token validation,
        - emits audit logs with subject/user ID.[^7_1]
- **Per‑team autonomy**:
    - Teams can add routes for their microservices, but they must reference shared auth policies (e.g. `auth-keycloak-standard`, `auth-keycloak-internal-only`).
- **Portal‑driven self‑service**:
    - Teams publish their APIs to the portal and select which scopes/roles are required.
    - Other teams can “subscribe” to an API, which triggers client registration/role grants automatically through Keycloak.[^7_6][^7_8]

This gives you a cohesive platform where teams move fast, but security and auth remain consistent.

***

If you share which API gateway you’re considering (e.g. Kong, NGINX, Spring Cloud Gateway, Apigee, AWS API Gateway), I can sketch a very concrete, product‑specific diagram plus example config (routes, OIDC plugin settings, Keycloak client config) tailored to that stack.
<span style="display:none">[^7_16][^7_17][^7_18]</span>

<div align="center">⁂</div>

[^7_1]: https://www.redhat.com/ko/topics/api/what-does-an-api-gateway-do

[^7_2]: https://dev.to/mayormaier/architecting-a-keycloak-deployment-in-aws-2id4

[^7_3]: https://didit.me/ko/blog/how-api-first-identity-platforms-accelerate-developer-integration-and-innovation-de/

[^7_4]: https://frontegg.com/guides/enterprise-sso

[^7_5]: https://www.ibm.com/kr-ko/think/topics/api-gateway

[^7_6]: https://ideatec.co.kr/ipaas_news_/?bmode=view\&idx=8475995

[^7_7]: https://www.janua.fr/protecting-keycloak-redhat-sso-with-a-reverse-proxy/

[^7_8]: https://kr.linkedin.com/pulse/api-management-integration-enterprise-application-development-cpanc?tl=ko

[^7_9]: https://www.keycloak.org/server/reverseproxy

[^7_10]: https://support.catonetworks.com/hc/en-us/articles/26243212522141-Configuring-Keycloak-SSO

[^7_11]: https://www.nginxkorea.co.kr/source/?q=YToyOntzOjQ6InBhZ2UiO2k6MjtzOjEyOiJrZXl3b3JkX3R5cGUiO3M6MzoiYWxsIjt9\&bmode=view\&idx=144342160\&t=board

[^7_12]: https://nginxstore.com/blog/api-gateway/api-개발자-경험이-중요한-이유/

[^7_13]: https://blog.logto.io/ko/enterprise-sso

[^7_14]: https://docs.genians.com/nac/5.0/release/ko/authentication/integrate-external/oidc-keycloak.html

[^7_15]: https://velog.io/@bytebliss/Keycloak-고가용성-인증-시스템-구축-가이드

[^7_16]: https://api7.ai/ko/blog/api-gateway-in-api-economy

[^7_17]: https://www.workato.com/the-connector/ko/국내-기업이-사용할-수-있는-api-통합-플랫폼의-필수조건/

[^7_18]: https://www.reddit.com/r/aws/comments/1gpixqo/what_does_api_gateway_actually_do/

