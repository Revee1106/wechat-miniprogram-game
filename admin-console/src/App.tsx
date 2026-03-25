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

type ViewState =
  | { mode: "list" }
  | { mode: "editor"; eventId?: string };

export default function App() {
  const [authState, setAuthState] = useState<
    | { status: "loading" }
    | { status: "unauthenticated" }
    | { status: "authenticated"; session: AdminSession }
    | { status: "error"; message: string }
  >({ status: "loading" });
  const [isSigningIn, setIsSigningIn] = useState(false);
  const [view, setView] = useState<ViewState>({ mode: "list" });
  const [refreshToken, setRefreshToken] = useState(0);

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
    setView({ mode: "list" });
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

  const pageTitle = view.mode === "editor" ? "事件工坊" : "事件库";
  const pageSubtitle =
    view.mode === "editor"
      ? view.eventId
        ? `正在整理事件 ${view.eventId}`
        : "正在新建一条事件配置"
      : "维护事件模板、选项与运行配置";

  if (view.mode === "editor") {
    return (
      <div className="console-shell">
        <header className="console-topbar">
          <div className="console-brand">
            <span className="console-brand__eyebrow">WENDAO CONTROL</span>
            <h1 className="console-brand__title">问道控制台</h1>
            <p className="console-brand__subtitle">{pageTitle} · {pageSubtitle}</p>
          </div>
          <div className="console-userbar">
            <span className="console-userbar__badge">执笔人 {authState.session.username}</span>
            <button className="button-ghost" type="button" onClick={() => void handleLogout()}>
              退出登录
            </button>
          </div>
        </header>
        <div className="console-page">
          <EventEditorPage
            eventId={view.eventId}
            onBack={() => {
              setRefreshToken((value) => value + 1);
              setView({ mode: "list" });
            }}
            onSaved={(eventId) => {
              setRefreshToken((value) => value + 1);
              setView({ mode: "editor", eventId });
            }}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="console-shell">
      <header className="console-topbar">
        <div className="console-brand">
          <span className="console-brand__eyebrow">WENDAO CONTROL</span>
          <h1 className="console-brand__title">问道控制台</h1>
          <p className="console-brand__subtitle">{pageTitle} · {pageSubtitle}</p>
        </div>
        <div className="console-userbar">
          <span className="console-userbar__badge">执笔人 {authState.session.username}</span>
          <button className="button-ghost" type="button" onClick={() => void handleLogout()}>
            退出登录
          </button>
        </div>
      </header>
      <div className="console-page">
        <EventListPage
          refreshToken={refreshToken}
          onCreateEvent={() => setView({ mode: "editor" })}
          onEditEvent={(eventId) => setView({ mode: "editor", eventId })}
        />
      </div>
    </div>
  );
}
