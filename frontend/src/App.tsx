import { useState, useEffect, useRef, Suspense } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls, useGLTF, Environment, Center } from '@react-three/drei'
import * as THREE from 'three'
import './App.css'

// ─── GLB Model Component (used inside Canvas) ────────────────────
function GLBModel({ url, autoRotate = true }: { url: string; autoRotate?: boolean }) {
  const { scene } = useGLTF(url)
  const ref = useRef<THREE.Group>(null)

  useEffect(() => {
    // Compute bounding box and normalize scale so model fits in view
    const box = new THREE.Box3().setFromObject(scene)
    const size = box.getSize(new THREE.Vector3())
    const maxDim = Math.max(size.x, size.y, size.z)
    const scale = 2 / maxDim
    scene.scale.setScalar(scale)

    // Center the model
    const center = box.getCenter(new THREE.Vector3())
    scene.position.set(-center.x * scale, -center.y * scale, -center.z * scale)
  }, [scene])

  useFrame((_, delta) => {
    if (autoRotate && ref.current) {
      ref.current.rotation.y += delta * 0.5
    }
  })

  return (
    <group ref={ref}>
      <primitive object={scene} />
    </group>
  )
}

// ─── GLB Viewer (full Three.js canvas) ────────────────────────────
function GLBViewer({ url, size = 200, autoRotate = true, interactive = true }: {
  url: string; size?: number; autoRotate?: boolean; interactive?: boolean;
}) {
  return (
    <div
      className="glb-viewer"
      style={{ width: size, height: size }}
    >
      <Canvas
        camera={{ position: [0, 0.5, 3], fov: 45 }}
        style={{ background: 'transparent' }}
        gl={{ alpha: true, antialias: true }}
      >
        <ambientLight intensity={0.6} />
        <directionalLight position={[5, 5, 5]} intensity={1} />
        <directionalLight position={[-3, 2, -3]} intensity={0.4} />
        <Suspense fallback={null}>
          <Center>
            <GLBModel url={url} autoRotate={autoRotate && !interactive} />
          </Center>
          <Environment preset="sunset" />
        </Suspense>
        {interactive && (
          <OrbitControls
            enablePan={false}
            enableZoom={true}
            minDistance={1.5}
            maxDistance={6}
            autoRotate={autoRotate}
            autoRotateSpeed={2}
          />
        )}
      </Canvas>
    </div>
  )
}

// ─── Loading Spinner (Minecraft style) ────────────────────────────
function LoadingBlock() {
  return (
    <div className="loading-block">
      <div className="loading-cube" />
      <div className="loading-text">LOADING...</div>
    </div>
  )
}

