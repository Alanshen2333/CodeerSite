import api from "../api";
import type { SshKey, CreateSshKeyInput } from "@/types/user";

export async function getSshKeys(): Promise<{ keys: SshKey[] }> {
  const res = await api.get<{ keys: SshKey[] }>("/auth/ssh-keys");
  return res.data;
}

export async function createSshKey(data: CreateSshKeyInput): Promise<{ key: SshKey }> {
  const res = await api.post<{ key: SshKey }>("/auth/ssh-keys", data);
  return res.data;
}

export async function deleteSshKey(id: string): Promise<void> {
  await api.delete(`/auth/ssh-keys/${id}`);
}
