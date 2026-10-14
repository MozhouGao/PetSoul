import { Component, Suspense, useEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { Canvas } from '@react-three/fiber'
import { Center, OrbitControls, useAnimations, useGLTF } from '@react-three/drei'
import { LoopRepeat } from 'three'
import type { AnimationAction } from 'three'
import './App.css'

const STORAGE_KEY = 'petsoul.models'
const ACTIONS = ['walk', 'sit', 'stretch'] as const

type SoundClip = { id: number; url: string; label: string; duration?: number }

type SavedModel = {
  modelId: string
  modelUrl: string
  riggedModelUrl: string | null
  breed: string
  colors: string
  createdAt: string
  sounds: SoundClip[]
}

type Screen = 'gallery' | 'create' | 'view'

function loadModels(): SavedModel[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    const parsed = raw ? JSON.parse(raw) : []
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function saveModels(models: SavedModel[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(models))
}

async function errorText(response: Response): Promise<string> {
  try {
    const data = await response.json()
    if (typeof data.detail === 'string') return data.detail
    if (data.detail && typeof data.detail.error === 'string') return data.detail.error
    if (typeof data.error === 'string') return data.error
  } catch {
    /* response was not JSON */
  }
  return response.statusText || 'Request failed'
}

function DogModel({ url, clip }: { url: string; clip: string }) {
  const gltf = useGLTF(url)
  const { actions } = useAnimations(gltf.animations, gltf.scene)

  useEffect(() => {
    const chosen = actions[clip] ?? actions.idle ?? Object.values(actions).find(Boolean)
    if (!chosen) return
    const action = chosen as AnimationAction
    action.setLoop(LoopRepeat, Infinity)
    action.reset().fadeIn(0.2).play()
    return () => {
      action.fadeOut(0.2)
    }
  }, [actions, clip])

  return (
    <Center>
      <primitive object={gltf.scene} />
    </Center>
  )
}

class ModelBoundary extends Component<{ children: ReactNode; resetKey: string }, { failed: boolean }> {
  state = { failed: false }
  static getDerivedStateFromError() {
    return { failed: true }
  }
  componentDidUpdate(prev: { resetKey: string }) {
    if (prev.resetKey !== this.props.resetKey && this.state.failed) this.setState({ failed: false })
  }
  render() {
    if (this.state.failed) {
      return <div className="model-error">This model file could not be loaded.</div>
    }
    return this.props.children
  }
}

function Viewer({ url, clip }: { url: string; clip: string }) {
  return (
    <div className="viewer">
      <ModelBoundary resetKey={url}>
        <Canvas camera={{ position: [0, 0.6, 3], fov: 45 }}>
          <ambientLight intensity={0.7} />
          <directionalLight position={[3, 4, 2]} intensity={1.2} />
          <Suspense fallback={null}>
            <DogModel url={url} clip={clip} />
          </Suspense>
          <OrbitControls enablePan />
        </Canvas>
      </ModelBoundary>
    </div>
  )
}

export default function App() {
  const [models, setModels] = useState<SavedModel[]>(() => loadModels())
  const [screen, setScreen] = useState<Screen>('gallery')
  const [currentId, setCurrentId] = useState<string | null>(null)
  const [clip, setClip] = useState('idle')
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [action, setAction] = useState<(typeof ACTIONS)[number]>('walk')
  const photoRef = useRef<HTMLInputElement>(null)
  const videoRef = useRef<HTMLInputElement>(null)
  const lastSound = useRef(-1)

  const current = models.find(model => model.modelId === currentId) ?? null

  function remember(next: SavedModel[]) {
    setModels(next)
    saveModels(next)
  }

  function openModel(model: SavedModel) {
    setCurrentId(model.modelId)
    setClip('idle')
    setError('')
    setStatus('')
    setScreen('view')
  }

  function playSound(sounds: SoundClip[]) {
    if (sounds.length === 0) return
    let index = 0
    if (sounds.length > 1) {
      do { index = Math.floor(Math.random() * sounds.length) } while (index === lastSound.current)
    }
    lastSound.current = index
    const audio = new Audio(sounds[index].url)
    audio.play().catch(() => setError('The browser blocked playback. Tap Play sound again.'))
  }

  async function createFromPhoto() {
    const file = photoRef.current?.files?.[0]
    if (!file) {
      setError('Choose a photo first.')
      return
    }
    setBusy(true)
    setError('')
    setStatus('Creating the 3D model. This usually takes 1–3 minutes.')
    try {
      const body = new FormData()
      body.append('file', file)
      const response = await fetch('/generate-3d-model', { method: 'POST', body })
      if (!response.ok) throw new Error(await errorText(response))
      const data = await response.json()
      const profile = data.profile ?? {}
      const saved: SavedModel = {
        modelId: data.model_id,
        modelUrl: data.model_url,
        riggedModelUrl: data.rigged_model_url ?? null,
        breed: profile.breed || profile.species || 'Dog',
        colors: Array.isArray(profile.coat_colors) ? profile.coat_colors.join(', ') : '',
        createdAt: new Date().toISOString(),
        sounds: [],
      }
      remember([saved, ...models.filter(model => model.modelId !== saved.modelId)])
      if (photoRef.current) photoRef.current.value = ''
      openModel(saved)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not create the model.')
      setStatus('')
    } finally {
      setBusy(false)
    }
  }

  async function addVideo() {
    if (!current) return
    const file = videoRef.current?.files?.[0]
    if (!file) {
      setError('Choose a video first.')
      return
    }
    setBusy(true)
    setError('')
    setStatus(`Learning ${action} and saving the sound from the video.`)
    try {
      const body = new FormData()
      body.append('file', file)
      body.append('action', action)
      const response = await fetch(`/pet-assets/${current.modelId}/videos`, { method: 'POST', body })
      if (!response.ok) throw new Error(await errorText(response))
      const data = await response.json()
      const sounds: SoundClip[] = Array.isArray(data.sounds) ? data.sounds : current.sounds
      const updated: SavedModel = {
        ...current,
        riggedModelUrl: data.rigged_model_url || current.riggedModelUrl,
        sounds: sounds.length ? [...current.sounds, ...sounds] : current.sounds,
      }
      remember(models.map(model => model.modelId === updated.modelId ? updated : model))
      setClip(action)
      if (videoRef.current) videoRef.current.value = ''
      setStatus(data.sound_error
        ? `Motion updated. ${data.sound_error}`
        : 'Motion and sound were saved on this pet.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not use that video.')
      setStatus('')
    } finally {
      setBusy(false)
    }
  }

  function removeCurrent() {
    if (!current) return
    remember(models.filter(model => model.modelId !== current.modelId))
    setScreen('gallery')
    setCurrentId(null)
  }

  return (
    <main className="page">
      <header>
        <h1>Pet Soul</h1>
        {screen !== 'gallery' && (
          <button onClick={() => { setScreen('gallery'); setError(''); setStatus('') }}>All pets</button>
        )}
      </header>

      {screen === 'gallery' && (
        <section className="stack">
          <div className="row">
            <button className="primary" onClick={() => { setScreen('create'); setError(''); setStatus('') }}>
              New pet from photo
            </button>
          </div>
          {models.length === 0 ? (
            <p className="muted">No pets yet. A photo creates a 3D model and keeps it in this browser.</p>
          ) : (
            <div className="cards">
              {models.map(model => (
                <button key={model.modelId} className="card" onClick={() => openModel(model)}>
                  <strong>{model.breed}</strong>
                  <span>{model.colors || 'No coat colors'} · {new Date(model.createdAt).toLocaleString()}</span>
                </button>
              ))}
            </div>
          )}
        </section>
      )}

      {screen === 'create' && (
        <section className="stack">
          <h2>Create a 3D pet</h2>
          <p className="muted">Use a clear photo of one dog. The model is saved in this browser when it finishes.</p>
          <label className="file">
            Photo
            <input ref={photoRef} type="file" accept="image/*" />
          </label>
          <button className="primary" disabled={busy} onClick={createFromPhoto}>
            {busy ? 'Creating…' : 'Create 3D model'}
          </button>
        </section>
      )}

      {screen === 'view' && current && (
        <section className="stack">
          <div>
            <h2>{current.breed}</h2>
            <p className="muted">{current.colors}</p>
          </div>
          <Viewer url={current.riggedModelUrl || current.modelUrl} clip={clip} />
          <div className="row">
            {['idle', 'walk', 'run', 'sit', 'stand', 'stretch'].map(name => (
              <button key={name} onClick={() => { setClip(name); playSound(current.sounds) }} disabled={!current.riggedModelUrl && name !== 'idle'}>
                {name}
              </button>
            ))}
            <button onClick={() => playSound(current.sounds)} disabled={current.sounds.length === 0}>
              Play sound
            </button>
          </div>
          <div className="stack">
            <h2>Add a video</h2>
            <p className="muted">Side view, full body, about 5–10 seconds. The motion replaces that action, and the audio becomes the pet’s sound.</p>
            <div className="row">
              <select value={action} onChange={event => setAction(event.target.value as (typeof ACTIONS)[number])}>
                {ACTIONS.map(name => <option key={name} value={name}>{name}</option>)}
              </select>
              <input ref={videoRef} type="file" accept="video/*" />
              <button className="primary" disabled={busy} onClick={addVideo}>
                {busy ? 'Working…' : 'Add action and sound'}
              </button>
            </div>
          </div>
          <button onClick={removeCurrent}>Remove from this browser</button>
        </section>
      )}

      {status && <p className="status">{status}</p>}
      {error && <p className="status error">{error}</p>}
    </main>
  )
}
