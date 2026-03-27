import { useEffect, useState } from "react";

import {
  fetchAdminSession,
  loginAdmin,
  logoutAdmin,
  type AdminSession,
} from "./api/client";
import { EventEditorPage } from "./pages/EventEditorPage";
import { EventListPage } from "./pages/EventListPage";
import { LoginPage } from "./pages/LoginPage";
import { RealmEditorPage } from "./pages/RealmEditorPage";
import { RealmListPage } from "./pages/RealmListPage";

type ViewState =
  | { mode: "events" }
  | { mode: "event-editor"; eventId?: string }
  | { mode: "realms" }
  | { mode: "realm-editor"; realmKey?: string };

export default function App() {
  const [authState, setAuthState] = useState<
    | { status: "loading" }
    | { status: "unauthenticated" }
    | { status: "authenticated"; session: AdminSession }
    | { status: "error"; message: string }
  >({ status: "loading" });
  const [isSigningIn, setIsSigningIn] = useState(false);
  const [view, setView] = useState<ViewState>({ mode: "events" });
  const [eventRefreshToken, setEventRefreshToken] = useState(0);
  const [realmRefreshToken, setRealmRefreshToken] = useState(0);

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
      setView({ mode: "events" });
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
    setView({ mode: "events" });
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

  const isRealmMode = view.mode === "realms" || view.mode === "realm-editor";
  const pageTitle = isRealmMode ? "境界工坊" : view.mode === "event-editor" ? "事件工坊" : "事件谱册";
  const pageSubtitle =
    view.mode === "event-editor"
      ? view.eventId
        ? `正在整理事件 ${view.eventId}`
        : "正在新建事件配置"
      : view.mode === "realm-editor"
        ? view.realmKey
          ? `正在整理境界 ${view.realmKey}`
          : "正在新建境界配置"
        : isRealmMode
          ? "维护境界谱册、突破门槛与开放状态"
          : "维护事件模板、选项与运行配置";

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
              className={`console-nav__button ${!isRealmMode ? "console-nav__button--active" : ""}`}
              type="button"
              onClick={() => setView({ mode: "events" })}
            >
              事件配置
            </button>
            <button
              className={`console-nav__button ${isRealmMode ? "console-nav__button--active" : ""}`}
              type="button"
              onClick={() => setView({ mode: "realms" })}
            >
              境界配置
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
        {view.mode === "event-editor" ? (
          <EventEditorPage
            eventId={view.eventId}
            onBack={() => {
              setEventRefreshToken((value) => value + 1);
              setView({ mode: "events" });
            }}
            onSaved={(eventId) => {
              setEventRefreshToken((value) => value + 1);
              setView({ mode: "event-editor", eventId });
            }}
          />
        ) : null}

        {view.mode === "realm-editor" ? (
          <RealmEditorPage
            realmKey={view.realmKey}
            onBack={() => {
              setRealmRefreshToken((value) => value + 1);
              setView({ mode: "realms" });
            }}
            onSaved={(realmKey) => {
              setRealmRefreshToken((value) => value + 1);
              setView({ mode: "realm-editor", realmKey });
            }}
          />
        ) : null}

        {view.mode === "events" ? (
          <EventListPage
            refreshToken={eventRefreshToken}
            onCreateEvent={() => setView({ mode: "event-editor" })}
            onEditEvent={(eventId) => setView({ mode: "event-editor", eventId })}
          />
        ) : null}

        {view.mode === "realms" ? (
          <RealmListPage
            refreshToken={realmRefreshToken}
            onCreateRealm={() => setView({ mode: "realm-editor" })}
            onEditRealm={(realmKey) => setView({ mode: "realm-editor", realmKey })}
          />
        ) : null}
      </div>
    </div>
  );
}
