import api from "../api";
import type { VoteCreateInput } from "@/types";

export async function vote(data: VoteCreateInput): Promise<void> {
  await api.post("/votes", data);
}

export async function removeVote(targetType: string, targetId: string): Promise<void> {
  await api.delete("/votes", {
    params: { target_type: targetType, target_id: targetId },
  });
}
