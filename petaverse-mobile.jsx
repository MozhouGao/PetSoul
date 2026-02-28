import { useState, useEffect, useRef, useCallback } from "react";

// ─── Inject Fonts ────────────────────────────────────────────────
const FONT_URL = "https://fonts.googleapis.com/css2?family=Nunito:wght@400;500;600;700;800;900&family=Baloo+2:wght@400;500;600;700;800&display=swap";
if (!document.querySelector(`link[href*="Nunito"]`)) {
  const l = document.createElement("link");
  l.rel = "stylesheet";
  l.href = FONT_URL;
  document.head.appendChild(l);
}

// ─── Theme ───────────────────────────────────────────────────────
const C = {
  bg: "#FFFAF5",
  card: "#FFFFFF",
  primary: "#FF6161",
  primarySoft: "#FFE0E0",
  secondary: "#3DD6C8",
  secondarySoft: "#D6FFF9",
  accent: "#FFCB47",
  accentSoft: "#FFF5D6",
  purple: "#9B7DFF",
  purpleSoft: "#EDE7FF",
  text: "#1E1832",
  textSoft: "#9490A3",
  border: "#F0EBE5",
  overlay: "rgba(30,24,50,0.55)",
};

// ─── Global Styles ───────────────────────────────────────────────
const CSS = `
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent;}
@keyframes fadeUp{from{opacity:0;transform:translateY(18px)}to{opacity:1;transform:translateY(0)}}
@keyframes fadeIn{from{opacity:0}to{opacity:1}}
@keyframes scaleIn{from{opacity:0;transform:scale(.88)}to{opacity:1;transform:scale(1)}}
@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-8px)}}
@keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.06)}}
@keyframes spin{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}
@keyframes wiggle{0%,100%{transform:rotate(0)}25%{transform:rotate(-4deg)}75%{transform:rotate(4deg)}}
@keyframes progressBar{from{width:0}to{width:100%}}
@keyframes bounceIn{0%{opacity:0;transform:scale(.3)}50%{transform:scale(1.06)}70%{transform:scale(.96)}100%{transform:scale(1)}}
@keyframes slideUp{from{transform:translateY(100%)}to{transform:translateY(0)}}
@keyframes gradShift{0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}}
input:focus{outline:none}
`;

// ─── Phone Frame ─────────────────────────────────────────────────
const PhoneFrame = ({ children }) => (
  <div style={{
    minHeight: "100vh",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    background: "linear-gradient(160deg,#F5F0FF 0%,#FFF5F0 40%,#F0FFF9 100%)",
    padding: 24,
    fontFamily: "'Nunito', sans-serif",
  }}>
    <div style={{
      width: 390,
      height: 844,
      borderRadius: 48,
      background: "#111",
      padding: 10,
      boxShadow: "0 40px 120px rgba(30,24,50,0.25), 0 0 0 1px rgba(255,255,255,0.1) inset",
      position: "relative",
    }}>
      {/* Notch */}
      <div style={{
        position: "absolute",
        top: 10,
        left: "50%",
        transform: "translateX(-50%)",
        width: 126,
        height: 34,
        background: "#111",
        borderRadius: "0 0 20px 20px",
        zIndex: 100,
      }}>
        <div style={{
          width: 12, height: 12, borderRadius: "50%", background: "#1a1a2e",
          position: "absolute", right: 18, top: 10,
          boxShadow: "inset 0 0 3px rgba(255,255,255,0.08)",
        }}/>
      </div>
      {/* Screen */}
      <div style={{
        width: "100%",
        height: "100%",
        borderRadius: 40,
        overflow: "hidden",
        background: C.bg,
        position: "relative",
      }}>
        {children}
      </div>
    </div>
  </div>
);

// ─── Status Bar ──────────────────────────────────────────────────
const StatusBar = ({ light = false }) => (
  <div style={{
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "14px 28px 6px",
    fontSize: 13,
    fontWeight: 700,
    color: light ? "#fff" : C.text,
    position: "relative",
    zIndex: 50,
  }}>
    <span>9:41</span>
    <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
      <svg width="16" height="11" viewBox="0 0 16 11" fill="none">
        <rect x="0" y="3" width="3" height="8" rx="1" fill={light?"#fff":C.text} opacity=".4"/>
        <rect x="4.5" y="2" width="3" height="9" rx="1" fill={light?"#fff":C.text} opacity=".6"/>
        <rect x="9" y="0" width="3" height="11" rx="1" fill={light?"#fff":C.text} opacity=".8"/>
        <rect x="13" y="0" width="3" height="11" rx="1" fill={light?"#fff":C.text}/>
      </svg>
      <svg width="15" height="11" viewBox="0 0 15 11" fill="none">
        <path d="M7.5 2C10 2 12.2 3.2 13.8 5.2L7.5 11 1.2 5.2C2.8 3.2 5 2 7.5 2Z" fill={light?"#fff":C.text} opacity=".8"/>
      </svg>
      <svg width="24" height="12" viewBox="0 0 24 12" fill="none">
        <rect x=".5" y=".5" width="20" height="11" rx="2" stroke={light?"#fff":C.text} strokeOpacity=".35"/>
        <rect x="22" y="3.5" width="1.5" height="5" rx=".75" fill={light?"#fff":C.text} opacity=".4"/>
        <rect x="2" y="2" width="14" height="8" rx="1" fill={light?"#fff":C.text}/>
      </svg>
    </div>
  </div>
);

