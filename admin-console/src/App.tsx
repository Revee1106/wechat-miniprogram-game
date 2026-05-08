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
import { EquipmentConfigPage } from "./pages/EquipmentConfigPage";
import { EventListPage } from "./pages/EventListPage";
import { LoginPage } from "./pages/LoginPage";
import { MaterialConfigPage } from "./pages/MaterialConfigPage";
import { RealmListPage } from "./pages/RealmListPage";

type ViewMode =
  | "events"
  | "realms"
  | "dwelling"
  | "materials"
  | "alchemy"
  | "equipment"
  | "battle";

const viewCopy: Record<ViewMode, { title: string; subtitle: string; nav: string }> = {
  events: {
    title: "事件工坊",
    subtitle: "集中维护事件清单与结果编辑",
    nav: "事件配置",
  },
  realms: {
    title: "境界谱录",
    subtitle: "集中维护境界清单与突破配置",
    nav: "境界配置",
  },
  dwelling: {
    title: "洞府工坊",
    subtitle: "集中维护设施清单与等级配置",
    nav: "洞府配置",
  },
  materials: {
    title: "材料工坊",
    subtitle: "集中维护洞府、炼丹与后续系统引用的材料配置",
    nav: "材料配置",
  },
  alchemy: {
    title: "丹道工坊",
    subtitle: "集中维护丹道等级、丹方、材料与成丹效果",
    nav: "丹道配置",
  },
  equipment: {
    title: "装备工坊",
    subtitle: "集中维护武器、防具、饰品与法宝配置",
    nav: "装备配置",
  },
  battle: {
    title: "战斗工坊",
    subtitle: "集中维护敌人模板与战利品配置",
    nav: "战斗配置",
  },
};

const navOrder: ViewMode[] = [
  "events",
  "realms",
  "dwelling",
  "materials",
  "alchemy",
  "equipment",
  "battle",
];

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

  const copy = viewCopy[view];

  return (
    <div className="console-shell">
      <header className="console-topbar">
        <div className="console-brand">
          <span className="console-brand__eyebrow">WENDAO CONTROL</span>
          <h1 className="console-brand__title">问道控制台</h1>
          <p className="console-brand__subtitle">
            {copy.title} 路 {copy.subtitle}
          </p>
        </div>
        <div className="console-topbar__actions">
          <nav className="console-nav" aria-label="主导航">
            {navOrder.map((mode) => (
              <button
                key={mode}
                className={`console-nav__button ${
                  view === mode ? "console-nav__button--active" : ""
                }`}
                type="button"
                onClick={() => setView(mode)}
              >
                {viewCopy[mode].nav}
              </button>
            ))}
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
        {view === "materials" ? <MaterialConfigPage /> : null}
        {view === "alchemy" ? <AlchemyConfigPage /> : null}
        {view === "equipment" ? <EquipmentConfigPage /> : null}
        {view === "battle" ? <BattleEnemyListPage /> : null}
      </div>
    </div>
  );
}
