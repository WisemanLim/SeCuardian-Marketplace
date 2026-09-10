<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# 브라우저 등에서 자동으로 연결되는 AI 도우이와의 대화시의 트래픽을 어떻게 알 수 있을까요. 예를 들어 chrome에서 gemini를 통해 질의응답 또는 파일 분석시 네트워크 트래픽 등을 확인할 수 있는 방법은?

Chrome에서 Gemini 같은 브라우저 내 AI 도우미의 트래픽을 보려면 기본적으로 **브라우저 개발자 도구(Network 탭)**와 **저수준 네트워크 로그(net-export, net‑internals, 패킷 캡쳐 툴)**를 조합해서 보는 방식이 가장 현실적입니다.[^1_1][^1_2][^1_3][^1_4][^1_5]

## 1. 가장 간단한 방법: Chrome DevTools Network 탭

Gemini가 브라우저 안에서 호출하는 HTTP(S) 요청은 결국 브라우저 네트워크 스택을 타기 때문에, DevTools의 Network 패널로 기본적인 트래픽은 모두 볼 수 있습니다.[^1_6][^1_1]

1. DevTools 열기
    - Windows/Linux: `Ctrl + Shift + I` 또는 `F12`.[^1_2]
    - macOS: `Command + Option + I`.[^1_2]
2. Network 탭 선택
    - 상단 탭에서 **Network**를 클릭합니다.[^1_1][^1_6]
3. 로그 유지 설정
    - Gemini를 여러 번 호출할 경우를 대비해 “Preserve log / 로그 유지” 옵션을 켜두면, 페이지 전환이나 리로드 동안 요청 목록이 지워지지 않습니다.[^1_2]
4. Gemini 사용 흐름 재현
    - 이제 Chrome에서 Gemini 패널을 열고 질문/파일 업로드/웹페이지 요약 등 원하는 시나리오를 실행합니다.[^1_7]
5. 요청 필터링 및 상세 보기
    - Host, Path, Method, Status, Size, Time 등의 컬럼을 보면서 Gemini 관련 도메인을 찾습니다
(예: `*.google.com`, `*.gemini.google.com` 계열로 추정).[^1_6][^1_1]
    - 각 요청을 클릭하면
        - Headers 탭: 요청/응답 헤더, URL, 쿼리 파라미터, 인증 토큰 형태 등 확인.[^1_1]
        - Payload/Request body: 프롬프트 텍스트나 메타데이터가 어떻게 전송되는지 확인 가능(일부는 암호화/압축).[^1_1]
        - Response: 모델 응답(텍스트, JSON 구조 등)을 확인.[^1_1]
6. 전체 세션 내보내기 (HAR)
    - 상단 메뉴에서 **Export HAR…** 를 선택하면, 관측한 모든 네트워크 요청을 HAR(HTTP Archive) 파일로 저장할 수 있습니다.[^1_2]
    - 이후 Python/R로 HAR를 파싱해서,
        - 총 요청 수
        - 총 전송/수신 바이트
        - AI API 콜만 필터링한 트래픽량
등을 계산할 수 있습니다.

이 방식은 “Gemini를 쓸 때 어떤 HTTP 요청이 오가는지, 어느 도메인으로 어느 정도 데이터를 보내는지” 수준까지는 꽤 정밀하게 알 수 있습니다.

## 2. 브라우저 레벨 저수준 로그: chrome://net-export, chrome://net-internals

DevTools는 HTTP 단위의 뷰를 제공하지만, 더 저수준에서 브라우저 네트워크 스택 전체 이벤트를 보고 싶으면 **net-export / net‑internals**를 사용할 수 있습니다.[^1_3][^1_4][^1_5]

### 2‑1. chrome://net-export

1. 주소창에 `chrome://net-export/` 입력.[^1_5][^1_3]
2. “Start Logging to Disk” 클릭 후 저장 경로 지정.[^1_3][^1_5]
3. 다른 탭에서 Gemini를 사용하면서 질문/파일 업로드/자동 탐색 등을 수행.[^1_8][^1_7]
4. “Stop Logging”을 누르면 JSON 형태의 NetLog 파일이 만들어집니다.[^1_5][^1_3]

이 NetLog 파일을 전용 뷰어나 분석 스크립트로 열면, HTTP 요청 뿐 아니라 DNS, TLS 핸드셰이크, HTTP/2 세션 정보 등 브라우저 수준의 다양한 네트워크 이벤트를 확인할 수 있습니다.[^1_5]
이를 통해:

- Gemini 호출 시 어떤 프로토콜(HTTP/2, HTTP/3 등)이 사용되는지.[^1_4][^1_5]
- 세션/스트림 단위로 어떤 호스트와 얼마나 자주 통신하는지.[^1_4][^1_5]
- 재시도/에러/타임아웃 등의 저수준 이벤트.[^1_5]

까지 볼 수 있습니다.

### 2‑2. chrome://net-internals (HTTP/2 분석 등)

`chrome://net-internals`는 HTTP/2 같은 프로토콜을 더 세밀하게 보고 분석하는 용도로 쓰입니다.[^1_4][^1_5]

- 메뉴에서 HTTP/2를 선택
- Gemini 사용 시점에 어떤 호스트로 HTTP/2 세션이 열렸는지 확인
- 특정 세션 ID를 클릭해서 Events 뷰로 들어가면, 스트림 ID, 우선순위, 서버 푸시 등 저수준 트래픽 흐름을 볼 수 있습니다.[^1_4][^1_5]

다만 이 도구는 UI가 다소 로우레벨이고, “총 트래픽량”을 간단하게 보는 것보다 **프로토콜 분석**에 더 적합합니다.[^1_4][^1_5]

## 3. 브라우저 바깥에서 보는 방법: 패킷 캡쳐/프록시 툴

브라우저 단에서 보이지 않는 부분까지 포함해 OS 레벨 트래픽을 보고 싶으면, **Fiddler, Wireshark, tcpdump** 같은 툴을 사용할 수 있습니다.[^1_2][^1_5]

### 3‑1. Fiddler (HTTP 프록시)

- Fiddler는 HTTP(S) 트래픽을 프록시 레벨에서 수집하는 도구로, Windows/macOS/Linux에서 동작합니다.[^1_2]
- 브라우저를 Fiddler 프록시를 사용하도록 설정한 후 Gemini를 호출하면, 모든 HTTP 요청과 응답을 Fiddler에서 캡쳐할 수 있습니다.[^1_2]
- HTTPS를 해독하려면 Fiddler의 루트 인증서를 설치하고, 브라우저가 이를 신뢰하도록 설정해야 합니다.[^1_2]

이렇게 하면 DevTools에서 보이는 것과 유사한 정보지만, 브라우저 외 다른 애플리케이션 트래픽까지 한 화면에서 볼 수 있고, 장기적인 세션 분석에 더 적합합니다.[^1_2]

### 3‑2. tcpdump / Wireshark (패킷 레벨 캡쳐)

