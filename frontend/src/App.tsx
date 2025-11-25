import { type FormEvent, useEffect, useMemo, useState } from 'react'
import Editor from '@monaco-editor/react'
import './App.css'
import {
  fetchDashboard,
  fetchProfile,
  requestLoginCode,
  verifyLoginCode,
} from './modules/auth/api'
import type {
  AuthStage,
  DashboardSnapshot,
  UserProfile,
} from './modules/auth/types'
import {
  defaultConsole,
  quickTests,
  runtimeTargets,
  sampleFiles,
  type ConsoleLine,
  type IdeFile,
} from './modules/ide/sampleWorkspace'

const TOKEN_STORAGE_KEY = 'vibecode_token'
type ViewMode = 'auth' | 'dashboard' | 'ide'

const timestamp = () =>
  new Intl.DateTimeFormat('ru-RU', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  }).format(new Date())

type ConsoleLevel = ConsoleLine['level']

const createLog = (message: string, level: ConsoleLevel = 'info'): ConsoleLine => ({
  id: `${level}-${crypto.randomUUID()}`,
  level,
  message,
  timestamp: timestamp(),
})

function App() {
  const [files, setFiles] = useState<IdeFile[]>(sampleFiles)
  const [activeFileId, setActiveFileId] = useState(sampleFiles[0]?.id ?? '')
  const [consoleLines, setConsoleLines] = useState<ConsoleLine[]>(defaultConsole)
  const [selectedRuntime, setSelectedRuntime] = useState(runtimeTargets[0]?.id ?? '')
  const [authStage, setAuthStage] = useState<AuthStage>('request')
  const [authLoading, setAuthLoading] = useState(false)
  const [authError, setAuthError] = useState<string | null>(null)
  const [email, setEmail] = useState('')
  const [fullName, setFullName] = useState('')
  const [code, setCode] = useState('')
  const [token, setToken] = useState<string | null>(() =>
    window.localStorage.getItem(TOKEN_STORAGE_KEY),
  )
  const [user, setUser] = useState<UserProfile | null>(null)
  const [dashboard, setDashboard] = useState<DashboardSnapshot | null>(null)
  const [viewMode, setViewMode] = useState<ViewMode>(() =>
    token ? 'dashboard' : 'auth',
  )

  const activeFile = useMemo(
    () => files.find((file) => file.id === activeFileId) ?? files[0],
    [files, activeFileId],
  )

  const handleEditorChange = (value?: string) => {
    if (!activeFile || activeFile.readOnly) return

    setFiles((prev) =>
      prev.map((file) =>
        file.id === activeFile.id ? { ...file, content: value ?? '' } : file,
      ),
    )
  }

  const appendLog = (message: string, level?: ConsoleLevel) =>
    setConsoleLines((prev) => [...prev, createLog(message, level)])

  const hydrateProfile = async (tokenValue: string) => {
    try {
      const [profile, snapshot] = await Promise.all([
        fetchProfile(tokenValue),
        fetchDashboard(tokenValue),
      ])
      setUser(profile)
      setDashboard(snapshot)
    } catch (error) {
      console.error(error)
      handleLogout()
    }
  }

  useEffect(() => {
    if (!token) {
      setUser(null)
      setDashboard(null)
      setViewMode('auth')
      return
    }
    void hydrateProfile(token).then(() => setViewMode('dashboard'))
  }, [token])

  const handleRunSuite = () => {
    if (!user) {
      setViewMode('auth')
      setAuthError('Сначала авторизуйся, чтобы отправлять задания.')
      return
    }
    const runtime = runtimeTargets.find((item) => item.id === selectedRuntime)
    appendLog(`Enqueued Docker job via executor (${runtime?.version ?? 'runtime'})`)
    appendLog('Queue → Redis → Executor', 'info')
  }

  const handleQuickValidation = () => {
    appendLog('Started fast tier validation (lint + smoke tests)', 'success')
  }

  const isFileActive = (fileId: string) => fileId === activeFile?.id

  const handleRequestCode = async (event: FormEvent) => {
    event.preventDefault()
    setAuthLoading(true)
    setAuthError(null)
    try {
      await requestLoginCode({ email, fullName })
      setAuthStage('verify')
      appendLog(`Код отправлен на ${email}`, 'success')
    } catch (error) {
      setAuthError(error instanceof Error ? error.message : 'Ошибка отправки кода')
    } finally {
      setAuthLoading(false)
    }
  }

  const handleVerifyCode = async (event: FormEvent) => {
    event.preventDefault()
    setAuthLoading(true)
    setAuthError(null)
    try {
      const response = await verifyLoginCode({ email, code })
      window.localStorage.setItem(TOKEN_STORAGE_KEY, response.access_token)
      setToken(response.access_token)
      setUser(response.user)
      setCode('')
      setAuthStage('request')
      setViewMode('dashboard')
      appendLog('Авторизация успешна', 'success')
    } catch (error) {
      setAuthError(error instanceof Error ? error.message : 'Ошибка авторизации')
    } finally {
      setAuthLoading(false)
    }
  }

  const handleLogout = () => {
    window.localStorage.removeItem(TOKEN_STORAGE_KEY)
    setToken(null)
    setUser(null)
    setDashboard(null)
    setViewMode('auth')
    setAuthStage('request')
  }

  if (viewMode !== 'ide') {
    return (
      <div className="screen">
        {viewMode === 'auth' && (
          <section className="auth-screen">
            <div className="auth-card">
              <h1>Добро пожаловать в VibeCode IDE</h1>
              <p className="subtitle">
                Получи одноразовый код подтверждения и мы подготовим личный кабинет.
              </p>
              {authStage === 'request' && (
                <form onSubmit={handleRequestCode}>
                  <label>
                    E-mail
                    <input
                      type="email"
                      value={email}
                      onChange={(event) => setEmail(event.target.value)}
                      required
                    />
                  </label>
                  <label>
                    Имя (необязательно)
                    <input
                      type="text"
                      value={fullName}
                      onChange={(event) => setFullName(event.target.value)}
                      placeholder="Как к тебе обращаться"
                    />
                  </label>
                  <button type="submit" disabled={authLoading}>
                    {authLoading ? 'Отправляем...' : 'Получить код'}
                  </button>
                </form>
              )}

              {authStage === 'verify' && (
                <form onSubmit={handleVerifyCode} className="verify-form">
                  <p className="verify-info">
                    Введите код, который пришёл на <strong>{email || 'почту'}</strong>
                  </p>
                  <label>
                    6-значный код
                    <input
                      type="text"
                      value={code}
                      onChange={(event) => setCode(event.target.value)}
                      minLength={6}
                      maxLength={6}
                      required
                    />
                  </label>
                  <div className="verify-actions">
                    <button type="submit" disabled={authLoading}>
                      {authLoading ? 'Проверяем...' : 'Подтвердить'}
                    </button>
                    <button
                      type="button"
                      className="ghost"
                      onClick={() => setAuthStage('request')}
                    >
                      Запросить код ещё раз
                    </button>
                  </div>
                </form>
              )}

              {authError && <p className="auth-error">{authError}</p>}
            </div>
          </section>
        )}

        {viewMode === 'dashboard' && user && (
          <section className="dashboard-screen">
            <div>
              <p className="eyebrow">Аккаунт подтверждён</p>
              <h1>Привет, {user.full_name ?? user.email}!</h1>
              <p className="subtitle">
                Мы сохранили твои настройки и готовы запустить редактор, когда захочешь.
              </p>
              {dashboard && (
                <ul className="stats">
                  <li>
                    <span>Последний статус</span>
                    <strong>{dashboard.last_executor_status}</strong>
                  </li>
                  <li>
                    <span>Очередь</span>
                    <strong>{dashboard.pending_jobs}</strong>
                  </li>
                  <li>
                    <span>Язык</span>
                    <strong>{dashboard.last_language}</strong>
                  </li>
                </ul>
              )}
            </div>
            <div className="dashboard-actions">
              <button type="button" className="ghost" onClick={handleLogout}>
                Выйти
              </button>
              <button type="button" className="primary" onClick={() => setViewMode('ide')}>
                Перейти в редактор
              </button>
            </div>
          </section>
        )}
      </div>
    )
  }

  return (
    <div className="app-shell">
      <header className="top-bar">
        <div className="project-meta">
          <p className="project-name">VibeCode Jam IDE</p>
          <span className="project-branch">
            feature/runtime-split · TypeScript workspace
          </span>
        </div>
        <div className="top-bar-actions">
          {user && (
            <div className="user-chip">
              <div>
                <p>{user.full_name ?? user.email}</p>
                <span>{user.email}</span>
              </div>
              <button type="button" onClick={() => setViewMode('dashboard')}>
                Назад
              </button>
            </div>
          )}
          <button type="button" className="ghost">
            Open command palette
          </button>
          <button type="button" className="primary" onClick={handleRunSuite}>
            Run in Docker
          </button>
        </div>
      </header>

      <div className="app-body">
        <aside className="side-panel">
          {user && (
            <div className="account-card">
              <p className="panel-title">Аккаунт</p>
              <strong>{user.full_name ?? 'Безымянный разработчик'}</strong>
              <span>{user.email}</span>
              {dashboard && (
                <ul className="account-meta">
                  <li>
                    <p>Последний ран</p>
                    <span>{dashboard.last_executor_status}</span>
                  </li>
                  <li>
                    <p>В очереди</p>
                    <span>{dashboard.pending_jobs}</span>
                  </li>
                  <li>
                    <p>Язык</p>
                    <span>{dashboard.last_language}</span>
                  </li>
                </ul>
              )}
            </div>
          )}
          <div className="panel-title">Runtimes</div>
          <ul className="runtime-list">
            {runtimeTargets.map((runtime) => (
              <li key={runtime.id}>
                <label className="runtime-item">
                  <input
                    type="radio"
                    name="runtime"
                    value={runtime.id}
                    checked={selectedRuntime === runtime.id}
                    onChange={() => setSelectedRuntime(runtime.id)}
                  />
                  <div>
                    <p>{runtime.label}</p>
                    <span>{runtime.description}</span>
                  </div>
                  <code>{runtime.version}</code>
                </label>
              </li>
            ))}
          </ul>

          <div className="panel-title">Workspace</div>
          <ul className="file-tree">
            {files.map((file) => (
              <li key={file.id}>
                <button
                  type="button"
                  className={isFileActive(file.id) ? 'file active' : 'file'}
                  onClick={() => setActiveFileId(file.id)}
                >
                  <div>
                    <p>{file.name}</p>
                    <span>{file.path}</span>
                  </div>
                  <span className="lang-chip">{file.language}</span>
                </button>
              </li>
            ))}
          </ul>
        </aside>

        <section className="workspace">
          <div className="tabs">
            {files.map((file) => (
              <button
                key={file.id}
                type="button"
                className={isFileActive(file.id) ? 'tab active' : 'tab'}
                onClick={() => setActiveFileId(file.id)}
              >
                {file.name}
                {file.readOnly && <span className="readonly-indicator">ro</span>}
              </button>
            ))}
          </div>

          <div className="editor-surface">
            {activeFile ? (
              <Editor
                language={activeFile.language}
                theme="vs-dark"
                value={activeFile.content}
                onChange={handleEditorChange}
                height="100%"
                options={{
                  minimap: { enabled: false },
                  fontSize: 14,
                  smoothScrolling: true,
                  readOnly: !!activeFile.readOnly,
                  scrollBeyondLastLine: false,
                }}
              />
            ) : (
              <div className="empty-state">No file selected</div>
            )}
          </div>

          <div className="bottom-panels">
            <section className="panel console">
              <header>
                <div>
                  <p>Console</p>
                  <span>Executor & DAP stream</span>
                </div>
                <button type="button" onClick={handleQuickValidation}>
                  Quick test
                </button>
              </header>

              <ul className="console-log">
                {consoleLines.map((line) => (
                  <li key={line.id} className={line.level}>
                    <span className="timestamp">{line.timestamp}</span>
                    <span className="message">{line.message}</span>
                  </li>
                ))}
              </ul>
            </section>

            <section className="panel tests">
              <header>
                <div>
                  <p>Fast tier</p>
                  <span>Runs on backend w/o containers</span>
                </div>
              </header>
              <ul className="test-list">
                {quickTests.map((test) => (
                  <li key={test.id} className={test.status}>
      <div>
                      <p>{test.name}</p>
                      <span>{test.durationMs ? `${test.durationMs}ms` : 'queued'}</span>
                    </div>
                    <span className="status-pill">{test.status}</span>
                  </li>
                ))}
              </ul>
            </section>
          </div>
        </section>
      </div>

    </div>
  )
}

export default App
