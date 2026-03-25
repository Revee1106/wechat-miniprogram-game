import { useState } from "react";

type LoginPageProps = {
  errorMessage: string | null;
  isSubmitting: boolean;
  onLogin: (username: string, password: string) => Promise<void>;
};

export function LoginPage({
  errorMessage,
  isSubmitting,
  onLogin,
}: LoginPageProps) {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onLogin(username, password);
  }

  return (
    <main className="login-shell">
      <section className="login-panel">
        <header className="login-panel__header">
          <span className="login-panel__eyebrow">WENDAO CONTROL</span>
          <h1>问道控制台</h1>
          <p>控制台登录</p>
          <p className="field__hint">
            这里用于维护事件模板、选项与运行配置。请使用管理员口令进入。
          </p>
        </header>
        <form className="login-panel__form" onSubmit={(event) => void handleSubmit(event)}>
          <label className="field">
            <span className="field__label">管理员账号</span>
            <input
              aria-label="管理员账号"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
            />
          </label>
          <label className="field">
            <span className="field__label">管理密码</span>
            <input
              aria-label="管理密码"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </label>
          <button className="button-primary" disabled={isSubmitting} type="submit">
            {isSubmitting ? "进入中..." : "进入控制台"}
          </button>
        </form>
        {errorMessage ? (
          <div className="status-card__banner status-card__banner--error" role="alert">
            {errorMessage}
          </div>
        ) : null}
      </section>
    </main>
  );
}