- `tcpdump`로 인터페이스 단위 캡쳐:
`tcpdump -i [interface] -w trace.pcap` 형태로 실행하여 raw TCP 패킷을 수집합니다.[^1_2]
- 생성된 `trace.pcap` 파일을 Wireshark로 열면,
    - 특정 IP/포트(예: Gemini backend 서버)에 대한 트래픽 필터링
    - 총 바이트, RTT, 재전송 등 네트워크 성능 분석
을 할 수 있습니다.[^1_5]

이 방식은 암호화된 TLS 내용을 복호화하지 않는 이상 애플리케이션 payload는 보이지 않지만, **순수 네트워크 레벨의 트래픽 양과 품질**을 분석하는 데 강력합니다.[^1_5][^1_2]

## 4. 실제로 “AI 도우미 트래픽”을 계량하는 접근 방법

질문하신 관점이 “브라우저 등에서 자동으로 연결되는 AI 도우미와의 대화 시 트래픽을 어떻게 알 수 있는가”라면, 실무적으로는 다음 조합이 많이 쓰일 것 같습니다.

### 4‑1. 도메인/프로세스 기준 필터링

1. Chrome DevTools Network에서 Gemini 관련 도메인을 추려서 목록화.[^1_7][^1_6][^1_1]
2. 해당 도메인을 기준으로 HAR에서 요청만 필터링해 총 `encodedDataLength` 혹은 `transferSize` 합계를 계산.
3. Fiddler나 Wireshark에서는 IP 또는 호스트 이름을 기준으로 필터링해 동일하게 합산.

이렇게 하면 “Gemini와의 상호작용 동안 전송/수신된 총 바이트”를 정량화할 수 있습니다.[^1_1][^1_2]

### 4‑2. 기능별 세션 기준 측정

- 질의응답, 코드 리뷰, 파일 분석, 웹페이지 자동 탐색 등 기능별로 시나리오를 정의.[^1_8][^1_7]
- 각 시나리오 실행 전에 net-export나 HAR 로깅을 시작하고, 종료 후 파일로 저장.[^1_3][^1_5][^1_2]
- 파일을 분석해서
    - 요청 수
    - 평균/최대 응답 크기
    - 업로드된 파일에 대응하는 요청의 Content-Length
를 뽑아 기능별 트래픽 프로파일을 만들 수 있습니다.


### 4‑3. 자동화/스크립트화

- HAR/NetLog를 파싱하는 Python/R 스크립트를 작성해서, 특정 도메인/패턴에 대한 트래픽을 정기적으로 집계.
- 결과를 시계열로 저장하면, “하루/주간/월간 Gemini 사용량 및 네트워크 비용” 같은 지표도 만들 수 있습니다.


## 5. 한계와 주의점 (개인정보/보안)

- Chrome Gemini는 구글 계정과 연동될 수 있으며, 전송되는 프롬프트/파일에는 민감 정보가 포함될 수 있습니다.[^1_9][^1_7]
- DevTools/Fiddler 등에서 요청 내용을 볼 수 있다는 것은, 그 환경에 접근 가능한 사람은 해당 데이터를 볼 수 있다는 뜻이기도 하니, 캡쳐 파일(NetLog, HAR, pcap)을 저장할 때 권한 관리가 필요합니다.[^1_5][^1_2]
- TLS 암호화를 해제해서 패킷 payload를 보는 작업은, 로컬 분석 목적이라도 보안 리스크가 있으니 시험용 환경이나 비민감 데이터로 제한하는 것이 좋습니다.[^1_5][^1_2]

***

지금 궁금하신 건 “트래픽 양(바이트/요청 수) 계량”에 더 관심이 있으신가요, 아니면 “어떤 데이터가 정확히 어떤 형태로 외부로 나가는지”를 포렌식/컴플라이언스 관점에서 보고 싶은 쪽에 더 가깝나요?
<span style="display:none">[^1_10][^1_11][^1_12][^1_13][^1_14][^1_15]</span>

<div align="center">⁂</div>

[^1_1]: https://developer.chrome.com/docs/devtools/network/overview

[^1_2]: https://learn.microsoft.com/ko-kr/azure/azure-web-pubsub/howto-troubleshoot-network-trace

[^1_3]: https://sweethygge.tistory.com/12

[^1_4]: https://itchipmunk.tistory.com/271

[^1_5]: https://carrido-hobbies-well-being.tistory.com/100

[^1_6]: https://developer.chrome.com/docs/devtools/network?hl=ko

[^1_7]: https://gemini.google/kr/overview/gemini-in-chrome/?hl=ko

[^1_8]: https://support.google.com/chrome/answer/16821166?hl=ko

[^1_9]: https://blog.naver.com/ifchris/224278782150

[^1_10]: https://developer.chrome.com/docs/devtools/network

[^1_11]: https://developer.chrome.com/blog/new-in-devtools-131?hl=ko

[^1_12]: https://chromewebstore.google.com/detail/network-monitor/hknlclmampgjlgmnlihfohdinjbagmge?hl=ko

[^1_13]: https://inmarketing.kr/goolgenews/gemini-in-chrome-guide-2026/

[^1_14]: https://docs.cloud.google.com/storage/docs/analyze-data-gemini-cloud-assist?hl=ko

[^1_15]: https://www.youtube.com/watch?v=5uPwjfiFs58


---

# Cli기반으로 상세하게 모니터링을 하고 싶습니다 대화내용의 핵심이 아닌 사용량을 분석하기 위해 트래픽 모니타링이이 주요 목적입니다.

CLI 기반으로 네트워크 트래픽을 모니터링해서 “AI 도우미 사용량”을 정량 분석하려면, **프로세스 기준 도구 + 인터페이스 기준 도구 + 패킷 캡처 도구**를 조합하는 방식이 가장 실용적입니다.[^2_1][^2_2][^2_3][^2_4][^2_5][^2_6]

***

## 1. 기준 잡기: 무엇을 트래픽으로 볼 것인가

대화 내용이 아니라 **사용량(트래픽량)**이 목적이라면, 최소 다음 세 축을 분리해서 보는 게 좋습니다.

- 프로세스 기준: `chrome` 프로세스가 얼마나 보내고 받는지.[^2_2][^2_4][^2_5]
- 인터페이스 기준: 특정 NIC(예: `eth0`, `wlan0`) 수준의 총 트래픽.[^2_4][^2_5][^2_6][^2_1]
- 목적지 기준: Google/Gemini 관련 IP/도메인으로 나가는 트래픽만 필터링.[^2_3][^2_7][^2_1]

이걸 CLI 도구로 매핑하면:

- 프로세스별: `nethogs`.[^2_5][^2_6][^2_2][^2_4]
- 인터페이스 실시간: `iftop`, `nload`, `cbm`.[^2_7][^2_1][^2_2][^2_4][^2_5]
- 누적 통계: `vnstat`.[^2_1][^2_7][^2_5]
- 패킷/목적지 필터링: `tcpdump`, `tshark`, `ngrep`.[^2_3][^2_7][^2_1]

***

## 2. 프로세스 기준: Chrome/Gemini 트래픽 양 보기 (nethogs)

CLI에서 “브라우저 프로세스가 실제로 얼마나 쓰고 있는지”를 보는 데에 `nethogs`가 가장 직관적입니다.[^2_6][^2_2][^2_4][^2_5]

