/**
 * Pantalla de escaneo QR para registrar asistencia.
 *
 * Flujo:
 *   1) Usuario está logueado e inscrito a un evento.
 *   2) Toca "Escanear QR" en el detalle → abre esta pantalla.
 *   3) La cámara escanea el QR del evento (URL tipo `/checkin/<uuid>/`).
 *   4) Se POSTea el código a `/api/v1/public/account/checkin/`.
 *   5) Toast de éxito + cierra (vuelve al detalle).
 */
import { useEffect, useRef, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { Ionicons } from '@expo/vector-icons';

import { api } from '@/api/client';
import { colors, radius, shadows, spacing, themed, typography } from '@/theme/tokens';
import { useTheme } from '@/stores/theme';
import { Button, useToast } from '@/components/ui';

type CheckinResponse = {
  ok: boolean;
  created: boolean;
  already_registered: boolean;
  sesion_titulo: string;
  fecha: string;
  hora: string;
};

export default function ScannerScreen() {
  const [permission, requestPermission] = useCameraPermissions();
  const [submitting, setSubmitting] = useState(false);
  const handledRef = useRef(false);
  const insets = useSafeAreaInsets();
  const theme = useTheme();
  const t = themed(theme);
  const toast = useToast();

  useEffect(() => {
    if (permission && !permission.granted && permission.canAskAgain) {
      requestPermission();
    }
  }, [permission?.granted]);

  async function handleScan(value: string) {
    if (handledRef.current || submitting) return;
    handledRef.current = true;
    setSubmitting(true);

    try {
      const res = await api.post<CheckinResponse>(
        '/api/v1/public/account/checkin/',
        { codigo_qr: value },
      );
      if (res.already_registered) {
        toast.info('Ya tenías asistencia registrada en este evento.', 'Listo');
      } else {
        toast.success(`Asistencia registrada — ${res.sesion_titulo}`, '¡Confirmado!');
      }
      // Pequeño delay para que el toast se vea antes de cerrar
      setTimeout(() => {
        if (router.canGoBack()) router.back();
        else router.replace('/(tabs)');
      }, 600);
    } catch (e: any) {
      toast.error(e?.message ?? 'No pudimos validar el QR.', 'Error');
      // Reset para permitir reintentar
      setTimeout(() => { handledRef.current = false; setSubmitting(false); }, 1500);
    }
  }

  // Sin permiso aún
  if (!permission) {
    return (
      <SafeAreaView style={[styles.safe, { backgroundColor: t.bg }]}>
        <Text style={[styles.msg, { color: t.text }]}>Cargando cámara…</Text>
      </SafeAreaView>
    );
  }

  if (!permission.granted) {
    return (
      <SafeAreaView style={[styles.safe, { backgroundColor: t.bg }]}>
        <View style={styles.permWrap}>
          <Ionicons name="camera-outline" size={64} color={colors.brand} />
          <Text style={[styles.permTitle, { color: t.text }]}>Necesitamos la cámara</Text>
          <Text style={[styles.permText, { color: t.textMuted }]}>
            Para registrar tu asistencia necesitamos acceso a la cámara y escanear el QR del evento.
          </Text>
          <View style={{ marginTop: spacing.xl, alignSelf: 'stretch', gap: spacing.sm }}>
            <Button tone="brand" variant="filled" size="lg" fullWidth onPress={requestPermission}>
              Permitir cámara
            </Button>
            <Button tone="neutral" variant="ghost" size="lg" fullWidth onPress={() => router.back()}>
              Cancelar
            </Button>
          </View>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <View style={styles.cameraWrap}>
      <CameraView
        style={StyleSheet.absoluteFillObject}
        facing="back"
        barcodeScannerSettings={{ barcodeTypes: ['qr'] }}
        onBarcodeScanned={({ data }) => handleScan(data)}
      />

      {/* Overlay con marco de scan + back + caption */}
      <View pointerEvents="box-none" style={[StyleSheet.absoluteFillObject, styles.overlay]}>
        <Pressable
          onPress={() => router.back()}
          style={[styles.backBtn, { top: insets.top + spacing.sm }]}
          hitSlop={12}
        >
          <Ionicons name="close" size={24} color="#FFFFFF" />
        </Pressable>

        <View style={styles.caption}>
          <Text style={styles.captionText}>Escaneá el QR del evento</Text>
        </View>

        <View style={styles.frame}>
          {/* 4 esquinas en L para guiar el encuadre */}
          <View style={[styles.corner, styles.cornerTL]} />
          <View style={[styles.corner, styles.cornerTR]} />
          <View style={[styles.corner, styles.cornerBL]} />
          <View style={[styles.corner, styles.cornerBR]} />
        </View>

        <View style={[styles.hint, { paddingBottom: insets.bottom + spacing.xl }]}>
          <Ionicons name="qr-code-outline" size={16} color="rgba(255,255,255,0.85)" />
          <Text style={styles.hintText}>Sostené el celular firme dentro del marco</Text>
        </View>
      </View>
    </View>
  );
}

const FRAME = 260;

const styles = StyleSheet.create({
  safe: { flex: 1 },
  msg:  { textAlign: 'center', marginTop: spacing.huge, fontSize: typography.base },

  permWrap: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.xl,
  },
  permTitle: {
    fontSize: typography.xl,
    fontWeight: typography.black,
    marginTop: spacing.lg,
    textAlign: 'center',
  },
  permText: {
    fontSize: typography.sm,
    marginTop: spacing.sm,
    textAlign: 'center',
    lineHeight: typography.sm * 1.5,
  },

  cameraWrap: { flex: 1, backgroundColor: '#000' },
  overlay: {
    alignItems: 'center',
    justifyContent: 'space-between',
  },

  backBtn: {
    position: 'absolute',
    left: spacing.base,
    width: 44, height: 44,
    borderRadius: radius.full,
    backgroundColor: 'rgba(0,0,0,0.55)',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.20)',
    alignItems: 'center', justifyContent: 'center',
  },

  caption: {
    marginTop: 110,
    paddingHorizontal: spacing.base,
    paddingVertical: spacing.sm,
    backgroundColor: 'rgba(0,0,0,0.45)',
    borderRadius: radius.full,
  },
  captionText: {
    color: '#FFFFFF',
    fontSize: typography.sm,
    fontWeight: typography.bold,
    letterSpacing: 0.3,
  },

  frame: {
    width: FRAME, height: FRAME,
    marginTop: spacing.xl,
  },
  corner: {
    position: 'absolute',
    width: 36, height: 36,
    borderColor: colors.brand,
  },
  cornerTL: { top: 0, left: 0, borderTopWidth: 4, borderLeftWidth: 4, borderTopLeftRadius: radius.md },
  cornerTR: { top: 0, right: 0, borderTopWidth: 4, borderRightWidth: 4, borderTopRightRadius: radius.md },
  cornerBL: { bottom: 0, left: 0, borderBottomWidth: 4, borderLeftWidth: 4, borderBottomLeftRadius: radius.md },
  cornerBR: { bottom: 0, right: 0, borderBottomWidth: 4, borderRightWidth: 4, borderBottomRightRadius: radius.md },

  hint: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    paddingHorizontal: spacing.base,
    paddingVertical: spacing.sm,
    backgroundColor: 'rgba(0,0,0,0.45)',
    borderRadius: radius.full,
    marginBottom: spacing.lg,
    ...shadows.lg,
  },
  hintText: {
    color: 'rgba(255,255,255,0.92)',
    fontSize: typography.sm,
    fontWeight: typography.medium,
  },
});
