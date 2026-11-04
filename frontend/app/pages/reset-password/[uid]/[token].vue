<script setup lang="ts">
import { KeyRound } from '@lucide/vue'

definePageMeta({ layout: 'auth' })
const route = useRoute()
const password = ref('')
const confirmation = ref('')
const errorMessage = ref('')
const submitting = ref(false)
const { request } = useApi()
const toast = useToast()

async function submit() {
  errorMessage.value = ''
  if (password.value !== confirmation.value) {
    errorMessage.value = 'The passwords do not match.'
    return
  }
  submitting.value = true
  try {
    await request('/auth/password-reset/confirm/', { method: 'POST', body: { uid: route.params.uid as string, token: route.params.token as string, password: password.value } })
    toast.success('Password updated', 'Sign in with your new password.')
    await navigateTo('/login')
  } catch (error) {
    errorMessage.value = isRateLimitError(error)
      ? 'Too many reset attempts. Wait before trying again.'
      : 'This reset link is invalid or expired, or the password does not meet the security requirements.'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <section class="auth-card">
    <span class="mb-6 grid size-12 place-items-center rounded-xl bg-secondary text-primary"><KeyRound /></span>
    <p class="eyebrow">Account recovery</p><h1>Choose a new password</h1><p>Use a strong password you do not use elsewhere.</p>
    <form class="stack" @submit.prevent="submit"><div class="grid gap-2"><Label for="password">New password</Label><Input id="password" v-model="password" type="password" autocomplete="new-password" minlength="8" required /><p class="text-xs text-muted-foreground">At least 8 characters; not common, personal, or entirely numeric.</p></div><div class="grid gap-2"><Label for="confirmation">Confirm password</Label><Input id="confirmation" v-model="confirmation" type="password" autocomplete="new-password" required /></div><p v-if="errorMessage" class="error" role="alert">{{ errorMessage }}</p><Button class="w-full" type="submit" :disabled="submitting">{{ submitting ? 'Updating…' : 'Update password' }}</Button></form>
  </section>
</template>