### 설치

- Debian/Ubuntu 계열:
`sudo apt install nethogs`.[^2_4][^2_7]
- RHEL/CentOS 계열:
`sudo yum install nethogs`.[^2_4]


### 사용

```bash
sudo nethogs
```

- 프로세스/사용자/인터페이스별로 실시간 송신/수신 대역폭(kB/s, MB/s)을 보여줍니다.[^2_2][^2_5][^2_6][^2_4]
- 여기서 `chrome` (또는 `google-chrome`, `chromium`) 프로세스를 확인하면, Gemini를 쓰는 동안 브라우저가 소비하는 대역폭을 실시간으로 볼 수 있습니다.[^2_5][^2_6][^2_2][^2_4]

실무적인 패턴:

- Gemini 사용 전후로 `nethogs` 스냅샷을 캡처해 평균/피크 대역폭을 비교.
- 스크린레코딩이나 `script` 명령으로 `nethogs` 출력 로그를 남겨서 나중에 정량 분석.

***

## 3. 인터페이스 기준: 실시간 트래픽 흐름 및 대역폭 (iftop/nload)

브라우저 이외의 다른 프로세스까지 포함해서 NIC 수준의 트래픽을 보고 싶으면 `iftop`과 `nload` 조합이 좋습니다.[^2_7][^2_6][^2_1][^2_2][^2_5][^2_4]

### 3‑1. iftop: IP/Port별 실시간 모니터링

`iftop`은 지정한 인터페이스의 현재 연결과 각 연결의 전송/수신 속도를 보여주는 실시간 CLI 도구입니다.[^2_6][^2_1][^2_2][^2_7][^2_5][^2_4]

설치/실행 예:

```bash
sudo apt install iftop    # Ubuntu 계열[web:25]
sudo iftop -i eth0        # eth0 인터페이스 모니터링[web:17][web:24][web:25][web:30]
```

- 좌우 방향 화살표로 송신/수신 속도 표시.[^2_1][^2_5][^2_6]
- 상단에는 전체 인터페이스 대역폭 평균/피크 등의 요약값.[^2_5][^2_1]
- 목적지 IP/포트를 보고 Gemini 관련 주소(예: Google IP 범위)만 관찰할 수 있습니다.[^2_3][^2_1]


### 3‑2. nload / cbm: 인터페이스별 간단 대역폭 뷰

`nload`와 `cbm`은 더 단순하게 인터페이스별 현재 트래픽을 그래픽처럼 보여주는 CLI 도구입니다.[^2_5]

```bash
sudo apt install nload
nload                      # 전체 인터페이스에서 송/수신 그래프 확인[web:27]
```

- 시간에 따른 업/다운 속도 그래프와 총 트래픽 누적치를 쉽게 볼 수 있습니다.[^2_5]

이 도구들은 “트래픽 양을 직관적으로 빠르게 확인하는” 용도로 좋고, 정량 분석은 `vnstat`와 같이 쓰는 편이 좋습니다.[^2_7][^2_1][^2_5]

***

## 4. 누적 사용량 통계: 일/월/시간 단위 집계 (vnstat)

“오늘 Gemini를 쓰느라 얼마나 데이터를 썼는지”처럼 **기간별 누적 트래픽**을 보고 싶으면 `vnstat`이 맞습니다.[^2_1][^2_7][^2_5]

### 설치/초기화

```bash
sudo apt install vnstat     # 설치[web:25][web:27]
sudo vnstat -u -i eth0      # eth0 인터페이스 데이터베이스 초기화[web:27]
```


### 조회

```bash
vnstat            # 인터페이스별 총 요약[web:25][web:27]
vnstat -d         # 일별 사용량[web:17][web:25][web:27]
vnstat -m         # 월별 사용량[web:17][web:25][web:27]
vnstat -h         # 시간당 사용량[web:17]
```

- `eth0` 전체 트래픽 중에서 Gemini에 해당하는 부분만 따로 분리하려면,
    - `tcpdump`로 구글/Gemini IP만 필터링해 별도로 누적량을 계산하거나,
    - VPN/별도 인터페이스를 통해 Gemini 트래픽을 분리하는 방식도 고려 가능합니다.

기본적으로 `vnstat`은 인터페이스 전체 기준이라 **“전체 브라우저+기타 앱 포함”**이지만, VPN/Proxy를 통한 분리로 “AI 도우미만 쓰는 NIC/터널”을 만들어 관리하는 패턴도 있습니다.[^2_8][^2_5]

***

## 5. 목적지 기준: 특정 도메인/IP에 대한 트래픽 (tcpdump/tshark/ngrep)

AI 도우미(Gemini)로 가는 트래픽만 보고 싶으면, **패킷 캡처 도구 + 필터링**이 필수입니다.[^2_9][^2_3][^2_7][^2_1]

### 5‑1. tcpdump: 필터링 캡처 후 후처리

기본 사용 예:[^2_6][^2_3][^2_7][^2_1]

```bash
sudo tcpdump -i eth0       # 모든 패킷을 콘솔에 출력[web:17][web:25][web:30]
sudo tcpdump -i eth0 host X.X.X.X -w gemini.pcap
                           # 특정 IP로 가는 패킷만 pcap 저장[web:17][web:25]
sudo tcpdump -i eth0 port 443 -w tls.pcap
                           # HTTPS 트래픽 캡처[web:25]
```

- Google/Gemini 서버 IP를 먼저 파악한 뒤(`dig`, `nslookup`, 혹은 DevTools에서 호스트 확인),[^2_10][^2_11][^2_7]
- 해당 IP를 `host` 필터로 걸어 캡처하면, 그 IP로 나가는 트래픽에 대한 **패킷 수, 총 바이트**를 pcap 파일에서 계산할 수 있습니다.[^2_9][^2_1]

CLI로 대략적인 크기를 보려면:

```bash
tcpdump -r gemini.pcap | wc -l     # 패킷 수[web:20]
ls -lh gemini.pcap                 # pcap 파일 크기 (대략 트래픽량 근사)[web:20]
```

보다 정확한 분석은 Wireshark CLI(`tshark`)를 사용해 `length` 필드를 합산하면 됩니다.[^2_12]

### 5‑2. tshark/ngrep: 실시간 필터링 뷰

`tshark`는 Wireshark의 CLI 버전으로, 필터링된 패킷 내용을 바로 CLI에서 볼 수 있습니다.[^2_12]

예:

```bash
sudo tshark -i eth0 -Y "ip.addr == X.X.X.X"
```

- `ip.addr == X.X.X.X`로 특정 IP를 필터링하고, 각 패킷 길이/시간을 출력하여 실시간 시계열 데이터를 만들 수 있습니다.[^2_12][^2_3]

`ngrep`은 특정 패턴(예: SNI, 호스트 이름)을 기반으로 패킷을 검색하는 데 유용합니다.[^2_3]

```bash
sudo ngrep -d eth0 "google"        # payload에 'google' 있는 패킷[web:22]
```

TLS 이후에는 payload가 암호화되지만, 여전히 SNI/일부 헤더에서 호스트 정보가 보일 수 있어 필터링에 활용 가능합니다.[^2_3]

***