// ─── Bottom Tab Bar ──────────────────────────────────────────────
const BottomTabs = ({ active, onTab }) => {
  const tabs = [
    { id: "home", label: "Home", icon: (a) => (
      <svg width="22" height="22" fill="none" viewBox="0 0 24 24">
        <path d="M3 10.5L12 3l9 7.5V20a1 1 0 01-1 1H4a1 1 0 01-1-1V10.5z"
          stroke={a?C.primary:C.textSoft} strokeWidth="2" fill={a?C.primarySoft:"none"} strokeLinejoin="round"/>
      </svg>
    )},
    { id: "catalog", label: "Pets", icon: (a) => (
      <svg width="22" height="22" fill="none" viewBox="0 0 24 24">
        <circle cx="8" cy="6" r="2.5" stroke={a?C.primary:C.textSoft} strokeWidth="2" fill={a?C.primarySoft:"none"}/>
        <circle cx="16" cy="6" r="2.5" stroke={a?C.primary:C.textSoft} strokeWidth="2" fill={a?C.primarySoft:"none"}/>
        <circle cx="5" cy="13" r="2.5" stroke={a?C.primary:C.textSoft} strokeWidth="2" fill={a?C.primarySoft:"none"}/>
        <circle cx="19" cy="13" r="2.5" stroke={a?C.primary:C.textSoft} strokeWidth="2" fill={a?C.primarySoft:"none"}/>
        <ellipse cx="12" cy="18" rx="4" ry="3" stroke={a?C.primary:C.textSoft} strokeWidth="2" fill={a?C.primarySoft:"none"}/>
      </svg>
    )},
    { id: "add", label: "", icon: () => (
      <div style={{
        width: 52, height: 52, borderRadius: 18,
        background: `linear-gradient(135deg, ${C.primary}, #FF8E6B)`,
        display: "flex", alignItems: "center", justifyContent: "center",
        marginTop: -26,
        boxShadow: `0 8px 24px ${C.primary}44`,
      }}>
        <svg width="24" height="24" fill="none" viewBox="0 0 24 24">
          <path d="M12 5v14M5 12h14" stroke="#fff" strokeWidth="2.5" strokeLinecap="round"/>
        </svg>
      </div>
    )},
    { id: "explore", label: "Explore", icon: (a) => (
      <svg width="22" height="22" fill="none" viewBox="0 0 24 24">
        <circle cx="12" cy="12" r="9" stroke={a?C.primary:C.textSoft} strokeWidth="2" fill={a?C.primarySoft:"none"}/>
        <path d="M15.5 8.5l-2 5-5 2 2-5 5-2z" stroke={a?C.primary:C.textSoft} strokeWidth="1.5" fill={a?C.primarySoft:"none"}/>
      </svg>
    )},
    { id: "profile", label: "Profile", icon: (a) => (
      <svg width="22" height="22" fill="none" viewBox="0 0 24 24">
        <circle cx="12" cy="8" r="4" stroke={a?C.primary:C.textSoft} strokeWidth="2" fill={a?C.primarySoft:"none"}/>
        <path d="M4 20c0-3.3 3.6-6 8-6s8 2.7 8 6" stroke={a?C.primary:C.textSoft} strokeWidth="2" strokeLinecap="round"/>
      </svg>
    )},
  ];

  return (
    <div style={{
      position: "absolute", bottom: 0, left: 0, right: 0,
      background: "rgba(255,255,255,0.92)", backdropFilter: "blur(20px)",
      borderTop: `1px solid ${C.border}`,
      display: "flex", alignItems: "flex-end", justifyContent: "space-around",
      paddingBottom: 28, paddingTop: 8, zIndex: 50,
    }}>
      {tabs.map(t => (
        <button key={t.id} onClick={() => onTab(t.id)} style={{
          background: "none", border: "none", cursor: "pointer",
          display: "flex", flexDirection: "column", alignItems: "center", gap: 2,
          padding: "4px 12px", minWidth: 56,
        }}>
          {t.icon(active === t.id)}
          {t.label && <span style={{
            fontSize: 10, fontWeight: active === t.id ? 800 : 600,
            color: active === t.id ? C.primary : C.textSoft,
            fontFamily: "'Nunito', sans-serif",
          }}>{t.label}</span>}
        </button>
      ))}
    </div>
  );
};

