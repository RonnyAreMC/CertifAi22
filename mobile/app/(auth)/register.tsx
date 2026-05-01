import { useState } from 'react';
import {
  KeyboardAvoidingView, Platform, Pressable, ScrollView,
  StyleSheet, Text, TextInput, View,
} from 'react-native';
import { Link, router } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';

import { colors, radius, spacing, themed, typography } from '@/theme/tokens';
import { useAuth } from '@/stores/auth';
import { useTheme } from '@/stores/theme';
import { BrandLogo, Button } from '@/components/ui';

export default function RegisterScreen() {
  const [form, setForm] = useState({
    nombres: '', apellidos: '', email: '',
    cedula: '', celular: '', password: '',
  });

  const register = useAuth((s) => s.register);
  const loading  = useAuth((s) => s.loading);
  const error    = useAuth((s) => s.error);
  const theme = useTheme();
  const t = themed(theme);

  function setField<K extends keyof typeof form>(k: K, v: string) {
    setForm((f) => ({ ...f, [k]: v }));
  }

  async function submit() {
    try { await register({ ...form, email: form.email.trim().toLowerCase() }); } catch {}
  }

  const valid = form.nombres && form.apellidos && form.email && form.password.length >= 6;

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: t.bg }]} edges={['top']}>
      <View style={styles.topBar}>
        <Pressable
          onPress={() => router.canGoBack() ? router.back() : router.replace('/(auth)/landing')}
          style={({ pressed }) => [styles.back, pressed && { opacity: 0.6 }]}
          hitSlop={12}
        >
          <Ionicons name="chevron-back" size={26} color={colors.brand} style={{ marginLeft: -4 }} />
          <Text style={styles.backText}>Atrás</Text>
        </Pressable>
        <BrandLogo size={22} />
      </View>

      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 20}
        style={{ flex: 1 }}
      >
        <ScrollView
          contentContainerStyle={styles.scroll}
          keyboardShouldPersistTaps="handled"
          keyboardDismissMode="on-drag"
          showsVerticalScrollIndicator={false}
        >

          <Text style={[styles.title, { color: t.text }]}>Crear cuenta</Text>
          <Text style={[styles.subtitle, { color: t.textMuted }]}>
            Centraliza tus certificados y descubre eventos.
          </Text>

          {error ? (
            <View style={styles.errorBox}>
              <Text style={styles.errorText}>{error}</Text>
            </View>
          ) : null}

          <Field theme={theme} label="Nombres"   value={form.nombres}
                 onChangeText={(v) => setField('nombres', v)}
                 autoCapitalize="words" autoComplete="given-name" textContentType="givenName" />
          <Field theme={theme} label="Apellidos" value={form.apellidos}
                 onChangeText={(v) => setField('apellidos', v)}
                 autoCapitalize="words" autoComplete="family-name" textContentType="familyName" />
          <Field theme={theme} label="Email"     value={form.email}
                 onChangeText={(v) => setField('email', v)}
                 keyboardType="email-address" autoCapitalize="none" autoCorrect={false}
                 autoComplete="email" textContentType="emailAddress" />
          <Field theme={theme} label="Cédula (opcional)"  value={form.cedula}
                 onChangeText={(v) => setField('cedula', v)}
                 keyboardType="number-pad" autoCapitalize="none" autoCorrect={false} />
          <Field theme={theme} label="Celular (opcional)" value={form.celular}
                 onChangeText={(v) => setField('celular', v)}
                 keyboardType="phone-pad" autoCapitalize="none" autoCorrect={false}
                 autoComplete="tel" textContentType="telephoneNumber" />
          <Field theme={theme} label="Contraseña (mín. 6)" value={form.password}
                 onChangeText={(v) => setField('password', v)}
                 secureTextEntry autoCapitalize="none" autoCorrect={false}
                 autoComplete="password-new" textContentType="newPassword" />

          <Button
            onPress={submit}
            loading={loading}
            disabled={!valid}
            tone="brand"
            variant="filled"
            size="lg"
            fullWidth
            style={{ marginTop: spacing.sm }}
          >
            {loading ? 'Creando…' : 'Crear cuenta'}
          </Button>

          <View style={styles.bottomRow}>
            <Text style={[styles.bottomMuted, { color: t.textMuted }]}>¿Ya tienes cuenta? </Text>
            <Link href="/(auth)/login" style={[styles.bottomLink, { color: colors.brand }]}>
              Inicia sesión
            </Link>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

function Field({
  theme, label, ...rest
}: React.ComponentProps<typeof TextInput> & { label: string; theme: 'light' | 'dark' }) {
  const t = themed(theme);
  const inputBg = theme === 'dark' ? 'rgba(255,255,255,0.06)' : 'rgba(15,23,42,0.04)';
  const inputBorder = theme === 'dark' ? 'rgba(255,255,255,0.10)' : 'rgba(15,23,42,0.10)';
  return (
    <View style={{ marginBottom: spacing.base }}>
      <Text style={[styles.label, { color: t.textMuted }]}>{label}</Text>
      <TextInput
        placeholderTextColor={t.textMuted}
        {...rest}
        style={[styles.input, { backgroundColor: inputBg, borderColor: inputBorder, color: t.text }]}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  safe:   { flex: 1 },
  scroll: {
    paddingHorizontal: spacing.xl,
    paddingTop: spacing.sm,
    paddingBottom: spacing.xl,
    flexGrow: 1,
    justifyContent: 'center',
  },

  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.xl,
    paddingTop: spacing.sm,
    paddingBottom: spacing.sm,
  },
  back: { flexDirection: 'row', alignItems: 'center' },
  backText: { color: colors.brand, fontSize: typography.base, fontWeight: typography.medium },

  title:    { fontSize: typography.xxl, fontWeight: typography.black, marginBottom: spacing.xs },
  subtitle: { fontSize: typography.sm, marginBottom: spacing.xl },

  errorBox: {
    backgroundColor: 'rgba(220,38,38,0.18)',
    borderColor: 'rgba(220,38,38,0.5)', borderWidth: 1,
    padding: spacing.md, borderRadius: radius.md, marginBottom: spacing.base,
  },
  errorText: { color: '#FCA5A5', fontSize: typography.sm, fontWeight: typography.medium },

  label: { fontSize: typography.xs, fontWeight: typography.bold, marginBottom: spacing.xs, textTransform: 'uppercase', letterSpacing: 1 },
  input: {
    borderWidth: 1,
    borderRadius: radius.md, padding: spacing.base,
    fontSize: typography.base,
  },

  bottomRow:   { flexDirection: 'row', justifyContent: 'center', marginTop: spacing.xl },
  bottomMuted: { fontSize: typography.sm },
  bottomLink:  { fontSize: typography.sm, fontWeight: typography.bold },
});
