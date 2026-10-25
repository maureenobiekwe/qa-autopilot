import { test, expect } from '@playwright/test';

// Starter auth regression. Adjust selectors/copy to the product's real UI and spec numbers.
const email = process.env.QA_EMAIL!;
const password = process.env.QA_PASSWORD!;

test.describe('Auth regression', () => {
  test('AUTH-TC-001 valid login lands on dashboard', async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel(/email/i).fill(email);
    await page.getByLabel(/password/i).fill(password);
    await page.getByRole('button', { name: /log in|sign in/i }).click();
    await expect(page).not.toHaveURL(/login/);
  });

  test('AUTH-TC-002 wrong password and unknown email show the same message', async ({ page }) => {
    const tryLogin = async (e: string, p: string) => {
      await page.goto('/login');
      await page.getByLabel(/email/i).fill(e);
      await page.getByLabel(/password/i).fill(p);
      await page.getByRole('button', { name: /log in|sign in/i }).click();
      return page.getByRole('alert').innerText();
    };
    const wrongPass = await tryLogin(email, 'WrongPass!123');
    const unknown = await tryLogin(`qa+nobody${Date.now()}@example.com`, 'WrongPass!123');
    expect(wrongPass).toBe(unknown); // no user enumeration
  });

  test('AUTH-TC-003 protected route redirects when logged out', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/login/);
  });

  test('AUTH-TC-004 protected API rejects missing and tampered tokens', async ({ request }) => {
    const api = process.env.API_BASE_URL;
    const none = await request.get(`${api}/me`);
    expect(none.status()).toBe(401);
    const tampered = await request.get(`${api}/me`, {
      headers: { Authorization: 'Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJhZG1pbiJ9.bad' },
    });
    expect(tampered.status()).toBe(401);
  });

  test('AUTH-TC-005 XSS in email field is not executed', async ({ page }) => {
    let dialogFired = false;
    page.on('dialog', d => { dialogFired = true; d.dismiss(); });
    await page.goto('/login');
    await page.getByLabel(/email/i).fill('<script>alert(1)</script>');
    await page.getByLabel(/password/i).fill('x');
    await page.getByRole('button', { name: /log in|sign in/i }).click();
    expect(dialogFired).toBe(false);
  });
});