// ─── 3D Pet Viewer (CSS 3D simulation) ───────────────────────────
const PetViewer3D = ({ type = "cat", size = 160, autoSpin = true }) => {
  const [rot, setRot] = useState(0);
  const [dragging, setDragging] = useState(false);
  const [autoR, setAutoR] = useState(autoSpin);
  const lastX = useRef(0);

  useEffect(() => {
    if (!autoR) return;
    const id = setInterval(() => setRot(r => r + 0.6), 16);
    return () => clearInterval(id);
  }, [autoR]);

  const onDown = e => {
    setDragging(true); setAutoR(false);
    lastX.current = e.clientX ?? e.touches?.[0]?.clientX ?? 0;
  };
  const onMove = e => {
    if (!dragging) return;
    const x = e.clientX ?? e.touches?.[0]?.clientX ?? 0;
    setRot(r => r + (x - lastX.current) * 0.6);
    lastX.current = x;
  };
  const onUp = () => { setDragging(false); setTimeout(() => setAutoR(true), 3000); };

  const colors = {
    cat: ["#FFB06B", "#FF6161"], dog: ["#9B7DFF", "#6C3CE0"],
    bunny: ["#3DD6C8", "#1AAF9F"], bird: ["#FFCB47", "#FF9A3C"],
    hamster: ["#FF8FAD", "#E05A82"],
  };
  const [c1, c2] = colors[type] || colors.cat;

  return (
    <div style={{
      width: size, height: size, perspective: 500, cursor: dragging ? "grabbing" : "grab",
      userSelect: "none", WebkitUserSelect: "none",
    }}
      onMouseDown={onDown} onMouseMove={onMove} onMouseUp={onUp} onMouseLeave={onUp}
      onTouchStart={onDown} onTouchMove={onMove} onTouchEnd={onUp}
    >
      <div style={{
        width: "100%", height: "100%", position: "relative",
        transformStyle: "preserve-3d", transform: `rotateY(${rot}deg)`,
      }}>
        {/* Body */}
        <div style={{
          position: "absolute", width: "56%", height: "60%", left: "22%", top: "28%",
          borderRadius: "50%",
          background: `radial-gradient(circle at 38% 32%, ${c1}, ${c2})`,
          boxShadow: `inset -8px -8px 24px rgba(0,0,0,0.12), 0 8px 32px ${c2}40`,
          transform: "translateZ(16px)",
        }}/>
        {/* Head */}
        <div style={{
          position: "absolute", width: "44%", height: "44%", left: "28%", top: "4%",
          borderRadius: "50%",
          background: `radial-gradient(circle at 36% 34%, ${c1}, ${c2})`,
          boxShadow: `inset -6px -6px 18px rgba(0,0,0,0.1)`,
          transform: "translateZ(24px)",
        }}>
          <div style={{ position:"absolute", width:8, height:8, borderRadius:"50%", background:"#1E1832", top:"42%", left:"26%", boxShadow:"inset 2px 1px 0 #fff" }}/>
          <div style={{ position:"absolute", width:8, height:8, borderRadius:"50%", background:"#1E1832", top:"42%", right:"26%", boxShadow:"inset 2px 1px 0 #fff" }}/>
          <div style={{ position:"absolute", width:7, height:5, borderRadius:"50%", background:"#FF8E8E", top:"60%", left:"calc(50% - 3.5px)" }}/>
        </div>
        {/* Ears for cat/bunny */}
        {(type === "cat" || type === "bunny") && <>
          <div style={{
            position: "absolute", width: type==="bunny"?"14%":"16%", height: type==="bunny"?"34%":"20%",
            left: "30%", top: type==="bunny"?"-6%":"0%",
            borderRadius: type==="bunny"?"50% 50% 50% 50%":"30% 70% 50% 50%",
            background: c1, transform: "translateZ(20px) rotate(-10deg)",
          }}/>
          <div style={{
            position: "absolute", width: type==="bunny"?"14%":"16%", height: type==="bunny"?"34%":"20%",
            right: "30%", top: type==="bunny"?"-6%":"0%",
            borderRadius: type==="bunny"?"50% 50% 50% 50%":"70% 30% 50% 50%",
            background: c1, transform: "translateZ(20px) rotate(10deg)",
          }}/>
        </>}
        {/* Floppy ears for dog */}
        {type === "dog" && <>
          <div style={{
            position: "absolute", width: "18%", height: "26%", left: "20%", top: "10%",
            borderRadius: "40% 60% 60% 40%", background: c2,
            transform: "translateZ(18px) rotate(-20deg)",
          }}/>
          <div style={{
            position: "absolute", width: "18%", height: "26%", right: "20%", top: "10%",
            borderRadius: "60% 40% 40% 60%", background: c2,
            transform: "translateZ(18px) rotate(20deg)",
          }}/>
        </>}
        {/* Shadow */}
        <div style={{
          position:"absolute", width:"46%", height:"8%", left:"27%", bottom:"8%",
          borderRadius:"50%", background:"rgba(0,0,0,0.08)", filter:"blur(6px)",
          transform:"translateZ(-8px)",
        }}/>
      </div>
    </div>
  );
};

