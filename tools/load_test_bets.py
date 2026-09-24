#!/usr/bin/env python3
"""Gera massa de dados em escala (teste de carga/escalabilidade) chamando as APIs
reais de auth-service/bets-service (via api-gateway) - cria um tenant novo e limpo
a cada execucao, cadastra os catalogos (casas de apostas/esportes/ligas/mercados/
tipsters/times) e depois cria + liquida um numero grande de apostas em paralelo
(thread pool), espalhadas ao longo de N dias, gerando os eventos BetCreated/
BetSettled que o stats-service consome de forma assincrona.

Pensado pra rodar tanto contra um ambiente local (default) quanto contra um
servidor de verdade (sobrescrevendo AUTH_BASE_URL/GATEWAY_BASE_URL) - mesmo
algoritmo, so o alvo muda. Cada execucao cria um tenant com slug aleatorio, entao
e seguro rodar varias vezes seguidas (nunca mistura com dados de uma execucao
anterior) - se quiser reaproveitar catalogos de um tenant ja existente, isso nao
e suportado por este script (decisao: "ambiente limpo para cada teste").

Uso:
    # local, 200 mil apostas, 32 threads (defaults)
    set -a && source services/auth-service/.env && set +a
    python tools/load_test_bets.py --n-bets 200000

    # 1 milhao, mais paralelismo
    python tools/load_test_bets.py --n-bets 1000000 --workers 64

    # contra um servidor remoto
    python tools/load_test_bets.py --n-bets 200000 \\
        --auth-base-url https://auth.exemplo.com \\
        --gateway-base-url https://api.exemplo.com \\
        --admin-api-key "$ADMIN_API_KEY"

Variaveis de ambiente equivalentes a cada flag (env vale como default, flag CLI
sempre tem prioridade): AUTH_BASE_URL, GATEWAY_BASE_URL, ADMIN_API_KEY, N_BETS,
DAYS_BACK, WORKERS, SETTLE_RATIO, PENDING_RECENT_DAYS.

ADMIN_API_KEY nunca e impresso por este script - vem do ambiente/flag e so
trafega no header X-Admin-Api-Key.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import random
import string
import sys
import threading
import time
import uuid
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from datetime import datetime, timedelta, timezone

import requests
from requests.adapters import HTTPAdapter

SPORTS = ["Futebol", "Basquete", "Tenis", "Volei", "MMA", "E-sports (CS2)", "Tenis de Mesa", "Futsal"]

LEAGUES = [
    "Brasileirao Serie A", "Copa do Brasil", "Libertadores", "Champions League",
    "Premier League", "La Liga", "NBA", "NBB", "ATP Tour", "WTA Tour",
]

MARKETS = [
    "Resultado Final", "Over/Under 2.5", "Ambas Marcam", "Handicap Asiatico",
    "Dupla Chance", "Total de Pontos", "Vencedor do Set", "Escanteios",
]

TIPSTERS = [
    "Tips do Fabio", "Green Certo", "Palpites VIP", "Trader de Odds",
    "Banca Solida", "Apostador Pro",
]

TEAMS_BY_SPORT = {
    "Futebol": ["Flamengo", "Palmeiras", "Corinthians", "Sao Paulo", "Gremio",
                "Internacional", "Real Madrid", "Barcelona", "Manchester City", "Liverpool"],
    "Basquete": ["Lakers", "Celtics", "Warriors", "Bulls", "Nets", "Heat", "Suns", "Bucks"],
    "Tenis": ["Djokovic", "Alcaraz", "Sinner", "Medvedev", "Zverev", "Nadal"],
    "Volei": ["Sesi Bauru", "Sada Cruzeiro", "Minas", "Renata"],
    "MMA": ["Charles Oliveira", "Islam Makhachev", "Alex Poatan", "Israel Adesanya"],
    "E-sports (CS2)": ["FURIA", "Imperial", "MIBR", "Natus Vincere", "G2", "Vitality"],
    "Tenis de Mesa": ["Hugo Calderano", "Ma Long", "Fan Zhendong"],
    "Futsal": ["Magnus Futsal", "Corinthians Futsal", "Jaragua"],
}

BETTING_HOUSES = [
    "Bet365", "Betano", "KTO", "Sportingbet", "Betfair", "1xBet", "Betway",
    "Betnacional", "Novibet", "EstrelaBet", "Betsson", "Stake", "Parimatch",
    "Betsul", "Rivalo", "F12.bet", "Vaidebet", "LeoVegas", "Bwin", "Betmotion",
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--auth-base-url", default=os.environ.get("AUTH_BASE_URL", "http://localhost:8081"))
    p.add_argument("--gateway-base-url", default=os.environ.get("GATEWAY_BASE_URL", "http://localhost:8080"))
    p.add_argument("--admin-api-key", default=os.environ.get("ADMIN_API_KEY"))
    p.add_argument("--n-bets", type=int, default=int(os.environ.get("N_BETS", "200000")))
    p.add_argument("--days-back", type=int, default=int(os.environ.get("DAYS_BACK", "365")))
    p.add_argument("--workers", type=int, default=int(os.environ.get("WORKERS", "32")))
    p.add_argument("--settle-ratio", type=float, default=float(os.environ.get("SETTLE_RATIO", "0.95")))
    p.add_argument("--pending-recent-days", type=int, default=int(os.environ.get("PENDING_RECENT_DAYS", "3")))
    p.add_argument("--progress-every", type=int, default=int(os.environ.get("PROGRESS_EVERY", "1000")))
    p.add_argument("--max-retries", type=int, default=int(os.environ.get("MAX_RETRIES", "3")))
    args = p.parse_args()
    if not args.admin_api_key:
        sys.exit("ADMIN_API_KEY ausente - passe --admin-api-key ou exporte a variavel de ambiente "
                  "(source o .env do auth-service do alvo antes de rodar)")
    return args


_thread_local = threading.local()


def make_session() -> requests.Session:
    if not hasattr(_thread_local, "session"):
        s = requests.Session()
        adapter = HTTPAdapter(pool_connections=200, pool_maxsize=200, max_retries=0)
        s.mount("http://", adapter)
        s.mount("https://", adapter)
        _thread_local.session = s
    return _thread_local.session


def request_with_retry(method: str, url: str, max_retries: int, **kwargs) -> requests.Response:
    last_exc: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            r = make_session().request(method, url, timeout=30, **kwargs)
            if r.status_code >= 500 and attempt < max_retries:
                time.sleep(0.5 * (attempt + 1))
                continue
            return r
        except requests.exceptions.RequestException as e:
            last_exc = e
            time.sleep(0.5 * (attempt + 1))
    raise last_exc  # type: ignore[misc]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def create_tenant(auth_base: str, admin_api_key: str, slug: str, tenant_name: str, max_retries: int) -> dict:
    r = request_with_retry(
        "POST", f"{auth_base}/api/v1/admin/tenants", max_retries,
        headers={"X-Admin-Api-Key": admin_api_key}, json={"slug": slug, "tenantName": tenant_name},
    )
    r.raise_for_status()
    return r.json()


def login(gateway_base: str, slug: str, email: str, password: str, max_retries: int) -> dict:
    r = request_with_retry(
        "POST", f"{gateway_base}/api/v1/auth/login", max_retries,
        json={"slug": slug, "email": email, "password": password},
    )
    r.raise_for_status()
    return r.json()


def change_password(gateway_base: str, token: str, current: str, new: str, max_retries: int) -> None:
    r = request_with_retry(
        "POST", f"{gateway_base}/api/v1/auth/change-password", max_retries,
        headers=auth_headers(token), json={"currentPassword": current, "newPassword": new},
    )
    r.raise_for_status()


def create_catalog(gateway_base: str, path: str, name: str, token: str, max_retries: int) -> str:
    r = request_with_retry(
        "POST", f"{gateway_base}/api/v1/{path}", max_retries,
        headers=auth_headers(token), json={"name": name},
    )
    r.raise_for_status()
    return r.json()["id"]


def create_team(gateway_base: str, name: str, sport_id: str, token: str, max_retries: int) -> str:
    r = request_with_retry(
        "POST", f"{gateway_base}/api/v1/teams", max_retries,
        headers=auth_headers(token), json={"name": name, "sportId": sport_id},
    )
    r.raise_for_status()
    return r.json()["id"]


def create_betting_house(gateway_base: str, name: str, initial_balance: float, token: str, max_retries: int) -> str:
    r = request_with_retry(
        "POST", f"{gateway_base}/api/v1/betting-houses", max_retries,
        headers=auth_headers(token), json={"name": name, "initialBalance": initial_balance},
    )
    r.raise_for_status()
    return r.json()["id"]


def rand_ticket() -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=10))


class Counters:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.created = 0
        self.won = 0
        self.lost = 0
        self.void = 0
        self.pending = 0
        self.errors = 0

    def bump(self, field: str) -> None:
        with self.lock:
            setattr(self, field, getattr(self, field) + 1)


def bet_worker(i: int, ctx: dict, counters: Counters, args: argparse.Namespace) -> None:
    gateway_base = ctx["gateway_base"]
    token = ctx["token"]
    slug = ctx["slug"]
    now = ctx["now"]
    sport_names = ctx["sport_names"]
    sport_ids = ctx["sport_ids"]
    team_ids_by_sport = ctx["team_ids_by_sport"]
    league_ids = ctx["league_ids"]
    market_ids = ctx["market_ids"]
    tipster_ids = ctx["tipster_ids"]
    house_ids = ctx["house_ids"]

    days_ago = random.randint(0, args.days_back)
    bet_dt = (now - timedelta(days=days_ago)).replace(
        hour=random.randint(10, 23), minute=random.randint(0, 59), second=random.randint(0, 59), microsecond=0
    )
    bet_date_iso = bet_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    sport_name = random.choice(sport_names)
    sport_id = sport_ids[sport_name]
    teams = team_ids_by_sport[sport_name]
    team1_name, team1_id = random.choice(teams)
    team2_name, team2_id = random.choice([t for t in teams if t[0] != team1_name])
    league_id = random.choice(league_ids)
    market_id = random.choice(market_ids)
    house_id = random.choice(house_ids)
    tipster_id = random.choice(tipster_ids) if random.random() < 0.7 else None

    stake = round(random.uniform(10, 500), 2)
    odd = round(random.uniform(1.10, 6.00), 2)
    bet_type = "live" if random.random() < 0.2 else "pre"

    payload = {
        "bettingHouseId": house_id,
        "sportId": sport_id,
        "leagueId": league_id,
        "marketId": market_id,
        "tipsterId": tipster_id,
        "ticketNumber": rand_ticket(),
        "team1Id": team1_id,
        "team2Id": team2_id,
        "description": f"{team1_name} x {team2_name}",
        "betType": bet_type,
        "playType": "Simples" if random.random() < 0.8 else "Multipla",
        "stake": stake,
        "odd": odd,
        "betDate": bet_date_iso,
    }
    idem_key = hashlib.sha256(f"{slug}-{i}".encode()).hexdigest()[:32]

    try:
        r = request_with_retry(
            "POST", f"{gateway_base}/api/v1/bets", args.max_retries,
            headers={**auth_headers(token), "Idempotency-Key": idem_key}, json=payload,
        )
        r.raise_for_status()
        bet = r.json()
        counters.bump("created")
    except requests.exceptions.RequestException:
        counters.bump("errors")
        return

    if days_ago <= args.pending_recent_days or random.random() > args.settle_ratio:
        counters.bump("pending")
        return

    roll = random.random()
    if roll < 0.03:
        status = "void"
    elif roll < 0.03 + 0.47:
        status = "won"
    else:
        status = "lost"

    try:
        r = request_with_retry(
            "PATCH", f"{gateway_base}/api/v1/bets/{bet['id']}/status", args.max_retries,
            headers=auth_headers(token), json={"status": status},
        )
        r.raise_for_status()
        counters.bump(status)
    except requests.exceptions.RequestException:
        counters.bump("errors")


def run_bounded(n: int, max_workers: int, submit_fn) -> None:
    """Roda submit_fn(i) para i em range(n), com no maximo ~2*max_workers tarefas
    em voo por vez - evita acumular 1 milhao de Future em memoria de uma vez."""
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        it = iter(range(n))
        in_flight = set()
        for _ in range(max_workers * 2):
            try:
                i = next(it)
            except StopIteration:
                break
            in_flight.add(ex.submit(submit_fn, i))
        while in_flight:
            done, in_flight = wait(in_flight, return_when=FIRST_COMPLETED)
            for f in done:
                f.result()  # re-levanta excecao nao tratada dentro do worker, se houver
            for _ in range(len(done)):
                try:
                    i = next(it)
                except StopIteration:
                    break
                in_flight.add(ex.submit(submit_fn, i))


def main() -> None:
    args = parse_args()
    slug = "loadtest-" + uuid.uuid4().hex[:8]
    tenant_name = f"Teste de Carga {slug}"

    print(f"[1/5] Criando tenant '{slug}' em {args.auth_base_url} ...", flush=True)
    tenant = create_tenant(args.auth_base_url, args.admin_api_key, slug, tenant_name, args.max_retries)
    if tenant.get("downstreamProvisioningFailures"):
        print("AVISO: provisionamento downstream falhou para:", tenant["downstreamProvisioningFailures"], flush=True)
    email = tenant["email"]
    temp_password = tenant["temporaryPassword"]
    print(f"  admin email={email}", flush=True)

    print("[2/5] Login e troca de senha temporaria...", flush=True)
    login_resp = login(args.gateway_base_url, slug, email, temp_password, args.max_retries)
    token = login_resp["token"]
    final_password = temp_password
    if login_resp.get("mustChangePassword"):
        final_password = "LoadTest@" + uuid.uuid4().hex[:10]
        change_password(args.gateway_base_url, token, temp_password, final_password, args.max_retries)
        login_resp = login(args.gateway_base_url, slug, email, final_password, args.max_retries)
        token = login_resp["token"]
    print("  login OK", flush=True)

    print("[3/5] Criando catalogos...", flush=True)
    sport_ids = {name: create_catalog(args.gateway_base_url, "sports", name, token, args.max_retries) for name in SPORTS}
    league_ids = [create_catalog(args.gateway_base_url, "leagues", name, token, args.max_retries) for name in LEAGUES]
    market_ids = [create_catalog(args.gateway_base_url, "markets", name, token, args.max_retries) for name in MARKETS]
    tipster_ids = [create_catalog(args.gateway_base_url, "tipsters", name, token, args.max_retries) for name in TIPSTERS]
    team_ids_by_sport = {}
    for sport_name, sport_id in sport_ids.items():
        team_ids_by_sport[sport_name] = [
            (name, create_team(args.gateway_base_url, name, sport_id, token, args.max_retries))
            for name in TEAMS_BY_SPORT[sport_name]
        ]
    house_ids = [
        create_betting_house(args.gateway_base_url, name, round(random.uniform(500, 5000), 2), token, args.max_retries)
        for name in BETTING_HOUSES
    ]
    print(f"  {len(sport_ids)} esportes, {len(league_ids)} ligas, {len(market_ids)} mercados, "
          f"{len(tipster_ids)} tipsters, {len(house_ids)} casas, "
          f"{sum(len(v) for v in team_ids_by_sport.values())} times/jogadores", flush=True)

    ctx = {
        "gateway_base": args.gateway_base_url,
        "token": token,
        "slug": slug,
        "now": datetime.now(timezone.utc),
        "sport_names": list(sport_ids.keys()),
        "sport_ids": sport_ids,
        "team_ids_by_sport": team_ids_by_sport,
        "league_ids": league_ids,
        "market_ids": market_ids,
        "tipster_ids": tipster_ids,
        "house_ids": house_ids,
    }
    counters = Counters()

    print(f"[4/5] Gerando {args.n_bets} apostas ({args.workers} threads em paralelo)...", flush=True)
    start = time.monotonic()
    last_report = [0]

    def submit_fn(i: int) -> None:
        bet_worker(i, ctx, counters, args)
        total_done = counters.created + counters.errors
        if total_done - last_report[0] >= args.progress_every:
            last_report[0] = total_done
            elapsed = time.monotonic() - start
            rate = total_done / elapsed if elapsed > 0 else 0
            remaining = args.n_bets - total_done
            eta_s = remaining / rate if rate > 0 else float("inf")
            print(
                f"  {total_done}/{args.n_bets} ({rate:.1f} apostas/s, "
                f"ETA {eta_s / 60:.1f} min, erros={counters.errors})",
                flush=True,
            )

    run_bounded(args.n_bets, args.workers, submit_fn)

    elapsed = time.monotonic() - start
    print("[5/5] Concluido.", flush=True)
    print("=" * 60, flush=True)
    print(f"tenant slug     : {slug}", flush=True)
    print(f"admin email     : {email}", flush=True)
    print(f"admin password  : {final_password}", flush=True)
    print(f"apostas criadas : {counters.created} / {args.n_bets} (erros={counters.errors})", flush=True)
    print(f"  won={counters.won} lost={counters.lost} void={counters.void} pending={counters.pending}", flush=True)
    print(f"tempo total     : {elapsed:.1f}s ({counters.created / elapsed:.1f} apostas/s)", flush=True)
    print("=" * 60, flush=True)


if __name__ == "__main__":
    main()