## 6. 실무적인 “AI 도우미 사용량 계량” 시나리오

질문 주신 목적이 “대화 내용의 핵심이 아니라 사용량 분석”이라면, 다음과 같은 워크플로우를 구성할 수 있습니다.

### 6‑1. 환경 가정

- OS: Linux 데스크톱 or 개발용 VM
- 브라우저: Chrome (Gemini 활성화).[^2_13][^2_14]
- 네트워크: 기본 NIC `eth0` 또는 `wlan0`.


### 6‑2. 하루 단위 사용량 측정

1. `vnstat`로 NIC 레벨 전체 트래픽 누적 로그 수집.[^2_7][^2_1][^2_5]

```bash
sudo vnstat -u -i eth0  # 초기화 1회[]
```

2. 모든 트래픽이 아닌 “Gemini만”을 알고 싶으면, Chrome을 Gemini 용 전용 프록시/VPN 인터페이스(예: `tun0`)로 보내도록 설정 후 해당 인터페이스 기준으로 `vnstat`를 사용.[^2_8][^2_5]
3. 하루가 끝난 뒤:

```bash
vnstat -d -i tun0       # Gemini 프록시 인터페이스 기준 일일 사용량[][]
```


### 6‑3. 세션 단위 상세 측정 (실험/벤치마크)

1. 특정 시간에만 캡처 시작:

```bash
sudo tcpdump -i eth0 host X.X.X.X -w gemini_session.pcap
# 여기서 Gemini로 10분 정도 집중 사용
# 종료 후 Ctrl+C
```

2. 이후 `tshark`로 패킷 길이 합산:

```bash
tshark -r gemini_session.pcap -q -z io,stat,0
# interval 0은 전체에 대한 트래픽 통계[]
```

여기서 전체 바이트/패킷 수/초당 바이트 등을 얻을 수 있습니다.[^2_9][^2_12]
3. 동시에 `nethogs` 기록을 남겨 프로세스별 대역폭을 비교함으로써,
“같은 시간대에 다른 프로세스가 얼마나 사용했는지”와 분리해서 볼 수 있습니다.[^2_2][^2_4][^2_6][^2_5]

### 6‑4. 자동화 스크립트 아이디어

- `tcpdump`를 cron/systemd timer로 일정 시간마다 자동 시작/종료.
- 캡처된 pcap을 `tshark`로 파싱해서 특정 IP/포트의 총 바이트를 CSV로 기록.
- `vnstat` 출력과 합쳐서, “일자/시간별 Gemini 트래픽” 대시보드(예: Grafana, CLI 기반 R plot) 구성.

***

## 7. CLI 도구 선택 표 (요약)

| 목적 | 도구 | 레벨 | 특징/장점 |
| :-- | :-- | :-- | :-- |
| 프로세스별 실시간 대역폭 | nethogs | 프로세스 | 각 프로세스별 송/수신 속도.[^2_2][^2_4][^2_5][^2_6] |
| 인터페이스 실시간 트래픽 | iftop | NIC/IP/Port | 현재 연결별 대역폭.[^2_1][^2_2][^2_4][^2_5][^2_7][^2_6] |
| 인터페이스 전체 실시간 뷰 | nload/cbm | NIC | 간단한 그래프형 트래픽 뷰.[^2_5] |
| 기간별 누적 사용량 | vnstat | NIC | 일/월/시간별 통계.[^2_1][^2_5][^2_7] |
| 세션별 상세 패킷/바이트 | tcpdump | 패킷 | 필터링+pcap 저장 후 후처리.[^2_1][^2_3][^2_7][^2_9][^2_6] |
| CLI 패킷 분석/집계 | tshark | 패킷 | Wireshark CLI, length 합산 등.[^2_12] |
| 패턴 기반 필터링 | ngrep | 패킷 | 특정 문자열/패턴 검색.[^2_3] |


***

OS 환경을 Linux 데스크톱/VM로 두고 설명드렸는데, 실제로 사용하고 계신 주력 OS가 무엇인지(Windows, macOS, WSL2 포함)에 따라 도구 셋과 설치 방법을 조금 조정해 드리는 게 좋을 것 같습니다. 현재 트래픽 모니터링을 하시려는 환경(OS/플랫폼)은 어떤 것인가요?
<span style="display:none">[^2_15][^2_16][^2_17][^2_18][^2_19]</span>

<div align="center">⁂</div>

[^2_1]: https://colinch4.github.io/2023-12-21/09-51-52-104821-리눅스-네트워크-트래픽-모니터링/

[^2_2]: https://blog.pages.kr/1858

[^2_3]: https://boansecurity.tistory.com/197

[^2_4]: https://hbase.tistory.com/13

[^2_5]: https://ko.ubunlog.com/도구-모니터-네트워크-우분투/

[^2_6]: https://boansecurity.tistory.com/196

[^2_7]: https://spaces25.tistory.com/54

[^2_8]: https://docs.redhat.com/ko/documentation/openshift_container_platform/4.16/pdf/network_observability/netobserv-cli-using

[^2_9]: https://itgenius.tistory.com/225

[^2_10]: https://developer.chrome.com/docs/devtools/network/overview

[^2_11]: https://developer.chrome.com/docs/devtools/network?hl=ko

[^2_12]: https://labex.io/ko/tutorials/wireshark-how-to-analyze-cybersecurity-network-traffic-with-wireshark-cli-415094

[^2_13]: https://support.google.com/chrome/answer/16821166?hl=ko

[^2_14]: https://gemini.google/kr/overview/gemini-in-chrome/?hl=ko

[^2_15]: https://jaehyojjang.dev/리눅스서버/리눅스/2024-02-10-cli-monitoring-tools/

[^2_16]: https://byeo.tistory.com/entry/네트워크-트래픽-관측-도구-Network-Traffic-Monitoring-Tool

[^2_17]: https://www.reddit.com/r/linux/comments/e24tx/bandwidth_monitoring_tools_cli_some_gui/

[^2_18]: https://whchoi98.gitbook.io/kirocli/kiro-cli/lab-6.-kiro-cli/undefined-1

[^2_19]: https://www.cisco.com/c/ko_kr/support/docs/smb/switches/cisco-small-business-300-series-managed-switches/smb5569-configure-remote-network-monitoring-rmon-events-control-sett.html


---

# CLI 모니터링 세트: nethogs와 vnstat으로 AI 도구별 실시간 트래픽부터 일일 사용량까지 분석하는 자동화 스크립트 구축하기​

특정 도메인으로 향하는 트래픽만 로깅하는 tcpdump 명령어 예시
트래픽 데이터를 시계열로 저장하고 시각화하는 CLI 도구 추천

원하시는 목적이라면 `nethogs`로 **프로세스별 실시간 대역폭**을 보고, `vnstat`으로 **인터페이스 기준 5분/시간/일 단위 누적량**을 저장한 뒤, 필요한 경우 `tcpdump`/`tshark`로 **특정 도메인 또는 목적지 IP만 따로 캡처**하는 3단 구성이 가장 안정적입니다.[^3_1][^3_2]
특히 `nethogs`는 프로세스 기준, `vnstat`은 커널 인터페이스 통계 기준이므로 서로 역할이 다르고, 함께 써야 “어떤 프로세스가 얼마나 썼는지”와 “하루 전체 사용량이 얼마인지”를 동시에 관리할 수 있습니다.[^3_2][^3_1]

