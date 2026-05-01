# CertifAI — App móvil (Expo)

App móvil para participantes que consume el API público de CertifAI:
ver certificados, dashboard, inscripción a eventos y perfil.

Stack: **Expo SDK 51 + Expo Router + TypeScript + Zustand + Reanimated 3**.

---

## Estructura

```
mobile/
├── app/                       # Rutas (file-based routing de Expo Router)
│   ├── _layout.tsx            # Layout raíz + redirect según sesión
│   ├── (auth)/                # Stack público
│   │   ├── login.tsx
│   │   └── register.tsx
│   └── (tabs)/                # Stack autenticado (4 tabs)
│       ├── index.tsx          # Dashboard (stats + próximos)
│       ├── certificates.tsx
│       ├── events.tsx         # Mis eventos / Disponibles
│       └── profile.tsx
├── components/
│   └── ui/                    # Design system
│       ├── GradientText.tsx   # Texto con gradiente animado
│       ├── AuroraBackground.tsx
│       ├── Heading.tsx
│       ├── Card.tsx           # Card con press-lift animado
│       └── index.ts
├── api/client.ts              # Fetch wrapper + token bearer (SecureStore)
├── stores/auth.ts             # Zustand: login, register, logout, refresh
├── theme/tokens.ts            # Design tokens UNEMI (espejo del web)
├── babel.config.js            # Plugin reanimated (obligatorio)
└── app.json
```

### Design System

Inspirado en `tareas/eneritzdev` (que la usuaria validó). Componentes:

| Componente         | Propósito                                                            |
| ------------------ | -------------------------------------------------------------------- |
| `GradientText`     | Título con gradiente que se mueve (equiv. `text-gradient-animated`) |
| `AuroraBackground` | Halos de color que flotan detrás del hero                            |
| `Heading`          | Títulos semánticos display/title/heading × niveles 1–4               |
| `Card`             | Card con `pressable` que se eleva al tocarlo (`hover:-translate-y`)  |

```tsx
import { AuroraBackground, Card, GradientText } from '@/components/ui';

<SafeAreaView style={{ flex: 1 }}>
  <AuroraBackground />
  <GradientText style={{ fontSize: 38, fontWeight: '900' }}>
    {participante.nombres}
  </GradientText>
  <Card onPress={open}>
    <Text>...</Text>
  </Card>
</SafeAreaView>
```

---

## Cómo correr

### 1) Backend Django

Asegúrate de que el backend esté corriendo en el puerto **8500**:

```bash
python manage.py runserver 0.0.0.0:8500
```

> El API móvil vive en `/api/v1/public/account/`
> (login, register, me, logout, dashboard, certificates, events, events/<id>/register).

### 2) Configurar URL del backend

Edita [`mobile/app.json`](app.json) → `expo.extra.apiBaseUrl`:

- **Emulador Android** → `http://10.0.2.2:8500`
- **iOS Simulator** → `http://localhost:8500`
- **Dispositivo físico** → `http://<IP-de-tu-PC>:8500`
  (con tu PC y el celular en la misma WiFi; ej. `http://192.168.1.42:8500`)

### 3) Instalar dependencias

```bash
cd mobile
npm install
```

> ⚠️ Esto instala todas las deps incluyendo `expo-linear-gradient`,
> `@react-native-masked-view/masked-view` y `react-native-reanimated`,
> que son las que el design system necesita para las animaciones.

### 4) Arrancar

```bash
npx expo start
```

Luego escanea el QR con la app **Expo Go** (Android/iOS) o pulsa `a`/`i`
para abrir en emulador.

---

## Autenticación

- El backend emite un token al hacer `POST /login/` o `/register/`.
- El cliente lo guarda en **expo-secure-store** (Keychain en iOS, EncryptedSharedPreferences en Android).
- Cada request agrega `Authorization: Token <key>`.
- Vence a los 30 días; al fallar `/me/` la app cierra sesión silenciosamente.

---

## Endpoints consumidos

| Método | Endpoint                                              | Pantalla         |
| ------ | ----------------------------------------------------- | ---------------- |
| POST   | `/api/v1/public/account/login/`                       | login.tsx        |
| POST   | `/api/v1/public/account/register/`                    | register.tsx     |
| POST   | `/api/v1/public/account/logout/`                      | profile.tsx      |
| GET    | `/api/v1/public/account/me/`                          | (refresh)        |
| GET    | `/api/v1/public/account/dashboard/`                   | index.tsx        |
| GET    | `/api/v1/public/account/certificates/?q=`             | certificates.tsx |
| GET    | `/api/v1/public/account/events/?tab=mios\|disponibles`| events.tsx       |
| POST   | `/api/v1/public/account/events/<id>/register/`        | events.tsx       |

---

## Diseño

Los tokens en [`theme/tokens.ts`](theme/tokens.ts) reflejan el sistema del web:
paleta UNEMI (naranja `#F58830` + azul `#162054`), sin morados ni verdes.
Tipografía pesada (System Black) para títulos.

Iconos de la app y splash: por defecto Expo usa los iconos genéricos.
Para personalizar, agrega `assets/icon.png` (1024×1024) y `assets/splash.png`,
y reactivá las claves `icon` / `splash.image` en [`app.json`](app.json).

---

## Build de producción

```bash
# instalar EAS CLI una sola vez
npm i -g eas-cli

# desde mobile/
eas build --platform android   # APK / AAB
eas build --platform ios       # IPA (requiere cuenta Apple Developer)
```

Antes de buildear, cambia `apiBaseUrl` a la URL pública del backend.
