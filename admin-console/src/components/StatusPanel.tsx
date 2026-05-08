type StatusPanelProps = {
  statusMessage: string | null;
  errorMessage: string | null;
};

export function StatusPanel({ statusMessage, errorMessage }: StatusPanelProps) {
  if (!statusMessage && !errorMessage) {
    return null;
  }

  return (
    <section className="status-card">
      {statusMessage ? (
        <div className="status-card__banner">{statusMessage}</div>
      ) : null}
      {errorMessage ? (
        <div className="status-card__banner status-card__banner--error" role="alert">
          {errorMessage}
        </div>
      ) : null}
    </section>
  );
}