## 모니터링 세트

`nethogs`는 `/proc`와 `libpcap`를 이용해 프로세스별 대역폭을 보여주며, Linux에서 프로세스 기반 분석에 적합합니다.[^3_1]
`vnstat`은 패킷 스니퍼가 아니라 커널 인터페이스 통계를 읽어 5분, 시간, 일, 월, 년 단위로 가볍게 누적 기록하므로 장기 사용량 집계에 적합합니다.[^3_2]

추천 조합은 아래와 같습니다.

- 실시간 누가 쓰는지: `nethogs`.[^3_1]
- 하루/월간 얼마나 썼는지: `vnstat`, `vnstatd`.[^3_2]
- 특정 AI 서비스 목적지만 따로 수집: `tcpdump` + `tshark`.[^3_2]


## 자동화 스크립트

`vnstat`은 `--json`, `--live`, `--traffic`, `--hours`, `--days` 같은 질의 기능을 제공하고, 데이터 저장은 `vnstatd`가 담당합니다.[^3_2]
`nethogs`는 공식적으로 프로세스별 실시간 확인 도구이며, 비루트 실행 시 `setcap`으로 `cap_net_admin`, `cap_net_raw` 등이 필요할 수 있습니다.[^3_1]

아래는 Linux 데스크톱에서 바로 쓸 수 있는 예시입니다.

### 1) 설치

```bash
sudo apt update
sudo apt install -y vnstat nethogs tcpdump tshark gnuplot jq
```

`vnstat`은 기본적으로 `/var/lib/vnstat/` 데이터베이스와 `/etc/vnstat.conf` 설정을 사용합니다.[^3_2]

### 2) 인터페이스 등록 및 데몬 시작

```bash
ip -br link
sudo vnstat -i wlan0 --add
sudo systemctl enable --now vnstat
vnstat -i wlan0
```

`vnstat --add`로 인터페이스 DB 엔트리를 만들 수 있고, 이후 `vnstatd`가 주기적으로 수집합니다.[^3_2]

### 3) 실시간 + 일일 사용량 자동 수집 스크립트

```bash
#!/usr/bin/env bash
set -euo pipefail

IFACE="${1:-wlan0}"
OUTDIR="${2:-$HOME/ai-traffic-monitor}"
STAMP="$(date +%F)"
mkdir -p "$OUTDIR"/{logs,csv,json}

echo "[^3_1] vnstat 일일/시간별 JSON 저장"
vnstat -i "$IFACE" --json > "$OUTDIR/json/vnstat-${IFACE}-${STAMP}.json"

echo "[^3_2] 시간별 CSV 추출"
jq -r '
  .interfaces[^3_0].traffic.hour[] |
  [.date.year, .date.month, .date.day, .time.hour, .rx, .tx] | @csv
' "$OUTDIR/json/vnstat-${IFACE}-${STAMP}.json" \
> "$OUTDIR/csv/vnstat-hourly-${IFACE}-${STAMP}.csv"

echo "[^3_3] 일별 CSV 추출"
jq -r '
  .interfaces[^3_0].traffic.day[] |
  [.date.year, .date.month, .date.day, .rx, .tx] | @csv
' "$OUTDIR/json/vnstat-${IFACE}-${STAMP}.json" \
> "$OUTDIR/csv/vnstat-daily-${IFACE}-${STAMP}.csv"

echo "[^3_4] nethogs 60초 스냅샷"
timeout 60s sudo nethogs -t "$IFACE" > "$OUTDIR/logs/nethogs-${IFACE}-${STAMP}.log" || true

echo "완료: $OUTDIR"
```

이 스크립트는 `vnstat --json` 결과를 저장한 뒤 `jq`로 시간별/일별 CSV를 만들고, `nethogs -t` 텍스트 모드 출력을 60초간 로그로 남깁니다.[^3_1][^3_2]
`vnstat`의 JSON 출력은 공식 옵션이며, 5분/시간/일/월/년 단위 데이터를 구조화된 형태로 제공하므로 후처리에 적합합니다.[^3_2]

### 4) cron 등록 예시

매 10분마다 JSON과 실시간 스냅샷을 남기려면 다음처럼 등록할 수 있습니다.

```bash
crontab -e
```

```cron
*/10 * * * * /home/USER/bin/ai_traffic_collect.sh wlan0 /home/USER/ai-traffic-monitor
```

이렇게 하면 `vnstatd`의 장기 DB와 별개로, 사용자 정의 CSV/로그가 계속 누적됩니다.[^3_2]

## tcpdump 예시

중요한 점은 `tcpdump`는 **도메인 이름 자체**가 아니라 실제로는 IP 기반으로 필터링하는 경우가 가장 안정적이라는 점입니다. `tcpdump` 필터는 주로 host, port, net, proto 기준이며, “특정 도메인”은 먼저 DNS로 IP를 해석한 뒤 쓰는 방식이 일반적입니다.[^3_2]

### 1) 도메인 IP 확인

```bash
dig +short gemini.google.com
```

여러 IP가 나올 수 있으므로, CDN이나 Anycast 환경에서는 결과가 바뀔 수 있습니다.

### 2) 특정 목적지 IP만 캡처

```bash
sudo tcpdump -i wlan0 host 142.250.207.46 -w gemini-traffic.pcap
```

이 명령은 지정한 인터페이스에서 해당 IP와 오가는 모든 패킷을 pcap으로 저장합니다.[^3_2]

### 3) HTTPS만 제한

```bash
sudo tcpdump -i wlan0 host 142.250.207.46 and port 443 -w gemini-https.pcap
```

AI 도구 대부분은 HTTPS를 사용하므로, 보통 `port 443` 조건을 같이 거는 편이 노이즈를 줄이기 좋습니다.[^3_2]

### 4) 여러 IP를 동시에 필터링

```bash
sudo tcpdump -i wlan0 '(host 142.250.207.46 or host 142.250.207.78) and port 443' -w ai-tool.pcap
```


### 5) DNS 질의로 도메인 매핑까지 같이 보기

```bash
sudo tcpdump -i wlan0 '(port 53 or port 443)' -w dns-and-tls.pcap
```

이렇게 하면 먼저 DNS 응답에서 어떤 도메인이 어떤 IP로 풀렸는지 보고, 뒤이은 TLS 연결과 매칭하는 방식으로 분석할 수 있습니다.

### 6) tshark로 바이트 통계 추출

```bash
tshark -r gemini-https.pcap -q -z io,stat,60
```

이 명령은 60초 단위 I/O 통계를 보여주므로 세션별 트래픽량 계량에 유용합니다.[^3_2]

## 시계열 저장과 시각화

CLI 중심이라면 `vnstat` 자체가 이미 5분/시간/일 단위 시계열 저장소 역할을 하고, `--json`으로 외부 도구와 연결하기 쉽습니다.[^3_2]
시각화는 목적에 따라 `vnstati`, `gnuplot`, `termgraph`, `feedgnuplot` 계열이 실용적이고, 좀 더 현대적인 TUI를 원하면 `bandwhich` 같은 대안도 고려할 수 있습니다.[^3_1]

