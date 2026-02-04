const baseUrl = import.meta.env.VITE_API_BASE_URL;

export async function getHealth() {
  const res = await fetch(`${baseUrl}/health`);
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
  return res.json() as Promise<{ status: string }>;
}
