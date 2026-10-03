import { randomUUID } from 'node:crypto';
import { expect, type Page } from '@playwright/test';

export function newAccount() {
  return {
    email: `e2e-${randomUUID()}@example.com`,
    password: `E2e!${randomUUID()}`,
  };
}

export function apiResponse(page: Page, method: string, path: string, status = 200) {
  return page.waitForResponse(response =>
    new URL(response.url()).pathname === `/api/v1${path}` &&
    response.request().method() === method && response.status() === status,
  );
}

export async function listRendered(page: Page) {
  // Both alternatives are success states from TodoList/TodoPage, not a
  // requirement that a newly registered account has an empty list.
  await expect(page.getByText('No todos yet', { exact: true }).or(
    page.getByText(/^Showing \d+ of \d+ todos$/),
  )).toBeVisible();
  await expect(page.getByText('Loading todos...', { exact: true })).toBeHidden();
  await expect(page.getByText('Failed to load todos. Please try again.')).toBeHidden();
}

export async function authenticate(
  page: Page,
  account: ReturnType<typeof newAccount>,
  mode: 'register' | 'login',
) {
  await page.goto(`/${mode}`);
  await page.getByLabel('Email', { exact: true }).fill(account.email);
  await page.getByLabel('Password', { exact: true }).fill(account.password);
  if (mode === 'register') {
    await page.getByLabel('Confirm Password', { exact: true }).fill(account.password);
  }
  await Promise.all([
    apiResponse(page, 'POST', `/auth/${mode}`, mode === 'register' ? 201 : 200),
    apiResponse(page, 'GET', '/todos').then(response => response.finished()),
    page.getByRole('button', {
      name: mode === 'register' ? 'Create Account' : 'Sign In', exact: true,
    }).click(),
  ]);
  await expect(page).toHaveURL(/\/$/);
  await expect(page.getByRole('banner').getByText(account.email, { exact: true })).toBeVisible();
  await listRendered(page);
}

export async function logout(page: Page) {
  await Promise.all([
    apiResponse(page, 'POST', '/auth/logout'),
    page.getByRole('button', { name: 'Logout', exact: true }).click(),
  ]);
  await expect(page).toHaveURL(/\/login$/);
  await expect(page.getByRole('button', { name: 'Sign In', exact: true })).toBeVisible();
}

export async function createTodo(page: Page, title: string, description: string) {
  await page.getByRole('button', { name: 'Add Todo', exact: true }).click();
  const dialog = page.getByRole('dialog', { name: 'Create Todo', exact: true });
  await dialog.getByLabel('Title', { exact: true }).fill(title);
  await dialog.getByLabel('Description (optional)', { exact: true }).fill(description);
  const [created] = await Promise.all([
    apiResponse(page, 'POST', '/todos', 201),
    apiResponse(page, 'GET', '/todos').then(response => response.finished()),
    dialog.getByRole('button', { name: 'Create', exact: true }).click(),
  ]);
  await expect(dialog).toBeHidden();
  await listRendered(page);
  await expect(page.getByRole('checkbox', { name: title, exact: true })).toBeVisible();
  await expect(page.getByText(description, { exact: true })).toBeVisible();
  return await created.json() as { id: string };
}