추천은 아래와 같습니다.

- 장기 저장: `vnstat`, `vnstatd`.[^3_2]
- PNG 그래프 빠르게 생성: `vnstati` 또는 `gnuplot`.[^3_2]
- 터미널 ASCII 차트: `termgraph`.
- 실시간 연결/호스트 관찰: `iftop`, `bandwhich`.[^3_1]
- 패킷 통계 후처리: `tshark`.[^3_2]


### gnuplot 예시

시간별 CSV를 그래프로 그리는 예시는 다음과 같습니다.

```bash
gnuplot <<'EOF'
set datafile separator ","
set terminal dumb size 120,30
set title "Hourly AI Traffic"
set xlabel "Hour Index"
set ylabel "Bytes"
plot "/home/USER/ai-traffic-monitor/csv/vnstat-hourly-wlan0-2026-07-04.csv" using 4:5 with lines title "RX", \
     "/home/USER/ai-traffic-monitor/csv/vnstat-hourly-wlan0-2026-07-04.csv" using 4:6 with lines title "TX"
EOF
```

터미널 안에서 바로 ASCII 그래프로 볼 수 있어 SSH 환경에도 잘 맞습니다.

### PNG 파일로 저장

```bash
gnuplot <<'EOF'
set datafile separator ","
set terminal pngcairo size 1400,700
set output "ai-traffic-hourly.png"
set title "Hourly AI Traffic"
set xlabel "Hour"
set ylabel "Bytes"
plot "vnstat-hourly-wlan0-2026-07-04.csv" using 4:5 with lines lw 2 title "RX", \
     "vnstat-hourly-wlan0-2026-07-04.csv" using 4:6 with lines lw 2 title "TX"
EOF
```


## 운영 팁

`nethogs`는 프로세스 기준이라 Chrome 전체를 보여주지만, 탭별 또는 AI 서비스별 완전 분리는 기본적으로 어렵고 `unknown TCP` 버킷이 일부 나타날 수 있습니다.[^3_1]
반면 `vnstat`은 인터페이스 전체 기준이어서 AI 도구만의 사용량을 정확히 분리하려면, 별도 브라우저 프로필, 프록시, VPN 인터페이스, 또는 목적지 IP 기준 `tcpdump` 후처리를 같이 써야 합니다.[^3_1][^3_2]

실무적으로는 이렇게 정리하는 것이 좋습니다.

- 1차 계량: `vnstat`으로 일/시간 사용량 추적.[^3_2]
- 2차 원인 파악: `nethogs`로 어느 프로세스가 순간적으로 많이 쓰는지 확인.[^3_1]
- 3차 AI 서비스 분리: `tcpdump`/`tshark`로 특정 목적지 IP만 집계.
- 4차 자동 리포팅: `jq + csv + gnuplot` 조합으로 일일 보고서 생성.

원하시면 다음 단계로 바로 이어서, **Linux 데스크톱용 완성형 Bash 프로젝트 구조**까지 만들어 드리겠습니다. 예를 들면 `install.sh`, `collect.sh`, `report.sh`, `systemd user timer`, `gnuplot 템플릿`까지 한 세트로 정리할 수 있습니다.[^3_1][^3_2]
<span style="display:none">[^3_10][^3_11][^3_12][^3_13][^3_14][^3_15][^3_16][^3_17][^3_5][^3_6][^3_7][^3_8][^3_9]</span>

<div align="center">⁂</div>

[^3_1]: https://developer.chrome.com/docs/devtools/network/overview

[^3_2]: https://learn.microsoft.com/ko-kr/azure/azure-web-pubsub/howto-troubleshoot-network-trace

[^3_3]: https://github.com/raboof/nethogs

[^3_4]: https://en.wikipedia.org/wiki/VnStat

[^3_5]: https://github.com/sbwml/package_new_nethogs

[^3_6]: https://github.com/raboof/nethogs/blob/main/.project

[^3_7]: https://github.com/OpenMandrivaAssociation/nethogs/blob/master/nethogs.spec

[^3_8]: https://github.com/sublimino/nethogs-docker

[^3_9]: https://github.com/raboof/nethogs/blob/main/INSTALL

[^3_10]: https://packages.gentoo.org/packages/net-analyzer/nethogs

[^3_11]: https://github.com/raboof/nethogs/blob/main/doc/nethogs.8

[^3_12]: https://github.com/topics/nethogs

[^3_13]: https://archlinux.org/packages/extra/x86_64/nethogs/

[^3_14]: https://github.com/raboof/nethogs/blob/main/DESIGN

[^3_15]: https://packages.debian.org/source/stable/nethogs

[^3_16]: https://github.com/raboof/nethogs/blob/main/setup.py

[^3_17]: https://blog.innern.net/104


---

# AI 도구별 실시간·누적 사용량 분석 CLI 자동화 스크립트 구축 및 대시보드 배포​

특정 도메인 전용 트래픽 로그 추출 자동화 및 데이터 시각화 파이프라인 설계
Linux 시스템에서 도메인 기반 트래픽 로그 분석법
Tshark를 활용한 특정 API 통신 패킷 크기 계산 스크립트
Prometheus와 Grafana를 이용한 시스템 네트워크 모니터링 구축

원하시는 범위를 한 번에 만족하려면, Linux에서 **도메인/IP 기반 패킷 수집 계층**, **TShark 집계 계층**, **시계열 저장 계층**, **Prometheus/Grafana 대시보드 계층**으로 분리해 설계하는 것이 가장 관리하기 쉽습니다.[^4_1][^4_2]
핵심은 도메인 이름 자체는 패킷 필터의 1급 식별자가 아니므로, 먼저 DNS 또는 별도 매핑으로 목적지 IP 집합을 만들고, 그 IP 집합에 대해 `tcpdump`/`tshark`로 수집한 뒤, 결과를 Prometheus 텍스트 메트릭 또는 CSV/JSON으로 내보내는 구조입니다.[^4_2]

## 아키텍처

Prometheus의 Node Exporter는 Linux 호스트의 커널 및 하드웨어 관련 메트릭을 노출하며, Prometheus는 이를 주기적으로 scrape하고 Grafana는 그 결과를 시각화합니다.[^4_1]
네트워크 전체 바이트율은 `node_network_receive_bytes_total`, `node_network_transmit_bytes_total` 같은 메트릭으로 볼 수 있지만, 특정 AI 도구나 특정 API 도메인 단위 분석은 Node Exporter만으로는 부족하므로 별도 패킷 분석 파이프라인이 필요합니다.[^4_3][^4_1]

권장 계층은 아래와 같습니다.

- 시스템 전체 네트워크 모니터링: Node Exporter + Prometheus + Grafana.[^4_3][^4_1]
- 특정 도메인/API 트래픽 계량: `tcpdump` 또는 `tshark`.[^4_2]
- 일별/시간별 장기 집계: `vnstat`.[^4_4]
- 프로세스별 순간 점검: `nethogs`.[^4_5]
- AI 서비스별 대시보드: `tshark` 집계 결과를 Prometheus textfile exporter 형식으로 노출.