// ─── Pet Viewer (CSS 3D fallback, pixel-style) ────────────────────
function PetViewer3D({ type = 'cat', size = 160, autoSpin = true }: {
  type?: string; size?: number; autoSpin?: boolean;
}) {
  const [rot, setRot] = useState(0)
  const [dragging, setDragging] = useState(false)
  const [autoR, setAutoR] = useState(autoSpin)
  const lastX = useRef(0)

  useEffect(() => {
    if (!autoR) return
    const id = setInterval(() => setRot(r => r + 0.6), 16)
    return () => clearInterval(id)
  }, [autoR])

  const onDown = (e: React.MouseEvent | React.TouchEvent) => {
    setDragging(true); setAutoR(false)
    const clientX = 'clientX' in e ? e.clientX : e.touches?.[0]?.clientX ?? 0
    lastX.current = clientX
  }
  const onMove = (e: React.MouseEvent | React.TouchEvent) => {
    if (!dragging) return
    const x = 'clientX' in e ? e.clientX : e.touches?.[0]?.clientX ?? 0
    setRot(r => r + (x - lastX.current) * 0.6)
    lastX.current = x
  }
  const onUp = () => { setDragging(false); setTimeout(() => setAutoR(true), 3000) }

  const colors: Record<string, [string, string]> = {
    cat: ['#7EC850', '#3D5C21'],
    dog: ['#AA55FF', '#6633AA'],
    bunny: ['#55FFFF', '#229999'],
    bird: ['#FFAA00', '#CC7700'],
    hamster: ['#FF5555', '#AA3333'],
  }
  const [c1, c2] = colors[type] || colors.cat

  return (
    <div
      className="pet-viewer"
      style={{ width: size, height: size, perspective: 500 }}
      onMouseDown={onDown} onMouseMove={onMove} onMouseUp={onUp} onMouseLeave={onUp}
      onTouchStart={onDown} onTouchMove={onMove} onTouchEnd={onUp}
    >
      <div style={{
        width: '100%', height: '100%', position: 'relative',
        transformStyle: 'preserve-3d', transform: `rotateY(${rot}deg)`,
      }}>
        {/* Body */}
        <div style={{
          position: 'absolute', width: '50%', height: '50%', left: '25%', top: '32%',
          background: c1, border: `3px solid ${c2}`,
          transform: 'translateZ(12px)',
          boxShadow: `inset -4px -4px 0px ${c2}`,
        }}/>
        {/* Head */}
        <div style={{
          position: 'absolute', width: '40%', height: '40%', left: '30%', top: '6%',
          background: c1, border: `3px solid ${c2}`,
          transform: 'translateZ(20px)',
          boxShadow: `inset -3px -3px 0px ${c2}`,
        }}>
          <div style={{ position: 'absolute', width: 5, height: 5, background: '#1A1A1A', top: '38%', left: '22%' }}/>
          <div style={{ position: 'absolute', width: 5, height: 5, background: '#1A1A1A', top: '38%', right: '22%' }}/>
          <div style={{ position: 'absolute', width: 4, height: 3, background: '#FF8888', top: '58%', left: 'calc(50% - 2px)' }}/>
        </div>
        {/* Ears */}
        {(type === 'cat' || type === 'bunny') && <>
          <div style={{
            position: 'absolute', width: type === 'bunny' ? '12%' : '14%',
            height: type === 'bunny' ? '28%' : '16%',
            left: '32%', top: type === 'bunny' ? '-4%' : '2%',
            background: c1, border: `2px solid ${c2}`,
            transform: 'translateZ(18px)',
          }}/>
          <div style={{
            position: 'absolute', width: type === 'bunny' ? '12%' : '14%',
            height: type === 'bunny' ? '28%' : '16%',
            right: '32%', top: type === 'bunny' ? '-4%' : '2%',
            background: c1, border: `2px solid ${c2}`,
            transform: 'translateZ(18px)',
          }}/>
        </>}
        {type === 'dog' && <>
          <div style={{
            position: 'absolute', width: '16%', height: '22%', left: '22%', top: '12%',
            background: c2, border: `2px solid ${c2}`,
            transform: 'translateZ(16px)',
          }}/>
          <div style={{
            position: 'absolute', width: '16%', height: '22%', right: '22%', top: '12%',
            background: c2, border: `2px solid ${c2}`,
            transform: 'translateZ(16px)',
          }}/>
        </>}
        <div style={{
          position: 'absolute', width: '44%', height: '6%', left: '28%', bottom: '10%',
          background: 'rgba(0,0,0,0.2)', transform: 'translateZ(-6px)',
        }}/>
      </div>
    </div>
  )
}

// ─── Smart Viewer: GLB if available, CSS fallback otherwise ───────
function PetModelViewer({ modelUrl, type = 'cat', size = 160, autoSpin = true, interactive = false }: {
  modelUrl?: string; type?: string; size?: number; autoSpin?: boolean; interactive?: boolean;
}) {
  if (modelUrl) {
    return <GLBViewer url={modelUrl} size={size} autoRotate={autoSpin} interactive={interactive} />
  }
  return <PetViewer3D type={type} size={size} autoSpin={autoSpin} />
}

