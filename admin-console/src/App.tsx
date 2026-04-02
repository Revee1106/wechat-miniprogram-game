import { useEffect, useState } from "react";

import {
  fetchAdminSession,
  loginAdmin,
  logoutAdmin,
  type AdminSession,
} from "./api/client";
import { DwellingListPage } from "./pages/DwellingListPage";
import { EventListPage } from "./pages/EventListPage";
import { LoginPage } from "./pages/LoginPage";
import { RealmListPage } from "./pages/RealmListPage";

type ViewMode = "events" | "realms" | "dwelling";

export default function App() {
  const [authState, setAuthState] = useState<
    | { status: "loading" }
    | { status: "unauthenticated" }
    | { status: "authenticated"; session: AdminSession }
    | { status: "error"; message: string }
  >({ status: "loading" });
  const [isSigningIn, setIsSigningIn] = useState(false);
  const [view, setView] = useState<ViewMode>("events");

  useEffect(() => {
    let isMounted = true;

    async function loadSession() {
      try {
        const session = await fetchAdminSession();
        if (!isMounted) {
          return;
        }
        if (!session) {
          setAuthState({ status: "unauthenticated" });
          return;
        }
        setAuthState({ status: "authenticated", session });
      } catch (error) {
        if (isMounted) {
          setAuthState({
            status: "error",
            message: (error as Error).message,
          });
        }
      }
    }

    void loadSession();

    return () => {
      isMounted = false;
    };
  }, []);

  async function handleLogin(username: string, password: string) {
    setIsSigningIn(true);
    try {
      const session = await loginAdmin(username, password);
      setAuthState({ status: "authenticated", session });
      setView("events");
    } catch (error) {
      setAuthState({
        status: "error",
        message: (error as Error).message,
      });
    } finally {
      setIsSigningIn(false);
    }
  }

  async function handleLogout() {
    await logoutAdmin();
    setView("events");
    setAuthState({ status: "unauthenticated" });
  }

  if (authState.status === "loading") {
    return (
      <div className="console-shell">
        <div className="page-loading">正在确认控制台会话...</div>
      </div>
    );
  }

  if (authState.status === "unauthenticated" || authState.status === "error") {
    return (
      <div className="console-shell">
        <LoginPage
          errorMessage={authState.status === "error" ? authState.message : null}
          isSubmitting={isSigningIn}
          onLogin={handleLogin}
        />
      </div>
    );
  }

  const pageTitle =
    view === "dwelling" ? "洞府工坊" : view === "realms" ? "境界谱录" : "事件工坊";
  const pageSubtitle =
    view === "dwelling"
      ? "紧凑式设施清单与等级配置工作台"
      : view === "realms"
        ? "紧凑式境界清单与突破配置工作台"
        : "紧凑式事件清单与结果编排工作台";

  return (
    <div className="console-shell">
      <header className="console-topbar">
        <div className="console-brand">
          <span className="console-brand__eyebrow">WENDAO CONTROL</span>
          <h1 className="console-brand__title">问道控制台</h1>
          <p className="console-brand__subtitle">
            {pageTitle} · {pageSubtitle}
          </p>
        </div>
        <div className="console-topbar__actions">
          <nav className="console-nav" aria-label="主导航">
            <button
              className={`console-nav__button ${view === "events" ? "console-nav__button--active" : ""}`}
              type="button"
              onClick={() => setView("events")}
            >
              事件配置
            </button>
            <button
              className={`console-nav__button ${view === "realms" ? "console-nav__button--active" : ""}`}
              type="button"
              onClick={() => setView("realms")}
            >
              境界配置
            </button>
            <button
              className={`console-nav__button ${view === "dwelling" ? "console-nav__button--active" : ""}`}
              type="button"
              onClick={() => setView("dwelling")}
            >
              洞府配置
            </button>
          </nav>
          <div className="console-userbar">
            <span className="console-userbar__badge">执笔人 {authState.session.username}</span>
            <button className="button-ghost" type="button" onClick={() => void handleLogout()}>
              退出登录
            </button>
          </div>
        </div>
      </header>

      <div className="console-page">
        {view === "events" ? <EventListPage /> : null}
        {view === "realms" ? <RealmListPage /> : null}
        {view === "dwelling" ? <DwellingListPage /> : null}
      </div>
    </div>
  );
}