## 도메인 기반 분석법

Linux에서 도메인 기반 트래픽 로그 분석은 보통 “도메인 → DNS 해석 → IP 집합 → IP 기반 캡처 → 후처리”로 진행합니다. `tshark`와 `tcpdump`의 capture filter는 pcap 문법을 사용하고, 실시간 캡처에서 display filter보다 capture filter가 더 효율적입니다.[^4_2]

실무적으로는 두 방식이 있습니다.

- DNS 선해석 방식: `dig`/`getent ahosts`로 도메인의 현재 IP들을 구한 뒤 `host A or host B ...` 형태로 캡처.[^4_2]
- DNS+TLS 상관 분석 방식: DNS(53 또는 DoH 제외 시 한계 있음)와 TLS 트래픽을 함께 저장한 뒤, 후처리 시 도메인과 세션을 매칭.

첫 번째 방식이 자동화는 가장 쉽습니다. 다만 CDN, Anycast, 짧은 TTL 때문에 IP가 바뀔 수 있으므로 주기적 재해석이 필요합니다.

### 도메인 전용 캡처 스크립트 예시

```bash
#!/usr/bin/env bash
set -euo pipefail

DOMAIN="${1:-gemini.google.com}"
IFACE="${2:-wlan0}"
OUTDIR="${3:-$HOME/domain-captures}"
STAMP="$(date +%F-%H%M%S)"
mkdir -p "$OUTDIR"

IPS=$(dig +short "$DOMAIN" A | sort -u | xargs)
if [ -z "${IPS:-}" ]; then
  echo "IP 해석 실패: $DOMAIN" >&2
  exit 1
fi

FILTER=""
for ip in $IPS; do
  if [ -n "$FILTER" ]; then
    FILTER="$FILTER or "
  fi
  FILTER="${FILTER}host $ip"
done

FILTER="(${FILTER}) and tcp port 443"

echo "DOMAIN=$DOMAIN"
echo "IPS=$IPS"
echo "FILTER=$FILTER"

sudo tcpdump -i "$IFACE" -nn -s 0 -w "$OUTDIR/${DOMAIN}-${STAMP}.pcap" "$FILTER"
```

이 스크립트는 도메인의 A 레코드를 해석하고, 해당 IP들에 대한 HTTPS 트래픽만 `pcap`으로 남깁니다. `tcpdump`는 raw packet data를 저장하는 용도이며, 저장된 파일은 후속 `tshark -r` 분석에 적합합니다.[^4_2]

### 순환 로그 자동화

장시간 운영에는 ring buffer가 유용합니다. `tshark`는 `-b` 옵션으로 다중 파일 또는 링 버퍼 캡처를 지원합니다.[^4_2]

```bash
sudo tshark -i wlan0 \
  -f "(host 142.250.0.0/15) and tcp port 443" \
  -b duration:300 -b files:24 \
  -w /var/log/ai-capture/gemini_ring.pcapng
```

이 예시는 5분마다 파일을 바꾸고 최대 24개 파일만 유지하는 구조입니다.[^4_2]

## Tshark 패킷 크기 계산

TShark는 live capture 또는 기존 pcap 파일을 읽을 수 있고, `-T fields -e ...` 형식으로 원하는 필드를 CSV처럼 출력할 수 있습니다.[^4_2]
API 통신 패킷 크기 계산에는 보통 `frame.len`, `ip.len`, `tcp.len`, `http.content_length`, `tcp.stream` 같은 필드를 조합합니다.[^4_2]

### 전체 패킷 크기 합계

```bash
tshark -r gemini.pcapng -T fields -e frame.len
```

이 결과를 합산하면 캡처된 전체 프레임 크기 합계를 구할 수 있습니다.

```bash
tshark -r gemini.pcapng -T fields -e frame.len \
| awk '{sum += $1} END {print sum}'
```

이 스크립트는 pcap 내 모든 프레임의 총 바이트를 계산합니다.[^4_2]

### 특정 API 호스트에 대한 HTTP/2 또는 TLS 세션 크기 추정

암호화된 HTTPS에서는 애플리케이션 payload를 그대로 보기 어렵기 때문에, 현실적으로는 `frame.len` 또는 TCP payload 길이 합으로 추정합니다.

```bash
tshark -r gemini.pcapng \
  -Y 'ip.addr == 142.250.207.46 && tcp.port == 443' \
  -T fields -e frame.time_epoch -e ip.src -e ip.dst -e tcp.stream -e frame.len
```

이렇게 하면 시간, 출발지/목적지, 스트림, 프레임 길이를 행 단위로 얻을 수 있습니다.[^4_2]

### 스트림별 총 바이트 계산

```bash
tshark -r gemini.pcapng \
  -Y 'ip.addr == 142.250.207.46 && tcp.port == 443' \
  -T fields -e tcp.stream -e frame.len \
| awk '
  NF==2 {sum[$1] += $2}
  END {
    for (s in sum) print s, sum[s]
  }' | sort -n
```

이 스크립트는 TCP stream별 총 프레임 바이트를 계산합니다.[^4_2]

### 시계열 1분 집계

```bash
tshark -r gemini.pcapng \
  -q -z io,stat,60,"SUM(frame.len)frame.len and ip.addr==142.250.207.46"
```

TShark의 `-z io,stat,<interval>` 통계는 시간 구간별 합계와 빈도를 내는 데 유용합니다.[^4_2]

## Prometheus 연계

Node Exporter는 `/metrics` 엔드포인트에서 `node_` 접두사의 다양한 시스템 메트릭을 노출하며, Prometheus는 `prometheus.yml`의 `scrape_configs`에 따라 이를 15초 간격 등으로 수집할 수 있습니다.[^4_1]
예시로 Prometheus 공식 가이드는 `localhost:9100`의 Node Exporter를 scrape하도록 설정하고, Prometheus UI에서 `rate(node_network_receive_bytes_total[1m])` 같은 식을 바로 조회하는 방식을 보여줍니다.[^4_1]

### 최소 구성

`prometheus.yml` 예시는 다음과 같습니다.

```yaml
global:
  scrape_interval: 15s

scrape_configs:
- job_name: node
  static_configs:
  - targets: ['localhost:9100']
```

이 구성은 Prometheus 공식 가이드에 제시된 기본 예시와 동일한 패턴입니다.[^4_1]

### 네트워크 관련 PromQL

- 수신 바이트율: `rate(node_network_receive_bytes_total[5m])`.[^4_3][^4_1]
- 송신 바이트율: `rate(node_network_transmit_bytes_total[5m])`.[^4_3][^4_1]
- 인터페이스별 수신: `rate(node_network_receive_bytes_total{device="wlan0"}[5m])`.[^4_3]
- 인터페이스별 송신: `rate(node_network_transmit_bytes_total{device="wlan0"}[5m])`.[^4_3]

이는 시스템 전체 네트워크 대역폭 추이를 보는 데 적합하지만, 특정 AI API만 분리하지는 못합니다.[^4_1][^4_3]

## 사용자 정의 메트릭