// ─── Bottom Hotbar ────────────────────────────────────────────────
function BottomBar({ active, onTab }: { active: string; onTab: (t: string) => void }) {
  const tabs = [
    { id: 'home', label: 'Home', icon: '\u2302' },
    { id: 'catalog', label: 'Pets', icon: '\uD83D\uDC3E' },
    { id: 'add', label: '+', icon: '+' },
    { id: 'explore', label: 'Map', icon: '\uD83D\uDDFA' },
    { id: 'profile', label: 'You', icon: '\u263A' },
  ]

  return (
    <div className="bottom-bar">
      <div className="hotbar">
        {tabs.map(t => (
          <div
            key={t.id}
            className={`hotbar-slot ${active === t.id ? 'active' : ''} ${t.id === 'add' ? 'hotbar-add' : ''}`}
            onClick={() => onTab(t.id)}
          >
            <span className="slot-icon">{t.icon}</span>
            {t.id !== 'add' && <span className="slot-label">{t.label}</span>}
          </div>
        ))}
      </div>
    </div>
  )
}

// ─── Auth Screen ──────────────────────────────────────────────────
function AuthScreen({ onAuth }: { onAuth: () => void }) {
  const [mode, setMode] = useState<'signin' | 'signup'>('signin')
  const [email, setEmail] = useState('')
  const [pass, setPass] = useState('')
  const [name, setName] = useState('')

  return (
    <div className="auth-screen">
      <div style={{ display: 'flex', gap: 16, marginBottom: 24 }}>
        {(['cat', 'dog', 'bunny', 'bird'] as const).map((t, i) => (
          <div key={t} style={{ animation: `mc-bob ${2 + i * 0.3}s ease-in-out infinite`, animationDelay: `${i * 0.2}s` }}>
            <PetViewer3D type={t} size={48} autoSpin />
          </div>
        ))}
      </div>

      <h1 className="auth-title">PETAVERSE</h1>
      <p className="auth-subtitle">Your pets, digitally alive</p>

      <div className="auth-card mc-panel">
        <div className="auth-tabs">
          <button
            className={`auth-tab ${mode === 'signin' ? 'active' : ''}`}
            onClick={() => setMode('signin')}
          >Sign In</button>
          <button
            className={`auth-tab ${mode === 'signup' ? 'active' : ''}`}
            onClick={() => setMode('signup')}
          >Sign Up</button>
        </div>

        <div className="auth-form">
          {mode === 'signup' && (
            <input className="mc-input" placeholder="Your name" value={name} onChange={e => setName(e.target.value)} />
          )}
          <input className="mc-input" type="email" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} />
          <input className="mc-input" type="password" placeholder="Password" value={pass} onChange={e => setPass(e.target.value)} />
          {mode === 'signin' && <button className="auth-forgot">Forgot password?</button>}
        </div>

        <button className="mc-btn mc-btn-primary" style={{ width: '100%', marginBottom: 12 }} onClick={onAuth}>
          {mode === 'signin' ? 'SIGN IN' : 'CREATE ACCOUNT'}
        </button>

        <div className="auth-divider">
          <div className="auth-divider-line" />
          <span className="auth-divider-text">OR</span>
          <div className="auth-divider-line" />
        </div>

        <div className="social-btns">
          <button className="mc-btn social-btn" onClick={onAuth}>Apple</button>
          <button className="mc-btn social-btn" onClick={onAuth}>Google</button>
        </div>
      </div>
    </div>
  )
}

// ─── Catalog Screen ───────────────────────────────────────────────
interface Pet {
  id: number
  name: string
  type: string
  mood: string
  level: number
  modelUrl?: string
}

