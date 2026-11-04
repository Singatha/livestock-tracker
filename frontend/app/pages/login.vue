<script setup lang="ts">
import { ArrowRight, PawPrint } from '@lucide/vue'
definePageMeta({ layout: 'auth' })
const username = ref('')
const password = ref('')
const errorMessage = ref('')
const submitting = ref(false)
const { request, resetCsrfToken } = useApi()
const toast = useToast()

async function submit() {
  submitting.value = true
  errorMessage.value = ''
  try {
    await request('/auth/login/', {
      method: 'POST',
      body: { username: username.value, password: password.value },
    })
    // Django rotates the CSRF secret on login; discard the pre-login token.
    resetCsrfToken()
    toast.success('Welcome back', 'You are now signed in.')
    await navigateTo('/')
  } catch (error) {
    errorMessage.value = isRateLimitError(error)
      ? 'Too many sign-in attempts. Wait a moment before trying again.'
      : 'Unable to sign in. Check your username and password.'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <section class="auth-card relative overflow-hidden">
    <div class="absolute inset-x-0 top-0 h-1 bg-primary" />
    <span class="mb-6 grid size-12 place-items-center rounded-xl bg-secondary text-primary"><PawPrint /></span>
    <p class="eyebrow">Livestock management</p>
    <h1>Welcome back</h1>
    <p>Sign in to manage your farm, animals, and upcoming work.</p>
    <form class="stack" @submit.prevent="submit">
      <div class="grid gap-2"><Label for="username">Username</Label><Input id="username" v-model="username" autocomplete="username" placeholder="Your username" required /></div>
      <div class="grid gap-2"><div class="flex items-center justify-between"><Label for="password">Password</Label><NuxtLink class="text-sm font-semibold text-primary hover:underline" to="/forgot-password">Forgot password?</NuxtLink></div><Input id="password" v-model="password" type="password" autocomplete="current-password" placeholder="Your password" required /></div>
      <p v-if="errorMessage" class="error" role="alert">{{ errorMessage }}</p>
      <Button class="h-10 w-full" type="submit" :disabled="submitting">{{ submitting ? 'Signing in…' : 'Sign in' }}<ArrowRight v-if="!submitting" /></Button>
    </form>
    <p class="mt-6 text-center text-sm text-muted-foreground">New to Flockwise? <NuxtLink class="font-semibold text-primary hover:underline" to="/signup">Create an account</NuxtLink></p>
  </section>
</template>