특정 도메인/API 통신량을 Grafana에서 보고 싶다면, `tshark` 결과를 주기적으로 계산해서 Prometheus가 읽을 수 있는 텍스트 형식으로 내보내는 방식이 가장 단순합니다. 이 패턴은 Node Exporter의 textfile collector 또는 별도 exporter로 구현할 수 있습니다.[^4_1]

예를 들어 1분마다 최근 pcap 파일을 읽어서 아래 형식의 파일을 생성합니다.

```text
ai_domain_rx_bytes_total{domain="gemini.google.com"} 12345678
ai_domain_packets_total{domain="gemini.google.com"} 9123
ai_domain_last_interval_bytes{domain="gemini.google.com"} 543210
```


### 생성 스크립트 예시

```bash
#!/usr/bin/env bash
set -euo pipefail

PCAP="${1:-/var/log/ai-capture/gemini_last.pcapng}"
DOMAIN="${2:-gemini.google.com}"
OUT="${3:-/var/lib/node_exporter/textfile_collector/ai_domain.prom}"

BYTES=$(tshark -r "$PCAP" -T fields -e frame.len | awk '{s+=$1} END{print s+0}')
PKTS=$(tshark -r "$PCAP" -q | tail -n 1 | awk '{print $1}')
NOW=$(date +%s)

cat > "$OUT" <<EOF
ai_domain_capture_timestamp_seconds{domain="$DOMAIN"} $NOW
ai_domain_bytes_total{domain="$DOMAIN"} $BYTES
ai_domain_packets_total{domain="$DOMAIN"} $PKTS
EOF
```

이렇게 하면 Prometheus가 해당 파일을 scrape하여 Grafana에서 도메인별 패널을 만들 수 있습니다.[^4_1][^4_2]

## Grafana 대시보드

Grafana Labs와 여러 가이드는 Node Exporter용 사전 구성 대시보드를 제공하며, 일반적으로 Prometheus를 데이터 소스로 연결한 후 Node Exporter 대시보드를 import해서 사용합니다.[^4_6][^4_7][^4_8]
기본 인프라 대시보드 위에 사용자 정의 패널을 추가해 `ai_domain_bytes_total`, `rate(ai_domain_bytes_total[5m])` 같은 메트릭을 함께 그리면 시스템 전체 트래픽과 AI API 전용 트래픽을 한 화면에서 볼 수 있습니다.[^4_6][^4_1]

추천 패널 구성은 아래와 같습니다.

- 시스템 수신/송신 바이트율, 인터페이스별 패널.[^4_3][^4_1]
- CPU, 메모리, 디스크, 네트워크 기본 패널.[^4_6][^4_1]
- AI 도메인별 최근 5분 바이트율.
- AI 도메인별 일일 총 바이트.
- 패킷 수, 평균 패킷 크기, 세션 수.
- 캡처 오류, DNS 해석 실패, pcap rotation 상태.


## 파이프라인 설계

운영 가능한 파이프라인은 다음 순서가 좋습니다.

1. `systemd` 서비스로 `tshark` 또는 `tcpdump` ring buffer 캡처 실행.[^4_2]
2. 주기적 배치 스크립트로 최신 pcap 파일 분석, `frame.len`·`tcp.stream` 집계.[^4_2]
3. 결과를 CSV/JSON과 Prometheus text metric 둘 다 저장.
4. Prometheus가 Node Exporter와 사용자 정의 메트릭을 scrape.[^4_1]
5. Grafana에서 시스템 메트릭 + AI 도메인 메트릭 통합 대시보드 구성.[^4_6][^4_1]

이 구조의 장점은 수집과 분석과 시각화를 분리할 수 있다는 점입니다. 수집기는 `pcapng`만 남기고, 분석기는 언제든 다시 돌릴 수 있으며, 대시보드는 Prometheus 메트릭만 보면 됩니다.[^4_1][^4_2]

## 운영 주의점

도메인 기반 분석은 CDN, Anycast, 다중 A 레코드, TLS 암호화 때문에 “도메인 = 단일 IP = 단일 서비스”로 단순화되지 않는 경우가 많습니다. 따라서 중요한 서비스는 DNS 해석 결과를 주기적으로 갱신하고, 필요한 경우 `tshark`의 필드 추출과 DNS 로그를 함께 저장해 상관 분석하는 편이 더 정확합니다.[^4_2]

또한 live capture에서는 display filter보다 capture filter가 성능상 유리하며, 고속 구간에서는 ring buffer와 충분한 capture buffer 설정이 필요합니다.[^4_2]
TShark 매뉴얼은 `-f`가 capture filter, `-Y`가 display filter이며, busy network에서는 display filter 사용 시 패킷 손실 가능성이 더 높다고 설명합니다.[^4_2]

원하시면 다음 단계로 **Docker Compose 기반 Prometheus + Grafana + Node Exporter + AI 도메인 커스텀 exporter 전체 프로젝트 파일**까지 만들어 드릴 수 있습니다.[^4_7][^4_1]
<span style="display:none">[^4_10][^4_11][^4_12][^4_13][^4_14][^4_15][^4_16][^4_17][^4_18][^4_19][^4_9]</span>

<div align="center">⁂</div>

[^4_1]: https://developer.chrome.com/docs/devtools/network

[^4_2]: https://developer.chrome.com/blog/new-in-devtools-131?hl=ko

[^4_3]: https://grafana.com/docs/grafana-cloud/knowledge-graph/advanced-configuration/enable-prom-metrics-collection/infrastructure/node/

[^4_4]: https://learn.microsoft.com/ko-kr/azure/azure-web-pubsub/howto-troubleshoot-network-trace

[^4_5]: https://developer.chrome.com/docs/devtools/network/overview

[^4_6]: https://grafana.com/oss/prometheus/exporters/node-exporter/

[^4_7]: https://medium.com/@os.sybil/part-iii-prometheus-and-grafana-for-infrastructure-and-application-monitoring-with-docker-1b66f2b00f55

[^4_8]: https://grafana.com/grafana/dashboards/11074-node-exporter-for-prometheus-dashboard-en-v20201010/

[^4_9]: https://medium.com/@singhprashant2599/monitoring-with-grafana-and-prometheus-using-node-exporter-912abc408232

[^4_10]: https://grafana.com/docs/grafana-cloud/send-data/metrics/metrics-prometheus/prometheus-config-examples/noagent_linuxnode/

[^4_11]: https://prometheus.io/docs/guides/node-exporter/

[^4_12]: https://grafana.com/grafana/dashboards/15297-prometheus-network-exporter/

[^4_13]: https://www.youtube.com/watch?v=YUabB_7H710

[^4_14]: https://github.com/grafana/alloy/issues/1224

[^4_15]: https://mycup.tistory.com/320

[^4_16]: https://github.com/arihantdalai/Network-Monitoring-Dashboard-Using-Prometheus-Node-Exporter-Grafana

[^4_17]: https://www.wireshark.org/docs/man-pages/tshark.html

[^4_18]: https://platformengineer.hashnode.dev/integrating-node-exporter-with-prometheus-and-grafana-for-comprehensive-system-monitoring

[^4_19]: https://with-cloud.tistory.com/22