function CatalogScreen({ onViewPet, onTab }: { onViewPet: (p: Pet) => void; onTab: (t: string) => void }) {
  const pets: Pet[] = [
    { id: 1, name: 'Mochi', type: 'cat', mood: 'Happy', level: 5, modelUrl: '/models/pet_0e1d1521_1771566605.glb' },
    { id: 2, name: 'Biscuit', type: 'dog', mood: 'Playful', level: 8 },
    { id: 3, name: 'Clover', type: 'bunny', mood: 'Sleepy', level: 3 },
    { id: 4, name: 'Sunny', type: 'bird', mood: 'Excited', level: 6 },
  ]

  const moodEmoji: Record<string, string> = { Happy: ':)', Playful: ';)', Sleepy: '-_-', Excited: ':D' }

  return (
    <div className="catalog-screen">
      <div className="catalog-header">
        <p className="catalog-greeting">&gt; Hello, Player_1</p>
        <h1 className="catalog-title">YOUR PETS</h1>

        <div className="stats-row">
          {[
            { label: 'Pets', val: String(pets.length), emoji: '\uD83D\uDC3E' },
            { label: 'Best Lvl', val: '8', emoji: '\u2B50' },
            { label: 'Streak', val: '5d', emoji: '\uD83D\uDD25' },
          ].map(s => (
            <div key={s.label} className="stat-block">
              <span className="stat-emoji">{s.emoji}</span>
              <div className="stat-value">{s.val}</div>
              <div className="stat-label">{s.label}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="pet-grid">
        {pets.map((pet, i) => (
          <div
            key={pet.id}
            className="pet-card mc-panel"
            onClick={() => onViewPet(pet)}
            style={{ animation: `mc-slideUp 0.3s ease ${i * 0.06}s both` }}
          >
            <PetModelViewer modelUrl={pet.modelUrl} type={pet.type} size={120} autoSpin />
            <div className="pet-name">{pet.name}</div>
            <div className="pet-badges">
              <span className="pet-badge pet-badge-level">Lvl {pet.level}</span>
              <span className="pet-badge pet-badge-mood">{moodEmoji[pet.mood]} {pet.mood}</span>
            </div>
          </div>
        ))}
      </div>

      <BottomBar active="catalog" onTab={onTab} />
    </div>
  )
}

// ─── Pet Detail Modal ─────────────────────────────────────────────
function PetDetailModal({ pet, onClose }: { pet: Pet | null; onClose: () => void }) {
  if (!pet) return null

  const stats = [
    { label: 'Happiness', val: 85, color: 'var(--mc-accent)' },
    { label: 'Energy', val: 72, color: 'var(--mc-secondary)' },
    { label: 'Hunger', val: 45, color: 'var(--mc-danger)' },
    { label: 'Social', val: 90, color: 'var(--mc-purple)' },
  ]

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-panel mc-panel" onClick={e => e.stopPropagation()}>
        <button className="mc-btn modal-close" onClick={onClose}>X</button>

        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 8 }}>
          <PetModelViewer modelUrl={pet.modelUrl} type={pet.type} size={240} autoSpin interactive />
        </div>

        <div className="detail-name">{pet.name}</div>
        <div className="detail-type">
          {pet.type.charAt(0).toUpperCase() + pet.type.slice(1)} // Level {pet.level}
        </div>

        <div className="stats-grid">
          {stats.map(s => (
            <div key={s.label} className="stat-card">
              <div className="stat-card-header">
                <span className="stat-card-label">{s.label}</span>
                <span className="stat-card-value" style={{ color: s.color }}>{s.val}%</span>
              </div>
              <div className="stat-bar-bg">
                <div className="stat-bar-fill" style={{ width: `${s.val}%`, background: s.color }} />
              </div>
            </div>
          ))}
        </div>

        <div className="action-buttons">
          {[
            { emoji: '\uD83C\uDF56', label: 'Feed' },
            { emoji: '\uD83C\uDFBE', label: 'Play' },
            { emoji: '\uD83D\uDCA4', label: 'Rest' },
          ].map(a => (
            <button key={a.label} className="mc-btn action-btn">
              <span className="action-emoji">{a.emoji}</span>
              {a.label}
            </button>
          ))}
        </div>

        <div className="drag-hint">&gt; Drag to rotate / scroll to zoom _</div>
      </div>
    </div>
  )
}

