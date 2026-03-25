import type { ValidationResponse } from "../api/client";

type ValidationPanelProps = {
  validation: ValidationResponse | null;
  statusMessage: string | null;
  errorMessage: string | null;
};

export function ValidationPanel({
  validation,
  statusMessage,
  errorMessage,
}: ValidationPanelProps) {
  return (
    <section className="status-card">
      <h2>校验回执</h2>
      {statusMessage ? (
        <div className="status-card__banner">{statusMessage}</div>
      ) : null}
      {errorMessage ? (
        <div className="status-card__banner status-card__banner--error" role="alert">
          {errorMessage}
        </div>
      ) : null}
      {validation ? (
        <div>
          <p>{validation.is_valid ? "当前配置校验通过。" : "当前配置存在问题，请先修正。"}</p>
          {validation.errors.length > 0 ? (
            <ul>
              {validation.errors.map((error) => (
                <li key={error}>{error}</li>
              ))}
            </ul>
          ) : null}
          {validation.warnings.length > 0 ? (
            <ul>
              {validation.warnings.map((warning) => (
                <li key={warning}>{warning}</li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : (
        <p>尚未执行校验。保存后可立即校验，也可手动重载运行时配置。</p>
      )}
    </section>
  );
}
