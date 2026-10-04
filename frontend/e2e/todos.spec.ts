import { randomUUID } from 'node:crypto';
import { test, expect, type BrowserContext } from '@playwright/test';
import { authenticate, apiResponse, createTodo, listRendered, logout, newAccount } from './helpers';

test('Full User Journey: register, login, create, complete, reload and logout', async ({ page }) => {
  const account = newAccount();
  const title = `Journey ${randomUUID()}`;
  const description = `Description ${randomUUID()}`;
  await authenticate(page, account, 'register');
  await logout(page);
  await authenticate(page, account, 'login');
  const todo = await createTodo(page, title, description);
  const checkbox = page.getByRole('checkbox', { name: title, exact: true });
  await expect(checkbox).not.toBeChecked();
  await Promise.all([
    apiResponse(page, 'PUT', `/todos/${todo.id}`),
    apiResponse(page, 'GET', '/todos').then(response => response.finished()),
    checkbox.click(),
  ]);
  await expect(checkbox).toBeChecked();
  await Promise.all([
    apiResponse(page, 'GET', '/todos').then(response => response.finished()),
    page.reload(),
  ]);
  await listRendered(page);
  await expect(checkbox).toBeChecked();
  await expect(page.getByText(description, { exact: true })).toBeVisible();
  await logout(page);
});

test('Cross-User Data Isolation: B cannot see A private todo in an independent session', async (
  { browser, baseURL }, testInfo,
) => {
  const contexts: BrowserContext[] = [];
  let failed = true;
  try {
    for (const name of ['user-a', 'user-b']) {
      const context = await browser.newContext({
        baseURL,
        recordVideo: { dir: testInfo.outputPath(name) },
      });
      contexts.push(context);
    }
    const pageA = await contexts[0].newPage();
    const pageB = await contexts[1].newPage();
    const userA = newAccount();
    const userB = newAccount();
    const title = `Private ${randomUUID()}`;
    await authenticate(pageA, userA, 'register');
    await createTodo(pageA, title, `Private description ${randomUUID()}`);
    await authenticate(pageB, userB, 'register');
    await logout(pageB);
    // Registration auto-login is deliberately not used as the login assertion.
    await authenticate(pageB, userB, 'login');
    await expect(pageB.getByRole('checkbox', { name: title, exact: true })).toHaveCount(0);
    await expect(pageB.getByText(title, { exact: true })).toHaveCount(0);
    await expect(pageA.getByRole('checkbox', { name: title, exact: true })).toBeVisible();
    failed = false;
  } finally {
    await Promise.all(contexts.map(async (context, index) => {
      const pages = context.pages();
      try {
        if (failed) {
          for (const [pageIndex, page] of pages.entries()) {
            await page.screenshot({ path: testInfo.outputPath(`user-${index}-${pageIndex}.png`) });
          }
        }
      } finally {
        await context.close();
        if (!failed) {
          await Promise.all(pages.map(page => page.video()?.delete()));
        }
      }
    }));
  }
});
