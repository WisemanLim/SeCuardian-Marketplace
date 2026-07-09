export type Locale = "ko" | "en";

export function getLocale(): Locale {
  return (localStorage.getItem("locale") as Locale) ?? "ko";
}

export function setLocale(locale: Locale): void {
  localStorage.setItem("locale", locale);
  window.dispatchEvent(new Event("localeChanged"));
}

// R18-7: 선호언어 (마이페이지 설정, 서버 tbl_users.preferred_lang 동기) — 타 언어 확장 대비 string
export function getPreferredLang(): string {
  return localStorage.getItem("preferred_lang") ?? "ko";
}

export function setPreferredLang(lang: string): void {
  localStorage.setItem("preferred_lang", lang);
  window.dispatchEvent(new Event("localeChanged"));
}

/**
 * R18-7 다국어 설명 선택 fallback 체인:
 * descriptions[UI언어] → descriptions[선호언어] → descriptions.ko → 존재하는 첫 언어 → 레거시 컬럼
 */
export function pickDescription(
  descriptions?: Record<string, string> | null,
  legacyKo?: string | null,
  legacyEn?: string | null,
): string {
  const d = descriptions ?? {};
  const ui = getLocale();
  const pref = getPreferredLang();
  return (
    d[ui] ||
    d[pref] ||
    d["ko"] ||
    Object.values(d).find((v) => !!v) ||
    (ui === "en" ? legacyEn || legacyKo : legacyKo) ||
    ""
  );
}
