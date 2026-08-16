import { expect, test } from '@playwright/test'

test('complete the evidence-led scenario', async ({ page }, testInfo) => {
  const errors: string[] = []
  page.on('console', (message) => { if (message.type() === 'error') errors.push(message.text()) })
  await page.goto('/')
  await expect(page.getByText('사라진 선폭의 비밀')).toBeVisible()
  await expect(page.locator('.station-tag')).toHaveCount(6)
  await page.waitForTimeout(800)
  await page.screenshot({ path: testInfo.outputPath('first-viewport.png'), fullPage: true })

  if (testInfo.project.name === 'mobile') {
    await expect(page.locator('.workbench')).toBeVisible()
    expect(errors).toEqual([])
    return
  }

  await page.getByRole('button', { name: /Lot 보류/ }).click()
  await page.getByRole('button', { name: /판단을 기록하고/ }).click()
  await expect(page.getByRole('heading', { name: 'LLM Coach' })).toBeVisible()
  await page.getByRole('button', { name: '수정 채택' }).click()
  await page.getByRole('button', { name: /판단을 기록하고/ }).click()
  await page.getByRole('button', { name: '분포로 판단' }).click()
  await page.getByRole('button', { name: /판단을 기록하고/ }).click()
  await page.getByRole('button', { name: /대조군.*Screening/ }).click()
  await page.getByRole('button', { name: /판단을 기록하고/ }).click()
  await page.getByRole('button', { name: /이 분석 조합/ }).click()
  await page.getByRole('button', { name: /판단을 기록하고/ }).click()
  await page.getByRole('button', { name: /한정 적용/ }).click()
  await page.getByRole('button', { name: /판단을 기록하고/ }).click()
  await expect(page.getByText('시나리오 해결 · 입력 증거 기준')).toBeVisible()
  await page.screenshot({ path: testInfo.outputPath('complete.png'), fullPage: true })
  expect(errors).toEqual([])
})