// ─── Add Pet Screen ───────────────────────────────────────────────
function AddPetScreen({ onTab }: { onTab: (t: string) => void }) {
  const [step, setStep] = useState(1)
  const [preview, setPreview] = useState<string | null>(null)
  const [petName, setPetName] = useState('')
  const [progress, setProgress] = useState(0)
  const [done, setDone] = useState(false)
  const [generatedModelUrl, setGeneratedModelUrl] = useState<string | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)
  const fileObjRef = useRef<File | null>(null)

  const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    if (f) {
      fileObjRef.current = f
      const r = new FileReader()
      r.onload = ev => { setPreview(ev.target?.result as string); setStep(2) }
      r.readAsDataURL(f)
    }
  }

  const generate = async () => {
    setStep(3)
    setProgress(0)
    setDone(false)
    setGeneratedModelUrl(null)

    const file = fileObjRef.current
    if (!file) {
      // Demo mode: simulate progress without real API call
      let p = 0
      const id = setInterval(() => {
        p += Math.random() * 9 + 2
        if (p >= 100) { p = 100; clearInterval(id); setTimeout(() => setDone(true), 400) }
        setProgress(Math.min(p, 100))
      }, 180)
      return
    }

    // Real API call to generate-3d-model
    const formData = new FormData()
    formData.append('file', file)

    // Simulate progress while waiting for the API
    let p = 0
    const progressId = setInterval(() => {
      p += Math.random() * 3 + 1
      if (p > 90) p = 90 // Cap at 90% until API responds
      setProgress(Math.min(p, 90))
    }, 500)

    try {
      const response = await fetch('/generate-3d-model', {
        method: 'POST',
        body: formData,
      })

      clearInterval(progressId)

      if (response.ok) {
        // The response is a binary GLB file
        const blob = await response.blob()
        const objectUrl = URL.createObjectURL(blob)
        setGeneratedModelUrl(objectUrl)
        setProgress(100)
        setTimeout(() => setDone(true), 400)
      } else {
        // Handle error - still show done but without model
        setProgress(100)
        setTimeout(() => setDone(true), 400)
      }
    } catch {
      clearInterval(progressId)
      // Fallback: complete without model
      setProgress(100)
      setTimeout(() => setDone(true), 400)
    }
  }

  const reset = () => {
    if (generatedModelUrl) URL.revokeObjectURL(generatedModelUrl)
    setStep(1); setPreview(null); setPetName(''); setProgress(0); setDone(false)
    setGeneratedModelUrl(null); fileObjRef.current = null
  }

  return (
    <div className="add-screen">
      <div className="add-header">
        <button
          className="mc-btn back-btn"
          onClick={() => step > 1 ? setStep(step - 1) : onTab('catalog')}
        >
          &lt; BACK
        </button>
      </div>

      <div className="step-dots">
        {[1, 2, 3].map(s => (
          <div key={s} className={`step-dot ${step >= s ? 'active' : ''}`} style={{ width: step >= s ? 28 : 8 }} />
        ))}
      </div>

      <div className="add-content">
        {/* Step 1: Upload */}
        {step === 1 && (
          <div style={{ animation: 'mc-slideUp 0.3s ease' }}>
            <h2 className="add-title">ADD A PET</h2>
            <p className="add-subtitle">Upload a photo to craft a 3D companion</p>

            <div className="upload-zone" onClick={() => fileRef.current?.click()}>
              <input ref={fileRef} type="file" accept="image/*" onChange={handleFile} style={{ display: 'none' }} />
              <div className="upload-icon">[+]</div>
              <p className="upload-text">Click to upload a photo</p>
              <p className="upload-hint">JPG, PNG, or HEIC up to 10MB</p>
            </div>

            <button className="mc-btn" style={{ width: '100%', marginBottom: 24 }} onClick={() => fileRef.current?.click()}>
              TAKE A PHOTO
            </button>

            <p className="sample-label">-- OR TRY A SAMPLE --</p>
            <div className="sample-grid">
              {['cat', 'dog', 'bunny', 'bird'].map(t => (
                <div key={t} className="sample-slot mc-slot" onClick={() => { setPreview('sample'); setStep(2) }}>
                  <PetViewer3D type={t} size={38} autoSpin={false} />
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Step 2: Name */}
        {step === 2 && (
          <div style={{ animation: 'mc-slideUp 0.3s ease' }}>
            <h2 className="add-title">NAME YOUR PET</h2>
            <p className="add-subtitle">Give your companion a name</p>

            <div className="preview-frame">
              {preview === 'sample'
                ? <PetViewer3D type="cat" size={70} autoSpin />
                : preview && <img src={preview} alt="Pet" />
              }
            </div>

            <div className="name-input-group">
              <input className="mc-input" value={petName} onChange={e => setPetName(e.target.value)} placeholder="What's their name?" />
            </div>

            <button
              className={`mc-btn ${petName ? 'mc-btn-primary' : ''}`}
              style={{ width: '100%', opacity: petName ? 1 : 0.5, cursor: petName ? 'pointer' : 'not-allowed' }}
              onClick={() => petName && generate()}
            >
              GENERATE 3D MODEL
            </button>
          </div>
        )}

        {/* Step 3: Progress / Done */}
        {step === 3 && (
          <div style={{ animation: 'mc-slideUp 0.3s ease', textAlign: 'center' }}>
            {!done ? (
              <>
                <div className="progress-ring">
                  <svg width="100" height="100" viewBox="0 0 100 100" style={{ transform: 'rotate(-90deg)' }}>
                    <rect x="10" y="10" width="80" height="80" fill="none" stroke="var(--mc-border-light)" strokeWidth="6"/>
                    <rect x="10" y="10" width="80" height="80" fill="none" stroke="var(--mc-primary-light)" strokeWidth="6"
                      strokeDasharray={320} strokeDashoffset={320 * (1 - progress / 100)}
                      style={{ transition: 'stroke-dashoffset 0.3s ease' }}/>
                  </svg>
                  <div className="progress-text">{Math.round(progress)}%</div>
                </div>

                <h2 className="add-title" style={{ marginBottom: 16 }}>CRAFTING {petName.toUpperCase()}</h2>

                <div className="progress-steps">
                  {[
                    { l: 'Analyzing photo', t: 25 },
                    { l: 'Detecting features', t: 50 },
                    { l: 'Building 3D mesh', t: 75 },
                    { l: 'Applying textures', t: 90 },
                  ].map((s, i) => (
                    <div key={i} className={`progress-step ${progress > i * 25 ? '' : 'dim'}`}>
                      <div className={`progress-check ${progress > s.t ? 'done' : ''}`}>
                        {progress > s.t ? '\u2713' : ''}
                      </div>
                      <span className={`progress-label ${progress > s.t ? 'done' : ''}`}>{s.l}</span>
                    </div>
                  ))}
                </div>

                <LoadingBlock />
              </>
            ) : (
              <div className="done-section">
                <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 12 }}>
                  <PetModelViewer
                    modelUrl={generatedModelUrl ?? undefined}
                    type="cat"
                    size={280}
                    autoSpin
                    interactive
                  />
                </div>
                <div className="done-title">MEET {petName.toUpperCase()}!</div>
                <div className="done-subtitle">Your digital pet is ready</div>
                <div className="done-actions">
                  <button className="mc-btn" style={{ flex: 1 }} onClick={() => onTab('catalog')}>
                    VIEW COLLECTION
                  </button>
                  <button className="mc-btn mc-btn-primary" style={{ flex: 1 }} onClick={reset}>
                    ADD ANOTHER
                  </button>
                </div>
                <div className="drag-hint" style={{ marginTop: 12 }}>&gt; Drag to rotate / scroll to zoom _</div>
              </div>
            )}
          </div>
        )}
      </div>

      <BottomBar active="add" onTab={onTab} />
    </div>
  )
}

// ─── Main App ─────────────────────────────────────────────────────
export default function App() {
  const [screen, setScreen] = useState<'auth' | 'catalog' | 'add'>('auth')
  const [selectedPet, setSelectedPet] = useState<Pet | null>(null)

  const handleTab = (tab: string) => {
    setSelectedPet(null)
    if (tab === 'add') setScreen('add')
    else if (tab === 'catalog' || tab === 'home') setScreen('catalog')
    else if (tab === 'profile') setScreen('auth')
    else setScreen('catalog')
  }

  return (
    <div className="app-container">
      {screen === 'auth' && <AuthScreen onAuth={() => setScreen('catalog')} />}
      {screen === 'catalog' && (
        <>
          <CatalogScreen onViewPet={setSelectedPet} onTab={handleTab} />
          <PetDetailModal pet={selectedPet} onClose={() => setSelectedPet(null)} />
        </>
      )}
      {screen === 'add' && <AddPetScreen onTab={handleTab} />}
    </div>
  )
}
