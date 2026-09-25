"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { getToken, clearToken } from "@/lib/auth";
import styles from "./Header.module.css";

const NAV_LINKS = [
  { href: "/training", label: "Training", num: "01" },
  { href: "/account/progress", label: "Progress", num: "02" },
  { href: "/account", label: "Account", num: "03" },
];

export function Header() {
  const [scrolled, setScrolled] = useState(false);
  const [authed, setAuthed] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const pathname = usePathname();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 32);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    setAuthed(Boolean(getToken()));
  }, [pathname]);

  return (
    <header className={`${styles.header} ${scrolled ? styles.scrolled : ""}`}>
      <div className={styles.inner}>
        <Link href="/" className={styles.brand} aria-label="Drone Training Platform — home">
          <span className={styles.brandMark}>◼</span>
          <span className={styles.brandWord}>DRONE/TRAINING</span>
          <span className={styles.brandYear}>EST · 2026</span>
        </Link>

        <nav className={styles.nav} aria-label="Primary">
          {NAV_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={`${styles.navLink} ${
                pathname?.startsWith(link.href) ? styles.active : ""
              }`}
            >
              <span className={styles.navNum}>{link.num}</span>
              <span>{link.label}</span>
            </Link>
          ))}
        </nav>

        <div className={styles.actions}>
          {authed ? (
            <>
              <Link href="/account" className={styles.signIn}>
                Profile
              </Link>
              <button
                className={styles.signUp}
                onClick={() => {
                  clearToken();
                  setAuthed(false);
                  window.location.href = "/";
                }}
              >
                Sign out
              </button>
            </>
          ) : (
            <>
              <Link href="/login" className={styles.signIn}>
                Sign in
              </Link>
              <Link href="/register" className={styles.signUp}>
                Apply
              </Link>
            </>
          )}
          <button
            className={styles.menu}
            aria-label="Toggle menu"
            onClick={() => setMenuOpen((v) => !v)}
          >
            <span />
            <span />
          </button>
        </div>
      </div>

      {menuOpen && (
        <div className={styles.mobile}>
          {NAV_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              onClick={() => setMenuOpen(false)}
              className={styles.mobileLink}
            >
              <span className={styles.navNum}>{link.num}</span>
              <span>{link.label}</span>
            </Link>
          ))}
        </div>
      )}
    </header>
  );
}