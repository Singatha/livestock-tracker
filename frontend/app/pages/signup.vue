<script setup lang="ts">
import { ArrowRight, UserPlus } from '@lucide/vue'
import type { User } from '~/types/api'

definePageMeta({ layout: 'auth' })
const form = reactive({ first_name: '', last_name: '', username: '', email: '', password: '' })
const errorMessage = ref('')
const submitting = ref(false)
const { request, resetCsrfToken } = useApi()
const toast = useToast()

async function submit() {
  submitting.value = true
  errorMessage.value = ''
  try {
    await request<User>('/auth/signup/', { method: 'POST', body: form })
    resetCsrfToken()
    toast.success('Account created', 'Welcome to Flockwise. Create your first farm to get started.')
    await navigateTo('/farms/new')
  } catch (error) {
    errorMessage.value = isRateLimitError(error)
      ? 'Too many account requests. Wait before trying again.'
      : 'We could not create your account. Check that the username and email are unique and the password is strong.'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <section class="auth-card relative overflow-hidden">
    <div class="absolute inset-x-0 top-0 h-1 bg-primary" />
    <span class="mb-6 grid size-12 place-items-center rounded-xl bg-secondary text-primary"><UserPlus /></span>
    <p class="eyebrow">Get started</p><h1>Create your account</h1><p>Your account can own a farm or join one through an invitation.</p>
    <form class="stack" @submit.prevent="submit">
      <div class="grid grid-cols-2 gap-4"><div class="grid gap-2"><Label for="first-name">First name</Label><Input id="first-name" v-model="form.first_name" autocomplete="given-name" /></div><div class="grid gap-2"><Label for="last-name">Last name</Label><Input id="last-name" v-model="form.last_name" autocomplete="family-name" /></div></div>
      <div class="grid gap-2"><Label for="username">Username</Label><Input id="username" v-model="form.username" autocomplete="username" placeholder="e.g. thandi" required /><p class="text-xs text-muted-foreground">Used when signing in. Letters, numbers, and @/./+/-/_ only.</p></div>
      <div class="grid gap-2"><Label for="email">Email</Label><Input id="email" v-model="form.email" type="email" autocomplete="email" placeholder="you@example.com" required /><p class="text-xs text-muted-foreground">Used for invitations and password recovery.</p></div>
      <div class="grid gap-2"><Label for="password">Password</Label><Input id="password" v-model="form.password" type="password" autocomplete="new-password" minlength="8" required /><p class="text-xs text-muted-foreground">Use at least 8 characters and avoid common or entirely numeric passwords.</p></div>
      <p v-if="errorMessage" class="error" role="alert">{{ errorMessage }}</p>
      <Button class="w-full" type="submit" :disabled="submitting">{{ submitting ? 'Creating account…' : 'Create account' }}<ArrowRight v-if="!submitting" /></Button>
    </form>
    <p class="mt-6 text-center text-sm text-muted-foreground">Already have an account? <NuxtLink class="font-semibold text-primary hover:underline" to="/login">Sign in</NuxtLink></p>
  </section>
</template>
