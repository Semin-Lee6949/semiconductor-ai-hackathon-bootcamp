import { expect, test } from '@playwright/test'

test('complete the evidence-led scenario', async ({ page }, testInfo) => {
  const errors: string[] = []
  page.on('console', (message) => { if (message.type() === 'error') errors.push(message.text()) })
  await page.route('**/api/sessions/*/coach', async (route) => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ model: 'qwen2.5:1.5b', response: '가설 1은 Dose 변화, 가설 2는 현상 균일도, 가설 3은 측정 편향입니다. 각각을 대조군과 위치별 분포로 반증하세요.' }),
  }))
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
  await page.reload()
  await expect(page.getByRole('heading', { name: 'LLM Coach' })).toBeVisible()
  await expect(page.getByText('이전 실험을 복원했어.')).toBeVisible()
  await page.getByRole('button', { name: /EVIDENCE/ }).click()
  await expect(page.getByRole('dialog', { name: 'Evidence trail' })).toContainText('Lot 보류 후 분포 확인')
  await page.getByRole('button', { name: 'Evidence 닫기' }).click()
  await expect(page.getByText('OLLAMA EVIDENCE MENTOR', { exact: true })).toBeVisible()
  await page.getByRole('button', { name: /검증 프레임 \+ Ollama 질문 생성/ }).click()
  await expect(page.locator('.mentor-answer')).toContainText('가설 1은 Dose 변화')
  await page.getByRole('button', { name: '수정 채택' }).click()
  await page.getByRole('button', { name: /판단을 기록하고/ }).click()
  await expect(page.getByText('WAFER MAP', { exact: true })).toBeVisible()
  await page.getByRole('button', { name: '분포로 판단' }).click()
  await page.getByRole('button', { name: /판단을 기록하고/ }).click()
  await expect(page.getByText('SCREENING DOE', { exact: true })).toBeVisible()
  await page.getByRole('button', { name: /대조군.*Screening/ }).click()
  await page.getByRole('button', { name: /판단을 기록하고/ }).click()
  await expect(page.getByText('ANALYSIS TOOL BAY', { exact: true })).toBeVisible()
  await page.screenshot({ path: testInfo.outputPath('analysis-stage.png'), fullPage: true })
  await page.getByRole('button', { name: /이 분석 조합/ }).click()
  await page.getByRole('button', { name: /판단을 기록하고/ }).click()
  await expect(page.getByText('HOLDOUT GATE', { exact: true })).toBeVisible()
  await page.getByRole('button', { name: /한정 적용/ }).click()
  await page.getByRole('button', { name: /판단을 기록하고/ }).click()
  await expect(page.getByText('시나리오 해결 · 입력 증거 기준')).toBeVisible()
  await page.getByLabel('내 판단·배운 점·한계').fill('평균값만 보지 않고 위치별 분포와 대안 가설을 확인한 뒤 최소 분석으로 검증하는 접근이 중요하다고 판단했다.')
  const downloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: /Base64 HTML 면접 슬라이드/ }).click()
  const download = await downloadPromise
  expect(download.suggestedFilename()).toBe('virtual-fab-interview-slides.html')
  await page.screenshot({ path: testInfo.outputPath('complete.png'), fullPage: true })
  expect(errors).toEqual([])
})
