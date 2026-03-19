export async function signIn(provider, { callbackUrl = '/home' } = {}) {
  const res = await fetch('/api/auth/csrf');
  const { csrfToken } = await res.json();

  const form = document.createElement('form');
  form.method = 'POST';
  form.action = `/api/auth/signin/${provider}`;
  form.style.display = 'none';

  for (const [name, value] of Object.entries({ csrfToken, callbackUrl })) {
    const input = document.createElement('input');
    input.type = 'hidden';
    input.name = name;
    input.value = value;
    form.appendChild(input);
  }

  document.body.appendChild(form);
  form.submit();
}

export async function signOut({ callbackUrl = '/' } = {}) {
  const res = await fetch('/api/auth/csrf');
  const { csrfToken } = await res.json();

  const form = document.createElement('form');
  form.method = 'POST';
  form.action = '/api/auth/signout';
  form.style.display = 'none';

  for (const [name, value] of Object.entries({ csrfToken, callbackUrl })) {
    const input = document.createElement('input');
    input.type = 'hidden';
    input.name = name;
    input.value = value;
    form.appendChild(input);
  }

  document.body.appendChild(form);
  form.submit();
}

export async function getSession() {
  const res = await fetch('/api/auth/session');
  const session = await res.json();
  return session?.user ? session : null;
}
