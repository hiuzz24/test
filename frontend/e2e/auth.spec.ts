import { test, expect } from '@playwright/test';
import { authenticate, apiResponse, logout, newAccount } from './helpers';

for (const scenario of ['wrong password', 'unknown email'] as const) {
  test(`Login ${scenario}: generic toast without document reload`, async ({ page }) => {
    const account = newAccount();
    await authenticate(page, account, 'register');
    await logout(page);
    const email = scenario === 'wrong password' ? account.email : newAccount().email;
    await page.getByLabel('Email', { exact: true }).fill(email);
    await page.getByLabel('Password', { exact: true }).fill('Intentionally-wrong!123');
    const documentRequests: string[] = [];
    page.on('request', request => {
      if (request.isNavigationRequest() && request.frame() === page.mainFrame()) {
        documentRequests.push(request.url());
      }
    });

    const [response] = await Promise.all([
      apiResponse(page, 'POST', '/auth/login', 401),
      page.getByRole('button', { name: 'Sign In', exact: true }).click(),
    ]);
    expect(await response.json()).toEqual({ detail: 'Invalid email or password' });
    await expect(page.getByText('Invalid email or password', { exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Sign In', exact: true })).toBeEnabled();
    await expect(page.getByLabel('Email', { exact: true })).toHaveValue(email);
    expect(documentRequests).toEqual([]);
  });
}
