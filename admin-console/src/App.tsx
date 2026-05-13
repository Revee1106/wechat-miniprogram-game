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
    subtitle: "管理事件清单、触发条件、选项与结果",
    nav: "事件配置",
  },
  realms: {
    title: "境界谱录",
    subtitle: "管理境界清单、突破条件、成功率与失败惩罚",
    nav: "境界配置",
  },
  dwelling: {
    title: "洞府工坊",
    subtitle: "管理洞府设施、等级消耗、维护与产出",
    nav: "洞府配置",
  },
  materials: {
    title: "材料工坊",
    subtitle: "管理材料定义、稀有度、来源与标签",
    nav: "材料配置",
  },
  alchemy: {
    title: "丹道工坊",
    subtitle: "管理丹道等级、丹方材料、成丹效果与品级",
    nav: "丹道配置",
  },
  equipment: {
    title: "装备工坊",
    subtitle: "管理武器、防具、饰品与法宝属性",
    nav: "装备配置",
  },
  battle: {
    title: "战斗工坊",
    subtitle: "管理敌人模板、战斗数值与战利品配置",
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

  return (
    <div className="console-shell">
      <header className="console-topbar">
        <div className="console-topbar__main">
          <div className="console-brand">
            <span className="console-brand__eyebrow">WENDAO CONTROL</span>
            <h1 className="console-brand__title">问道控制台</h1>
          </div>
          <div className="console-userbar">
            <span className="console-userbar__badge">当前用户 {authState.session.username}</span>
            <button className="button-ghost" type="button" onClick={() => void handleLogout()}>
              退出登录
            </button>
          </div>
        </div>
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
