import { queryClient } from "@/lib/queryClient";

export function replaceAuthSession(
  accessToken: string,
  refreshToken: string
) {
  queryClient.clear();
  localStorage.setItem("access_token", accessToken);
  localStorage.setItem("refresh_token", refreshToken);
}

export function clearAuthSession() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  queryClient.clear();
}
