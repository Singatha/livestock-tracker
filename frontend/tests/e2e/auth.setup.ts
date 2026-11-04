import { mkdir } from 'node:fs/promises'
import { dirname } from 'node:path'
import { expect, test as setup } from '@playwright/test'

const authFile = 'tests/e2e/.auth/owner.json'

setup('sign in as the farm owner', async ({ page }) => {
  const username = process.env.E2E_USERNAME || 'e2e-owner'
  const password = process.env.E2E_PASSWORD || 'e2e-password-2026'

  await page.goto('/login')
  await page.getByLabel('Username').fill(username)
  await page.getByLabel('Password').fill(password)
  await page.getByRole('button', { name: 'Sign in' }).click()

  await expect(page).toHaveURL('/')
  await expect(page.getByRole('heading', { name: 'Good morning' })).toBeVisible()
  await expect(page.getByLabel('Selected farm')).toHaveValue(/.+/)

  await mkdir(dirname(authFile), { recursive: true })
  await page.context().storageState({ path: authFile })
})
