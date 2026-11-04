<script setup lang="ts">
import { Mail } from '@lucide/vue'

definePageMeta({ layout: 'auth' })
const email = ref('')
const submitted = ref(false)
const submitting = ref(false)
const errorMessage = ref('')
const { request } = useApi()

async function submit() {
  submitting.value = true
  errorMessage.value = ''
  try {
    await request('/auth/password-reset/', { method: 'POST', body: { email: email.value } })
    submitted.value = true
  } catch (error) {
    errorMessage.value = isRateLimitError(error)
      ? 'Too many reset requests. Wait before trying again.'
      : 'We could not request a reset link. Please try again.'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <section class="auth-card">
    <span class="mb-6 grid size-12 place-items-center rounded-xl bg-secondary text-primary"><Mail /></span>
    <p class="eyebrow">Account recovery</p><h1>Reset your password</h1>
    <template v-if="submitted"><p>If an account matches <strong>{{ email }}</strong>, a reset link will arrive shortly. Check your inbox and spam folder.</p><Button as-child class="mt-7 w-full" variant="outline"><NuxtLink to="/login">Back to sign in</NuxtLink></Button></template>
    <form v-else class="stack" @submit.prevent="submit"><div class="grid gap-2"><Label for="email">Account email</Label><Input id="email" v-model="email" type="email" autocomplete="email" placeholder="you@example.com" required /><p class="text-xs text-muted-foreground">We will send a time-limited reset link if the address belongs to an account.</p></div><p v-if="errorMessage" class="error" role="alert">{{ errorMessage }}</p><Button class="w-full" type="submit" :disabled="submitting">{{ submitting ? 'Sending…' : 'Send reset link' }}</Button><NuxtLink class="text-center text-sm font-semibold text-primary hover:underline" to="/login">Back to sign in</NuxtLink></form>
  </section>
</template>
