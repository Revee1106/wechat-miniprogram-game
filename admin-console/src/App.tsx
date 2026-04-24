import { useEffect, useState } from "react";

import {
  fetchAdminSession,
  loginAdmin,
  logoutAdmin,
  type AdminSession,
} from "./api/client";
import { AlchemyConfigPage } from "./pages/AlchemyConfigPage";
import { BattleEnemyListPage } from "./pages/BattleEnemyListPage";
import { DwellingListPage } from "./pages/DwellingListPage";
import { EventListPage } from "./pages/EventListPage";
import { LoginPage } from "./pages/LoginPage";
import { RealmListPage } from "./pages/RealmListPage";

type ViewMode = "events" | "realms" | "dwelling" | "alchemy" | "battle";

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
    view === "dwelling"
      ? "洞府工坊"
      : view === "realms"
        ? "境界谱录"
        : view === "alchemy"
          ? "丹道工坊"
        : view === "battle"
          ? "战斗工坊"
          : "事件工坊";
  const pageSubtitle =
    view === "dwelling"
      ? "集中维护设施清单与等级配置"
      : view === "realms"
        ? "集中维护境界清单与突破配置"
        : view === "alchemy"
          ? "集中维护丹道等级、丹方、材料与成丹效果"
        : view === "battle"
          ? "集中维护敌人模板与战利品配置"
          : "集中维护事件清单与结果编排";

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
            <button
              className={`console-nav__button ${view === "alchemy" ? "console-nav__button--active" : ""}`}
              type="button"
              onClick={() => setView("alchemy")}
            >
              丹道配置
            </button>
            <button
              className={`console-nav__button ${view === "battle" ? "console-nav__button--active" : ""}`}
              type="button"
              onClick={() => setView("battle")}
            >
              战斗配置
            </button>
          </nav>
          <div className="console-userbar">
            <span className="console-userbar__badge">当前用户 {authState.session.username}</span>
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
        {view === "alchemy" ? <AlchemyConfigPage /> : null}
        {view === "battle" ? <BattleEnemyListPage /> : null}
      </div>
    </div>
  );
}
