import { expect, test } from '@playwright/test'

test('registers an animal and schedules its first task', async ({ page }) => {
  const earTag = `E2E-${Date.now()}`
  const taskTitle = `Health check for ${earTag}`
  const dueDate = new Date()
  dueDate.setDate(dueDate.getDate() + 7)

  await page.goto('/animals/new')
  await page.getByLabel('Ear tag', { exact: true }).fill(earTag)
  await page.getByLabel('Name', { exact: true }).fill('Playwright Ewe')
  await page.getByRole('combobox', { name: 'Sex', exact: true }).selectOption('female')
  await page.getByRole('textbox', { name: 'Breed', exact: true }).fill('Dorper')
  await page.getByRole('combobox', { name: 'Flock', exact: true }).selectOption({ label: 'Breeding Ewes' })
  await page.getByRole('button', { name: 'Register animal' }).click()

  await expect(page).toHaveURL('/animals')
  await page.getByRole('link', { name: earTag, exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Playwright Ewe' })).toBeVisible()

  await page.getByRole('link', { name: 'Schedule task' }).click()
  await page.getByRole('textbox', { name: 'Due date', exact: true }).fill(dueDate.toISOString().slice(0, 10))
  await page.getByRole('textbox', { name: 'Title', exact: true }).fill(taskTitle)
  await page.getByRole('button', { name: 'Schedule task' }).click()

  await expect(page.getByRole('heading', { name: 'Playwright Ewe' })).toBeVisible()
  await expect(page.getByRole('heading', { name: taskTitle })).toBeVisible()
})

test('downloads a farm-scoped animal report', async ({ page }) => {
  await page.goto('/reports')
  await expect(page.getByRole('heading', { name: 'Reports & analytics' })).toBeVisible()

  const downloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: 'animals', exact: true }).click()
  const download = await downloadPromise

  expect(download.suggestedFilename()).toBe('animals-report.csv')
  const stream = await download.createReadStream()
  const chunks: Buffer[] = []
  for await (const chunk of stream) chunks.push(Buffer.from(chunk))
  expect(Buffer.concat(chunks).toString('utf8')).toContain('SH-001')
})

test('prevents a worker from managing the farm team', async ({ browser }) => {
  const context = await browser.newContext()
  const page = await context.newPage()
  const username = `${process.env.E2E_USERNAME || 'e2e-owner'}-worker`
  const password = process.env.E2E_PASSWORD || 'e2e-password-2026'

  await page.goto('/login')
  await page.getByLabel('Username').fill(username)
  await page.getByLabel('Password').fill(password)
  await page.getByRole('button', { name: 'Sign in' }).click()
  await expect(page.getByRole('heading', { name: 'Good morning' })).toBeVisible()

  await page.goto('/settings/team')
  await expect(page.getByRole('alert')).toContainText(
    'Only farm owners and managers can manage the team.',
  )

  await context.close()
})
