#!/usr/bin/env bash
set -euo pipefail

# Simple smoke test against Google Trends explore API to detect 429/SSL bans.
# Mimics a desktop browser by default; accepts env overrides for headers/cookies.

readonly KEYWORD="${1:-automation}"
readonly URL_ENCODED_REQ="%7B%22comparisonItem%22%3A%5B%7B%22keyword%22%3A%22${KEYWORD// /%20}%22%2C%22geo%22%3A%22%22%2C%22time%22%3A%22now%207-d%22%7D%5D%2C%22category%22%3A0%7D"
readonly URL="https://trends.google.com/trends/api/explore?hl=en-US&tz=0&req=${URL_ENCODED_REQ}"

readonly USER_AGENT="${BROWSER_USER_AGENT:-Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36}"
readonly ACCEPT_HEADER="${BROWSER_ACCEPT:-text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7}"
readonly ACCEPT_LANGUAGE="${BROWSER_ACCEPT_LANGUAGE:-en-US,en;q=0.9}"
readonly INLINE_COOKIE="${BROWSER_COOKIE:-}"
readonly COOKIE_JAR="${GOOGLE_COOKIE_JAR:-output/tmp/google_trends_cookie.txt}"

printf 'Testing Google Trends explore endpoint...\n'
printf 'Keyword: %s\n' "$KEYWORD"
printf 'URL: %s\n' "$URL"
printf 'User-Agent: %s\n' "$USER_AGENT"
mkdir -p "$(dirname "$COOKIE_JAR")"

tmp_file="$(mktemp)"
trap 'rm -f "$tmp_file"' EXIT

run_request() {
  local use_cookie="$1"
  : > "$tmp_file"

  local args=(
    curl
    --silent
    --show-error
    --compressed
    --max-time 20
    --output "$tmp_file"
    --write-out '%{http_code}'
    --header "accept: ${ACCEPT_HEADER}"
    --header "accept-language: ${ACCEPT_LANGUAGE}"
    --header 'cache-control: no-cache'
    --header 'pragma: no-cache'
    --header 'sec-ch-ua: "Not?A_Brand";v="8", "Chromium";v="141", "Google Chrome";v="141"'
    --header 'sec-ch-ua-mobile: ?0'
    --header 'sec-ch-ua-platform: "Windows"'
    --header 'sec-fetch-dest: document'
    --header 'sec-fetch-mode: navigate'
    --header 'sec-fetch-site: none'
    --header 'sec-fetch-user: ?1'
    --header 'upgrade-insecure-requests: 1'
    --header "user-agent: ${USER_AGENT}"
    --cookie-jar "$COOKIE_JAR"
    "$URL"
  )

  if [[ -n "$INLINE_COOKIE" ]]; then
    printf 'Using inline cookie from env.\n' >&2
    args+=(--cookie "${INLINE_COOKIE}")
  elif [[ "$use_cookie" == "1" ]]; then
    printf 'Using persisted cookie jar: %s\n' "$COOKIE_JAR" >&2
    args+=(--cookie "$COOKIE_JAR")
  else
    printf 'No cookie supplied; treated as anonymous client.\n' >&2
  fi

  "${args[@]}" || printf 'curl_error'
}

has_cookie=0
if [[ -s "$COOKIE_JAR" ]]; then
  has_cookie=1
fi

printf 'Cookie jar path: %s%s\n' "$COOKIE_JAR" "$( [[ -s "$COOKIE_JAR" ]] && printf ' (reusing existing cookies)' )"

http_status="$(run_request "$has_cookie")"

if [[ "$http_status" == "curl_error" ]]; then
  printf 'curl failed—network or TLS error encountered.\n' >&2
  exit 1
fi

printf 'HTTP status: %s\n' "$http_status"

case "$http_status" in
  200)
    printf 'Sample response (first 3 lines):\n'
    head -n 3 "$tmp_file"
    ;;
  429)
    if [[ -n "$INLINE_COOKIE" ]]; then
      printf 'Received 429 Too Many Requests even with inline cookie.\n'
    elif [[ "$has_cookie" -eq 0 && -s "$COOKIE_JAR" ]]; then
      printf 'Initial 429; retrying with freshly issued cookie...\n'
      sleep 2
      http_status="$(run_request 1)"
      printf 'Retry HTTP status: %s\n' "$http_status"
      if [[ "$http_status" == "200" ]]; then
        printf 'Sample response (first 3 lines):\n'
        head -n 3 "$tmp_file"
      else
        printf 'Still not successful after retry.\n'
      fi
    else
      printf 'Received 429 Too Many Requests—current IP is likely rate limited.\n'
    fi
    ;;
  *)
    printf 'Unexpected status from Google Trends. Full response preview:\n'
    head -n 10 "$tmp_file"
    ;;
esac
