import type { ReactNode } from "react";

export type WorkbenchTab = {
  id: string;
  label: string;
  badge?: string | number | null;
};

type ConfigWorkbenchProps = {
  className?: string;
  title: string;
  description: string;
  hideHero?: boolean;
  chips?: ReactNode;
  registryTitle: string;
  registryDescription?: string;
  registryToolbar?: ReactNode;
  registryContent: ReactNode;
  detailTitle: string;
  detailDescription?: string;
  detailMeta?: ReactNode;
  detailToolbar?: ReactNode;
  detailTabs?: WorkbenchTab[];
  activeTab?: string;
  onTabChange?: (tabId: string) => void;
  detailContent: ReactNode;
  actionBar?: ReactNode;
  statusPanel?: ReactNode;
};

export function ConfigWorkbench({
  className,
  title,
  description,
  hideHero = false,
  chips,
  registryTitle,
  registryDescription,
  registryToolbar,
  registryContent,
  detailTitle,
  detailDescription,
  detailMeta,
  detailToolbar,
  detailTabs,
  activeTab,
  onTabChange,
  detailContent,
  actionBar,
  statusPanel,
}: ConfigWorkbenchProps) {
  return (
    <main className={className ? `section-grid config-workbench ${className}` : "section-grid config-workbench"}>
      {!hideHero ? (
        <section className="hero-panel config-workbench__hero">
          <div className="section-card__body">
            <div>
              <h1>{title}</h1>
              <p>{description}</p>
            </div>
            {chips ? <div className="chip-row">{chips}</div> : null}
          </div>
        </section>
      ) : null}

      {statusPanel}

      <section className="config-workbench__layout">
        <aside className="section-card config-workbench__panel config-workbench__panel--registry">
          <header className="section-card__header config-workbench__panel-header">
            <div>
              <h2>{registryTitle}</h2>
              {registryDescription ? <p>{registryDescription}</p> : null}
            </div>
            {registryToolbar}
          </header>
          <div className="config-workbench__panel-body">{registryContent}</div>
        </aside>

        <section className="section-card config-workbench__panel config-workbench__panel--detail">
          <header className="section-card__header config-workbench__panel-header">
            <div>
              <h2>{detailTitle}</h2>
              {detailDescription ? <p>{detailDescription}</p> : null}
            </div>
            {detailToolbar}
          </header>

          {detailMeta ? <div className="config-workbench__meta">{detailMeta}</div> : null}

          {detailTabs && detailTabs.length > 0 && activeTab && onTabChange ? (
            <nav className="tab-strip" aria-label={`${detailTitle}标签`}>
              {detailTabs.map((tab) => {
                const isActive = tab.id === activeTab;
                return (
                  <button
                    key={tab.id}
                    aria-pressed={isActive}
                    className={isActive ? "tab-strip__button tab-strip__button--active" : "tab-strip__button"}
                    type="button"
                    onClick={() => onTabChange(tab.id)}
                  >
                    <span>{tab.label}</span>
                    {tab.badge !== undefined && tab.badge !== null ? (
                      <small>{tab.badge}</small>
                    ) : null}
                  </button>
                );
              })}
            </nav>
          ) : null}

          <div className="config-workbench__detail-body">{detailContent}</div>

          {actionBar ? <footer className="sticky-action-bar">{actionBar}</footer> : null}
        </section>
      </section>
    </main>
  );
}
