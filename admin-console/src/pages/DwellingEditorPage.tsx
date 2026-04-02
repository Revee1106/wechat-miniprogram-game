import { useEffect, useState } from "react";

import {
  fetchDwellingFacilityDetail,
  reloadDwelling,
  updateDwellingFacility,
  type DwellingFacilityInput,
  type DwellingLevelInput,
} from "../api/client";

type DwellingEditorPageProps = {
  facilityId: string;
  onBack: () => void;
  onSaved: (facilityId: string) => void;
};

type EditableDwellingLevel = DwellingLevelInput & {
  entryCostText: string;
  maintenanceCostText: string;
  resourceYieldText: string;
  specialEffectsText: string;
};

type EditableDwellingFacility = Omit<DwellingFacilityInput, "levels"> & {
  levels: EditableDwellingLevel[];
};

export function DwellingEditorPage({
  facilityId,
  onBack,
  onSaved,
}: DwellingEditorPageProps) {
  const [facility, setFacility] = useState<EditableDwellingFacility | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    let isMounted = true;

    async function load() {
      setIsLoading(true);
      try {
        const detail = await fetchDwellingFacilityDetail(facilityId);
        if (!isMounted) {
          return;
        }
        setFacility(toEditableFacility(detail));
        setStatusMessage(null);
        setErrorMessage(null);
      } catch (error) {
        if (isMounted) {
          setErrorMessage((error as Error).message);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    void load();

    return () => {
      isMounted = false;
    };
  }, [facilityId]);

  function handleFacilityFieldChange(
    field: keyof Omit<EditableDwellingFacility, "levels">,
    value: string
  ) {
    setFacility((current) => (current ? { ...current, [field]: value } : current));
  }

  function handleLevelFieldChange(
    targetLevel: number,
    field:
      | "entryCostText"
      | "maintenanceCostText"
      | "resourceYieldText"
      | "specialEffectsText"
      | "cultivation_exp_gain",
    value: string | number
  ) {
    setFacility((current) => {
      if (!current) {
        return current;
      }
      return {
        ...current,
        levels: current.levels.map((level) =>
          level.level === targetLevel ? { ...level, [field]: value } : level
        ),
      };
    });
  }

  function handleAddLevel() {
    setFacility((current) => {
      if (!current) {
        return current;
      }
      const nextLevel = current.levels.length + 1;
      return {
        ...current,
        levels: [
          ...current.levels,
          {
            level: nextLevel,
            entry_cost: {},
            maintenance_cost: {},
            resource_yields: {},
            cultivation_exp_gain: 0,
            special_effects: {},
            entryCostText: "",
            maintenanceCostText: "",
            resourceYieldText: "",
            specialEffectsText: "",
          },
        ],
      };
    });
  }

  async function handleSave() {
    if (!facility) {
      return;
    }

    try {
      setErrorMessage(null);
      setStatusMessage(null);
      const payload = toApiFacility(facility);
      const savedFacility = await updateDwellingFacility(facility.facility_id, payload);
      setFacility(toEditableFacility(savedFacility));
      const result = await reloadDwelling();
      setStatusMessage(`洞府配置已保存，并已重载运行时。当前共载入 ${result.facility_count} 项设施。`);
      onSaved(savedFacility.facility_id);
    } catch (error) {
      setErrorMessage((error as Error).message);
    }
  }

  if (isLoading || !facility) {
    return <div className="page-loading">正在加载洞府配置...</div>;
  }

  return (
    <main className="section-grid workbench-page">
      <section className="hero-panel">
        <div className="section-card__body">
          <div>
            <h1>洞府工坊</h1>
            <p>维护设施基础信息与各等级配置，等级从 1 开始连续增长。</p>
          </div>
          <div className="chip-row">
            <span className="chip">设施 {facility.display_name}</span>
            <span className="chip chip--soft">内部标识 {facility.facility_id}</span>
            <span className="chip chip--soft">等级数 {facility.levels.length}</span>
          </div>
        </div>

        <div className="section-card__body">
          {statusMessage ? <div className="status-card__banner">{statusMessage}</div> : null}
          {errorMessage ? (
            <div className="status-card__banner status-card__banner--error" role="alert">
              {errorMessage}
            </div>
          ) : null}
          <div className="toolbar">
            <button className="button-secondary" type="button" onClick={onBack}>
              返回洞府谱录
            </button>
            <button className="button-accent" type="button" onClick={handleAddLevel}>
              新增等级
            </button>
            <button className="button-primary" type="button" onClick={() => void handleSave()}>
              保存洞府配置
            </button>
          </div>
        </div>
      </section>

      <section className="section-card">
        <div className="section-card__header">
          <div>
            <h2>设施基础信息</h2>
            <p>设施 ID 不可修改，其他基础文案与类型可由控制台维护。</p>
          </div>
        </div>
        <div className="field-grid field-grid--three">
          <label className="field">
            <span className="field__label">设施 ID</span>
            <input readOnly value={facility.facility_id} />
          </label>
          <label className="field">
            <span className="field__label">设施名称</span>
            <input
              aria-label="设施名称"
              value={facility.display_name}
              onChange={(event) => handleFacilityFieldChange("display_name", event.target.value)}
            />
          </label>
          <label className="field">
            <span className="field__label">设施类型</span>
            <input
              value={facility.facility_type}
              onChange={(event) => handleFacilityFieldChange("facility_type", event.target.value)}
            />
          </label>
          <label className="field field--full">
            <span className="field__label">设施摘要</span>
            <textarea
              value={facility.summary}
              onChange={(event) => handleFacilityFieldChange("summary", event.target.value)}
            />
          </label>
          <label className="field field--full">
            <span className="field__label">功能解锁文案</span>
            <textarea
              value={facility.function_unlock_text}
              onChange={(event) =>
                handleFacilityFieldChange("function_unlock_text", event.target.value)
              }
            />
          </label>
        </div>
      </section>

      <div className="library-grid">
        {facility.levels.map((level) => (
          <section
            key={level.level}
            className="section-card"
            data-testid={`dwelling-level-${level.level}`}
          >
            <div className="section-card__header">
              <div>
                <h2>等级 {level.level}</h2>
                <p>维护进入该等级成本、每月维护、产出、修为收益与特殊效果。</p>
              </div>
            </div>
            <div className="field-grid field-grid--single">
              <label className="field">
                <span className="field__label">进入该等级成本</span>
                <textarea
                  aria-label="进入该等级成本"
                  value={level.entryCostText}
                  onChange={(event) =>
                    handleLevelFieldChange(level.level, "entryCostText", event.target.value)
                  }
                />
              </label>
              <label className="field">
                <span className="field__label">维护成本</span>
                <textarea
                  value={level.maintenanceCostText}
                  onChange={(event) =>
                    handleLevelFieldChange(level.level, "maintenanceCostText", event.target.value)
                  }
                />
              </label>
              <label className="field">
                <span className="field__label">资源产出</span>
                <textarea
                  value={level.resourceYieldText}
                  onChange={(event) =>
                    handleLevelFieldChange(level.level, "resourceYieldText", event.target.value)
                  }
                />
              </label>
              <label className="field">
                <span className="field__label">修为收益</span>
                <input
                  type="number"
                  value={level.cultivation_exp_gain}
                  onChange={(event) =>
                    handleLevelFieldChange(
                      level.level,
                      "cultivation_exp_gain",
                      Number(event.target.value) || 0
                    )
                  }
                />
              </label>
              <label className="field">
                <span className="field__label">特殊效果</span>
                <textarea
                  value={level.specialEffectsText}
                  onChange={(event) =>
                    handleLevelFieldChange(level.level, "specialEffectsText", event.target.value)
                  }
                />
              </label>
            </div>
          </section>
        ))}
      </div>
    </main>
  );
}

function toEditableFacility(facility: DwellingFacilityInput): EditableDwellingFacility {
  return {
    ...facility,
    levels: facility.levels.map((level) => ({
      ...level,
      entryCostText: stringifyNumberMap(level.entry_cost),
      maintenanceCostText: stringifyNumberMap(level.maintenance_cost),
      resourceYieldText: stringifyNumberMap(level.resource_yields),
      specialEffectsText: stringifyNumberMap(level.special_effects),
    })),
  };
}

function toApiFacility(facility: EditableDwellingFacility): DwellingFacilityInput {
  return {
    facility_id: facility.facility_id.trim(),
    display_name: facility.display_name.trim(),
    facility_type: facility.facility_type.trim(),
    summary: facility.summary.trim(),
    function_unlock_text: facility.function_unlock_text.trim(),
    levels: facility.levels.map((level, index) => ({
      level: index + 1,
      entry_cost: parseNumberMap(level.entryCostText),
      maintenance_cost: parseNumberMap(level.maintenanceCostText),
      resource_yields: parseNumberMap(level.resourceYieldText),
      cultivation_exp_gain: Number(level.cultivation_exp_gain) || 0,
      special_effects: parseNumberMap(level.specialEffectsText),
    })),
  };
}

function stringifyNumberMap(value: Record<string, number>): string {
  return Object.entries(value)
    .map(([key, amount]) => `${key}:${amount}`)
    .join("\n");
}

function parseNumberMap(raw: string): Record<string, number> {
  return raw
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .reduce<Record<string, number>>((result, line) => {
      const [key, value] = line.split(":");
      const normalizedKey = String(key || "").trim();
      if (!normalizedKey) {
        return result;
      }
      result[normalizedKey] = Number(String(value || "").trim()) || 0;
      return result;
    }, {});
}