// ─── Landing / Auth Screen ───────────────────────────────────────
const AuthScreen = ({ onAuth }) => {
  const [mode, setMode] = useState("signin");
  const [email, setEmail] = useState("");
  const [pass, setPass] = useState("");
  const [name, setName] = useState("");
  const [show, setShow] = useState(false);

  useEffect(() => { setTimeout(() => setShow(true), 80); }, []);

  const inputStyle = (focused) => ({
    width: "100%", padding: "14px 16px", borderRadius: 14,
    border: `2px solid ${focused ? C.secondary : C.border}`, background: "#fff",
    fontSize: 15, fontFamily: "'Nunito',sans-serif", fontWeight: 600,
    color: C.text, transition: "border .25s",
    boxShadow: focused ? `0 0 0 3px ${C.secondary}18` : "none",
  });

  const FocusInput = ({ placeholder, type="text", value, onChange, icon }) => {
    const [f, setF] = useState(false);
    return (
      <div style={{ position: "relative", marginBottom: 14 }}>
        <span style={{ position:"absolute", left:14, top:"50%", transform:"translateY(-50%)", fontSize:16, opacity:.45, pointerEvents:"none" }}>{icon}</span>
        <input type={type} placeholder={placeholder} value={value}
          onChange={e => onChange(e.target.value)}
          onFocus={() => setF(true)} onBlur={() => setF(false)}
          style={{ ...inputStyle(f), paddingLeft: 42 }}
        />
      </div>
    );
  };

  return (
    <div style={{ height: "100%", display: "flex", flexDirection: "column", background: C.bg, position: "relative", overflow: "hidden" }}>
      <StatusBar />

      {/* Decorative Blobs */}
      <div style={{ position:"absolute", top:-40, right:-40, width:160, height:160, borderRadius:"50%", background:`${C.primary}12`, filter:"blur(2px)" }}/>
      <div style={{ position:"absolute", bottom:80, left:-50, width:180, height:180, borderRadius:"50%", background:`${C.secondary}10`, filter:"blur(2px)" }}/>

      {/* Top Section */}
      <div style={{
        flex: 1, display: "flex", flexDirection: "column", alignItems: "center",
        justifyContent: "center", padding: "0 20px", paddingTop: 10,
        opacity: show ? 1 : 0, transform: show ? "none" : "translateY(16px)",
        transition: "all .6s cubic-bezier(.34,1.56,.64,1)",
      }}>
        {/* Animated pets */}
        <div style={{ display: "flex", gap: 12, marginBottom: 20 }}>
          {["cat","dog","bunny","bird"].map((t,i) => (
            <div key={t} style={{ animation: `float ${2.8+i*.4}s ease-in-out infinite`, animationDelay: `${i*.25}s` }}>
              <PetViewer3D type={t} size={52} autoSpin={true} />
            </div>
          ))}
        </div>

        <h1 style={{
          fontFamily: "'Baloo 2', cursive", fontSize: 34, fontWeight: 800,
          background: `linear-gradient(135deg, ${C.primary}, ${C.purple})`,
          backgroundSize: "200% 200%", animation: "gradShift 4s ease infinite",
          WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
          marginBottom: 4,
        }}>Petaverse</h1>
        <p style={{ fontSize: 14, color: C.textSoft, fontWeight: 600, marginBottom: 6 }}>
          Your pets, digitally alive
        </p>
      </div>

      {/* Auth Card - slides up from bottom */}
      <div style={{
        background: "#fff", borderRadius: "28px 28px 0 0",
        padding: "24px 24px 40px", position: "relative",
        boxShadow: "0 -8px 40px rgba(0,0,0,0.06)",
        animation: show ? "slideUp .5s cubic-bezier(.34,1.56,.64,1) .15s both" : "none",
      }}>
        {/* Tab Switch */}
        <div style={{ display: "flex", background: C.bg, borderRadius: 14, padding: 3, marginBottom: 22 }}>
          {["signin","signup"].map(m => (
            <button key={m} onClick={() => setMode(m)} style={{
              flex: 1, padding: "11px 0", borderRadius: 12, border: "none",
              background: mode===m ? "#fff" : "transparent",
              color: mode===m ? C.text : C.textSoft,
              fontFamily: "'Nunito',sans-serif", fontWeight: mode===m ? 800 : 600, fontSize: 14,
              cursor: "pointer", transition: "all .25s",
              boxShadow: mode===m ? "0 2px 8px rgba(0,0,0,0.05)" : "none",
            }}>
              {m==="signin" ? "Sign In" : "Sign Up"}
            </button>
          ))}
        </div>

        {mode === "signup" && <FocusInput icon="👤" placeholder="Your name" value={name} onChange={setName} />}
        <FocusInput icon="✉" placeholder="Email" type="email" value={email} onChange={setEmail} />
        <FocusInput icon="🔒" placeholder="Password" type="password" value={pass} onChange={setPass} />

        {mode==="signin" && (
          <div style={{ textAlign: "right", marginTop: -8, marginBottom: 10 }}>
            <button style={{ background:"none", border:"none", color:C.primary, fontFamily:"'Nunito',sans-serif", fontWeight:700, fontSize:12.5, cursor:"pointer" }}>
              Forgot password?
            </button>
          </div>
        )}

        <button onClick={onAuth} style={{
          width: "100%", padding: "15px 0", borderRadius: 16, border: "none",
          background: `linear-gradient(135deg, ${C.primary}, #FF8E6B)`,
          color: "#fff", fontSize: 16, fontFamily: "'Nunito',sans-serif", fontWeight: 800,
          cursor: "pointer", boxShadow: `0 6px 20px ${C.primary}40`,
          transition: "transform .2s", marginBottom: 18,
        }}
          onMouseDown={e => e.currentTarget.style.transform = "scale(.97)"}
          onMouseUp={e => e.currentTarget.style.transform = "none"}
        >
          {mode==="signin" ? "Sign In" : "Create Account"}
        </button>

        {/* Social */}
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16 }}>
          <div style={{ flex: 1, height: 1, background: C.border }}/>
          <span style={{ fontSize: 11, color: C.textSoft, fontWeight: 700 }}>OR</span>
          <div style={{ flex: 1, height: 1, background: C.border }}/>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          {[{icon:"🍎",l:"Apple"},{icon:"🔵",l:"Google"}].map(s => (
            <button key={s.l} onClick={onAuth} style={{
              flex: 1, padding: "12px 0", borderRadius: 14,
              border: `1.5px solid ${C.border}`, background: "#fff",
              fontFamily: "'Nunito',sans-serif", fontWeight: 700, fontSize: 13.5,
              color: C.text, cursor: "pointer", display: "flex",
              alignItems: "center", justifyContent: "center", gap: 6,
            }}>
              <span>{s.icon}</span>{s.l}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

// ─── Pet Catalog Screen ──────────────────────────────────────────
const CatalogScreen = ({ onViewPet, onTab }) => {
  const [show, setShow] = useState(false);
  useEffect(() => { setTimeout(() => setShow(true), 60); }, []);

  const pets = [
    { id:1, name:"Mochi", type:"cat", mood:"Happy", level:5, color:C.primary },
    { id:2, name:"Biscuit", type:"dog", mood:"Playful", level:8, color:C.purple },
    { id:3, name:"Clover", type:"bunny", mood:"Sleepy", level:3, color:C.secondary },
    { id:4, name:"Sunny", type:"bird", mood:"Excited", level:6, color:C.accent },
  ];

  const moodEmoji = { Happy:"😊", Playful:"🎾", Sleepy:"😴", Excited:"🤩" };

  return (
    <div style={{ height: "100%", display: "flex", flexDirection: "column", background: C.bg, position: "relative" }}>
      <StatusBar />

      {/* Header */}
      <div style={{
        padding: "8px 22px 14px",
        opacity: show?1:0, transform: show?"none":"translateY(12px)", transition: "all .5s ease",
      }}>
        <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom: 4 }}>
          <div>
            <p style={{ fontSize: 13, color: C.textSoft, fontWeight: 700 }}>Hello, Jamie 👋</p>
            <h1 style={{ fontFamily:"'Baloo 2',cursive", fontSize: 26, fontWeight: 800, color: C.text, lineHeight: 1.15 }}>
              Your Pets
            </h1>
          </div>
          <div style={{
            width: 42, height: 42, borderRadius: 15,
            background: `linear-gradient(135deg, ${C.purple}, ${C.secondary})`,
            display: "flex", alignItems: "center", justifyContent: "center",
            color: "#fff", fontFamily: "'Baloo 2',cursive", fontWeight: 800, fontSize: 18,
            boxShadow: `0 4px 14px ${C.purple}30`,
          }}>J</div>
        </div>

        {/* Stats row */}
        <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
          {[
            { label:"Pets", val: pets.length, emoji:"🐾", bg:C.primarySoft },
            { label:"Best Lvl", val:"8", emoji:"⭐", bg:C.accentSoft },
            { label:"Streak", val:"5d", emoji:"🔥", bg:C.purpleSoft },
          ].map(s => (
            <div key={s.label} style={{
              flex: 1, background: s.bg, borderRadius: 16, padding: "10px 12px",
              textAlign: "center",
            }}>
              <div style={{ fontSize: 12 }}>{s.emoji}</div>
              <div style={{ fontFamily:"'Baloo 2',cursive", fontSize: 18, fontWeight: 800, color: C.text, lineHeight: 1 }}>{s.val}</div>
              <div style={{ fontSize: 10, color: C.textSoft, fontWeight: 700 }}>{s.label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Pet Grid */}
      <div style={{
        flex: 1, overflowY: "auto", padding: "8px 22px 100px",
        WebkitOverflowScrolling: "touch",
      }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
          {pets.map((pet, i) => (
            <div key={pet.id} onClick={() => onViewPet(pet)} style={{
              background: "#fff", borderRadius: 22, padding: "16px 12px 14px",
              boxShadow: "0 4px 20px rgba(30,24,50,0.06)",
              border: `1.5px solid ${C.border}`,
              cursor: "pointer", transition: "all .25s",
              animation: `fadeUp .4s ease ${i * .08}s both`,
            }}
              onMouseDown={e => e.currentTarget.style.transform="scale(.96)"}
              onMouseUp={e => e.currentTarget.style.transform="none"}
              onMouseLeave={e => e.currentTarget.style.transform="none"}
            >
              <div style={{ display: "flex", justifyContent: "center", marginBottom: 8 }}>
                <PetViewer3D type={pet.type} size={100} autoSpin />
              </div>
              <h3 style={{
                fontFamily: "'Baloo 2',cursive", fontSize: 17, fontWeight: 800,
                textAlign: "center", color: C.text, marginBottom: 4,
              }}>{pet.name}</h3>
              <div style={{ display: "flex", justifyContent: "center", gap: 6 }}>
                <span style={{
                  padding: "3px 10px", borderRadius: 10, background: C.secondarySoft,
                  fontSize: 10.5, fontWeight: 700, color: "#1AAF9F",
                }}>Lvl {pet.level}</span>
                <span style={{
                  padding: "3px 10px", borderRadius: 10, background: C.accentSoft,
                  fontSize: 10.5, fontWeight: 700, color: "#C49A10",
                }}>{moodEmoji[pet.mood]} {pet.mood}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <BottomTabs active="catalog" onTab={onTab} />
    </div>
  );
};

// ─── Pet Detail Sheet ────────────────────────────────────────────
const PetDetailSheet = ({ pet, onClose }) => {
  if (!pet) return null;
  const stats = [
    { label:"Happiness", val:85, color:C.accent },
    { label:"Energy", val:72, color:C.secondary },
    { label:"Hunger", val:45, color:C.primary },
    { label:"Social", val:90, color:C.purple },
  ];

  return (
    <div style={{
      position:"absolute", inset:0, zIndex:80,
      background: C.overlay, backdropFilter:"blur(6px)",
      animation:"fadeIn .2s ease",
    }} onClick={onClose}>
      <div onClick={e => e.stopPropagation()} style={{
        position:"absolute", bottom:0, left:0, right:0,
        background:"#fff", borderRadius:"28px 28px 0 0",
        padding:"12px 22px 36px",
        boxShadow:"0 -12px 40px rgba(0,0,0,0.12)",
        animation:"slideUp .35s cubic-bezier(.34,1.56,.64,1)",
        maxHeight:"88%", overflowY:"auto",
      }}>
        {/* Handle */}
        <div style={{ width:36, height:4, borderRadius:2, background:C.border, margin:"0 auto 16px" }}/>

        <div style={{ display:"flex", justifyContent:"center", marginBottom:12 }}>
          <PetViewer3D type={pet.type} size={180} autoSpin />
        </div>

        <h2 style={{ fontFamily:"'Baloo 2',cursive", fontSize:28, fontWeight:800, textAlign:"center", marginBottom:2, color:C.text }}>
          {pet.name}
        </h2>
        <p style={{ textAlign:"center", fontSize:13, color:C.textSoft, fontWeight:600, marginBottom:20 }}>
          {pet.type[0].toUpperCase()+pet.type.slice(1)} · Level {pet.level}
        </p>

        {/* Stats */}
        <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:10, marginBottom:20 }}>
          {stats.map(s => (
            <div key={s.label} style={{ background:C.bg, borderRadius:16, padding:"12px 14px" }}>
              <div style={{ display:"flex", justifyContent:"space-between", marginBottom:6 }}>
                <span style={{ fontSize:11.5, fontWeight:700, color:C.textSoft }}>{s.label}</span>
                <span style={{ fontSize:11.5, fontWeight:800, color:s.color, fontFamily:"'Baloo 2',cursive" }}>{s.val}%</span>
              </div>
              <div style={{ height:5, borderRadius:3, background:`${s.color}20`, overflow:"hidden" }}>
                <div style={{ height:"100%", width:`${s.val}%`, borderRadius:3, background:s.color, animation:"progressBar .8s ease" }}/>
              </div>
            </div>
          ))}
        </div>

        {/* Actions */}
        <div style={{ display:"flex", gap:10 }}>
          {[
            { emoji:"🍖", label:"Feed", bg:C.primarySoft },
            { emoji:"🎾", label:"Play", bg:C.secondarySoft },
            { emoji:"💤", label:"Rest", bg:C.purpleSoft },
          ].map(a => (
            <button key={a.label} style={{
              flex:1, padding:"14px 0", borderRadius:16, border:"none",
              background:a.bg, cursor:"pointer", display:"flex", flexDirection:"column",
              alignItems:"center", gap:4, transition:"transform .15s",
            }}
              onMouseDown={e => e.currentTarget.style.transform="scale(.94)"}
              onMouseUp={e => e.currentTarget.style.transform="none"}
            >
              <span style={{ fontSize:22 }}>{a.emoji}</span>
              <span style={{ fontSize:11.5, fontWeight:800, color:C.text, fontFamily:"'Nunito',sans-serif" }}>{a.label}</span>
            </button>
          ))}
        </div>

        <p style={{ textAlign:"center", fontSize:11.5, color:C.textSoft, marginTop:16, fontWeight:600, fontStyle:"italic" }}>
          Drag the model to rotate
        </p>
      </div>
    </div>
  );
};

// ─── Add Pet Screen ──────────────────────────────────────────────
const AddPetScreen = ({ onTab }) => {
  const [step, setStep] = useState(1);
  const [preview, setPreview] = useState(null);
  const [petName, setPetName] = useState("");
  const [progress, setProgress] = useState(0);
  const [done, setDone] = useState(false);
  const fileRef = useRef(null);

  const handleFile = e => {
    const f = e.target.files?.[0];
    if (f) {
      const r = new FileReader();
      r.onload = ev => { setPreview(ev.target.result); setStep(2); };
      r.readAsDataURL(f);
    }
  };

  const generate = () => {
    setStep(3);
    let p = 0;
    const id = setInterval(() => {
      p += Math.random() * 9 + 2;
      if (p >= 100) { p = 100; clearInterval(id); setTimeout(() => setDone(true), 400); }
      setProgress(Math.min(p, 100));
    }, 180);
  };

  const reset = () => { setStep(1); setPreview(null); setPetName(""); setProgress(0); setDone(false); };

  const stepDots = (
    <div style={{ display:"flex", justifyContent:"center", gap:6, marginBottom:24 }}>
      {[1,2,3].map(s => (
        <div key={s} style={{
          width: step>=s ? 28 : 8, height: 8, borderRadius: 4,
          background: step>=s ? `linear-gradient(90deg,${C.primary},#FF8E6B)` : C.border,
          transition: "all .4s cubic-bezier(.34,1.56,.64,1)",
        }}/>
      ))}
    </div>
  );

  return (
    <div style={{ height:"100%", display:"flex", flexDirection:"column", background:C.bg, position:"relative" }}>
      <StatusBar />

      {/* Top bar */}
      <div style={{ display:"flex", alignItems:"center", padding:"4px 18px 10px" }}>
        <button onClick={() => step>1 ? setStep(step-1) : onTab("catalog")} style={{
          background:"rgba(255,255,255,0.7)", border:"none", borderRadius:12,
          padding:"8px 16px", fontFamily:"'Nunito',sans-serif", fontWeight:700,
          fontSize:14, color:C.text, cursor:"pointer", backdropFilter:"blur(8px)",
        }}>
          ← Back
        </button>
      </div>

      <div style={{ flex:1, overflowY:"auto", padding:"0 22px 110px", WebkitOverflowScrolling:"touch" }}>
        {stepDots}

        {/* ─── Step 1: Upload ─── */}
        {step === 1 && (
          <div style={{ animation:"fadeUp .4s ease" }}>
            <h2 style={{ fontFamily:"'Baloo 2',cursive", fontSize:26, fontWeight:800, textAlign:"center", marginBottom:4 }}>
              Add a Pet
            </h2>
            <p style={{ textAlign:"center", color:C.textSoft, fontSize:13.5, fontWeight:600, marginBottom:24 }}>
              Upload a photo to create a 3D companion
            </p>

            {/* Upload zone */}
            <div onClick={() => fileRef.current?.click()} style={{
              border:`2.5px dashed ${C.primary}30`, borderRadius:24, padding:"40px 20px",
              textAlign:"center", cursor:"pointer", background:"rgba(255,255,255,0.6)",
              backdropFilter:"blur(6px)", transition:"all .25s", marginBottom:18,
            }}
              onMouseOver={e => { e.currentTarget.style.borderColor=C.primary; e.currentTarget.style.background="rgba(255,255,255,0.9)"; }}
              onMouseOut={e => { e.currentTarget.style.borderColor=C.primary+"30"; e.currentTarget.style.background="rgba(255,255,255,0.6)"; }}
            >
              <input ref={fileRef} type="file" accept="image/*" onChange={handleFile} style={{display:"none"}} />
              <div style={{
                width:64, height:64, borderRadius:20, margin:"0 auto 14px",
                background:`linear-gradient(135deg,${C.primarySoft},${C.accentSoft})`,
                display:"flex", alignItems:"center", justifyContent:"center", fontSize:28,
              }}>📸</div>
              <p style={{ fontFamily:"'Baloo 2',cursive", fontSize:16, fontWeight:700, marginBottom:4 }}>Tap to upload a photo</p>
              <p style={{ fontSize:12, color:C.textSoft, fontWeight:600 }}>JPG, PNG, or HEIC up to 10MB</p>
            </div>

            {/* Camera btn */}
            <button onClick={() => fileRef.current?.click()} style={{
              width:"100%", padding:"13px 0", borderRadius:14, border:`2px solid ${C.primary}25`,
              background:"transparent", fontFamily:"'Nunito',sans-serif", fontWeight:800,
              fontSize:14, color:C.primary, cursor:"pointer", marginBottom:28,
            }}>📷 Take a Photo</button>

            {/* Sample pets */}
            <p style={{ textAlign:"center", fontSize:11, color:C.textSoft, fontWeight:700, letterSpacing:1, textTransform:"uppercase", marginBottom:12 }}>
              Or try a sample
            </p>
            <div style={{ display:"flex", justifyContent:"center", gap:12 }}>
              {["cat","dog","bunny","bird"].map(t => (
                <div key={t} onClick={() => { setPreview("sample"); setStep(2); }} style={{
                  width:60, height:60, borderRadius:18, background:"rgba(255,255,255,0.8)",
                  border:`2px solid ${C.border}`, display:"flex", alignItems:"center",
                  justifyContent:"center", cursor:"pointer", transition:"all .2s",
                }}
                  onMouseDown={e => e.currentTarget.style.transform="scale(.92)"}
                  onMouseUp={e => e.currentTarget.style.transform="none"}
                  onMouseLeave={e => e.currentTarget.style.transform="none"}
                >
                  <PetViewer3D type={t} size={42} autoSpin={false} />
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ─── Step 2: Name ─── */}
        {step === 2 && (
          <div style={{ animation:"fadeUp .4s ease" }}>
            <h2 style={{ fontFamily:"'Baloo 2',cursive", fontSize:26, fontWeight:800, textAlign:"center", marginBottom:4 }}>
              Name Your Pet
            </h2>
            <p style={{ textAlign:"center", color:C.textSoft, fontSize:13.5, fontWeight:600, marginBottom:22 }}>
              Give your companion a name
            </p>

            {/* Preview */}
            <div style={{
              width:120, height:120, borderRadius:28, margin:"0 auto 22px", overflow:"hidden",
              border:`3px solid #fff`, boxShadow:"0 6px 24px rgba(0,0,0,0.08)",
              display:"flex", alignItems:"center", justifyContent:"center",
              background:`linear-gradient(135deg,${C.primarySoft},${C.accentSoft})`,
            }}>
              {preview === "sample"
                ? <PetViewer3D type="cat" size={80} autoSpin />
                : <img src={preview} alt="Pet" style={{ width:"100%", height:"100%", objectFit:"cover" }}/>
              }
            </div>

            {/* Name input */}
            <div style={{ position:"relative", marginBottom:20 }}>
              <span style={{ position:"absolute", left:14, top:"50%", transform:"translateY(-50%)", fontSize:15, opacity:.4 }}>🏷️</span>
              <input value={petName} onChange={e => setPetName(e.target.value)}
                placeholder="What's their name?" style={{
                  width:"100%", padding:"14px 16px 14px 42px", borderRadius:14,
                  border:`2px solid ${C.border}`, background:"#fff",
                  fontSize:15, fontFamily:"'Nunito',sans-serif", fontWeight:600, color:C.text,
                }}
              />
            </div>

            <button onClick={generate} disabled={!petName} style={{
              width:"100%", padding:"15px 0", borderRadius:16, border:"none",
              background: petName ? `linear-gradient(135deg,${C.primary},#FF8E6B)` : C.border,
              color: petName ? "#fff" : C.textSoft,
              fontSize:16, fontFamily:"'Nunito',sans-serif", fontWeight:800,
              cursor: petName ? "pointer" : "not-allowed",
              boxShadow: petName ? `0 6px 20px ${C.primary}40` : "none",
              transition:"all .25s",
            }}>
              Generate 3D Model ✨
            </button>
          </div>
        )}

        {/* ─── Step 3: Generating / Done ─── */}
        {step === 3 && (
          <div style={{ animation:"fadeUp .4s ease", textAlign:"center" }}>
            {!done ? (
              <>
                {/* Progress ring */}
                <div style={{ width:110, height:110, margin:"0 auto 22px", position:"relative" }}>
                  <svg width="110" height="110" viewBox="0 0 110 110" style={{ transform:"rotate(-90deg)" }}>
                    <circle cx="55" cy="55" r="48" fill="none" stroke={C.border} strokeWidth="8"/>
                    <circle cx="55" cy="55" r="48" fill="none" stroke={C.primary} strokeWidth="8"
                      strokeDasharray={2*Math.PI*48} strokeDashoffset={2*Math.PI*48*(1-progress/100)}
                      strokeLinecap="round" style={{ transition:"stroke-dashoffset .3s ease" }}/>
                  </svg>
                  <div style={{
                    position:"absolute", inset:0, display:"flex", alignItems:"center", justifyContent:"center",
                    fontFamily:"'Baloo 2',cursive", fontSize:26, fontWeight:800, color:C.primary,
                  }}>{Math.round(progress)}%</div>
                </div>

                <h2 style={{ fontFamily:"'Baloo 2',cursive", fontSize:22, fontWeight:800, marginBottom:16 }}>
                  Creating {petName}
                </h2>

                {[
                  {l:"Analyzing photo", t:25},
                  {l:"Detecting features", t:50},
                  {l:"Building 3D mesh", t:75},
                  {l:"Applying textures", t:90},
                ].map((s,i) => (
                  <div key={i} style={{
                    display:"flex", alignItems:"center", gap:10, padding:"6px 0",
                    justifyContent:"center",
                    opacity: progress > i*25 ? 1 : .3, transition:"opacity .4s",
                  }}>
                    <div style={{
                      width:20, height:20, borderRadius:7,
                      background: progress>s.t ? C.secondary : C.border,
                      display:"flex", alignItems:"center", justifyContent:"center",
                      fontSize:10, color:"#fff", fontWeight:800, transition:"all .3s",
                    }}>{progress>s.t ? "✓" : ""}</div>
                    <span style={{
                      fontSize:13, fontWeight: progress>s.t ? 700 : 500,
                      color: progress>s.t ? C.text : C.textSoft,
                    }}>{s.l}</span>
                  </div>
                ))}
              </>
            ) : (
              <div style={{ animation:"bounceIn .5s ease" }}>
                <div style={{ display:"flex", justifyContent:"center", marginBottom:16 }}>
                  <PetViewer3D type="cat" size={200} autoSpin />
                </div>
                <h2 style={{ fontFamily:"'Baloo 2',cursive", fontSize:28, fontWeight:800, marginBottom:4 }}>
                  Meet {petName}! 🎉
                </h2>
                <p style={{ color:C.textSoft, fontSize:14, fontWeight:600, marginBottom:24 }}>
                  Your digital pet is ready
                </p>
                <div style={{ display:"flex", gap:10 }}>
                  <button onClick={() => onTab("catalog")} style={{
                    flex:1, padding:"14px 0", borderRadius:14, border:`2px solid ${C.secondary}`,
                    background:"transparent", color:C.secondary,
                    fontFamily:"'Nunito',sans-serif", fontWeight:800, fontSize:14, cursor:"pointer",
                  }}>View Collection</button>
                  <button onClick={reset} style={{
                    flex:1, padding:"14px 0", borderRadius:14, border:"none",
                    background:`linear-gradient(135deg,${C.primary},#FF8E6B)`, color:"#fff",
                    fontFamily:"'Nunito',sans-serif", fontWeight:800, fontSize:14, cursor:"pointer",
                    boxShadow:`0 6px 20px ${C.primary}40`,
                  }}>Add Another</button>
                </div>
                <p style={{ marginTop:16, fontSize:11.5, color:C.textSoft, fontStyle:"italic", fontWeight:600 }}>
                  Drag the model to rotate
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      <BottomTabs active="add" onTab={onTab} />
    </div>
  );
};

// ─── Main App ────────────────────────────────────────────────────
export default function App() {
  const [screen, setScreen] = useState("auth"); // auth | catalog | add
  const [selectedPet, setSelectedPet] = useState(null);

  const handleTab = (tab) => {
    setSelectedPet(null);
    if (tab === "add") setScreen("add");
    else if (tab === "catalog" || tab === "home") setScreen("catalog");
    else if (tab === "profile") setScreen("auth");
    else setScreen("catalog");
  };

  return (
    <>
      <style>{CSS}</style>
      <PhoneFrame>
        {screen === "auth" && <AuthScreen onAuth={() => setScreen("catalog")} />}
        {screen === "catalog" && (
          <>
            <CatalogScreen onViewPet={setSelectedPet} onTab={handleTab} />
            <PetDetailSheet pet={selectedPet} onClose={() => setSelectedPet(null)} />
          </>
        )}
        {screen === "add" && <AddPetScreen onTab={handleTab} />}
      </PhoneFrame>
    </>
  );
}
