export type Locale = "ko" | "en";

export function getLocale(): Locale {
  return (localStorage.getItem("locale") as Locale) ?? "ko";
}

export function setLocale(locale: Locale): void {
  localStorage.setItem("locale", locale);
  window.dispatchEvent(new Event("localeChanged"));
}
